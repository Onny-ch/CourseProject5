"""Главная URL конфигурация проекта."""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework.permissions import AllowAny

schema_view = get_schema_view(
    openapi.Info(
        title="Habits Tracker API",
        default_version="v1",
        description="Документация API для сервиса отслеживания привычек.",
    ),
    public=True,
    permission_classes=[AllowAny],
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("apps.habits.urls")),
    path("api/v1/", include("apps.users.urls")),
    path("api/v1/", include("apps.notifications.urls")),
    path("api/schema/", schema_view.without_ui(cache_timeout=0), name="schema-json"),
    path(
        "api/docs/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    path(
        "api/redoc/",
        schema_view.with_ui("redoc", cache_timeout=0),
        name="schema-redoc",
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
