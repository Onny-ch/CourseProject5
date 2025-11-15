"""Модели для приложения уведомлений."""
from datetime import time

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class Notification(models.Model):
    """Модель уведомления о привычке."""

    MAX_EXECUTION_TIME = 120
    MIN_PERIODICITY = 1
    MAX_PERIODICITY = 7

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name="Пользователь",
        help_text="Пользователь, которому отправляется уведомление",
    )
    habit = models.ForeignKey(
        "habits.Habit",
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name="Привычка",
        help_text="Привычка, о которой отправляется уведомление",
    )
    time = models.TimeField(
        default=time(9, 0),
        verbose_name="Время",
        help_text="Время выполнения привычки",
    )
    periodicity = models.PositiveSmallIntegerField(
        default=1,
        verbose_name="Периодичность",
        help_text="Периодичность выполнения в днях (от 1 до 7)",
    )
    execution_time = models.PositiveSmallIntegerField(
        default=10,
        verbose_name="Время на выполнение",
        help_text="Время на выполнение в секундах",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата создания",
        help_text="Дата создания уведомления",
    )
    sent_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Дата отправки",
        help_text="Дата фактической отправки уведомления",
    )
    is_sent = models.BooleanField(
        default=False,
        verbose_name="Отправлено",
        help_text="Статус отправки уведомления",
    )

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Уведомление"
        verbose_name_plural = "Уведомления"

    def clean(self) -> None:
        """Валидация полей уведомления."""
        super().clean()

        if self.execution_time and self.execution_time > self.MAX_EXECUTION_TIME:
            raise ValidationError(
                {
                    "execution_time": (
                        f"Время выполнения привычки не может превышать {self.MAX_EXECUTION_TIME} секунд."
                    )
                }
            )

        if not (self.MIN_PERIODICITY <= self.periodicity <= self.MAX_PERIODICITY):
            raise ValidationError(
                {
                    "periodicity": (
                        "Периодичность выполнения должна быть от 1 до 7 дней. "
                        "Нельзя выполнять привычку реже одного раза в неделю."
                    )
                }
            )

    def save(self, *args, **kwargs):
        """Сохраняет уведомление с валидацией."""
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"Уведомление для {self.user} о {self.habit}"
