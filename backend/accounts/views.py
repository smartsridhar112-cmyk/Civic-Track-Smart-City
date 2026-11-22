from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
from django.utils import timezone
from datetime import timedelta
from .models import Department, PasswordResetOTP
from rest_framework import generics, mixins, permissions, status, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView
from .permissions import IsAdmin
from .serializers import (
    DepartmentSerializer,
    OfficerRegisterSerializer,
    RegisterSerializer,
    UserSerializer,
)

User = get_user_model()


def issue_email_code(user, subject, message):
    recent = PasswordResetOTP.objects.filter(
        user=user,
        purpose=PasswordResetOTP.Purpose.PASSWORD_RESET,
        created_at__gte=timezone.now() - timedelta(minutes=1),
    ).exists()
    if recent:
        return
    code = get_random_string(6, allowed_chars="0123456789")
    PasswordResetOTP.objects.filter(user=user, purpose=PasswordResetOTP.Purpose.PASSWORD_RESET).delete()
    PasswordResetOTP.objects.create(
        user=user,
        purpose=PasswordResetOTP.Purpose.PASSWORD_RESET,
        code_hash=make_password(code),
        expires_at=timezone.now() + timedelta(minutes=10),
    )
    send_mail(subject, message.format(code=code), None, [user.email], fail_silently=False)


class PasswordResetRequestView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = str(request.data.get("email", "")).strip().lower()
        user = User.objects.filter(email__iexact=email, is_active=True).first() if email else None
        # Keep the response identical whether or not the account exists.
        if user:
            issue_email_code(
                user,
                "Your CivicTrack password reset code",
                "Your password reset code is {code}. It expires in 10 minutes.",
            )
        return Response({"detail": "If an active account matches that email, a reset code has been sent."})


class PasswordResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = str(request.data.get("email", "")).strip().lower()
        code = str(request.data.get("code", "")).strip()
        new_password = request.data.get("new_password", "")
        if not email or not code or not new_password:
            return Response({"detail": "Email, code, and new password are required."}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(email__iexact=email, is_active=True).first()
        reset = PasswordResetOTP.objects.filter(
            user=user,
            purpose=PasswordResetOTP.Purpose.PASSWORD_RESET,
        ).first() if user else None
        if not reset or reset.expires_at <= timezone.now() or reset.attempts >= 5:
            if reset and reset.attempts >= 5:
                reset.delete()
            return Response({"code": "The code is invalid or expired."}, status=status.HTTP_400_BAD_REQUEST)
        reset.attempts += 1
        reset.save(update_fields=["attempts"])
        if not check_password(code, reset.code_hash):
            return Response({"code": "The code is invalid or expired."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            validate_password(new_password, user=user)
        except ValidationError as exc:
            return Response({"new_password": list(exc.messages)}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save(update_fields=["password"])
        PasswordResetOTP.objects.filter(
            user=user,
            purpose=PasswordResetOTP.Purpose.PASSWORD_RESET,
        ).delete()
        return Response({"detail": "Password changed successfully. You can now sign in."})


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

class OfficerRegisterView(generics.CreateAPIView):
    serializer_class = OfficerRegisterSerializer
    permission_classes = [permissions.AllowAny]

class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        return Response(UserSerializer(request.user).data)

class DepartmentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Department.objects.all().order_by("name")
    serializer_class = DepartmentSerializer
    permission_classes = [permissions.AllowAny]

class AdminUserViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = User.objects.select_related("department").all()
    serializer_class = UserSerializer
    permission_classes = [IsAdmin]

    def update(self, request, *args, **kwargs):
        return Response(
            {"detail": "Use PATCH to update user settings."},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def partial_update(self, request, *args, **kwargs):
        user = self.get_object()
        allowed = {"role", "department", "is_active"}
        extra = set(request.data) - allowed
        if extra:
            return Response({"detail": f"Unsupported fields: {sorted(extra)}"}, status=400)
        if "role" in request.data:
            if request.data["role"] not in User.Role.values:
                return Response({"role": "Invalid role."}, status=400)
            user.role = request.data["role"]
        if "department" in request.data:
            dep_id = request.data["department"]
            if dep_id in (None, ""):
                user.department = None
            else:
                try:
                    user.department = Department.objects.get(pk=dep_id)
                except Department.DoesNotExist:
                    return Response({"department": "Department not found."}, status=400)
        if "is_active" in request.data:
            if not isinstance(request.data["is_active"], bool):
                return Response({"is_active": "Must be true or false."}, status=400)
            user.is_active = request.data["is_active"]
        user.save()
        return Response(UserSerializer(user).data)
