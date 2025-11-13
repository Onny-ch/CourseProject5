"""Тесты для приложения уведомлений."""
from datetime import time
from unittest.mock import Mock, patch

import pytz
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from apps.habits.models import Habit

from .models import Notification
from .tasks import format_habit_message, send_daily_reminders, send_habit_reminder, send_telegram_message

User = get_user_model()


class NotificationModelTest(TestCase):
    """Тесты для модели Notification."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            username="testuser",
            password="testpass123",
        )
        self.habit = Habit.objects.create(
            user=self.user,
            place="Дом",
            action="Зарядка",
            is_pleasant=False,
        )

    def test_create_notification(self):
        """Тест создания уведомления."""
        notification = Notification.objects.create(
            user=self.user,
            habit=self.habit,
            time=time(9, 0),
            periodicity=1,
            execution_time=10,
        )
        self.assertEqual(notification.user, self.user)
        self.assertEqual(notification.habit, self.habit)
        self.assertEqual(notification.time, time(9, 0))
        self.assertEqual(notification.periodicity, 1)
        self.assertEqual(notification.execution_time, 10)
        self.assertFalse(notification.is_sent)
        self.assertIsNone(notification.sent_at)

    def test_notification_default_values(self):
        """Тест значений по умолчанию."""
        notification = Notification.objects.create(
            user=self.user,
            habit=self.habit,
        )
        self.assertEqual(notification.time, time(9, 0))
        self.assertEqual(notification.periodicity, 1)
        self.assertEqual(notification.execution_time, 10)

    def test_execution_time_validation_max(self):
        """Тест валидации максимального времени выполнения."""
        notification = Notification(
            user=self.user,
            habit=self.habit,
            execution_time=Notification.MAX_EXECUTION_TIME + 1,
        )
        with self.assertRaises(ValidationError):
            notification.full_clean()

    def test_execution_time_validation_valid(self):
        """Тест валидации допустимого времени выполнения."""
        notification = Notification(
            user=self.user,
            habit=self.habit,
            execution_time=Notification.MAX_EXECUTION_TIME,
        )
        notification.full_clean()
        notification.save()
        self.assertEqual(notification.execution_time, Notification.MAX_EXECUTION_TIME)

    def test_periodicity_validation_min(self):
        """Тест валидации минимальной периодичности."""
        notification = Notification(
            user=self.user,
            habit=self.habit,
            periodicity=Notification.MIN_PERIODICITY - 1,
        )
        with self.assertRaises(ValidationError):
            notification.full_clean()

    def test_periodicity_validation_max(self):
        """Тест валидации максимальной периодичности."""
        notification = Notification(
            user=self.user,
            habit=self.habit,
            periodicity=Notification.MAX_PERIODICITY + 1,
        )
        with self.assertRaises(ValidationError):
            notification.full_clean()

    def test_periodicity_validation_valid(self):
        """Тест валидации допустимой периодичности."""
        for periodicity in range(
            Notification.MIN_PERIODICITY, Notification.MAX_PERIODICITY + 1
        ):
            notification = Notification(
                user=self.user,
                habit=self.habit,
                periodicity=periodicity,
            )
            notification.full_clean()
            notification.save()
            self.assertEqual(notification.periodicity, periodicity)

    def test_notification_str_representation(self):
        """Тест строкового представления уведомления."""
        notification = Notification.objects.create(
            user=self.user,
            habit=self.habit,
        )
        expected = f"Уведомление для {self.user} о {self.habit}"
        self.assertEqual(str(notification), expected)

    def test_notification_ordering(self):
        """Тест сортировки уведомлений."""
        notification1 = Notification.objects.create(
            user=self.user,
            habit=self.habit,
        )
        notification2 = Notification.objects.create(
            user=self.user,
            habit=self.habit,
        )

        notifications = list(Notification.objects.all())
        self.assertEqual(notifications[0], notification2)
        self.assertEqual(notifications[1], notification1)


class NotificationSerializerTest(TestCase):
    """Тесты для сериализатора Notification."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            username="testuser",
            password="testpass123",
        )
        self.habit = Habit.objects.create(
            user=self.user,
            place="Дом",
            action="Зарядка",
            is_pleasant=False,
        )
        self.other_user = User.objects.create_user(
            email="other@example.com",
            username="otheruser",
            password="testpass123",
        )
        self.public_habit = Habit.objects.create(
            user=self.other_user,
            place="Парк",
            action="Бег",
            is_pleasant=False,
            is_public=True,
        )

    def test_validate_periodicity_min(self):
        """Тест валидации минимальной периодичности в сериализаторе."""
        from rest_framework.test import APIRequestFactory

        from .serializers import NotificationSerializer

        factory = APIRequestFactory()
        request = factory.get("/")
        request.user = self.user

        serializer = NotificationSerializer(
            data={
                "habit": self.habit.id,
                "periodicity": 0,
            },
            context={"request": request},
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("periodicity", serializer.errors)

    def test_validate_periodicity_max(self):
        """Тест валидации максимальной периодичности в сериализаторе."""
        from rest_framework.test import APIRequestFactory

        from .serializers import NotificationSerializer

        factory = APIRequestFactory()
        request = factory.get("/")
        request.user = self.user

        serializer = NotificationSerializer(
            data={
                "habit": self.habit.id,
                "periodicity": 8,
            },
            context={"request": request},
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("periodicity", serializer.errors)

    def test_validate_execution_time_max(self):
        """Тест валидации максимального времени выполнения в сериализаторе."""
        from rest_framework.test import APIRequestFactory

        from .serializers import NotificationSerializer

        factory = APIRequestFactory()
        request = factory.get("/")
        request.user = self.user

        serializer = NotificationSerializer(
            data={
                "habit": self.habit.id,
                "execution_time": 121,
            },
            context={"request": request},
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("execution_time", serializer.errors)

    def test_validate_habit_own_habit(self):
        """Тест валидации собственной привычки."""
        from rest_framework.test import APIRequestFactory

        from .serializers import NotificationSerializer

        factory = APIRequestFactory()
        request = factory.get("/")
        request.user = self.user

        serializer = NotificationSerializer(
            data={
                "habit": self.habit.id,
            },
            context={"request": request},
        )
        self.assertTrue(serializer.is_valid())

    def test_validate_habit_public_habit(self):
        """Тест валидации публичной привычки."""
        from rest_framework.test import APIRequestFactory

        from .serializers import NotificationSerializer

        factory = APIRequestFactory()
        request = factory.get("/")
        request.user = self.user

        serializer = NotificationSerializer(
            data={
                "habit": self.public_habit.id,
            },
            context={"request": request},
        )
        self.assertTrue(serializer.is_valid())

    def test_validate_habit_private_other_user(self):
        """Тест валидации приватной привычки другого пользователя."""
        from rest_framework.test import APIRequestFactory

        from .serializers import NotificationSerializer

        private_habit = Habit.objects.create(
            user=self.other_user,
            place="Офис",
            action="Работа",
            is_pleasant=False,
            is_public=False,
        )

        factory = APIRequestFactory()
        request = factory.get("/")
        request.user = self.user

        serializer = NotificationSerializer(
            data={
                "habit": private_habit.id,
            },
            context={"request": request},
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("habit", serializer.errors)


class NotificationAPITest(APITestCase):
    """Тесты для API уведомлений."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            username="testuser",
            password="testpass123",
            tg_chat_id=123456789,
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

        self.habit = Habit.objects.create(
            user=self.user,
            place="Дом",
            action="Зарядка",
            is_pleasant=False,
        )

        self.other_user = User.objects.create_user(
            email="other@example.com",
            username="otheruser",
            password="testpass123",
        )
        self.public_habit = Habit.objects.create(
            user=self.other_user,
            place="Парк",
            action="Бег",
            is_pleasant=False,
            is_public=True,
        )

    def test_create_notification(self):
        """Тест создания уведомления."""
        payload = {
            "habit": self.habit.id,
            "time": "09:00:00",
            "periodicity": 1,
            "execution_time": 10,
        }

        response = self.client.post(
            reverse("notification-list"), payload, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Notification.objects.count(), 1)
        notification = Notification.objects.get()
        self.assertEqual(notification.user, self.user)
        self.assertEqual(notification.habit, self.habit)

    def test_create_notification_with_public_habit(self):
        """Тест создания уведомления с публичной привычкой."""
        payload = {
            "habit": self.public_habit.id,
            "time": "10:00:00",
            "periodicity": 2,
        }

        response = self.client.post(
            reverse("notification-list"), payload, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        notification = Notification.objects.get()
        self.assertEqual(notification.habit, self.public_habit)

    def test_list_notifications(self):
        """Тест получения списка уведомлений."""
        Notification.objects.create(
            user=self.user,
            habit=self.habit,
            time=time(9, 0),
        )
        Notification.objects.create(
            user=self.user,
            habit=self.habit,
            time=time(10, 0),
        )

        response = self.client.get(reverse("notification-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)

    def test_retrieve_notification(self):
        """Тест получения уведомления."""
        notification = Notification.objects.create(
            user=self.user,
            habit=self.habit,
            time=time(9, 0),
        )

        response = self.client.get(
            reverse("notification-detail", kwargs={"pk": notification.id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["habit"], self.habit.id)

    def test_update_notification(self):
        """Тест обновления уведомления."""
        notification = Notification.objects.create(
            user=self.user,
            habit=self.habit,
            time=time(9, 0),
            periodicity=1,
        )

        payload = {"time": "10:00:00", "periodicity": 2}
        response = self.client.patch(
            reverse("notification-detail", kwargs={"pk": notification.id}),
            payload,
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        notification.refresh_from_db()
        self.assertEqual(notification.time, time(10, 0))
        self.assertEqual(notification.periodicity, 2)

    def test_delete_notification(self):
        """Тест удаления уведомления."""
        notification = Notification.objects.create(
            user=self.user,
            habit=self.habit,
            time=time(9, 0),
        )

        response = self.client.delete(
            reverse("notification-detail", kwargs={"pk": notification.id})
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Notification.objects.filter(id=notification.id).exists())

    def test_user_cannot_access_other_user_notifications(self):
        """Тест, что пользователь не может получить доступ к чужим уведомлениям."""
        other_notification = Notification.objects.create(
            user=self.other_user,
            habit=self.public_habit,
            time=time(9, 0),
        )

        response = self.client.get(
            reverse("notification-detail", kwargs={"pk": other_notification.id})
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_send_message_success(self):
        """Тест успешной отправки сообщения."""
        notification = Notification.objects.create(
            user=self.user,
            habit=self.habit,
            time=time(9, 0),
        )

        with patch("apps.notifications.views.requests.post") as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.raise_for_status = Mock()
            mock_post.return_value = mock_response

            response = self.client.post(
                reverse("habit-send-message", kwargs={"habit_id": self.habit.id})
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            notification.refresh_from_db()
            self.assertTrue(notification.is_sent)
            self.assertIsNotNone(notification.sent_at)

    def test_send_message_habit_not_found(self):
        """Тест отправки сообщения для несуществующей привычки."""
        response = self.client.post(
            reverse("habit-send-message", kwargs={"habit_id": 999})
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_send_message_no_tg_chat_id(self):
        """Тест отправки сообщения без tg_chat_id."""
        self.user.tg_chat_id = None
        self.user.save()

        response = self.client.post(
            reverse("habit-send-message", kwargs={"habit_id": self.habit.id})
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("tg_chat_id", response.data["error"])

    def test_send_message_no_notification(self):
        """Тест отправки сообщения без уведомления."""
        response = self.client.post(
            reverse("habit-send-message", kwargs={"habit_id": self.habit.id})
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("уведомление", response.data["error"].lower())

    def test_send_notification_endpoint(self):
        """Тест эндпоинта отправки уведомления."""
        notification = Notification.objects.create(
            user=self.user,
            habit=self.habit,
            time=time(9, 0),
        )

        with patch("apps.notifications.views.send_telegram_message") as mock_send:
            mock_send.return_value = True

            response = self.client.post(
                reverse(
                    "notification-send", kwargs={"notification_id": notification.id}
                )
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            notification.refresh_from_db()
            self.assertTrue(notification.is_sent)


class NotificationTasksTest(TestCase):
    """Тесты для задач Celery."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            username="testuser",
            password="testpass123",
            tg_chat_id=123456789,
            timezone="UTC",
        )
        self.habit = Habit.objects.create(
            user=self.user,
            place="Дом",
            action="Зарядка",
            is_pleasant=False,
        )

    def test_format_habit_message(self):
        """Тест форматирования сообщения о привычке."""
        notification = Notification.objects.create(
            user=self.user,
            habit=self.habit,
            time=time(9, 0),
        )

        message = format_habit_message(notification)
        self.assertEqual(message, "Я буду Зарядка в 09:00 в Дом")

    @patch("apps.notifications.tasks.settings")
    @patch("apps.notifications.tasks.requests.post")
    def test_send_telegram_message_success(self, mock_post, mock_settings):
        """Тест успешной отправки сообщения в Telegram."""
        mock_settings.TELEGRAM_BOT_TOKEN = "test_token"
        mock_settings.TELEGRAM_URL = "https://api.telegram.org/bot"

        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        result = send_telegram_message("Тестовое сообщение", 123456789)
        self.assertTrue(result)
        mock_post.assert_called_once()

    @patch("apps.notifications.tasks.settings")
    def test_send_telegram_message_no_token(self, mock_settings):
        """Тест отправки сообщения без токена."""
        mock_settings.TELEGRAM_BOT_TOKEN = None

        result = send_telegram_message("Тестовое сообщение", 123456789)
        self.assertFalse(result)

    @patch("apps.notifications.tasks.settings")
    @patch("apps.notifications.tasks.requests.post")
    def test_send_telegram_message_failure(self, mock_post, mock_settings):
        """Тест неудачной отправки сообщения в Telegram."""
        mock_settings.TELEGRAM_BOT_TOKEN = "test_token"
        mock_settings.TELEGRAM_URL = "https://api.telegram.org/bot"

        import requests

        mock_post.side_effect = requests.RequestException("Connection error")

        result = send_telegram_message("Тестовое сообщение", 123456789)
        self.assertFalse(result)

    @patch("apps.notifications.tasks.send_telegram_message")
    def test_send_habit_reminder_success(self, mock_send):
        """Тест успешной отправки напоминания о привычке."""
        mock_send.return_value = True

        notification = Notification.objects.create(
            user=self.user,
            habit=self.habit,
            time=time(9, 0),
        )

        send_habit_reminder(notification.id)

        notification.refresh_from_db()
        self.assertTrue(notification.is_sent)
        self.assertIsNotNone(notification.sent_at)
        mock_send.assert_called_once()

    def test_send_habit_reminder_notification_not_found(self):
        """Тест отправки напоминания для несуществующего уведомления."""
        send_habit_reminder(999)
        # Не должно быть исключений

    def test_send_habit_reminder_no_tg_chat_id(self):
        """Тест отправки напоминания без tg_chat_id."""
        self.user.tg_chat_id = None
        self.user.save()

        notification = Notification.objects.create(
            user=self.user,
            habit=self.habit,
            time=time(9, 0),
        )

        send_habit_reminder(notification.id)

        notification.refresh_from_db()
        self.assertFalse(notification.is_sent)

    @patch("apps.notifications.tasks.send_telegram_message")
    @patch("apps.notifications.tasks.timezone")
    def test_send_daily_reminders_time_match(self, mock_timezone, mock_send):
        """Тест отправки ежедневных напоминаний при совпадении времени."""
        mock_send.return_value = True

        # Устанавливаем текущее время
        now = timezone.now().replace(hour=9, minute=0, second=0, microsecond=0)
        mock_timezone.now.return_value = now

        notification = Notification.objects.create(
            user=self.user,
            habit=self.habit,
            time=time(9, 0),
            periodicity=1,
        )

        send_daily_reminders()

        notification.refresh_from_db()
        self.assertTrue(notification.is_sent)
        self.assertIsNotNone(notification.sent_at)

    @patch("apps.notifications.tasks.timezone")
    def test_send_daily_reminders_time_no_match(self, mock_timezone):
        """Тест отправки ежедневных напоминаний при несовпадении времени."""
        # Устанавливаем текущее время
        from datetime import datetime

        now = datetime(2024, 1, 1, 10, 0, 0)
        now = pytz.UTC.localize(now)
        mock_timezone.now.return_value = now

        notification = Notification.objects.create(
            user=self.user,
            habit=self.habit,
            time=time(9, 0),
            periodicity=1,
        )

        send_daily_reminders()

        notification.refresh_from_db()
        self.assertFalse(notification.is_sent)

    @patch("apps.notifications.tasks.send_telegram_message")
    @patch("apps.notifications.tasks.timezone")
    def test_send_daily_reminders_periodicity(self, mock_timezone, mock_send):
        """Тест отправки ежедневных напоминаний с учетом периодичности."""
        mock_send.return_value = True

        # Устанавливаем текущее время
        from datetime import datetime, timedelta

        now = datetime(2024, 1, 2, 9, 0, 0)
        now = pytz.UTC.localize(now)
        mock_timezone.now.return_value = now

        notification = Notification.objects.create(
            user=self.user,
            habit=self.habit,
            time=time(9, 0),
            periodicity=2,
        )

        # Устанавливаем sent_at на вчера
        yesterday = now - timedelta(days=1)
        notification.sent_at = yesterday
        notification.is_sent = True
        notification.save()

        send_daily_reminders()

        # Не должно отправиться, так как прошло только 1 день, а periodicity=2
        notification.refresh_from_db()
        # Проверяем, что sent_at не изменился
        self.assertEqual(notification.sent_at.date(), yesterday.date())

    @patch("apps.notifications.tasks.send_telegram_message")
    @patch("apps.notifications.tasks.timezone")
    def test_send_daily_reminders_timezone(self, mock_timezone, mock_send):
        """Тест отправки ежедневных напоминаний с учетом timezone."""
        mock_send.return_value = True

        # Устанавливаем timezone пользователя
        self.user.timezone = "Europe/Moscow"
        self.user.save()

        # Устанавливаем текущее время UTC (например, 6:00 UTC = 9:00 MSK)
        from datetime import datetime

        now = datetime(2024, 1, 1, 6, 0, 0)
        now = pytz.UTC.localize(now)
        mock_timezone.now.return_value = now

        notification = Notification.objects.create(
            user=self.user,
            habit=self.habit,
            time=time(9, 0),  # 9:00 в timezone пользователя
            periodicity=1,
        )

        send_daily_reminders()

        notification.refresh_from_db()
        self.assertTrue(notification.is_sent)
