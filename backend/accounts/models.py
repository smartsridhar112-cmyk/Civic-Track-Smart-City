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
    # Retained for existing databases; signup does not require email verification.
    email_verified = models.BooleanField(default=True)
    phone = models.CharField(max_length=20, blank=True)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.CITIZEN)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name="officers")
    def __str__(self):
        return f"{self.username} ({self.role})"


class PasswordResetOTP(models.Model):
    class Purpose(models.TextChoices):
        PASSWORD_RESET = "PASSWORD_RESET", "Password reset"
        EMAIL_VERIFICATION = "EMAIL_VERIFICATION", "Email verification"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="password_reset_otps")
    purpose = models.CharField(max_length=20, choices=Purpose.choices, default=Purpose.PASSWORD_RESET)
    code_hash = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    attempts = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["-created_at"]
