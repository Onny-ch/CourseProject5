import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("config")
app.config_from_object("django.conf:settings", namespace="CELERY")

# Явно указываем приложения для autodiscover
app.autodiscover_tasks()


# Настройка расписания для celery-beat
app.conf.beat_schedule = {
    "send-daily-habit-reminders": {
        "task": "apps.notifications.tasks.send_daily_reminders",
        "schedule": crontab(minute="*"),  # Каждую минуту проверяем привычки
    },
}
app.conf.timezone = "UTC"


@app.task(bind=True)
def debug_task(self):
    """Простая заглушка отладочной задачи."""
    print(f"Request: {self.request!r}")


