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
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Администратор видит статус, остальные нет
        if self.user and not self.user.is_superuser and getattr(self.user, 'profile', None).role.code != 'admin':
            self.fields.pop('status', None)

        # Автоустановка initial для локации у заказчика
        if self.instance and self.instance.pk is None and self.user and getattr(self.user, 'profile', None):
            loc = self.user.profile.location
            self.fields['location'].initial = loc
            self.fields['location'].widget.attrs['readonly'] = True

        # Управление обязательностью полей для 'lifting'
        code = None
        if self.instance and self.instance.equipment_category:
            code = self.instance.equipment_category.code
        elif 'equipment_category' in self.data:
            try:
                category_id = int(self.data['equipment_category'])
                category = Category.objects.get(id=category_id)
                code = category.code
            except (ValueError, Category.DoesNotExist):
                code = None

        # Устанавливаем обязательность полей
        for field in ['responsible_certificate', 'rigger_name', 'rigger_certificates']:
            self.fields[field].required = (code == 'lifting')

    def clean(self):
        cleaned = super().clean()
        # Дополнительная логика валидации, если нужно
        return cleaned
    
class LoginForm(forms.Form):
    username = forms.CharField(label='Логин', max_length=150)
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput)
