"""
Management command to sync alert metrics from settings to database.

Usage:
    python manage.py sync_alert_metrics
    python manage.py sync_alert_metrics --clear-unused
"""
from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType

from alert_thresholds.conf import alert_settings
from alert_thresholds.models import AlertMetricDefinition


class Command(BaseCommand):
    help = 'Sync alert metric definitions from settings to database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear-unused',
            action='store_true',
            help='Deactivate metrics from settings that are no longer defined',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        clear_unused = options['clear_unused']

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - No changes will be made'))

        metrics_config = alert_settings.metrics
        created_count = 0
        updated_count = 0
        synced_codes = []

        for code, config in metrics_config.items():
            synced_codes.append(code)

            label = config.get('label', code)
            description = config.get('description', '')
            default_operator = config.get('default_operator', 'gte')
            models_list = config.get('models', [])

            existing = AlertMetricDefinition.objects.filter(code=code).first()

            if existing:
                if not dry_run:
                    existing.label = label
                    existing.description = description
                    existing.default_operator = default_operator
                    existing.from_settings = True
                    existing.is_active = True
                    existing.save()

                    self._update_content_types(existing, models_list)

                self.stdout.write(f'  Updated: {code} -> "{label}"')
                updated_count += 1
            else:
                if not dry_run:
                    metric = AlertMetricDefinition.objects.create(
                        code=code,
                        label=label,
                        description=description,
                        default_operator=default_operator,
                        from_settings=True,
                        is_active=True,
                    )
                    self._update_content_types(metric, models_list)

                self.stdout.write(self.style.SUCCESS(f'  Created: {code} -> "{label}"'))
                created_count += 1

        # Handle unused metrics from settings
        if clear_unused:
            unused = AlertMetricDefinition.objects.filter(
                from_settings=True
            ).exclude(
                code__in=synced_codes
            )

            unused_count = unused.count()
            if unused_count > 0:
                if not dry_run:
                    unused.update(is_active=False)

                for metric in unused:
                    self.stdout.write(self.style.WARNING(f'  Deactivated: {metric.code}'))

                self.stdout.write(f'Deactivated {unused_count} unused metrics')

        # Summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            f'Sync complete: {created_count} created, {updated_count} updated'
        ))

    def _update_content_types(self, metric, models_list):
        """Update the applicable_content_types for a metric"""
        if not models_list or models_list == ['*']:
            metric.applicable_content_types.clear()
            return

        content_types = []
        for model_path in models_list:
            try:
                app_label, model_name = model_path.rsplit('.', 1)
                ct = ContentType.objects.get(
                    app_label=app_label.lower(),
                    model=model_name.lower()
                )
                content_types.append(ct)
            except (ValueError, ContentType.DoesNotExist) as e:
                self.stdout.write(self.style.WARNING(
                    f'    Warning: Could not find model "{model_path}": {e}'
                ))

        if content_types:
            metric.applicable_content_types.set(content_types)
