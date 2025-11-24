from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin

from .models import GenreModel, BookModel, SearchHistory

class BaseAdmin(admin.ModelAdmin):
    list_per_page = 10
    class Meta:
        abstract = True

class BookModelResource(resources.ModelResource):
    class Meta:
        model = BookModel


@admin.register(GenreModel)
class GenreAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)

admin.site.register(SearchHistory)


@admin.register(BookModel)
class BookAdmin(ImportExportModelAdmin, BaseAdmin):
    resource_classes = [BookModelResource]
    list_display = tuple(f.name for f in BookModel._meta.fields if f.name not in ('id',))
    # list_display = ("id", "title", "author", "genre", "year", "language")
    list_filter = ("language", "genre", "year")
    search_fields = ("title", "author", "description")