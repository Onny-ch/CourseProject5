"""URL конфигурация для приложения users."""
from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import LoginView, RegisterView, UserViewSet

router = DefaultRouter()
router.register(r"users", UserViewSet, basename="user")

urlpatterns = [
    path("auth/register/", RegisterView.as_view(), name="api-register"),
    path("auth/login/", LoginView.as_view(), name="api-login"),
] + router.urls
