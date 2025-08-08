from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _
from django.conf import settings

# --- Организация ---
class Organization(models.Model):
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
    organization = models.ForeignKey(
        Organization,
        verbose_name=_('Организация'),
        on_delete=models.CASCADE,
        related_name='departments',
        db_index=True
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

# --- Кастомный менеджер ---
class CustomUserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email обязателен')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Суперпользователь должен иметь is staff')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Суперпользователь должен иметь is_superuser')
        return self.create_user(email, password, **extra_fields)

# --- Пользователь ---
class User(AbstractUser):
    username = None
    email = models.EmailField(
        _('Почта'),
        unique=True,
        help_text=_('Обязательное поле'),
        db_index=True
    )
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    objects = CustomUserManager()

    def __str__(self):
        return self.email

    class Meta:
        verbose_name = _('Пользователь')
        verbose_name_plural = _('Пользователи')

# --- Профиль ---
class Profile(models.Model):
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
        related_name='profile',
        null=True,
        blank=True,
        help_text=_('Оставьте пустым, если профиль временный или без аккаунта')
    )
    last_name = models.CharField(_('Фамилия'), max_length=100)
    first_name = models.CharField(_('Имя'), max_length=100)
    middle_name = models.CharField(
        _('Отчество'),
        max_length=100,
        blank=True,
        default=''
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
        'core.Role',
        verbose_name=_('Роль'),
        on_delete=models.PROTECT,
        related_name='profiles',
        db_index=True
    )
    phone = models.CharField(
        _('Телефон'),
        max_length=20,
        unique=True,
        help_text=_('Номер телефона должен быть уникальным')
    )
    location = models.ForeignKey(
        'core.OrganizationLocation',
        verbose_name=_('Локация организации'),
        on_delete=models.PROTECT,
        related_name='profiles',
        db_index=True
    )
    class Meta:
        verbose_name = _('Профиль')
        verbose_name_plural = _('Профили')

    def __str__(self):
        return f"{self.last_name} {self.first_name}"

    @property
    def full_name(self):
        return f"{self.last_name} {self.first_name} {self.middle_name or ''}".strip()
    
