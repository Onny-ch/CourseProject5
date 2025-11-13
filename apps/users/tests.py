from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

User = get_user_model()


class UserModelTest(TestCase):
    """Тесты для модели User."""

    def test_create_user_with_email(self):
        """Тест создания пользователя с email."""
        user = User.objects.create_user(
            email="test@example.com",
            username="testuser",
            password="testpass123",
        )
        self.assertEqual(user.email, "test@example.com")
        self.assertEqual(user.username, "testuser")
        self.assertTrue(user.check_password("testpass123"))
        self.assertFalse(user.is_staff)
        self.assertTrue(user.is_active)

    def test_email_is_unique(self):
        """Тест уникальности email."""
        User.objects.create_user(
            email="test@example.com",
            username="user1",
            password="testpass123",
        )
        with self.assertRaises(Exception):
            User.objects.create_user(
                email="test@example.com",
                username="user2",
                password="testpass123",
            )

    def test_tg_chat_id_is_unique(self):
        """Тест уникальности tg_chat_id."""
        User.objects.create_user(
            email="user1@example.com",
            username="user1",
            password="testpass123",
            tg_chat_id=12345,
        )
        with self.assertRaises(Exception):
            User.objects.create_user(
                email="user2@example.com",
                username="user2",
                password="testpass123",
                tg_chat_id=12345,
            )

    def test_user_str_representation(self):
        """Тест строкового представления пользователя."""
        user = User.objects.create_user(
            email="test@example.com",
            username="testuser",
            password="testpass123",
        )
        self.assertEqual(str(user), "test@example.com")

    def test_user_fields(self):
        """Тест наличия всех полей в модели пользователя."""
        user = User.objects.create_user(
            email="test@example.com",
            username="testuser",
            password="testpass123",
            phone_number="+1234567890",
            country="Russia",
            tg_chat_id=12345,
        )
        self.assertEqual(user.phone_number, "+1234567890")
        self.assertEqual(user.country, "Russia")
        self.assertEqual(user.tg_chat_id, 12345)


class UserAPITest(APITestCase):
    """Тесты для API пользователей."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            username="testuser",
            password="testpass123",
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

    def test_get_current_user_profile(self):
        """Тест получения профиля текущего пользователя."""
        url = reverse("user-me")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], self.user.email)
        self.assertEqual(response.data["username"], self.user.username)

    def test_update_current_user_profile(self):
        """Тест обновления профиля текущего пользователя."""
        url = reverse("user-me")
        data = {
            "first_name": "Иван",
            "last_name": "Иванов",
            "phone_number": "+79001234567",
            "country": "Россия",
        }
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Иван")
        self.assertEqual(self.user.last_name, "Иванов")
        self.assertEqual(self.user.phone_number, "+79001234567")
        self.assertEqual(self.user.country, "Россия")

    def test_update_tg_chat_id(self):
        """Тест обновления tg_chat_id."""
        url = reverse("user-me")
        data = {"tg_chat_id": 123456789}
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.tg_chat_id, 123456789)

    def test_user_registration(self):
        """Тест регистрации нового пользователя."""
        url = reverse("user-list")
        data = {
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "newpass123",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email="newuser@example.com").exists())

    def test_user_cannot_access_other_users(self):
        """Тест, что пользователь не может получить доступ к чужим профилям."""
        other_user = User.objects.create_user(
            email="other@example.com",
            username="otheruser",
            password="testpass123",
        )
        url = reverse("user-detail", kwargs={"pk": other_user.id})
        response = self.client.get(url)
        # ViewSet возвращает объект, если он есть в queryset, но queryset фильтруется
        # Проверяем, что обычный пользователь не видит других пользователей в списке
        list_url = reverse("user-list")
        list_response = self.client.get(list_url)
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        # Обычный пользователь должен видеть только свой профиль
        user_ids = [user["id"] for user in list_response.data["results"]]
        self.assertIn(self.user.id, user_ids)
        self.assertNotIn(other_user.id, user_ids)

    def test_update_timezone(self):
        """Тест обновления timezone."""
        url = reverse("user-me")
        data = {"timezone": "Europe/Moscow"}
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.timezone, "Europe/Moscow")

    def test_user_list_as_staff(self):
        """Тест получения списка пользователей как staff."""
        self.user.is_staff = True
        self.user.save()

        other_user = User.objects.create_user(
            email="other@example.com",
            username="otheruser",
            password="testpass123",
        )

        url = reverse("user-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data["results"]), 2)

    def test_user_list_as_regular_user(self):
        """Тест получения списка пользователей как обычный пользователь."""
        other_user = User.objects.create_user(
            email="other@example.com",
            username="otheruser",
            password="testpass123",
        )

        url = reverse("user-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Обычный пользователь должен видеть только свой профиль
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["id"], self.user.id)

    def test_user_registration_returns_token(self):
        """Тест, что регистрация возвращает токен."""
        url = reverse("api-register")
        data = {
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "newpass123",
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("token", response.data)
        self.assertIn("user", response.data)
        self.assertIsNotNone(response.data["token"])

    def test_user_me_endpoint_put(self):
        """Тест обновления профиля через PUT."""
        url = reverse("user-me")
        data = {
            "first_name": "Иван",
            "last_name": "Иванов",
            "phone_number": "+79001234567",
        }
        response = self.client.put(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Иван")
        self.assertEqual(self.user.last_name, "Иванов")

