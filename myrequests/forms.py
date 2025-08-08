from django import forms
from myrequests.models import Request
from users.models import Department, Profile
from core.models import Category, Role,  Status,  OrganizationLocation

class ResponsibleForm(forms.ModelForm):
    department = forms.ModelChoiceField(
        queryset=Department.objects.select_related('organization').all(),
        label='Организация / Подразделение',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    location = forms.ModelChoiceField(
        queryset=OrganizationLocation.objects.all(),
        label='Локация',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    class Meta:
        model = Profile
        fields = ['last_name', 'first_name', 'middle_name', 'position', 'phone', 'birth_date','department', 'location']
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
            'last_name':  forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'middle_name':forms.TextInput(attrs={'class': 'form-control'}),
            'position':   forms.TextInput(attrs={'class': 'form-control'}),
            'phone':      forms.TextInput(attrs={'class': 'form-control phone-input'}),
        }

    def __init__(self, *args, profile=None, **kwargs):
        super().__init__(*args, **kwargs)

        # Предзаполнение локации и подразделения — из текущего профиля
        if profile:
            self.initial['location'] = profile.location_id

    def save(self, commit=True):
        instance = super().save(commit=False)

        # Роль по умолчанию — customer
        instance.role = Role.objects.get(code='customer')

        if commit:
            instance.save()
        return instance
    
class RequestForm(forms.ModelForm):
    location = forms.ModelChoiceField(
        queryset=OrganizationLocation.objects.none(),
        required=True
    )
    equipment_category = forms.ModelChoiceField(
        queryset=Category.objects.none(),
        required=True
    )
    status = forms.ModelChoiceField(
        queryset=Status.objects.none(),
        required=True
    )

    class Meta:
        model = Request
        fields = [
            'location', 'date_start', 'date_end', 'time_start', 'time_end',
            'work_object', 'work_type', 'transport_type', 'equipment_category',
            'break_periods', 'status', 'is_completed_fact', 'comment',
            'responsible', 'customer',
            'responsible_certificate', 'rigger_name', 'rigger_certificates',
        ]
        widgets = {
            'date_start': forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'date_end':   forms.DateInput(attrs={'type': 'date'}, format='%Y-%m-%d'),
            'time_start': forms.TimeInput(attrs={'type': 'time'}),
            'time_end':   forms.TimeInput(attrs={'type': 'time'}),
            'comment':    forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(
        self, *args,
        user=None,
        profile=None,
        locations=None,
        categories=None,
        statuses=None,
        new_status=None,
        **kwargs
    ):
        self.user = user
        self.profile = profile
        super().__init__(*args, **kwargs)

        # Подставляем QuerySet’ы
        if locations is not None:
            self.fields['location'].queryset = locations
        if categories is not None:
            self.fields['equipment_category'].queryset = categories
        if statuses is not None:
            self.fields['status'].queryset = statuses

        # Определяем роль из profile
        role_code = getattr(getattr(profile, 'role', None), 'code', None)

        # Для оператора: добавляем поле customer и не блокируем status
        if role_code == 'operator':
            self.fields['customer'] = forms.ModelChoiceField(
                queryset=Profile.objects.filter(role__code='customer'),
                required=True,
                label='Заказчик'
            )
        # Для заказчика: скрываем customer, блокируем location и status
        elif role_code == 'customer':
                    self.fields.pop('customer', None)

                    if not self.is_bound:
                        # Устанавливаем initial ответственного
                        if profile:
                            self.initial['responsible'] = profile.pk

                        if new_status:
                            self.initial['status'] = new_status.id
                        if profile and profile.location:
                            self.initial['location'] = profile.location.id

                    # Блокируем поля
                    for fn in ('location', 'status'):
                        fld = self.fields[fn]
                        fld.disabled = True
                        fld.widget.attrs['disabled'] = True
        # Для остальных не-операторов: блокируем только location
        elif profile:
            fld = self.fields['location']
            fld.disabled = True
            fld.widget.attrs['disabled'] = True

    def save(self, commit=True):
        # При disabled-полях подтягиваем из initial
        if 'status' in self.fields and self.fields['status'].disabled:
            self.instance.status_id = self.initial.get('status')
        if 'location' in self.fields and self.fields['location'].disabled:
            self.instance.location_id = self.initial.get('location')
        
        return super().save(commit=commit)
    





