from django.contrib import admin

from .models import Habit


@admin.register(Habit)
class HabitAdmin(admin.ModelAdmin):
    list_display = (
        "action",
        "user",
        "place",
        "is_pleasant",
        "related_habit",
        "is_public",
        "created_at",
    )
    list_filter = ("is_pleasant", "is_public", "created_at")
    search_fields = ("action", "place", "user__username")
    autocomplete_fields = ("related_habit",)
