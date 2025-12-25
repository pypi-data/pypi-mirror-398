"""
Django Admin classes for alert_thresholds package.
"""
from decimal import Decimal

from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from .choices import AlertLevel
from .models import AlertMetricDefinition, AlertThreshold


class AlertThresholdInline(GenericTabularInline):
    model = AlertThreshold
    extra = 0
    fields = ['metric', 'level', 'operator', 'threshold_value']
    readonly_fields = ['metric', 'level', 'operator']
    can_delete = False
    ct_field = 'content_type'
    ct_fk_field = 'object_id'

    def has_add_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('metric').order_by('metric__label', 'level')


class AlertThresholdAdminMixin:
    """
    Mixin to add alert threshold management to any ModelAdmin.

    Usage:
        @admin.register(MyModel)
        class MyModelAdmin(AlertThresholdAdminMixin, admin.ModelAdmin):
            list_display = ['name', ...]
    """
    change_form_template = 'admin/alert_thresholds/threshold_change_form.html'

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        if not change and hasattr(obj, 'create_default_thresholds'):
            obj.create_default_thresholds()

        if request.method == 'POST':
            self._save_thresholds_from_post(request, obj)

    def _save_thresholds_from_post(self, request, instance):
        ct = ContentType.objects.get_for_model(instance)

        if hasattr(instance, 'get_applicable_metrics'):
            metrics = instance.get_applicable_metrics()
        else:
            metrics = AlertMetricDefinition.objects.filter(is_active=True)

        for metric in metrics:
            for level in AlertLevel:
                field_name = f'threshold_{metric.code}_{level.value}'
                value = request.POST.get(field_name)

                if value == '':
                    value = None
                elif value:
                    try:
                        value = Decimal(value)
                    except (ValueError, TypeError):
                        value = None

                AlertThreshold.objects.update_or_create(
                    content_type=ct,
                    object_id=instance.pk,
                    metric=metric,
                    level=level.value,
                    defaults={
                        'threshold_value': value,
                        'operator': metric.default_operator,
                    }
                )

    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        extra_context = extra_context or {}

        if object_id:
            obj = self.get_object(request, object_id)
            if obj:
                if hasattr(obj, 'create_default_thresholds'):
                    obj.create_default_thresholds()

                extra_context['alert_thresholds_table'] = self._get_thresholds_table(obj)

        return super().changeform_view(request, object_id, form_url, extra_context)

    def _get_thresholds_table(self, instance):
        if hasattr(instance, 'get_applicable_metrics'):
            metrics = list(instance.get_applicable_metrics())
        else:
            return ''

        if not metrics:
            return ''

        thresholds_dict = {}
        operators_dict = {}

        if hasattr(instance, 'alert_thresholds'):
            for threshold in instance.alert_thresholds.select_related('metric').all():
                key = (threshold.metric.code, threshold.level)
                thresholds_dict[key] = threshold.threshold_value
                operators_dict[threshold.metric.code] = threshold.get_operator_display()

        colors = {
            AlertLevel.INFO: {'light': '#e7f3ff', 'dark': '#2a4365'},
            AlertLevel.WARNING: {'light': '#fff4e5', 'dark': '#663c00'},
            AlertLevel.CRITICAL: {'light': '#fff9e6', 'dark': '#664d03'},
            AlertLevel.EMERGENCY: {'light': '#ffe6e6', 'dark': '#661a1a'},
        }

        style_rules = ''
        for level in AlertLevel:
            style_rules += f'''
                html[data-theme="dark"] .alert-level-cell-{level.value} {{ background: {colors[level]["dark"]}; }}
                html[data-theme="light"] .alert-level-cell-{level.value} {{ background: {colors[level]["light"]}; }}
            '''

        html = f'''
        <style>{style_rules}</style>
        <div class="module" style="margin-top: 20px;">
            <h2>Alert Thresholds</h2>
            <table style="width: 100%; border-collapse: collapse;">
                <thead>
                    <tr style="background: #417690; color: white;">
                        <th style="text-align: left; padding: 12px;">Metric</th>
                        <th style="text-align: left; padding: 12px;">Operator</th>
                        <th style="text-align: center; padding: 12px; background: #5b9bd5;">Info</th>
                        <th style="text-align: center; padding: 12px; background: #af7942;">Warning</th>
                        <th style="text-align: center; padding: 12px; background: #f4b400;">Critical</th>
                        <th style="text-align: center; padding: 12px; background: #db4437;">Emergency</th>
                    </tr>
                </thead>
                <tbody>
        '''

        for metric in metrics:
            html += '<tr>'
            html += f'<td style="padding: 10px; font-weight: 500; background: var(--darkened-bg);">{metric.label}</td>'

            operator_display = operators_dict.get(metric.code, metric.get_default_operator_display())
            html += f'<td style="padding: 10px; background: var(--darkened-bg); color: #666; font-style: italic;">{operator_display}</td>'

            for level in AlertLevel:
                value = thresholds_dict.get((metric.code, level.value))
                field_name = f'threshold_{metric.code}_{level.value}'
                display_value = '' if value is None else value

                html += f'''
                <td class="alert-level-cell-{level.value}" style="padding: 10px; text-align: center;">
                    <input type="number" step="any"
                           name="{field_name}"
                           value="{display_value}"
                           placeholder="Not set"
                           style="width: 120px; padding: 8px; border: 1px solid #ccc; border-radius: 4px; text-align: right;">
                </td>
                '''

            html += '</tr>'

        html += '''
                </tbody>
            </table>
            <p style="color: #666; font-size: 12px; margin-top: 10px;">
                <em>Leave fields empty to disable alerts for that level. Values represent thresholds that trigger alerts.</em>
            </p>
        </div>
        '''

        return mark_safe(html)


@admin.register(AlertMetricDefinition)
class AlertMetricDefinitionAdmin(admin.ModelAdmin):
    list_display = ['code', 'label', 'default_operator', 'is_active', 'from_settings', 'updated']
    list_filter = ['is_active', 'from_settings', 'default_operator']
    search_fields = ['code', 'label', 'description']
    filter_horizontal = ['applicable_content_types']

    fieldsets = (
        (None, {
            'fields': ('code', 'label', 'description')
        }),
        ('Configuration', {
            'fields': ('default_operator', 'applicable_content_types', 'is_active')
        }),
        ('Metadata', {
            'fields': ('from_settings',),
            'classes': ('collapse',),
        }),
    )

    readonly_fields = ['from_settings']

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ['code']
        return self.readonly_fields


@admin.register(AlertThreshold)
class AlertThresholdAdmin(admin.ModelAdmin):
    list_display = ['id', 'content_object_link', 'metric', 'level_display', 'operator', 'threshold_value', 'updated']
    list_filter = ['metric', 'level', 'content_type']
    search_fields = ['metric__code', 'metric__label']
    readonly_fields = ['content_type', 'object_id', 'content_object_link', 'created', 'updated']

    fieldsets = (
        ('Related Object', {
            'fields': ('content_type', 'object_id', 'content_object_link')
        }),
        ('Threshold Configuration', {
            'fields': ('metric', 'level', 'operator', 'threshold_value')
        }),
        ('Timestamps', {
            'fields': ('created', 'updated'),
            'classes': ('collapse',),
        }),
    )

    def content_object_link(self, obj):
        if obj.content_object is None:
            return '-'

        try:
            url = reverse(
                f'admin:{obj.content_type.app_label}_{obj.content_type.model}_change',
                args=[obj.object_id]
            )
            return format_html('<a href="{}">{}</a>', url, obj.content_object)
        except Exception:
            return str(obj.content_object)

    content_object_link.short_description = 'Related Object'

    def level_display(self, obj):
        colors = {
            AlertLevel.INFO: '#5b9bd5',
            AlertLevel.WARNING: '#af7942',
            AlertLevel.CRITICAL: '#f4b400',
            AlertLevel.EMERGENCY: '#db4437',
        }
        color = colors.get(obj.level, '#666')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_level_display()
        )

    level_display.short_description = 'Level'
    level_display.admin_order_field = 'level'
