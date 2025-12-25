from contextlib import suppress
from datetime import date, timedelta
from types import DynamicClassAttribute
from typing import Any, Self

from celery import shared_task
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.template import Context, Template
from django.utils.translation import gettext_lazy as _
from pandas._libs.tslibs.offsets import BDay
from psycopg.types.range import DateRange
from wbcore.contrib.color.enums import WBColor
from wbcore.contrib.icons import WBIcon
from wbcore.models import WBModel
from wbcore.utils.models import ComplexToStringMixin
from wbcore.workers import Queue

from .incidents import CheckedObjectIncidentRelationship, RiskIncident, RiskIncidentType


class RiskCheckManager(models.Manager):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .annotate(
                passive_check=models.Case(
                    models.When(
                        models.Q(activator_id__isnull=True) & models.Q(activator_content_type__isnull=True),
                        then=models.Value(True),
                    ),
                    default=models.Value(False),
                )
            )
        )


class PassiveRiskCheckManager(RiskCheckManager):
    def get_queryset(self):
        return super().get_queryset().filter(passive_check=True)


class RiskCheck(ComplexToStringMixin, WBModel):
    class CheckStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        RUNNING = "RUNNING", "Running"
        FAILED = "FAILED", "Failed"
        SUCCESS = "SUCCESS", "Success"
        WARNING = "WARNING", "Warning"

        @DynamicClassAttribute
        def icon(self):
            return {
                "PENDING": WBIcon.PENDING.icon,
                "RUNNING": WBIcon.RUNNING.icon,
                "FAILED": WBIcon.REJECT.icon,
                "SUCCESS": WBIcon.CONFIRM.icon,
                "WARNING": WBIcon.WARNING.icon,
            }[self.value]

        @DynamicClassAttribute
        def color(self):
            return {
                "PENDING": WBColor.YELLOW_LIGHT.value,
                "RUNNING": WBColor.BLUE_LIGHT.value,
                "FAILED": WBColor.RED_LIGHT.value,
                "SUCCESS": WBColor.GREEN_LIGHT.value,
                "WARNING": WBColor.YELLOW_DARK.value,
            }[self.value]

    rule = models.ForeignKey(to="wbcompliance.RiskRule", related_name="checks", on_delete=models.CASCADE)

    creation_datetime = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Creation Date"),
        help_text=_("Time at which the check was created/triggered"),
    )
    evaluation_date = models.DateField(
        verbose_name=_("Evaluation Date"), help_text=_("The date at which the rule was evaluated")
    )

    checked_object_content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, related_name="triggered_checks"
    )
    checked_object_id = models.PositiveIntegerField()
    checked_object = GenericForeignKey("checked_object_content_type", "checked_object_id")
    checked_object_repr = models.CharField(max_length=256, blank=True, null=True)

    status = models.CharField(
        max_length=32, default=CheckStatus.PENDING, choices=CheckStatus.choices, verbose_name=_("Status")
    )
    activator_content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, max_length=256, blank=True, null=True
    )
    activator_id = models.PositiveIntegerField(blank=True, null=True)
    activator = GenericForeignKey("activator_content_type", "activator_id")

    objects = PassiveRiskCheckManager()
    all_objects = RiskCheckManager()

    @property
    def needs_incident(self) -> bool:
        # if the there is a similar checked object relationship, we needs to create a general incident if the check evaluates to a breach
        return (
            self.rule.checked_object_relationships.filter(
                checked_object_content_type=self.checked_object_content_type, checked_object_id=self.checked_object_id
            ).exists()
            or self.precheck
        )

    @property
    def precheck(self) -> bool:
        return self.activator_id is not None

    @property
    def previous_check(self) -> Self | None:
        """
        Property holding the last valid check

        Returns:
            The last valid check
        """
        with suppress(RiskCheck.DoesNotExist):
            return (
                RiskCheck.objects.filter(
                    evaluation_date__lt=self.evaluation_date,
                    rule=self.rule,
                    checked_object_content_type=self.checked_object_content_type,
                    checked_object_id=self.checked_object_id,
                )
                .order_by("-evaluation_date", "-creation_datetime")
                .first()
            )

    def save(self, *args, **kwargs):
        self.checked_object_repr = str(self.checked_object)
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        incidents = RiskIncident.all_objects.filter(
            id__in=list(
                CheckedObjectIncidentRelationship.objects.filter(rule_check_id=self.id).values_list(
                    "incident", flat=True
                )
            )
        )
        super().delete(*args, **kwargs)
        # ensure that incident without subincidents are deleted automatically
        for incident in incidents:
            if not incident.checked_object_relationships.exists():
                incident.delete()

    def compute_str(self) -> str:
        return _("{} - {}").format(
            self.checked_object,
            self.evaluation_date,
        )

    def evaluate(
        self, *explicit_dto, override_incident: bool = False, ignore_informational_threshold: bool = False, **kwargs
    ) -> list[models.Model]:
        """
        Evaluate the check and returns tuple of incidents information
        Args:
            override_incident: True if the existing incident needs to be overriden

        Returns:

        """
        self.status = self.CheckStatus.RUNNING
        self.save()
        rule_backend = self.rule.rule_backend.backend(
            self.evaluation_date, self.checked_object, self.rule.parameters, self.rule.thresholds.all()
        )
        self.status = self.CheckStatus.SUCCESS
        incidents = []
        report_template = Template(self.rule.rule_backend.incident_report_template)
        for incident_result in rule_backend.check_rule(*explicit_dto, **kwargs):
            if (
                ignore_informational_threshold
                and incident_result.severity.is_ignorable
                and incident_result.severity.is_informational
            ):
                self.status = self.CheckStatus.WARNING
            else:
                self.status = self.CheckStatus.FAILED
                # If the check is passive, we aggregated incident per breached object and return it for further processing
            if self.needs_incident:
                report = report_template.render(Context({"report_details": incident_result.report_details}))
                incident, created = self.get_or_create_incident(
                    self.evaluation_date,
                    incident_result.severity,
                    incident_result.breached_object,
                    incident_result.breached_object_repr,
                )
                incident.update_or_create_relationship(
                    self,
                    report,
                    incident_result.report_details,
                    incident_result.breached_value,
                    incident_result.severity,
                    override_incident=override_incident or created,
                )
                incidents.append(incident)
            else:
                # If the check is active, the only thing that matter is whether the check led to incident or not
                report = f"<p><strong>{incident_result.breached_object_repr}</strong>: {incident_result.breached_value}</p>"  # as we do not store the breached object, we need a way to display it in the subincident relationship. This is not optimal though
                CheckedObjectIncidentRelationship.objects.create(
                    rule_check=self,
                    report=report,
                    report_details=incident_result.report_details,
                    breached_value=incident_result.breached_value,
                    severity=incident_result.severity,
                )
        self.save()
        return incidents

    def get_or_create_incident(
        self,
        evaluation_date: date,
        incident_severity: "RiskIncidentType",
        breached_object: Any,
        breached_object_repr: str,
    ) -> tuple[RiskIncident, bool]:
        """
        Utility function to get or create incident base on the given breached object

        Args:
            evaluation_date: The incident date
            incident_severity: The incident severity
            breached_object: The breached object (i.e. the object that triggers the incident)
            breached_object_repr: Its string representation

        Returns:
            A tuple (incident, is_created)
        """

        # Consider that if an incident happens one business day in the future or past, it is continue
        date_range = DateRange(  # type: ignore
            (evaluation_date - BDay(1)).date(), (evaluation_date + BDay(1)).date(), "[]"
        )
        incidents = RiskIncident.objects.filter(rule=self.rule, date_range__overlap=date_range, precheck=self.precheck)
        if breached_object:
            # If a breached_object is provided, we lookup over it
            incidents = incidents.filter(
                breached_content_type=ContentType.objects.get_for_model(breached_object),
                breached_object_id=breached_object.id,
            )
        else:
            # Otherwise, we lookup over its string representation. Might need to change as this is not very robust
            incidents = incidents.filter(
                breached_object_repr=breached_object_repr,
            )
        created = False
        if incident := incidents.first():
            incident.date_range = DateRange(  # type: ignore
                lower=incident.date_range.lower, upper=(evaluation_date + timedelta(days=1))
            )
            incident.severity = incident_severity
        else:
            incident = RiskIncident(
                rule=self.rule,
                date_range=DateRange(lower=evaluation_date, upper=(evaluation_date + timedelta(days=1))),  # type: ignore
                breached_content_type=ContentType.objects.get_for_model(breached_object) if breached_object else None,
                breached_object_id=breached_object.id if breached_object else None,
                breached_object_repr=breached_object_repr,
                severity=incident_severity,
                status=RiskIncident.Status.OPEN,
            )
            created = True

        if self.rule.automatically_close_incident:
            incident.status = RiskIncident.Status.CLOSED
        elif self.precheck:
            incident.status = RiskIncident.Status.IGNORED
        incident.precheck = self.precheck
        incident.save()
        return incident, created

    class Meta:
        verbose_name = "Risk Check"
        verbose_name_plural = "Risk Checks"

    @classmethod
    def get_endpoint_basename(cls) -> str:
        return "wbcompliance:riskcheck"

    @classmethod
    def get_representation_endpoint(cls) -> str:
        return "wbcompliance:riskcheckrepresentation-list"

    @classmethod
    def get_representation_value_key(cls) -> str:
        return "id"


@shared_task(queue=Queue.HIGH_PRIORITY.value)
def evaluate_as_task(
    check_id: int,
    *dto,
    override_incident: bool = False,
    ignore_informational_threshold: bool = False,
    ignore_breached_object_content_types: list[tuple[int, int]] | None = None,
):
    if ignore_breached_object_content_types:
        ignore_breached_objects = [
            ContentType.objects.get(id=r[1]).get_object_for_this_type(id=r[0])
            for r in ignore_breached_object_content_types
        ]
    else:
        ignore_breached_objects = []
    check = RiskCheck.all_objects.get(id=check_id)
    check.evaluate(
        *dto,
        override_incident=override_incident,
        ignore_informational_threshold=ignore_informational_threshold,
        ignore_breached_objects=ignore_breached_objects,
    )
