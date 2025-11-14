from django.urls import path
from .views import BookViewSet, SearchHistoryViewSet, BookSearchViewSet

urlpatterns = [
    path("books/", BookViewSet.as_view({"get": "list"}), name="book-list"),
    path("books/<uuid:pk>/", BookViewSet.as_view({"get": "retrieve"}), name="book-detail"),
    path('search-history/', SearchHistoryViewSet.as_view({"get": "list"}), name="search-history"),
    path("search/", BookSearchViewSet.as_view({"post": "create"}), name="book-search"),
]
