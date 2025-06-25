from django.db import models
from django.contrib.auth.models import AbstractUser
from mptt.models import MPTTModel, TreeForeignKey
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinLengthValidator
from django.core.exceptions import ValidationError
from django.utils import timezone

# --- Локация организации ---
class OrganizationLocation(models.Model):
    """Локация организации (Альметьевск, Нижнекамск, Внешний)"""
    code = models.CharField(
        _('Код локации'),
        max_length=20,
        unique=True,
        help_text=_('Уникальный код локации (например: alm, nch, ext)')
    )
    name = models.CharField(
        _('Наименование'),
        max_length=100,
        unique=True
    )
    
    class Meta:
        verbose_name = _('Локация организации')
        verbose_name_plural = _('Локации организаций')
        ordering = ['name']
        
    def __str__(self):
        return self.name

# --- Статус ---
class Status(models.Model):
    """Статусы заявок"""
    code = models.CharField(
        _('Код статуса'),
        max_length=20,
        unique=True,
        help_text=_('Уникальный код статуса (например: new, work, done)')
    )
    name = models.CharField(
        _('Наименование'),
        max_length=100,
        unique=True
    )
    
    class Meta:
        verbose_name = _('Статус')
        verbose_name_plural = _('Статусы')
        ordering = ['name']
        
    def __str__(self):
        return self.name

# --- Роль ---
class Role(models.Model):
    """Роли пользователей"""
    code = models.CharField(
        _('Код роли'),
        max_length=20,
        unique=True,
        help_text=_('Уникальный код роли (например: admin, master)')
    )
    name = models.CharField(
        _('Наименование'),
        max_length=100,
        unique=True
    )
    
    class Meta:
        verbose_name = _('Роль')
        verbose_name_plural = _('Роли')
        ordering = ['name']
        
    def __str__(self):
        return self.name

# --- Организация ---
class Organization(MPTTModel):
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
    parent = TreeForeignKey(
        'self',
        verbose_name=_('Родительская организация'),
        on_delete=models.PROTECT,
        null=True, blank=True,
        related_name='children',
        db_index=True
    )
    inn = models.CharField(
        _('ИНН'),
        max_length=12,
        blank=True, null=True
    )

    class MPTTMeta:
        order_insertion_by = ['name']

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
    parent = TreeForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='children'
    )
    
    class Meta:
        verbose_name = _('Подразделение')
        verbose_name_plural = _('Подразделения')
        ordering = ['name']
        
    def __str__(self):
        return f"{self.organization.name} - {self.name}"

# --- Пользователь ---
class User(AbstractUser):
    email = models.EmailField(
        _('Почта'),
        unique=True,
        help_text=_('Обязательное поле')
    )
    
    # Переопределяем стандартные поля Django
    username = models.CharField(
        _('Логин'),
        max_length=150,
        unique=True,
        help_text=_('Обязательное поле. Только буквы, цифры и @/./+/-/_.')
    )
    
    class Meta:
        verbose_name = _('Пользователь')
        verbose_name_plural = _('Пользователи')
        
    def __str__(self):
        return self.username

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
        _('Дата рождения')
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

# --- Категория ---
class Category(models.Model):
    """Категория транспорта"""
    code = models.CharField(
        _('Код категории'),
        max_length=20,
        unique=True,
        help_text=_('Уникальный код роли (например: cargo, people, lifting)')
    )
    name = models.CharField(
        _('Наименование'),
        max_length=100,
        unique=True
    )
    
    class Meta:
        verbose_name = _('Категория')
        verbose_name_plural = _('Категории')
        ordering = ['name']
        
    def __str__(self):
        return self.name
    
# --- Заявка ---
class Request(models.Model):
    """Заявки на выполнение работ""" 
    customer = models.ForeignKey(
        Profile,
        verbose_name=_('Подающий заявку (заказчик)'),
        on_delete=models.PROTECT,
        related_name='customer_requests'
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
        _('Время окончания работ'),
        null=True,
        blank=True,
    )
    is_completed_fact = models.BooleanField(
        _('Окончание работ по факту'),
        default=False,
        help_text=_('Отметка "Да" если работы будут завершены по факту')
    )
    break_time = models.DurationField(
        _('Предполагаемое время ожидания'),
        null=True,
        blank=True,
        help_text=_('В формате ЧЧ:ММ:СС (необязательно)')
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
        related_name='responsible_requests',
        null=True
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

        if self.date_start and self.date_end and self.date_start > self.date_end:
            errors['date_end'] = 'Дата окончания не может быть раньше даты начала.'

        if self.time_start and self.time_end and self.time_start > self.time_end:
            errors['time_end'] = 'Время окончания не может быть раньше времени начала.'

        if self.equipment_category == 'lifting':
            if not self.responsible_certificate:
                errors['responsible_certificate'] = 'Для подъёмных сооружений обязательен номер удостоверения ответственного'
            if not self.rigger_name:
                errors['rigger_name'] = 'Для подъёмных сооружений укажите ФИО стропальщиков через запятую'
            if not self.rigger_certificates:
                errors['rigger_certificates'] = 'Для подъёмных сооружений укажите номера удостоверений стропальщиков через запятую'
        else:
            self.responsible_certificate = None
            self.rigger_name = None
            self.rigger_certificates = None

        if errors:
            raise ValidationError(errors)
    
    def save(self, *args, **kwargs):
        """Автоматическая обработка перед сохранением"""
        self.full_clean()  # Выполняем валидацию
        super().save(*args, **kwargs)



