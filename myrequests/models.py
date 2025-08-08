from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime
from users.models import Profile
from core.models import Status, Category, OrganizationLocation
# -------индексация--------
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField

class Request(models.Model):
    customer = models.ForeignKey(
        Profile,
        verbose_name=_('Подающий заявку (заказчик)'),
        on_delete=models.PROTECT,
        related_name='customer_requests',
        db_index=True
    )
    location = models.ForeignKey(
        OrganizationLocation,
        verbose_name=_('Локация организации'),
        on_delete=models.PROTECT,
        related_name='location_requests',
        db_index=True
    )
    created_at = models.DateTimeField(
        _('Дата и время подачи'),
        auto_now_add=True
    )
    date_start = models.DateField(
        _('Дата начала работ'),
        db_index=True
    )
    date_end = models.DateField(
        _('Дата окончания работ'),
        db_index=True
    )
    time_start = models.TimeField(
        _('Время начала работ')
    )
    time_end = models.TimeField(
        _('Время окончания работ')
    )
    is_completed_fact = models.BooleanField(
        _('Окончание работ по факту'),
        default=False,
        help_text=_('Отметка "Да" если работы будут завершены по факту')
    )
    break_periods = models.JSONField(
        _('Перерывы'),
        blank=True,
        default=list
    )
    work_object = models.CharField(
        _('Объект работ'),
        max_length=255
    )
    work_type = models.CharField(
        _('Вид работ'),
        max_length=255
    )
    transport_type = models.CharField(
        _('Вид транспорта'),
        max_length=255
    )
    status = models.ForeignKey(
        Status,
        verbose_name=_('Статус'),
        on_delete=models.PROTECT,
        related_name='status_requests',
        db_index=True
    )
    responsible = models.ForeignKey(
        Profile,
        verbose_name=_('Ответственный'),
        on_delete=models.PROTECT,
        related_name='responsible_requests'
    )
    comment = models.TextField(
        _('Комментарий'),
        blank=True
    )
    equipment_category = models.ForeignKey(
        Category,
        verbose_name=_('Категория техники'),
        on_delete=models.PROTECT,
        related_name='equipment_requests',
        db_index=True
    )
    responsible_certificate = models.CharField(
        _('Номер удостоверения ответственного'),
        max_length=100,
        blank=True,
        null=True,
        db_index=True,
        help_text=_('Только для категории "Подъемные сооружения и такелаж"')
    )
    rigger_name = models.CharField(
        _('ФИО стропольщика'),
        max_length=255,
        blank=True,
        null=True,
        help_text=_('Перечислите через запятую (только для категории "Подъемные сооружения и такелаж")')
    )
    rigger_certificates = models.TextField(
        _('Номера удостоверений стропольщиков'),
        blank=True,
        null=True,
        help_text=_('Перечислите через запятую (только для категории "Подъемные сооружения и такелаж")')
    )

    class Meta:
        verbose_name = _('Заявка')
        verbose_name_plural = _('Заявки')
        ordering = ['-created_at']

    def __str__(self):
        return f"Заявка #{self.id} - {self.work_object}"

    def clean(self):
        super().clean()
        errors = {}

        # Проверка времени: окончание после начала
        if self.date_start and self.date_end and self.time_start and self.time_end:
            dt_start = datetime.combine(self.date_start, self.time_start)
            dt_end = datetime.combine(self.date_end, self.time_end)
            if dt_end <= dt_start:
                errors['time_end'] = 'Дата и время окончания должны быть после начала'

        # Проверка перерывов
        break_errors = []
        for period in self.break_periods or []:
            try:
                start_str, end_str = period.split('-')
                t_start = datetime.strptime(start_str, '%H:%M').time()
                t_end = datetime.strptime(end_str, '%H:%M').time()
                if t_start >= t_end:
                    break_errors.append(f'В перерыве "{period}" начало должно быть раньше окончания')
                if (self.time_start and t_start < self.time_start) or (self.time_end and t_end > self.time_end):
                    break_errors.append(
                        f'Перерыв "{period}" выходит за пределы времени работ '
                        f'({self.time_start.strftime("%H:%M")}–{self.time_end.strftime("%H:%M")})'
                    )
            except Exception:
                break_errors.append(f'Неверный формат перерыва "{period}". Ожидается "HH:MM-HH:MM"')
        if break_errors:
            errors['break_periods'] = break_errors

        # Безопасная проверка категории техники
        if self.equipment_category_id:  # проверяем наличие ID категории
            # теперь безопасно обращаться к связанной категории
            if self.equipment_category.code == 'lifting':
                if not self.responsible_certificate:
                    errors['responsible_certificate'] = 'Обязательно укажите номер удостоверения ответственного'
                if not self.rigger_name:
                    errors['rigger_name'] = 'Обязательно укажите ФИО стропальщиков'
                if not self.rigger_certificates:
                    errors['rigger_certificates'] = 'Обязательно укажите номера удостоверений стропальщиков'
            else:
                # Очищаем поля, если не "lifting"
                self.responsible_certificate = ''
                self.rigger_name = ''
                self.rigger_certificates = ''
        else:
            # Категория техники не выбрана - очищаем поля
            self.responsible_certificate = ''
            self.rigger_name = ''
            self.rigger_certificates = ''

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        if not kwargs.get('update_fields'):
            self.full_clean()
        super().save(*args, **kwargs)
