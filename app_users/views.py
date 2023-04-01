import logging

from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.views import generic
from app_users.models import Profile
from app_users.forms import RegistrationForm, AuthForm, ProfileForm
from django.contrib.auth import get_user_model, login, authenticate
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin


logger = logging.getLogger(__name__)


class RegistrationFormView(generic.CreateView):
    model = get_user_model()
    form_class = RegistrationForm
    template_name = 'app_users/register.html'
    success_url = reverse_lazy('shops_home')

    def form_valid(self, form):
        user = form.save()
        username = form.cleaned_data.get('username')
        raw_password = form.cleaned_data.get('password1')
        Profile.objects.create(user=user)
        user = authenticate(username=username, password=raw_password)
        login(self.request, user)
        log_msg = f'Выполнен вход нового пользователя:: {username}'
        logger.info(log_msg)
        return redirect(self.success_url)


class AuthFormView(LoginView):
    authentication_form = AuthForm
    template_name = 'app_users/login.html'

    def form_valid(self, form):
        """Security check complete. Log the user in.
        Method redefined to get user objects and form logger message."""
        login(self.request, form.get_user())
        log_msg = f'Выполнен вход пользователя:: {self.request.user.username}'
        logger.info(log_msg)
        return HttpResponseRedirect(self.get_success_url())


class ProfileView(LoginRequiredMixin, generic.TemplateView):
    template_name = 'app_users/profile.html'


class ProfileEditView(LoginRequiredMixin, generic.UpdateView):
    model = Profile
    form_class = ProfileForm
    template_name = 'app_users/profile_edit.html'
    success_url = reverse_lazy('profile')

    def get_context_data(self, **kwargs):
        profile = self.object
        init_data = {"first_name": profile.user.first_name,
                     'last_name': profile.user.last_name}
        form = ProfileForm(instance=profile, initial=init_data)
        context = super().get_context_data(**kwargs)
        context['form'] = form
        return context

    def form_valid(self, form):
        profile = self.object
        user = profile.user
        user.first_name = form.cleaned_data.get('first_name')
        user.last_name = form.cleaned_data.get('last_name')
        user.save()
        return super().form_valid(form)
