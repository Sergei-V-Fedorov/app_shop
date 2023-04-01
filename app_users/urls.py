from django.urls import path
from app_users.views import RegistrationFormView, AuthFormView, ProfileView, ProfileEditView
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('register/', RegistrationFormView.as_view(), name='register'),
    path('login/', AuthFormView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('profile/<int:pk>/edit/', ProfileEditView.as_view(), name='profile_edit'),
]

