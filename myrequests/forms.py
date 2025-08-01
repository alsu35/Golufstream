from django import forms
from myrequests.models import Request
from users.models import Profile
from core.models import Category,  Status,  OrganizationLocation

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
            'responsible',
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
            if not self.is_bound and new_status:
                self.initial['status'] = new_status.id
            if not self.is_bound and profile and profile.location:
                self.initial['location'] = profile.location.id
            for fn in ('location', 'status'):
                fld = self.fields[fn]
                fld.disabled = True
                fld.widget.attrs['disabled'] = True
        # Для остальных не-операторов: блокируем только location
        elif profile:
            fld = self.fields['location']
            fld.disabled = True
            fld.widget.attrs['disabled'] = True

        # Операторы и админы имеют доступ к статусу => не блокируем его для них

    def save(self, commit=True):
        # При disabled-полях подтягиваем из initial
        if 'status' in self.fields and self.fields['status'].disabled:
            self.instance.status_id = self.initial.get('status')
        if 'location' in self.fields and self.fields['location'].disabled:
            self.instance.location_id = self.initial.get('location')
        return super().save(commit=commit)


