from django.contrib import admin
from .models import Complaint, ComplaintHistory

class ComplaintHistoryInline(admin.TabularInline):
    model = ComplaintHistory
    extra = 0
    can_delete = False
    readonly_fields = ["previous_status", "new_status", "remarks", "changed_by", "created_at"]
    def has_add_permission(self, request, obj=None):
        return False

@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ["complaint_id", "title", "citizen", "department", "assigned_officer", "category", "status", "priority", "created_at"]
    list_filter = ["status", "category", "priority", "department"]
    search_fields = ["title", "description", "location", "citizen__username"]
    readonly_fields = ["complaint_id", "created_at", "updated_at", "resolved_at"]
    inlines = [ComplaintHistoryInline]

@admin.register(ComplaintHistory)
class ComplaintHistoryAdmin(admin.ModelAdmin):
    list_display = ["complaint", "previous_status", "new_status", "changed_by", "created_at"]
    readonly_fields = ["complaint", "previous_status", "new_status", "remarks", "changed_by", "created_at"]
    def has_add_permission(self, request):
        return False
    def has_change_permission(self, request, obj=None):
        return False
