from django.contrib import admin
from app_users.models import Profile


class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'registration_date', 'funds', 'is_seller', 'avatar']


admin.site.register(Profile, ProfileAdmin)
