from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    AdminUserViewSet,
    DepartmentViewSet,
    MeView,
    OfficerRegisterView,
    RegisterView,
)

router = DefaultRouter()
router.register("departments", DepartmentViewSet, basename="department")
router.register("users", AdminUserViewSet, basename="user")
urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("register-officer/", OfficerRegisterView.as_view(), name="register-officer"),
    path("login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("me/", MeView.as_view(), name="me"),
    path("", include(router.urls)),
]
