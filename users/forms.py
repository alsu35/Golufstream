from django import forms

class LoginForm(forms.Form):
    email = forms.CharField(label='Логин', max_length=150)
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput)
