from django import forms
from django.contrib.auth.models import User

class LoginForm(forms.ModelForm):
    user_name = forms.CharField(max_length=50, required=True)
    password = forms.CharField(widget=forms.PasswordInput())

    class Meta:
        model = User

        fields = ['user_name', 'password']