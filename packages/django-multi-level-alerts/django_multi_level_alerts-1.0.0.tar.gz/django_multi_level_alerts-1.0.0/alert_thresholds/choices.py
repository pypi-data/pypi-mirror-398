from django.db import models


class AlertLevel(models.IntegerChoices):
    INFO = 1, 'Info'
    WARNING = 2, 'Warning'
    CRITICAL = 3, 'Critical'
    EMERGENCY = 4, 'Emergency'


class AlertOperator(models.TextChoices):
    GREATER_THAN = 'gt', 'Greater Than (>)'
    GREATER_THAN_OR_EQUAL = 'gte', 'Greater Than or Equal (≥)'
    LESS_THAN = 'lt', 'Less Than (<)'
    LESS_THAN_OR_EQUAL = 'lte', 'Less Than or Equal (≤)'
    EQUAL = 'eq', 'Equal (=)'
    NOT_EQUAL = 'ne', 'Not Equal (≠)'
