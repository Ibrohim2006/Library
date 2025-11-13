from django.contrib import admin
from .models import BookModel, SourceModel, BookAvailabilityModel


@admin.register(BookModel)
class BookAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "language", "year")


@admin.register(SourceModel)
class SourceAdmin(admin.ModelAdmin):
    list_display = ("name", "type", "base_url")


@admin.register(BookAvailabilityModel)
class BookAvailabilityAdmin(admin.ModelAdmin):
    list_display = ("book", "source", "availability_type",)
