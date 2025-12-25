"""
Configuration handler for alert_thresholds package.

Projects can define metrics in settings.py like:

ALERT_THRESHOLDS = {
    'metrics': {
        'max_price_diff_pct': {
            'label': 'Max Price Difference %',
            'default_operator': 'gte',
            'description': 'Alert when price difference exceeds threshold',
            'models': ['myapp.MyModel'],
        },
        'min_acceptable_pnl': {
            'label': 'Min Acceptable PnL',
            'default_operator': 'lt',
            'description': 'Alert when PnL drops below threshold',
            'models': ['myapp.Account', 'myapp.Portfolio'],
        },
    },
    'auto_create_thresholds': True,  # Auto-create threshold records for new objects
    'sync_on_startup': True,  # Sync settings metrics to DB on app ready
}
"""
from django.conf import settings

DEFAULTS = {
    'metrics': {},
    'auto_create_thresholds': True,
    'sync_on_startup': True,
}


class AlertThresholdsSettings:
    def __init__(self):
        self._settings = None

    @property
    def settings(self):
        if self._settings is None:
            user_settings = getattr(settings, 'ALERT_THRESHOLDS', {})
            self._settings = {**DEFAULTS, **user_settings}
        return self._settings

    @property
    def metrics(self):
        return self.settings.get('metrics', {})

    @property
    def auto_create_thresholds(self):
        return self.settings.get('auto_create_thresholds', True)

    @property
    def sync_on_startup(self):
        return self.settings.get('sync_on_startup', True)

    def get_metrics_for_model(self, model_label):
        result = []
        for code, config in self.metrics.items():
            models = config.get('models', [])
            if model_label in models or '*' in models:
                result.append(code)
        return result

    def get_metric_config(self, code):
        return self.metrics.get(code, {})

    def reload(self):
        self._settings = None


alert_settings = AlertThresholdsSettings()
