from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Пользовательская модель пользователей."""

    email = models.EmailField(
        unique=True,
        verbose_name="Email",
        help_text="Укажите email адрес",
    )
    avatar = models.ImageField(
        upload_to="avatars/",
        null=True,
        blank=True,
        verbose_name="Аватар",
        help_text="Загрузите аватар",
    )
    phone_number = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name="Номер телефона",
        help_text="Укажите номер телефона",
    )
    country = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="Страна",
        help_text="Укажите страну",
    )
    tg_chat_id = models.BigIntegerField(
        null=True,
        blank=True,
        unique=True,
        verbose_name="Телеграм chat-id",
        help_text="Укажите телеграм chat-id",
    )
    timezone = models.CharField(
        max_length=50,
        default="UTC",
        verbose_name="Часовой пояс",
        help_text="Часовой пояс пользователя (например, Europe/Moscow, UTC)",
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ("-date_joined",)

    def __str__(self) -> str:
        return self.email
