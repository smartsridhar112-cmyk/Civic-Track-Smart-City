from django.contrib.auth import get_user_model
from rest_framework import generics, mixins, permissions, status, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Department
from .permissions import IsAdmin
from .serializers import (
    DepartmentSerializer,
    OfficerRegisterSerializer,
    RegisterSerializer,
    UserSerializer,
)

User = get_user_model()

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
