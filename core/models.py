from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.core.cache import cache
from datetime import datetime
from django.utils import timezone

class NamedModel(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100, unique=True, db_index=True)

    class Meta:
        abstract = True
        ordering = ['name']

    def __str__(self):
        return self.name

# --- Статус заявки---
class Status(NamedModel):
    class Meta(NamedModel.Meta):
        verbose_name = _('Статус')
        verbose_name_plural = _('Статусы')
        ordering = ['name']

# --- Локация организации ---
class OrganizationLocation(NamedModel):
    class Meta(NamedModel.Meta):
        verbose_name = _('Локация организации')
        verbose_name_plural = _('Локации организаций')
        ordering = ['name']

# --- Роль ---
class Role(NamedModel):
    class Meta(NamedModel.Meta):
        verbose_name = _('Роль')
        verbose_name_plural = _('Роли')
        ordering = ['name']

# --- Категория ---
class Category(NamedModel):
    class Meta(NamedModel.Meta):
        verbose_name = _('Категория')
        verbose_name_plural = _('Категории')
        ordering = ['name']
    
        
# --- Организация ---
class Organization(models.Model):
    """Организации в древовидной структуре (MPTT)"""
    name = models.CharField(
        _('Сокращенное наименование'),
        max_length=100,
        help_text=_('Короткое название (СМУ, Контур, Инженеринг)'),
        db_index=True
    )
    full_name = models.CharField(
        _('Полное наименование'),
        max_length=255
    )
    inn = models.CharField(
        _('ИНН'),
        max_length=12,
        blank=True, null=True
    )
    class Meta:
        verbose_name = _('Организация')
        verbose_name_plural = _('Организации')

    def __str__(self):
        return self.name
# --- Подразделение ---
class Department(models.Model):
    """Подразделения внутри организаций"""
    organization = models.ForeignKey(
        Organization,
        verbose_name=_('Организация'),
        on_delete=models.CASCADE,
        related_name='departments'
    )
    name = models.CharField(
        _('Наименование'),
        max_length=255
    )
    class Meta:
        verbose_name = _('Подразделение')
        verbose_name_plural = _('Подразделения')
        ordering = ['name']
        
    def __str__(self):
        return f"{self.organization.name} - {self.name}"

# --- Пользователь ---
class User(AbstractUser):
    username = models.CharField(
        _('username'),
        max_length=150,
        unique=True,
        blank=True,
        null=True,
        validators=[AbstractUser.username_validator],
    )

    email = models.EmailField(
        _('Почта'),
        unique=True,
        help_text=_('Обязательное поле')
    )

    USERNAME_FIELD = 'email'  # логин по email
    REQUIRED_FIELDS = []       # username не обязателен
    
    def __str__(self):
        return self.email

    class Meta:
        verbose_name = _('Пользователь')
        verbose_name_plural = _('Пользователи')

# --- Профиль ---
class Profile(models.Model):
    """Профили сотрудников"""
    
    department = models.ForeignKey(
        Department,
        verbose_name=_('Подразделение'),
        on_delete=models.PROTECT,
        related_name='profiles',
        db_index=True
    )
    user = models.OneToOneField(
        User,
        verbose_name=_('Пользователь'),
        on_delete=models.CASCADE,
        related_name='profile'
    )
    last_name = models.CharField(_('Фамилия'), max_length=100)
    first_name = models.CharField(_('Имя'), max_length=100)
    middle_name = models.CharField(
        _('Отчество'), 
        max_length=100, 
        blank=True, 
        null=True
    )
    position = models.CharField(
        _('Должность'),
        max_length=255
    )
    birth_date = models.DateField(
        _('Дата рождения'),
        blank=True, null=True
    )
    role = models.ForeignKey(
        Role,
        verbose_name=_('Роль'),
        on_delete=models.PROTECT,
        related_name='profiles',
        db_index=True
    )
    phone = models.CharField(
        _('Телефон'),
        max_length=20
    )
    location = models.ForeignKey(
        OrganizationLocation,
        verbose_name=_('Локация организации'),
        on_delete=models.PROTECT,
        related_name='profiles',
        db_index=True
    )
    is_active = models.BooleanField(
        _('Активен'),
        default=True,
        help_text=_('Статус активности профиля')
    )

    class Meta:
        verbose_name = _('Профиль')
        verbose_name_plural = _('Профили')
        
    def __str__(self):
        return f"{self.last_name} {self.first_name}"

    @property
    def full_name(self):
        return f"{self.last_name} {self.first_name} {self.middle_name or ''}".strip()

# --- Заявка ---
class Request(models.Model):
    """Заявки на выполнение работ""" 
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
    
    @property
    def date_start_ended_allowed(self):
        if not hasattr(self, 'date_start') or not hasattr(self, 'time_start'):
            return False

        try:
            # Объединяем дату и время в одну timezone-aware дату
            start_datetime = datetime.combine(self.date_start, self.time_start)
            start_datetime = timezone.make_aware(start_datetime)
            return timezone.now() > start_datetime
        except Exception:
            return False
        
    @property
    def date_end_ended_allowed(self):
        if not hasattr(self, 'date_end') or not hasattr(self, 'time_end'):
            return False

        try:
            # Объединяем дату и время в одну timezone-aware дату
            end_datetime = datetime.combine(self.date_end, self.time_end)
            end_datetime = timezone.make_aware(end_datetime)
            return timezone.now() > end_datetime
        except Exception:
            return False
    
    def clean(self):
            super().clean()
            errors = {}
            
            # Проверка, что окончание позже начала
            if (
                'date_start' not in errors and
                'time_start' not in errors and
                self.date_start and self.date_end and self.time_start and self.time_end
            ):
                dt_start = datetime.combine(self.date_start, self.time_start)
                dt_end   = datetime.combine(self.date_end,   self.time_end)
                if dt_end <= dt_start:
                    errors['time_end'] = 'Дата и время окончания должны быть после начала'

            # 3) Специфика для подъёмных сооружений
            cat_id = self.equipment_category_id
            code = (
                Category.objects
                .filter(pk=cat_id)
                .values_list('code', flat=True)
                .first()
                if cat_id else None
            )

            # проверка перерывов внутри рабочего времени
            break_errors = []
            for period in self.break_periods or []:
                try:
                    start_str, end_str = period.split('-')
                    t_start = datetime.strptime(start_str, '%H:%M').time()
                    t_end   = datetime.strptime(end_str,   '%H:%M').time()
                    if t_start >= t_end:
                        break_errors.append(f'В перерыве "{period}" начало должно быть раньше окончания')
                    if self.time_start and t_start < self.time_start or self.time_end and t_end > self.time_end:
                        break_errors.append(
                            f'Перерыв "{period}" выходит за пределы времени работ '
                            f'({self.time_start.strftime("%H:%M")}–{self.time_end.strftime("%H:%M")})'
                        )
                except Exception:
                    break_errors.append(f'Неверный формат перерыва "{period}". Ожидается "HH:MM-HH:MM"')
            
            if break_errors:
                # аккумулируем все ошибки под единым ключом
                errors['break_periods'] = break_errors

            if code == 'lifting':
                if not self.responsible_certificate:
                    errors['responsible_certificate'] = \
                        'Для категории "Подъемные сооружения и такелаж" обязательно укажите номер удостоверения ответственного'
                if not self.rigger_name:
                    errors['rigger_name'] = \
                        'Для категории "Подъемные сооружения и такелаж" обязательно укажите ФИО стропальщиков'
                if not self.rigger_certificates:
                    errors['rigger_certificates'] = \
                        'Для категории "Подъемные сооружения и такелаж" обязательно укажите номера удостоверений стропальщиков'
            else:
                # если не lifting — очищаем подъемные поля
                self.responsible_certificate = ''
                self.rigger_name = ''
                self.rigger_certificates = ''

            if errors:
                raise ValidationError(errors)
                
    def save(self, *args, **kwargs):
        """Автоматическая обработка перед сохранением"""
        self.full_clean()
        super().save(*args, **kwargs)
