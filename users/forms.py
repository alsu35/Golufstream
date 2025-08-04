from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

from core.models import OrganizationLocation, Role
from .models import Profile, Department

User = get_user_model()

# авторизация
class LoginForm(forms.Form):
    email = forms.EmailField(label='Логин', max_length=150)
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput)

# регистрация
class RegisterForm(UserCreationForm):
    last_name = forms.CharField(max_length=100, label="Фамилия")
    first_name = forms.CharField(max_length=100, label="Имя")
    middle_name = forms.CharField(max_length=100, required=False, label="Отчество")
    phone = forms.CharField(max_length=20, label="Телефон")
    position = forms.CharField(max_length=255, label="Должность")
    birth_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="Дата рождения"
    )
    department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        label="Подразделение"
    )
    role = forms.ModelChoiceField(
        queryset=Role.objects.all(),
        label="Роль"
    )
    location = forms.ModelChoiceField(
        queryset=OrganizationLocation.objects.all(),
        label="Локация"
    )

    class Meta:
        model = User
        fields = ('email',)
        labels = {
            'email': 'Email'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Исключаем роль "Администратор" из списка
        self.fields['role'].queryset = Role.objects.exclude(code="admin")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
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
                location=self.cleaned_data['location']
            )
        return user