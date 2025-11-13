from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для модели пользователя."""

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "avatar",
            "phone_number",
            "country",
            "tg_chat_id",
            "timezone",
            "is_active",
            "date_joined",
            "last_login",
        )
        read_only_fields = ("id", "date_joined", "last_login", "is_active")


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Сериализатор для регистрации нового пользователя."""

    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ("id", "email", "username", "password")
        extra_kwargs = {
            "email": {"required": True},
        }

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class UserUpdateSerializer(serializers.ModelSerializer):
    """Сериализатор для обновления профиля пользователя."""

    class Meta:
        model = User
        fields = (
            "first_name",
            "last_name",
            "avatar",
            "phone_number",
            "country",
            "tg_chat_id",
            "timezone",
        )
