"""Представления для приложения уведомлений."""
import requests
from django.conf import settings
from django.db import models
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.habits.models import Habit

from .models import Notification
from .serializers import NotificationSerializer
from .tasks import format_habit_message, send_telegram_message


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def send_message(request, habit_id: int):
    """View-функция для отправки сообщения в Telegram о привычке."""
    try:
        habit = Habit.objects.get(id=habit_id, user=request.user)
    except Habit.DoesNotExist:
        return Response(
            {"error": "Привычка не найдена"},
            status=status.HTTP_404_NOT_FOUND,
        )

    if not habit.user.tg_chat_id:
        return Response(
            {"error": "У пользователя не указан tg_chat_id"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Находим уведомление для этой привычки
    notification = Notification.objects.filter(habit=habit, user=habit.user).first()
    if not notification:
        return Response(
            {"error": "Сначала создайте уведомление с указанием времени для этой привычки"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Формируем сообщение в формате "Я буду [ДЕЙСТВИЕ] в [ВРЕМЯ] в [МЕСТО]"
    message = format_habit_message(notification)

    # Отправляем сообщение в Telegram
    if not settings.TELEGRAM_BOT_TOKEN:
        return Response(
            {"error": "Telegram бот не настроен"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    
    data = {
        "text": message,
        "chat_id": habit.user.tg_chat_id,
    }

    try:
        response = requests.post(
            f"{settings.TELEGRAM_URL}{settings.TELEGRAM_BOT_TOKEN}/sendMessage",
            json=data,
            timeout=10,
        )
        response.raise_for_status()

        # Обновляем статус уведомления
        notification.is_sent = True
        notification.sent_at = timezone.now()
        notification.save()

        return Response(
            {"message": "Уведомление отправлено успешно", "notification_id": notification.id},
            status=status.HTTP_200_OK,
        )
    except requests.RequestException as e:
        # Оставляем уведомление как неотправленное
        error_message = str(e)
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = e.response.json()
                error_message = f"{error_message}. Детали: {error_detail}"
            except:
                error_message = f"{error_message}. Ответ: {e.response.text}"
        return Response(
            {"error": f"Не удалось отправить уведомление: {error_message}", "notification_id": notification.id},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def send_notification(request, notification_id: int):
    """API endpoint для отправки уведомления."""
    try:
        notification = Notification.objects.get(
            id=notification_id, user=request.user
        )
    except Notification.DoesNotExist:
        return Response(
            {"error": "Уведомление не найдено"},
            status=status.HTTP_404_NOT_FOUND,
        )

    if not notification.user.tg_chat_id:
        return Response(
            {"error": "У пользователя не указан tg_chat_id"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    message = format_habit_message(notification)
    success = send_telegram_message(message, notification.user.tg_chat_id)

    if success:
        notification.is_sent = True
        notification.sent_at = timezone.now()
        notification.save()
        return Response(
            {"message": "Уведомление отправлено успешно"},
            status=status.HTTP_200_OK,
        )
    else:
        return Response(
            {"error": "Не удалось отправить уведомление"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


class NotificationViewSet(viewsets.ModelViewSet):
    """ViewSet для работы с уведомлениями."""

    serializer_class = NotificationSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        """Возвращает уведомления текущего пользователя."""
        return Notification.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """Создает уведомление для текущего пользователя."""
        serializer.save(user=self.request.user)
