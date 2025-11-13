"""Сериализаторы для приложения уведомлений."""
from django.db import models
from rest_framework import serializers

from apps.habits.models import Habit

from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    """Сериализатор для модели уведомления."""

    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    habit = serializers.PrimaryKeyRelatedField(
        queryset=Habit.objects.none(),  # Будет переопределено в __init__
        help_text="Привычка, о которой отправляется уведомление",
    )

    class Meta:
        model = Notification
        fields = (
            "id",
            "user",
            "habit",
            "time",
            "periodicity",
            "execution_time",
            "created_at",
            "sent_at",
            "is_sent",
        )
        read_only_fields = ("created_at", "sent_at", "is_sent")

    def __init__(self, *args, **kwargs):
        """Инициализирует сериализатор с фильтрацией привычек."""
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            # Показываем только свои привычки и публичные
            self.fields["habit"].queryset = Habit.objects.filter(
                models.Q(user=request.user) | models.Q(is_public=True)
            )

    def validate_periodicity(self, value):
        """Валидация периодичности."""
        if value < 1 or value > 7:
            raise serializers.ValidationError(
                "Периодичность должна быть от 1 до 7 дней."
            )
        return value

    def validate_execution_time(self, value):
        """Валидация времени выполнения."""
        if value and value > 120:
            raise serializers.ValidationError(
                "Время выполнения не может превышать 120 секунд."
            )
        return value

    def validate_habit(self, value):
        """Валидация привычки."""
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            # Проверяем, что привычка доступна пользователю
            if value.user != request.user and not value.is_public:
                raise serializers.ValidationError(
                    "Вы можете выбрать только свои привычки или публичные."
                )
        return value

