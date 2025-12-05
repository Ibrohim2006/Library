from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns, set_language
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="Library API",
        default_version="v1",
        description="Library WEBSITE APIs",
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = i18n_patterns(
    path("api/v1/auth/", include("authentication.urls")),
    path("api/v1/library/", include("library.urls")),
    re_path(r"^swagger/$", schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui"), # type: ignore
    # prefix_default_language=False,
)

urlpatterns += [
    path("i18n/", include("django.conf.urls.i18n")),
    path("i18n/setlang/", set_language, name="set_language"),
    path("admin/", admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)