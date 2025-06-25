from django import forms
from .models import Request

class RequestForm(forms.ModelForm):
    class Meta:
        model = Request
        fields = [
            'customer','location','date_start','date_end',
            'time_start','time_end','break_time', 'status','work_object',
            'work_type','transport_type','equipment_category', 'is_completed_fact',
            'responsible','responsible_certificate',
            'rigger_name','rigger_certificates','comment',
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
                            '- «легковой» – легковой автомобиль\n'
                            '- «бочковой» – цистерна-бочка\n'
                            '- «питьевой» – цистерна для питьевой воды\n'
                            '- «кран» – автомобильный кран\n'
                            '- «КМУ» – кран-манипулятор\n'
                            '…и т. д.'
                        )
                    },
                    'equipment_category': {
                        'required': (
                            'Выберите категорию техники'
                        )
                    },
                    'date_start': {
                        'required': 'Укажите дату начала работ (формат ДД.ММ.ГГГГ)'
                    },
                    'date_end': {
                        'required': 'Укажите дату окончания работ (формат ДД.ММ.ГГГГ)'
                    },
                    'time_start': {
                        'required': 'Укажите время начала работ (формат ЧЧ:ММ)'
                    },
                    'time_end': {
                        'required': 'Укажите примерное время окончания работ (формат ЧЧ:ММ)'
                    },
                    'responsible': {
                        'required': 'Выберите ответственного исполнителя из списка'
                    }
                }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Если lifting - делаем и их обязательными
        if self.data.get('equipment_category') == 'lifting':
            for field in ['responsible_certificate', 'rigger_name', 'rigger_certificates']:
                self.fields[field].required = True