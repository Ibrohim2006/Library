from django.contrib import admin
from modeltranslation.admin import TranslationAdmin
from .models import GenreModel, BookModel


@admin.register(GenreModel)
class GenreAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)


@admin.register(BookModel)
class BookAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "author", "genre", "year", "language")
    list_filter = ("language", "genre", "year")
    search_fields = ("title", "author", "description")