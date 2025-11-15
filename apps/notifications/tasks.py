"""Задачи Celery для отправки уведомлений."""
from datetime import datetime

import pytz
import requests
from django.conf import settings
from django.utils import timezone

from celery import shared_task

from .models import Notification


def format_habit_message(notification) -> str:
    """Форматирует сообщение о привычке в формате "Я буду [ДЕЙСТВИЕ] в [ВРЕМЯ] в [МЕСТО]"."""
    time_str = notification.time.strftime("%H:%M")
    return (
        f"Я буду {notification.habit.action} в {time_str} в {notification.habit.place}"
    )


def send_telegram_message(text: str, chat_id: int) -> bool:
    """Вспомогательная функция для отправки сообщения в Telegram."""
    if not settings.TELEGRAM_BOT_TOKEN:
        return False

    data = {
        "text": text,
        "chat_id": chat_id,
    }
    try:
        response = requests.post(
            f"{settings.TELEGRAM_URL}{settings.TELEGRAM_BOT_TOKEN}/sendMessage",
            json=data,
            timeout=10,
        )
        response.raise_for_status()
        return True
    except requests.RequestException as e:
        # Логируем ошибку для отладки
        if hasattr(e, "response") and e.response is not None:
            try:
                error_detail = e.response.json()
                print(f"Telegram API error: {error_detail}")
            except Exception:
                print(f"Telegram API error: {e.response.text}")
        return False


@shared_task
def send_habit_reminder(notification_id: int) -> None:
    """Отправляет напоминание о привычке через Telegram."""
    try:
        notification = Notification.objects.get(id=notification_id)
    except Notification.DoesNotExist:
        return

    # Проверяем, что у пользователя есть tg_chat_id
    if not notification.user.tg_chat_id:
        return

    # Формируем и отправляем сообщение
    message = format_habit_message(notification)
    success = send_telegram_message(message, notification.user.tg_chat_id)

    if success:
        notification.is_sent = True
        notification.sent_at = timezone.now()
        notification.save()


@shared_task
def send_daily_reminders() -> None:
    """
    Отправляет ежедневные напоминания о привычках через celery-beat.
    Проверяет все активные уведомления и отправляет их согласно времени и периодичности из модели.
    """
    now = timezone.now()
    current_time = now.time()
    current_date = now.date()

    # Получаем все активные уведомления (с указанным tg_chat_id)
    notifications = Notification.objects.filter(
        user__tg_chat_id__isnull=False,
    ).select_related("user", "habit")

    for notification in notifications:
        # Проверяем, что у пользователя есть tg_chat_id
        if not notification.user.tg_chat_id:
            continue

        # Получаем timezone пользователя (по умолчанию UTC)
        user_timezone_str = notification.user.timezone or "UTC"

        if user_timezone_str == "UTC":
            # Вычисляем разницу между временем уведомления и текущим UTC временем
            notification_hour = notification.time.hour
            current_hour = current_time.hour
            hour_diff = notification_hour - current_hour

            # Если разница больше 2 часов, возможно это локальное время
            if abs(hour_diff) > 2:
                time_diff = abs(
                    (current_time.hour * 60 + current_time.minute)
                    - (notification.time.hour * 60 + notification.time.minute)
                )

                if time_diff <= 1:
                    if (
                        not notification.sent_at
                        or notification.sent_at.date() != current_date
                    ):
                        message = format_habit_message(notification)
                        success = send_telegram_message(
                            message, notification.user.tg_chat_id
                        )
                        if success:
                            notification.is_sent = True
                            notification.sent_at = timezone.now()
                            notification.save()
                    continue

        try:
            user_tz = pytz.timezone(user_timezone_str)
        except pytz.exceptions.UnknownTimeZoneError:
            # Если timezone неизвестен, используем UTC
            user_tz = pytz.UTC

        # Получаем текущее время в timezone пользователя
        user_local_now = now.astimezone(user_tz)
        user_local_date = user_local_now.date()

        # Создаем datetime с текущей датой и временем уведомления в timezone пользователя
        notification_datetime_user_tz = user_tz.localize(
            datetime.combine(user_local_date, notification.time)
        )
        # Конвертируем в UTC для сравнения
        notification_datetime_utc = notification_datetime_user_tz.astimezone(pytz.UTC)
        notification_time_utc = notification_datetime_utc.time()

        # Сравниваем текущее время UTC с временем уведомления в UTC
        time_diff = abs(
            (current_time.hour * 60 + current_time.minute)
            - (notification_time_utc.hour * 60 + notification_time_utc.minute)
        )
        if user_timezone_str == "UTC" and notification.time > current_time:
            direct_time_diff = abs(
                (current_time.hour * 60 + current_time.minute)
                - (notification.time.hour * 60 + notification.time.minute)
            )
            # Если прямая разница меньше, используем её
            if direct_time_diff < time_diff:
                time_diff = direct_time_diff

        if time_diff <= 1:
            # Проверяем, не отправляли ли уже это уведомление сегодня (в timezone пользователя)
            if notification.sent_at:
                # Конвертируем sent_at в timezone пользователя для сравнения
                sent_at_user_tz = notification.sent_at.astimezone(user_tz).date()
                if sent_at_user_tz == user_local_date:
                    continue

            # Если уведомление еще не отправлялось, отправляем его сразу
            should_send = False
            if not notification.sent_at:
                should_send = True
            else:
                # Если уведомление уже отправлялось, проверяем периодичность
                sent_at_user_tz = notification.sent_at.astimezone(user_tz).date()
                days_since_last_sent = (user_local_date - sent_at_user_tz).days

                # Проверяем, нужно ли отправлять уведомление согласно periodicity
                if days_since_last_sent >= notification.periodicity:
                    should_send = True

            if should_send:
                # Отправляем уведомление
                message = format_habit_message(notification)
                success = send_telegram_message(message, notification.user.tg_chat_id)

                if success:
                    # Обновляем статус отправки
                    notification.is_sent = True
                    notification.sent_at = timezone.now()
                    notification.save()
