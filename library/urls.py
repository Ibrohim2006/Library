from django.urls import path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from .views import *
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.routers import DefaultRouter

schema_view = get_schema_view(
    openapi.Info(
        title="Library API",
        default_version='v1',
        description="Library API docs",
    ),
    public=True,
    permission_classes=[AllowAny],
)

urlpatterns = [
    path("books/", BookViewSet.as_view({"get": "list"}), name="book-list"),
    path("books/<uuid:pk>/", BookViewSet.as_view({"get": "retrieve"}), name="book-detail"),
    path('search-history/', SearchHistoryViewSet.as_view({"get": "list"}), name="search-history"),
    path("search/", BookSearchViewSet.as_view({"post": "create"}), name="book-search"),
    path("auth/login/", TokenObtainPairView.as_view()),
    path("auth/refresh/", TokenRefreshView.as_view()),

    # Swagger
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
]

# Router
router = DefaultRouter()
router.register(r'books', BookViewSet, basename='books')
router.register(r'comments', CommentViewSet, basename='comments')
router.register(r'ratings', RatingViewSet, basename='ratings')
router.register(r'saved', SavedViewSet, basename='saved')
router.register(r'search-history', SearchHistoryViewSet, basename='search-history')
router.register(r'ai-search', BookSearchViewSet, basename='ai-search')

# ⚠️ MUHIM:
urlpatterns += router.urls
