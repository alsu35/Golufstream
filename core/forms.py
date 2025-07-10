from django import forms
from .models import Category, Request, Status


class RequestForm(forms.ModelForm):
    class Meta:
        model = Request
        fields = [
            # Базовые данные
            'location',
            'date_start', 'date_end',
            'time_start', 'time_end',
            # Информация о работе
            'work_object', 'work_type', 'transport_type', 'equipment_category', 'break_periods',
            # Статус выполнения и доп. поля
            'status', 'is_completed_fact', 'comment',
            # Дополнительно (только для 'lifting')
            'responsible', 'responsible_certificate', 'rigger_name', 'rigger_certificates'
        ]
        error_messages = {
            'location': {
                'required': 'Укажите, в какой локации будут выполняться работы (Альметьевск, Нижнекамск или Внешний)'
            },
            'work_object': {
                'required': 'Опишите, на каком объекте будут проводиться работы (например, «Административное здание №5»)'
            },
            'work_type': {
                'required': 'Укажите вид работ (например, «Погрузка-разгрузка», «Техническое обслуживание»)'
            },
            'transport_type': {
                'required': (
                    'Выберите тип транспорта или техники:\n'
                    '— «легковой» – легковой автомобиль\n'
                    '— «бочковой» – цистерна-бочка\n'
                    '— «питьевой» – цистерна для питьевой воды\n'
                    '— «кран» – автомобильный кран\n'
                    '— «КМУ» – кран-манипулятор\n'
                    '…и т. д.'
                )
            },
            'equipment_category': {
                'required': 'Выберите категорию техники'
            },
            'date_start': {
                'required': 'Укажите дату начала работ'
            },
            'date_end': {
                'required': 'Укажите дату окончания работ'
            },
            'time_start': {
                'required': 'Укажите время начала работ'
            },
            'time_end': {
                'required': 'Укажите примерное время окончания работ'
            },
            'responsible': {
                'required': 'Выберите ответственного исполнителя из списка'
            }
        }
        widgets = {
            'date_start': forms.DateInput(
                attrs={'type': 'date'},
                format='%Y-%m-%d'
            ),
            'date_end': forms.DateInput(
                attrs={'type': 'date'},
                format='%Y-%m-%d'
            ),
            'time_start': forms.TimeInput(attrs={'type': 'time'}),
            'time_end': forms.TimeInput(attrs={'type': 'time'}),
            'comment': forms.Textarea(attrs={'rows': 3}),
            'equipment_category': forms.Select(attrs={
                'class': 'form-select',
            }),
        }

    def __init__(self, *args, user=None, **kwargs):
        """
        Скрываем поле status, если пользователь не operator/admin/superuser.
        """
        super().__init__(*args, **kwargs)
        self.user = user

        # Проверяем роль
        is_power = (
            user and (
                user.is_superuser
                or getattr(user, 'profile', None) and user.profile.role.code in ('admin', 'operator')
            )
        )

        if not is_power:
            # Убираем поле из формы и не делаем его required
            self.fields.pop('status', None)

        # Автоустановка initial для локации у заказчика
        if self.instance and self.instance.pk is None and self.user and getattr(self.user, 'profile', None):
            loc = self.user.profile.location
            self.fields['location'].initial = loc
            self.fields['location'].widget.attrs['readonly'] = True

    def clean(self):
        cleaned = super().clean()
        return cleaned
    
    def save(self, commit=True):
        """
        Если поле status отсутствует — проставляем дефолтный 'new'.
        """
        obj = super().save(commit=False)

        # Если в форме нет status (пользователь не operator/admin)
        if 'status' not in self.cleaned_data:
            obj.status = Status.objects.get(code='new')

        if commit:
            obj.save()
        return obj
    
class LoginForm(forms.Form):
    username = forms.CharField(label='Логин', max_length=150)
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput)
