from django.contrib.auth import get_user_model
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.generics import CreateAPIView

from apps.users.serializers import UserRegistrationSerializer

from .models import Habit
from .permissions import IsOwner
from .serializers import HabitSerializer

User = get_user_model()


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


class RegisterView(CreateAPIView):
    """Эндпоинт регистрации пользователя, возвращающий токен аутентификации."""

    serializer_class = UserRegistrationSerializer
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)

    def perform_create(self, serializer):
        self.user = serializer.save()
        self.token, _ = Token.objects.get_or_create(user=self.user)

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        response.data = {
            "user": UserRegistrationSerializer(self.user).data,
            "token": self.token.key,
        }
        response.status_code = status.HTTP_201_CREATED
        return response
