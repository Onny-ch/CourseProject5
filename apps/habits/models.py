from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Habit(models.Model):
    """Модель привычки пользователя"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="habits",
        verbose_name="Пользователь",
        help_text="Укажите пользователя",
    )
    place = models.CharField(
        max_length=255,
        verbose_name="Место",
        help_text="Укажите место",
    )
    action = models.CharField(
        max_length=255,
        verbose_name="Действие",
        help_text="Укажите действие",
    )
    is_pleasant = models.BooleanField(
        default=False,
        verbose_name="Признак приятной привычки",
        help_text="Укажите признак приятной привычки",
    )
    related_habit = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="related_to",
        verbose_name="Связанная привычка",
        help_text="Укажите связанную привычку",
    )
    reward = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Вознаграждение ",
        help_text="Укажите вознаграждение",
    )
    is_public = models.BooleanField(
        default=False,
        verbose_name="Признак публичности",
        help_text="Укажите признак публичности",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания",
        help_text="Дата создания записи",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Дата обновления",
        help_text="Дата последнего обновления записи",
    )

    class Meta:
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.action} ({self.user})"

    def clean(self) -> None:
        super().clean()

        if self.reward and self.related_habit_id:
            raise ValidationError(
                {
                    "reward": (
                        "Нельзя одновременно указывать вознаграждение и связанную привычку."
                    )
                }
            )

        if self.related_habit:
            if not self.related_habit.is_pleasant:
                raise ValidationError(
                    {"related_habit": "Связанной может быть только приятная привычка."}
                )
            if self.related_habit.user_id != self.user_id:
                raise ValidationError(
                    {
                        "related_habit": (
                            "Связанная привычка должна принадлежать пользователю."
                        )
                    }
                )
            if self.related_habit_id == self.id:
                raise ValidationError(
                    {"related_habit": "Нельзя связывать привычку саму с собой."}
                )

        if self.is_pleasant and (self.reward or self.related_habit_id):
            raise ValidationError(
                {
                    "is_pleasant": (
                        "Приятная привычка не может иметь вознаграждение или связь."
                    )
                }
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
