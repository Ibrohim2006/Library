from tkinter.font import names

from django.urls import path
from .views import *

urlpatterns = [
    path("books/",get_books, name='get_books'),
    path("books/<int:pk>/",get_book, name='get_book'),
    path("reviews/<int:pk>/", add_review,name='add_review'),
    path("saved/<int:user_id>/<int:book_id>/",save_book,name='saved_book'),
    path("saved/<int:user_id>/",get_saved,name='get_saved')
]