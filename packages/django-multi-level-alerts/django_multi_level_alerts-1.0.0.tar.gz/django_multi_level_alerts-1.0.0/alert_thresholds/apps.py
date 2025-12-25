"""
Django AppConfig for alert_thresholds package.
"""
from django.apps import AppConfig


class AlertThresholdsConfig(AppConfig):
    name = 'alert_thresholds'
    verbose_name = 'Alert Thresholds'
    default_auto_field = 'django.db.models.BigAutoField'

    def ready(self):
        from django.db.models.signals import post_migrate
        post_migrate.connect(self._on_post_migrate, sender=self)

    def _on_post_migrate(self, sender, **kwargs):
        self._sync_metrics_from_settings()

    def _sync_metrics_from_settings(self):
        from django.contrib.contenttypes.models import ContentType
        from .conf import alert_settings
        from .models import AlertMetricDefinition

        synced = 0
        for code, config in alert_settings.metrics.items():
            metric, created = AlertMetricDefinition.objects.update_or_create(
                code=code,
                defaults={
                    'label': config.get('label', code),
                    'description': config.get('description', ''),
                    'default_operator': config.get('default_operator', 'gte'),
                    'from_settings': True,
                    'is_active': True,
                }
            )

            models_list = config.get('models', [])
            if models_list and models_list != ['*']:
                content_types = []
                for model_path in models_list:
                    try:
                        app_label, model_name = model_path.rsplit('.', 1)
                        ct = ContentType.objects.get(
                            app_label=app_label.lower(),
                            model=model_name.lower()
                        )
                        content_types.append(ct)
                    except (ValueError, ContentType.DoesNotExist):
                        pass
                if content_types:
                    metric.applicable_content_types.set(content_types)
            else:
                metric.applicable_content_types.clear()
            if created:
                synced += 1

        if synced > 0:
            print(f"[alert_thresholds] Synced {synced} new metric(s) from settings")
