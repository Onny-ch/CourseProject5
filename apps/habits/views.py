from rest_framework import mixins, permissions, viewsets

from .models import Habit
from .permissions import IsOwner
from .serializers import HabitSerializer


class HabitViewSet(viewsets.ModelViewSet):
    """CRUD операции для привычек текущего пользователя."""

    serializer_class = HabitSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        """Возвращает привычки текущего пользователя."""
        return Habit.objects.filter(user=self.request.user)

    def get_permissions(self):
        """Настраивает права доступа: создание доступно всем, остальное - только владельцу."""
        if self.action == "create":
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated(), IsOwner()]

    def perform_create(self, serializer):
        """Создает привычку для текущего пользователя."""
        serializer.save(user=self.request.user)


class PublicHabitViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    """Доступ только для чтения к публичным привычкам."""

    queryset = Habit.objects.filter(is_public=True)
    serializer_class = HabitSerializer
    permission_classes = (permissions.AllowAny,)
