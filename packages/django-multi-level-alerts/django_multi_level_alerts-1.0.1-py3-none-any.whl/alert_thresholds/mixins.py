from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models

from .choices import AlertLevel
from .conf import alert_settings


class AlertThresholdMixin(models.Model):
    """
    Mixin to add alert threshold functionality to any model.

    Usage:
        class MyModel(AlertThresholdMixin, models.Model):
            name = models.CharField(max_length=100)
            # ... other fields

    Then you can:
        obj = MyModel.objects.get(pk=1)
        obj.get_threshold('max_price_diff_pct', AlertLevel.CRITICAL)
        obj.check_threshold_exceeded('max_price_diff_pct', current_value=0.15)
    """
    alert_thresholds = GenericRelation(
        'alert_thresholds.AlertThreshold',
        content_type_field='content_type',
        object_id_field='object_id'
    )

    class Meta:
        abstract = True

    def get_applicable_metrics(self):
        from .models import AlertMetricDefinition

        model_label = f"{self._meta.app_label}.{self._meta.model_name}"
        ct = ContentType.objects.get_for_model(self)

        db_metrics = AlertMetricDefinition.objects.filter(
            is_active=True
        ).filter(
            models.Q(applicable_content_types__isnull=True) |
            models.Q(applicable_content_types=ct)
        ).distinct()

        return db_metrics

    def get_threshold(self, metric_code, level):
        """
        Get threshold value for a specific metric and level.

        Args:
            metric_code: The metric code (e.g., 'max_price_diff_pct')
            level: AlertLevel value (e.g., AlertLevel.CRITICAL)

        Returns:
            Decimal threshold value or None if not set
        """
        try:
            threshold = self.alert_thresholds.select_related('metric').get(
                metric__code=metric_code,
                level=level
            )
            return threshold.threshold_value
        except self.alert_thresholds.model.DoesNotExist:
            return None

    def get_thresholds_for_metric(self, metric_code):
        """
        Get all threshold levels for a specific metric.

        Returns:
            dict with keys: 'info', 'warning', 'critical', 'emergency'
        """
        thresholds = self.alert_thresholds.filter(
            metric__code=metric_code
        ).select_related('metric')

        result = {
            'info': None,
            'warning': None,
            'critical': None,
            'emergency': None,
        }

        level_map = {
            AlertLevel.INFO: 'info',
            AlertLevel.WARNING: 'warning',
            AlertLevel.CRITICAL: 'critical',
            AlertLevel.EMERGENCY: 'emergency',
        }

        for threshold in thresholds:
            key = level_map.get(threshold.level)
            if key:
                result[key] = threshold.threshold_value

        return result

    def get_all_thresholds(self):
        """
        Get all thresholds for this object, organized by metric.

        Returns:
            dict: {metric_code: {'info': val, 'warning': val, ...}, ...}
        """
        thresholds = self.alert_thresholds.select_related('metric').all()

        result = {}
        for threshold in thresholds:
            code = threshold.metric.code
            if code not in result:
                result[code] = {
                    'info': None,
                    'warning': None,
                    'critical': None,
                    'emergency': None,
                }

            level_map = {
                AlertLevel.INFO: 'info',
                AlertLevel.WARNING: 'warning',
                AlertLevel.CRITICAL: 'critical',
                AlertLevel.EMERGENCY: 'emergency',
            }
            key = level_map.get(threshold.level)
            if key:
                result[code][key] = threshold.threshold_value

        return result

    def check_threshold_exceeded(self, metric_code, current_value):
        """
        Check if current_value exceeds any threshold for the given metric.

        Returns:
            The highest AlertLevel triggered, or None if no thresholds exceeded.
        """
        thresholds = self.alert_thresholds.filter(
            metric__code=metric_code
        ).select_related('metric').order_by('-level')

        for threshold in thresholds:
            if threshold.check_condition(current_value):
                return threshold.level

        return None

    def get_triggered_threshold(self, metric_code, current_value):
        """
        Check thresholds and return both the level and threshold object.

        Returns:
            tuple: (AlertLevel, AlertThreshold) or (None, None)
        """
        thresholds = self.alert_thresholds.filter(
            metric__code=metric_code
        ).select_related('metric').order_by('-level')

        for threshold in thresholds:
            if threshold.check_condition(current_value):
                return threshold.level, threshold

        return None, None

    def create_default_thresholds(self):
        """
        Create default threshold records for all applicable metrics.
        Called automatically if auto_create_thresholds is enabled.
        """
        from .models import AlertMetricDefinition, AlertThreshold

        ct = ContentType.objects.get_for_model(self)
        metrics = self.get_applicable_metrics()

        created_count = 0
        for metric in metrics:
            for level in AlertLevel.values:
                _, created = AlertThreshold.objects.get_or_create(
                    content_type=ct,
                    object_id=self.pk,
                    metric=metric,
                    level=level,
                    defaults={
                        'threshold_value': None,
                        'operator': metric.default_operator,
                    }
                )
                if created:
                    created_count += 1

        return created_count

    @staticmethod
    def get_alert_level_name(level):
        """Get the display name for an alert level"""
        level_map = {
            AlertLevel.INFO: 'Info',
            AlertLevel.WARNING: 'Warning',
            AlertLevel.CRITICAL: 'Critical',
            AlertLevel.EMERGENCY: 'Emergency',
        }
        return level_map.get(level)
