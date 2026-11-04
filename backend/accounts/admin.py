from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Department, User

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "complaint_category"]
    search_fields = ["name"]
    list_filter = ["complaint_category"]

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ["username", "email", "role", "department", "is_active"]
    list_filter = ["role", "department", "is_active"]
    search_fields = ["username", "email", "phone"]
    fieldsets = BaseUserAdmin.fieldsets + (("CivicTrack Details", {"fields": ("phone", "role", "department")}),)
    add_fieldsets = BaseUserAdmin.add_fieldsets + (("CivicTrack Details", {"fields": ("email", "phone", "role", "department")}),)
