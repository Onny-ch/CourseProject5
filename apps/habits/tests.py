from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from .models import Habit

User = get_user_model()


class TestHabitAPI(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="tester",
            email="tester@example.com",
            password="strongpassword",
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

    def test_cannot_set_reward_and_related_habit(self):
        pleasant = Habit.objects.create(
            user=self.user,
            place="Дом",
            action="Посмотреть сериал",
            is_pleasant=True,
        )

        payload = {
            "place": "Улица",
            "action": "Быстрая прогулка",
            "is_pleasant": False,
            "related_habit": pleasant.id,
            "reward": "Десерт",
            "is_public": False,
        }

        response = self.client.post(reverse("habit-list"), payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("reward", response.data)

    def test_public_habits_list_accessible_without_auth(self):
        Habit.objects.create(
            user=self.user,
            place="Стадион",
            action="Утренняя зарядка",
            is_pleasant=False,
            reward="Завтрак",
            is_public=True,
        )

        self.client.credentials()  # удаляем аутентификацию
        response = self.client.get(reverse("public-habit-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_user_cannot_access_other_users_habits(self):
        other_user = User.objects.create_user(
            username="intruder",
            email="intruder@example.com",
            password="strongpassword",
        )
        Habit.objects.create(
            user=other_user,
            place="Офис",
            action="Читать новости",
            is_pleasant=False,
        )

        response = self.client.get(reverse("habit-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 0)

    def test_create_habit_assigns_authenticated_user(self):
        payload = {
            "place": "Дом",
            "action": "Завтрак",
            "is_pleasant": False,
            "is_public": True,
        }

        response = self.client.post(reverse("habit-list"), payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Habit.objects.count(), 1)
        habit = Habit.objects.get()
        self.assertEqual(habit.user, self.user)

    def test_list_habits(self):
        Habit.objects.create(
            user=self.user,
            place="Дом",
            action="Зарядка",
            is_pleasant=False,
        )
        Habit.objects.create(
            user=self.user,
            place="Парк",
            action="Бег",
            is_pleasant=False,
        )

        response = self.client.get(reverse("habit-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)

    def test_retrieve_habit(self):
        habit = Habit.objects.create(
            user=self.user,
            place="Дом",
            action="Зарядка",
            is_pleasant=False,
        )

        response = self.client.get(reverse("habit-detail", kwargs={"pk": habit.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["action"], "Зарядка")

    def test_update_habit(self):
        habit = Habit.objects.create(
            user=self.user,
            place="Дом",
            action="Зарядка",
            is_pleasant=False,
        )

        payload = {"place": "Парк", "action": "Бег"}
        response = self.client.patch(
            reverse("habit-detail", kwargs={"pk": habit.id}), payload, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        habit.refresh_from_db()
        self.assertEqual(habit.place, "Парк")
        self.assertEqual(habit.action, "Бег")

    def test_delete_habit(self):
        habit = Habit.objects.create(
            user=self.user,
            place="Дом",
            action="Зарядка",
            is_pleasant=False,
        )

        response = self.client.delete(reverse("habit-detail", kwargs={"pk": habit.id}))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Habit.objects.filter(id=habit.id).exists())

    def test_user_cannot_update_other_user_habit(self):
        other_user = User.objects.create_user(
            username="other",
            email="other@example.com",
            password="strongpassword",
        )
        habit = Habit.objects.create(
            user=other_user,
            place="Офис",
            action="Работа",
            is_pleasant=False,
        )

        payload = {"action": "Взлом"}
        response = self.client.patch(
            reverse("habit-detail", kwargs={"pk": habit.id}), payload, format="json"
        )
        # ViewSet возвращает 404 для несуществующих объектов в queryset пользователя
        self.assertIn(
            response.status_code,
            [status.HTTP_404_NOT_FOUND, status.HTTP_403_FORBIDDEN],
        )

    def test_any_authenticated_user_can_create_habit(self):
        other_user = User.objects.create_user(
            username="other",
            email="other@example.com",
            password="strongpassword",
        )
        other_token = Token.objects.create(user=other_user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {other_token.key}")

        payload = {
            "place": "Дом",
            "action": "Новая привычка",
            "is_pleasant": False,
        }

        response = self.client.post(reverse("habit-list"), payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        habit = Habit.objects.get(action="Новая привычка")
        self.assertEqual(habit.user, other_user)

    def test_public_habit_visible_to_all(self):
        habit = Habit.objects.create(
            user=self.user,
            place="Парк",
            action="Прогулка",
            is_pleasant=False,
            is_public=True,
        )

        self.client.credentials()
        response = self.client.get(reverse("public-habit-detail", kwargs={"pk": habit.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["action"], "Прогулка")

    def test_private_habit_not_visible_in_public_list(self):
        Habit.objects.create(
            user=self.user,
            place="Дом",
            action="Приватная привычка",
            is_pleasant=False,
            is_public=False,
        )

        self.client.credentials()
        response = self.client.get(reverse("public-habit-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 0)


class TestHabitModelValidation(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="validator",
            email="validator@example.com",
            password="strongpassword",
        )
        self.pleasant = Habit.objects.create(
            user=self.user,
            place="Лес",
            action="Прогулка",
            is_pleasant=True,
        )

    def _base_habit(self, **overrides):
        defaults = {
            "user": self.user,
            "place": "Дом",
            "action": "Зарядка",
            "is_pleasant": False,
        }
        defaults.update(overrides)
        return Habit(**defaults)

    def test_reward_and_related_habit_mutually_exclusive(self):
        habit = self._base_habit(related_habit=self.pleasant, reward="Шоколадка")
        with self.assertRaises(ValidationError):
            habit.full_clean()

    def test_related_habit_must_be_pleasant(self):
        unpleasant = self._base_habit(is_pleasant=False)
        unpleasant.save()
        habit = self._base_habit(related_habit=unpleasant)
        with self.assertRaises(ValidationError):
            habit.full_clean()

    def test_related_habit_must_belong_to_same_user(self):
        other_user = User.objects.create_user(
            username="outsider",
            email="outsider@example.com",
            password="strongpassword",
        )
        other_habit = Habit.objects.create(
            user=other_user,
            place="Парк",
            action="Бег",
            is_pleasant=True,
        )
        habit = self._base_habit(related_habit=other_habit)
        with self.assertRaises(ValidationError):
            habit.full_clean()

    def test_cannot_link_habit_to_itself(self):
        habit = self._base_habit()
        habit.save()
        habit.related_habit = habit
        with self.assertRaises(ValidationError):
            habit.full_clean()

    def test_pleasant_habit_cannot_have_reward_or_related(self):
        habit = self._base_habit(is_pleasant=True, reward="Торт")
        with self.assertRaises(ValidationError):
            habit.full_clean()

        habit = self._base_habit(is_pleasant=True, related_habit=self.pleasant)
        with self.assertRaises(ValidationError):
            habit.full_clean()

    def test_habit_str_representation(self):
        habit = self._base_habit()
        habit.save()
        self.assertEqual(str(habit), f"Зарядка ({self.user})")

    def test_habit_ordering(self):
        habit1 = self._base_habit(action="Первая")
        habit1.save()
        habit2 = self._base_habit(action="Вторая")
        habit2.save()

        habits = list(Habit.objects.all())
        self.assertEqual(habits[0], habit2)
        self.assertEqual(habits[1], habit1)
