from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django import forms

class WithdrawForm(forms.Form):
    amount = forms.DecimalField(max_digits=10, decimal_places=2)

class DepositForm(forms.Form):
    amount = forms.DecimalField(max_digits=10, decimal_places=2)

class FundTransferForm(forms.Form):
    amount = forms.DecimalField(max_digits=10, decimal_places=2)
    recipient = forms.ModelChoiceField(queryset=User.objects.all().exclude(username='admin'))



class EditUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password'] 