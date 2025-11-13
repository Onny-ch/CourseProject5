"""URL конфигурация для приложения habits."""
from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import HabitViewSet, PublicHabitViewSet, RegisterView

router = DefaultRouter()
router.register(r"habits", HabitViewSet, basename="habit")
router.register(r"public-habits", PublicHabitViewSet, basename="public-habit")

urlpatterns = [
    path("auth/register/", RegisterView.as_view(), name="api-register"),
] + router.urls
