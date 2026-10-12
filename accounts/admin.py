from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import Profile, User


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ("username", "email", "role", "is_active", "date_joined")
    list_filter = DjangoUserAdmin.list_filter + ("role",)
    search_fields = ("username", "email", "first_name", "last_name")
    fieldsets = DjangoUserAdmin.fieldsets + (("Role", {"fields": ("role",)}),)
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (("Email & role", {"fields": ("email", "role")}),)
    inlines = [ProfileInline]
