from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import MyUser

UserAdmin.fieldsets += (
    ('Extra Fields', {'fields': ('avatar',)}),
)


@admin.register(MyUser)
class UserAdmin(admin.ModelAdmin):
    search_fields = ('email', 'username',)
    list_display = ('email', 'username', 'first_name', 'last_name',)
    list_display_links = ('email', 'username',)
