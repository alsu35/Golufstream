from django import forms
from .models import Category, Request, Status, Profile
from django.forms.models import ModelChoiceIteratorValue
from django.core.exceptions import ValidationError

class RequestForm(forms.ModelForm):
    class Meta:
        model = Request
        fields = [
            # Базовые данные
            'location',
            'date_start', 'date_end',
            'time_start', 'time_end',
            # Информация о работе
            'work_object', 'work_type', 'transport_type',
            'equipment_category', 'break_periods',
            # Статус и логика
            'status', 'is_completed_fact', 'comment',
            # Ответственный и заказчик
            'responsible','customer',
            # Лифтинг-поля
            'responsible_certificate', 'rigger_name', 'rigger_certificates',
        ]
        widgets = {
            'date_start': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'date_end':   forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'time_start': forms.TimeInput(attrs={'type': 'time'}),
            'time_end':   forms.TimeInput(attrs={'type': 'time'}),
            'comment':    forms.Textarea(attrs={'rows': 3}),
        }
        error_messages = {
            'location':     {'required': 'Укажите локацию'},
            'work_object':  {'required': 'Опишите объект работ'},
            'work_type':    {'required': 'Укажите вид работ'},
            'transport_type': {
                'required': 'Выберите тип транспорта (легковой, бочковой, кран и т.п.)'
            },
            'equipment_category': {'required': 'Выберите категорию техники'},
            'date_start':   {'required': 'Укажите дату начала работ'},
            'date_end':     {'required': 'Укажите дату окончания работ'},
            'time_start':   {'required': 'Укажите время начала работ'},
            'time_end':     {'required': 'Укажите время окончания работ'},
            'responsible':  {'required': 'Выберите ответственного'},
        }

    def __init__(self, *args, **kwargs):
        # 1) Извлекаем текущего пользователя
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # 2) Определяем роль
        role = getattr(self.user, 'profile', None) and self.user.profile.role.code

        # 3) Показываем поле customer только для оператора
        if role == 'operator':
            # Ограничиваем список клиентов
            self.fields['customer'].queryset = Profile.objects.filter(role__code='customer')
        else:
            # Скрываем customer для всех остальных
            self.fields.pop('customer', None)

        # 4) Показываем поле status только для admin/operator/superuser
        is_power = self.user and (self.user.is_superuser or role in ('admin', 'operator'))
        if not is_power:
            self.fields.pop('status', None)

        # 5) Для не-операторов — локация readonly и проставлена по profile
        if self.user and getattr(self.user, 'profile', None):
            prof = self.user.profile
            if role != 'operator':
                self.fields['location'].initial = prof.location
                self.fields['location'].widget.attrs['readonly'] = True

    def save(self, commit=True):
        # 1) Сохраняем объект без commit
        obj = super().save(commit=False)

        # 2) Если поле status было скрыто — ставим дефолтный 'new'
        if 'status' not in self.cleaned_data:
            try:
                obj.status = Status.objects.get(code='new')
            except Status.DoesNotExist:
                raise ValidationError("Не найден статус 'new'")

        # 3) Сохраняем в базу
        if commit:
            obj.save()
        return obj
        
    
class LoginForm(forms.Form):
    username = forms.CharField(label='Логин', max_length=150)
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput)
