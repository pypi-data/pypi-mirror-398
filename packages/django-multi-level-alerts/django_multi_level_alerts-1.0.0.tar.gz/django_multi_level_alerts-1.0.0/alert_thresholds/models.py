from decimal import Decimal

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from .choices import AlertLevel, AlertOperator


class AlertMetricDefinition(models.Model):
    code = models.CharField(
        max_length=50,
        unique=True,
        help_text="Unique identifier for this metric (e.g., 'max_price_diff_pct')"
    )
    label = models.CharField(
        max_length=100,
        help_text="Human-readable label (e.g., 'Max Price Difference %')"
    )
    description = models.TextField(
        blank=True,
        help_text="Detailed description of what this metric measures"
    )
    default_operator = models.CharField(
        max_length=10,
        choices=AlertOperator.choices,
        default=AlertOperator.GREATER_THAN_OR_EQUAL,
        help_text="Default comparison operator for this metric"
    )
    applicable_content_types = models.ManyToManyField(
        ContentType,
        blank=True,
        related_name='alert_metrics',
        help_text="Models that can use this metric. Leave empty for all models."
    )

    from_settings = models.BooleanField(
        default=False,
        help_text="True if this metric was synced from settings.py"
    )

    is_active = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['label']
        verbose_name = 'Alert Metric'
        verbose_name_plural = 'Alert Metrics'

    def __str__(self):
        return self.label

    def is_applicable_to(self, model_or_instance):
        """Check if this metric can be used with a given model"""
        if not self.applicable_content_types.exists():
            return True  # No restrictions = applicable to all

        if isinstance(model_or_instance, models.Model):
            ct = ContentType.objects.get_for_model(model_or_instance)
        else:
            ct = ContentType.objects.get_for_model(model_or_instance)

        return self.applicable_content_types.filter(pk=ct.pk).exists()


class AlertThreshold(models.Model):
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name='alert_thresholds'
    )
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    metric = models.ForeignKey(
        AlertMetricDefinition,
        on_delete=models.CASCADE,
        related_name='thresholds'
    )
    level = models.IntegerField(
        choices=AlertLevel.choices,
        help_text="Alert severity level"
    )
    threshold_value = models.DecimalField(
        max_digits=24,
        decimal_places=8,
        null=True,
        blank=True,
        help_text="Threshold value. Leave empty to disable this alert level."
    )
    operator = models.CharField(
        max_length=10,
        choices=AlertOperator.choices,
        default=AlertOperator.GREATER_THAN_OR_EQUAL,
        help_text="Comparison operator for threshold check"
    )

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [['content_type', 'object_id', 'metric', 'level']]
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['metric', 'level']),
        ]
        ordering = ['metric', 'level']
        verbose_name = 'Alert Threshold'
        verbose_name_plural = 'Alert Thresholds'

    def __str__(self):
        op_display = self.get_operator_display()
        value = self.threshold_value if self.threshold_value is not None else 'Not set'
        return f"{self.metric.label} - {self.get_level_display()}: {op_display} {value}"

    def save(self, *args, **kwargs):
        # Set operator from metric default if not specified
        if not self.operator and self.metric:
            self.operator = self.metric.default_operator
        super().save(*args, **kwargs)

    def check_condition(self, current_value) -> bool:
        if self.threshold_value is None:
            return False

        try:
            current = Decimal(str(current_value))
            threshold = self.threshold_value
        except (ValueError, TypeError):
            return False

        operator_checks = {
            AlertOperator.GREATER_THAN: current > threshold,
            AlertOperator.GREATER_THAN_OR_EQUAL: current >= threshold,
            AlertOperator.LESS_THAN: current < threshold,
            AlertOperator.LESS_THAN_OR_EQUAL: current <= threshold,
            AlertOperator.EQUAL: current == threshold,
            AlertOperator.NOT_EQUAL: current != threshold,
        }

        return operator_checks.get(self.operator, False)

    @classmethod
    def get_for_object(cls, obj, metric_code=None):
        ct = ContentType.objects.get_for_model(obj)
        qs = cls.objects.filter(content_type=ct, object_id=obj.pk)

        if metric_code:
            qs = qs.filter(metric__code=metric_code)

        return qs.select_related('metric')

    @classmethod
    def check_all_thresholds(cls, obj, metric_code, current_value):
        thresholds = cls.get_for_object(obj, metric_code).order_by('-level')

        for threshold in thresholds:
            if threshold.check_condition(current_value):
                return threshold.level, threshold

        return None, None
