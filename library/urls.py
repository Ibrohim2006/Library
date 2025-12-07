from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_yasg import openapi
from drf_yasg.views import get_schema_view

from .views import (
    BookViewSet,
    SavedBookViewSet,
    CommentViewSet,
    RatingViewSet,
    SearchHistoryViewSet,
    BookSearchViewSet,
)

# ============================================================================
# SWAGGER SCHEMA
# ============================================================================
schema_view = get_schema_view(
    openapi.Info(
        title="Library API",
        default_version='v1',
        description="Professional Library Management API with AI Search",
        contact=openapi.Contact(email="admin@library.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=[AllowAny],
)

# ============================================================================
# ROUTER - Automatic REST endpoints
# ============================================================================
router = DefaultRouter()
router.register(r'books', BookViewSet, basename='books')
router.register(r'saved-books', SavedBookViewSet, basename='saved-books')
router.register(r'comments', CommentViewSet, basename='comments')
router.register(r'ratings', RatingViewSet, basename='ratings')
router.register(r'search-history', SearchHistoryViewSet, basename='search-history')
router.register(r'ai-search', BookSearchViewSet, basename='ai-search')

# ============================================================================
# URL PATTERNS
# ============================================================================
urlpatterns = [
    # Authentication endpoints
    path("auth/login/", TokenObtainPairView.as_view(), name="token-obtain"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="token-refresh"),

    # Swagger Documentation
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

    # Include all router URLs
    path('', include(router.urls)),
]