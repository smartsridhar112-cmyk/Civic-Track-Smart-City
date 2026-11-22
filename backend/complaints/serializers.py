from rest_framework import serializers
from .models import Complaint, ComplaintHistory

class ComplaintHistorySerializer(serializers.ModelSerializer):
    changed_by_username = serializers.CharField(source="changed_by.username", read_only=True, default=None)
    class Meta:
        model = ComplaintHistory
        fields = ["id", "previous_status", "new_status", "remarks", "changed_by", "changed_by_username", "created_at"]
        read_only_fields = fields

class ComplaintSerializer(serializers.ModelSerializer):
    citizen_username = serializers.CharField(source="citizen.username", read_only=True)
    department_name = serializers.CharField(source="department.name", read_only=True, default=None)
    assigned_officer_username = serializers.CharField(source="assigned_officer.username", read_only=True, default=None)
    history = ComplaintHistorySerializer(many=True, read_only=True)
    class Meta:
        model = Complaint
        fields = ["id", "complaint_id", "citizen", "citizen_username", "department", "department_name", "assigned_officer", "assigned_officer_username", "title", "description", "category", "location", "latitude", "longitude", "image", "resolution_image", "status", "priority", "resolution_remarks", "rejection_reason", "created_at", "updated_at", "resolved_at", "history"]
        read_only_fields = ["id", "complaint_id", "citizen", "citizen_username", "department", "department_name", "assigned_officer", "assigned_officer_username", "status", "priority", "resolution_image", "resolution_remarks", "rejection_reason", "created_at", "updated_at", "resolved_at", "history"]
    def validate_title(self, value):
        if not value.strip():
            raise serializers.ValidationError("Complaint title cannot be empty.")
        return value.strip()
    def validate_location(self, value):
        if not value.strip():
            raise serializers.ValidationError("Location is required.")
        return value.strip()

class ComplaintStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=[Complaint.Status.IN_PROGRESS, Complaint.Status.RESOLVED, Complaint.Status.REJECTED])
    remarks = serializers.CharField(required=False, allow_blank=True)
    rejection_reason = serializers.CharField(required=False, allow_blank=True)
    resolution_image = serializers.ImageField(required=False, allow_null=True)
