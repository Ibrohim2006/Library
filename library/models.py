from django.db import models

from authentication.models import UserModel
from core.base import BaseModel

LANGUAGE_CHOICES = (
    ("en", "English"),
    ("ru", "Russian"),
    ("uz", "Uzbek"),
)


class GenreModel(BaseModel):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "genre"
        verbose_name_plural = "Genres"
        verbose_name = "Genre"


class BookModel(BaseModel):
    author = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    description = models.TextField()
    genre = models.ForeignKey(GenreModel, on_delete=models.CASCADE, related_name="book_genre")
    year = models.PositiveIntegerField()
    language = models.CharField(max_length=20, choices=LANGUAGE_CHOICES, default="en")
    image = models.ImageField(upload_to="book/image")
    youtube_url = models.URLField(blank=True, null=True)
    library_url = models.URLField(blank=True, null=True)
    store_url = models.URLField(blank=True, null=True)

    def __str__(self):
        return f"{self.title} ({self.author})"

    class Meta:
        db_table = "book"
        verbose_name_plural = "Books"
        verbose_name = "Book"


class SearchHistory(BaseModel):
    user = models.ForeignKey(UserModel, on_delete=models.CASCADE, related_name="search_histories", )
    query = models.CharField(max_length=255)

    class Meta:
        db_table = "search_history"
        verbose_name = "Search history"
        verbose_name_plural = "Search histories"

    def __str__(self):
        return f"{self.user} – {self.query[:10]})"


class SearchRequestModel(BaseModel):
    query = models.CharField(max_length=255)
    language = models.CharField(max_length=15, choices=LANGUAGE_CHOICES, default="uz")

    class Meta:
        db_table = "search_request"
        verbose_name = "Search request"
        verbose_name_plural = "Search requests"

    def __str__(self):
        return f"{self.query} ({self.language})"


class FilterRequestModel(BaseModel):
    author = models.CharField(max_length=255, null=True, blank=True)
    genre = models.CharField(max_length=255, null=True, blank=True, )
    year = models.PositiveIntegerField(null=True, blank=True)
    language = models.CharField(max_length=5, choices=LANGUAGE_CHOICES, null=True, blank=True)
    search_term = models.CharField(max_length=255, null=True, blank=True, )

    class Meta:
        db_table = "filter_request"
        verbose_name = "Filter request"
        verbose_name_plural = "Filter requests"

    def __str__(self):
        return f"Filter(author={self.author}, genre={self.genre}, year={self.year}, lang={self.language})"
