from django.urls import path
from .views import BookViewSet

urlpatterns = [
    path("books/", BookViewSet.as_view({"get": "list"}), name="book-list"),
    path("books/search/", BookViewSet.as_view({"get": "retrieve"}), name="book-search"),
    path("books/<uuid:pk>/", BookViewSet.as_view({"get": "search"}), name="book-detail"),
    path("books/<uuid:pk>/availability/", BookViewSet.as_view({"get": "availability"}), name="book-availability"),
]
