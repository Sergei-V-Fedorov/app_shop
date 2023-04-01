from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.utils.translation import gettext_lazy as _
from app_users.models import Profile


class RegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=24, required=False, label=_('имя').capitalize())
    last_name = forms.CharField(max_length=24, required=False, label=_('фамилия').capitalize())

    class Meta:
        model = get_user_model()
        fields = ['username', 'password1', 'password2', 'first_name', 'last_name']


class AuthForm(AuthenticationForm):
    username = forms.CharField(max_length=24, label=_('логин').capitalize())
    password = forms.CharField(widget=forms.PasswordInput, label=_('пароль').capitalize())


class ProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=24, required=False, label=_('имя').capitalize())
    last_name = forms.CharField(max_length=24, required=False, label=_('фамилия').capitalize())

    class Meta:
        model = Profile
        fields = ['first_name', 'last_name', 'avatar']
