from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Department

User = get_user_model()

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ["id", "name", "description", "complaint_category"]

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "phone", "password", "password_confirm"]
        read_only_fields = ["id"]
    def validate_email(self, value):
        value = value.lower().strip()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value
    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        return attrs
    def create(self, validated_data):
        validated_data.pop("password_confirm")
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.role = User.Role.CITIZEN
        user.set_password(password)
        user.save()
        return user

class OfficerRegisterSerializer(RegisterSerializer):
    """Public officer signup creates an inactive account pending admin approval."""
    department = serializers.PrimaryKeyRelatedField(queryset=Department.objects.all())

    class Meta(RegisterSerializer.Meta):
        fields = RegisterSerializer.Meta.fields + ["department"]

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.role = User.Role.OFFICER
        user.is_active = False
        user.set_password(password)
        user.save()
        return user

class UserSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source="department.name", read_only=True, default=None)
    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "phone", "role", "department", "department_name", "is_active"]
        read_only_fields = fields
