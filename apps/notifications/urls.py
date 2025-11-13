"""URL конфигурация для приложения notifications."""
from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import NotificationViewSet, send_message, send_notification

router = DefaultRouter()
router.register(r"notifications", NotificationViewSet, basename="notification")

urlpatterns = [
    path(
        "habits/<int:habit_id>/send-message/",
        send_message,
        name="habit-send-message",
    ),
    path(
        "notifications/<int:notification_id>/send/",
        send_notification,
        name="notification-send",
    ),
] + router.urls
