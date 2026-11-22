from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    AdminUserViewSet,
    DepartmentViewSet,
    MeView,
    OfficerRegisterView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    RegisterView,
)

router = DefaultRouter()
router.register("departments", DepartmentViewSet, basename="department")
router.register("users", AdminUserViewSet, basename="user")
urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("register-officer/", OfficerRegisterView.as_view(), name="register-officer"),
    path("password-reset/request/", PasswordResetRequestView.as_view(), name="password-reset-request"),
    path("password-reset/confirm/", PasswordResetConfirmView.as_view(), name="password-reset-confirm"),
    path("login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("me/", MeView.as_view(), name="me"),
    path("", include(router.urls)),
]
