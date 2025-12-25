"""
alert_thresholds - A reusable Django package for managing alert thresholds.

Quick Start:
    1. Add 'alert_thresholds' to INSTALLED_APPS
    2. Run migrations: python manage.py migrate alert_thresholds
    3. Configure metrics in settings.py (optional)
    4. Add AlertThresholdMixin to your models
    5. Add AlertThresholdAdminMixin to your ModelAdmin classes

Example settings.py configuration:

    ALERT_THRESHOLDS = {
        'metrics': {
            'max_price_diff_pct': {
                'label': 'Max Price Difference %',
                'default_operator': 'gte',
                'description': 'Alert when price difference exceeds threshold',
                'models': ['myapp.MyModel'],
            },
        },
        'auto_create_thresholds': True,
        'sync_on_startup': True,
    }

Example model usage:

    from alert_thresholds.mixins import AlertThresholdMixin

    class MyModel(AlertThresholdMixin, models.Model):
        name = models.CharField(max_length=100)

Example admin usage:

    from alert_thresholds.admin import AlertThresholdAdminMixin

    @admin.register(MyModel)
    class MyModelAdmin(AlertThresholdAdminMixin, admin.ModelAdmin):
        list_display = ['name']
"""

default_app_config = 'alert_thresholds.apps.AlertThresholdsConfig'

__version__ = '1.0.0'
