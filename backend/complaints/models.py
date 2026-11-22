import uuid
from django.conf import settings
from django.db import models

class Complaint(models.Model):
    class Category(models.TextChoices):
        ROAD = "ROAD", "Road Damage"
        GARBAGE = "GARBAGE", "Garbage"
        WATER = "WATER", "Water Supply"
        ELECTRICITY = "ELECTRICITY", "Electricity"
        DRAINAGE = "DRAINAGE", "Drainage"
        OTHER = "OTHER", "Other"
    class Status(models.TextChoices):
        SUBMITTED = "SUBMITTED", "Submitted"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        RESOLVED = "RESOLVED", "Resolved"
        REJECTED = "REJECTED", "Rejected"
    class Priority(models.TextChoices):
        LOW = "LOW", "Low"
        MEDIUM = "MEDIUM", "Medium"
        HIGH = "HIGH", "High"
        URGENT = "URGENT", "Urgent"
    complaint_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    citizen = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="complaints")
    department = models.ForeignKey("accounts.Department", on_delete=models.SET_NULL, null=True, blank=True, related_name="complaints")
    assigned_officer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_complaints")
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.OTHER)
    location = models.CharField(max_length=255)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    image = models.ImageField(upload_to="complaints/original/", null=True, blank=True)
    resolution_image = models.ImageField(upload_to="complaints/resolutions/", null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SUBMITTED)
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.MEDIUM)
    resolution_remarks = models.TextField(blank=True)
    rejection_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    class Meta:
        ordering = ["-created_at"]
    def __str__(self):
        return f"{self.title} ({self.complaint_id})"

class ComplaintHistory(models.Model):
    complaint = models.ForeignKey(Complaint, on_delete=models.CASCADE, related_name="history")
    previous_status = models.CharField(max_length=20, choices=Complaint.Status.choices, blank=True)
    new_status = models.CharField(max_length=20, choices=Complaint.Status.choices)
    remarks = models.TextField(blank=True)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="complaint_history_entries")
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ["created_at"]
    def __str__(self):
        return f"{self.complaint.complaint_id}: {self.previous_status} -> {self.new_status}"
