"""URL конфигурация для приложения habits."""
from rest_framework.routers import DefaultRouter

from .views import HabitViewSet, PublicHabitViewSet

router = DefaultRouter()
router.register(r"habits", HabitViewSet, basename="habit")
router.register(r"public-habits", PublicHabitViewSet, basename="public-habit")

urlpatterns = router.urls
