"""Конфигурация админки для приложения уведомлений."""
from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Админка для модели уведомлений."""

    list_display = (
        "id",
        "user",
        "habit",
        "time",
        "periodicity",
        "execution_time",
        "is_sent",
        "created_at",
        "sent_at",
    )
    list_filter = ("is_sent", "created_at", "sent_at")
    search_fields = ("user__email", "user__username", "habit__action")
    readonly_fields = ("created_at", "sent_at")
    ordering = ("-created_at",)
