from django.contrib.auth.models import AbstractUser
from django.db import models

class Department(models.Model):
    class ComplaintCategory(models.TextChoices):
        ROAD = "ROAD", "Road Damage"
        GARBAGE = "GARBAGE", "Garbage"
        WATER = "WATER", "Water Supply"
        ELECTRICITY = "ELECTRICITY", "Electricity"
        DRAINAGE = "DRAINAGE", "Drainage"
        OTHER = "OTHER", "Other"

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    complaint_category = models.CharField(
        max_length=20,
        choices=ComplaintCategory.choices,
        null=True,
        blank=True,
        unique=True,
    )
    def __str__(self):
        return self.name

class User(AbstractUser):
    class Role(models.TextChoices):
        CITIZEN = "CITIZEN", "Citizen"
        OFFICER = "OFFICER", "Department Officer"
        ADMIN = "ADMIN", "Administrator"
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.CITIZEN)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name="officers")
    def __str__(self):
        return f"{self.username} ({self.role})"
