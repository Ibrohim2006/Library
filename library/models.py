from django.db import models
from core.base import BaseModel


class BookModel(BaseModel):
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255, blank=True, null=True)
    isbn = models.CharField(max_length=32, blank=True, null=True, db_index=True)
    language = models.CharField(max_length=10, blank=True, null=True)
    year = models.IntegerField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.title} ({self.author})"


class SourceModel(BaseModel):
    SOURCE_CHOICES = (
        ("national_library", "National Library"),
        ("university_library", "University Library"),
        ("private_service", "Private Service"),
    )
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=32, choices=SOURCE_CHOICES)
    base_url = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.name


class BookAvailabilityModel(BaseModel):
    AVAILABILITY_TYPE_CHOICES = (
        ("free_reading", "Free reading (library)"),
        ("paid_reading", "Paid reading (online)"),
        ("purchase", "Purchase"),
    )
    book = models.ForeignKey(BookModel, on_delete=models.CASCADE, related_name="availability_book")
    source = models.ForeignKey(SourceModel, on_delete=models.CASCADE, related_name="availability_source")
    availability_type = models.CharField(max_length=32, choices=AVAILABILITY_TYPE_CHOICES)

    location_name = models.CharField(max_length=255, blank=True, null=True)
    address = models.CharField(max_length=500, blank=True, null=True)

    url = models.URLField(blank=True, null=True)
    price = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    currency = models.CharField(max_length=8, blank=True, null=True)

    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.book} — {self.source}"
