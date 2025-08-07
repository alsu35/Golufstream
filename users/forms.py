import re
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from core.models import OrganizationLocation, Role
from .models import Profile, Department

User = get_user_model()

class LoginForm(forms.Form):
    email = forms.EmailField(label='Логин', max_length=150)
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput)


class RegisterForm(UserCreationForm):
    last_name   = forms.CharField(max_length=100, label="Фамилия", widget=forms.TextInput(attrs={'required': True}))
    first_name  = forms.CharField(max_length=100, label="Имя",     widget=forms.TextInput(attrs={'required': True}))
    middle_name = forms.CharField(max_length=100, required=False, label="Отчество")
    phone       = forms.CharField(max_length=20,  label="Телефон", widget=forms.TextInput(attrs={'required': True}))
    position    = forms.CharField(max_length=255, label="Должность", widget=forms.TextInput(attrs={'required': True}))
    birth_date  = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}), label="Дата рождения")

    department = forms.ModelChoiceField(queryset=Department.objects.none(), label="Подразделение")
    role       = forms.ModelChoiceField(queryset=Role.objects.none(),       label="Роль")
    location   = forms.ModelChoiceField(queryset=OrganizationLocation.objects.none(), label="Локация")

    class Meta:
        model  = User
        fields = ('email',)
        labels = {'email': 'Email'}
        widgets = {'email': forms.EmailInput(attrs={'required': True})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields['department'].queryset = (
            Department.objects
            .select_related('organization') 
            .all()
        )
        
        self.fields['location'].queryset   = OrganizationLocation.objects.all()
        self.fields['role'].queryset = Role.objects.exclude(code__in=['admin', 'operator'])

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
            raise ValidationError(_("Неверный формат email"))
        if User.objects.filter(email=email).exists():
            raise ValidationError(_("Пользователь с таким email уже существует"))
        return email

    def clean_phone(self):
        phone  = self.cleaned_data.get('phone')
        digits = re.sub(r'\D', '', phone)
        if len(digits) != 11 or not digits.startswith(('7', '8')):
            raise ValidationError(_("Неверный формат телефона. Используйте формат +7-XXX-XXX-XX-XX"))
        if Profile.objects.filter(phone__endswith=digits[-10:]).exists():
            raise ValidationError(_("Пользователь с таким телефоном уже существует"))
        return digits

    def clean_password1(self):
        password = self.cleaned_data.get('password1')
        if len(password) < 8:
            raise ValidationError(_("Пароль должен содержать минимум 8 символов"))
        if not re.search(r'[A-Z]', password):
            raise ValidationError(_("Пароль должен содержать хотя бы одну заглавную букву"))
        if not re.search(r'[a-z]', password):
            raise ValidationError(_("Пароль должен содержать хотя бы одну строчную букву"))
        if not re.search(r'[0-9]', password):
            raise ValidationError(_("Пароль должен содержать хотя бы одну цифру"))
        return password

    def clean(self):
        cleaned = super().clean()
        required = [
            'last_name', 'first_name', 'phone', 'email',
            'password1', 'password2', 'position',
            'department', 'role', 'location'
        ]
        for field in required:
            if not cleaned.get(field):
                raise ValidationError(_(f"Поле '{field}' обязательно для заполнения"))
        p1 = cleaned.get('password1')
        p2 = cleaned.get('password2')
        if p1 and p2 and p1 != p2:
            raise ValidationError(_("Пароли не совпадают"))
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            from django.db import transaction
            with transaction.atomic():
                user.save()
                Profile.objects.create(
                    user=user,
                    last_name=self.cleaned_data['last_name'],
                    first_name=self.cleaned_data['first_name'],
                    middle_name=self.cleaned_data['middle_name'],
                    phone=self.cleaned_data['phone'],
                    position=self.cleaned_data['position'],
                    birth_date=self.cleaned_data['birth_date'],
                    department=self.cleaned_data['department'],
                    role=self.cleaned_data['role'],
                    location=self.cleaned_data['location'],
                )
        return user
    