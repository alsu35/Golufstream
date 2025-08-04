from django.contrib import admin
from django.core.exceptions import ValidationError
from core.models import Status
from myrequests.models import Request
from django.utils.html import format_html
from django.urls import reverse

import logging
logger = logging.getLogger(__name__)

@admin.register(Request)
class RequestAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'created_at', 
        'get_customer', 'get_responsible','get_status',
        'date_start', 'date_end', 'break_periods', 'is_completed_fact'
    )
    list_filter = ('status', 'equipment_category')
    search_fields = ('customer__last_name', 'responsible__last_name', 'comment')
    date_hierarchy = 'created_at'
    autocomplete_fields = ('customer', 'responsible')
    readonly_fields = ('created_at',)
    save_on_top = True

    # ссылка на заказчика
    def get_customer(self, obj):
        url = reverse('admin:users_profile_change', args=[obj.customer.pk])
        return format_html('<a href="{}">{}</a>', url, obj.customer.full_name)
    get_customer.short_description = 'Заказчик'
    get_customer.admin_order_field = 'customer__last_name'

    # ссылка на ответственного
    def get_responsible(self, obj):
        url = reverse('admin:users_profile_change', args=[obj.responsible.pk])
        return format_html('<a href="{}">{}</a>', url, obj.responsible.full_name)
    get_responsible.short_description = 'Ответственный'
    get_responsible.admin_order_field = 'responsible__last_name'
    
    def get_status(self, obj):
        return obj.status.name
    get_status.short_description = 'Статус'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'status', 'customer__department__organization', 'equipment_category'
        )

    def get_readonly_fields(self, request, obj=None):
        readonly = list(super().get_readonly_fields(request, obj))
        if not request.user.is_superuser and not request.user.groups.filter(name='admin').exists():
            readonly.append('status')
        return readonly

    def save_model(self, request, obj, form, change):
            if not change and not request.user.is_superuser and not request.user.groups.filter(name='admin').exists():
                try:
                    obj.status = Status.objects.get(code='new')
                except Status.DoesNotExist as e:
                    logger.error("Статус 'new' не найден при сохранении заявки: %s", e)
                    raise ValidationError("Статус 'new' не найден")
            super().save_model(request, obj, form, change)