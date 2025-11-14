from django.urls import path
from .views import BookViewSet, SearchHistoryViewSet

urlpatterns = [
    path("books/", BookViewSet.as_view({"get": "list"}), name="book-list"),
    path("books/<uuid:pk>/", BookViewSet.as_view({"get": "retrieve"}), name="book-detail"),
    path('search-history/', SearchHistoryViewSet.as_view({"get": "list"}), name="search-history"),
]
