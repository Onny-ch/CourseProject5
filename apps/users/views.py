from django.contrib.auth import get_user_model
from rest_framework import permissions, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response

from .serializers import UserLoginSerializer, UserRegistrationSerializer, UserSerializer, UserUpdateSerializer

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet для работы с пользователями."""

    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_serializer_class(self):
        """Возвращает соответствующий сериализатор в зависимости от действия."""
        if self.action in ("update", "partial_update"):
            return UserUpdateSerializer
        return UserSerializer

    def get_permissions(self):
        """Настраивает права доступа в зависимости от действия."""
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        """Возвращает queryset в зависимости от прав пользователя."""
        if self.action == "list" and not self.request.user.is_staff:
            # Обычные пользователи видят только свой профиль
            return User.objects.filter(id=self.request.user.id)
        return User.objects.all()

    def create(self, request, *args, **kwargs):
        """Запрещает создание пользователей через UserViewSet. Используйте /api/v1/auth/register/."""
        return Response(
            {"error": "Используйте /api/v1/auth/register/ для регистрации"},
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    @action(detail=False, methods=["get", "put", "patch"])
    def me(self, request):
        """Эндпоинт для получения и обновления текущего пользователя."""
        serializer = UserSerializer(request.user)
        if request.method in ("PUT", "PATCH"):
            serializer = UserUpdateSerializer(
                request.user, data=request.data, partial=request.method == "PATCH"
            )
            if serializer.is_valid():
                serializer.save()
                return Response(UserSerializer(request.user).data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.data)


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


class LoginView(CreateAPIView):
    """Эндпоинт авторизации пользователя по email, возвращающий токен аутентификации."""

    serializer_class = UserLoginSerializer
    permission_classes = (permissions.AllowAny,)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"error": "Неверный email или пароль"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not user.check_password(password):
            return Response(
                {"error": "Неверный email или пароль"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not user.is_active:
            return Response(
                {"error": "Пользователь неактивен"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        token, _ = Token.objects.get_or_create(user=user)
        return Response({"token": token.key}, status=status.HTTP_200_OK)
