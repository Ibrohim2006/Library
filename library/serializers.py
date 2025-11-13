from rest_framework import serializers
from .models import BookModel, SourceModel, BookAvailabilityModel


class SourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = SourceModel
        fields = ["id", "name", "type", "base_url"]


class BookAvailabilitySerializer(serializers.ModelSerializer):
    book = serializers.PrimaryKeyRelatedField(read_only=True)
    source = SourceSerializer(read_only=True)

    class Meta:
        model = BookAvailabilityModel
        fields = [
            "id",
            "book",
            "source",
            "availability_type",
            "location_name",
            "address",
            "url",
            "price",
            "currency",
            "is_available",
        ]


class BookSerializer(serializers.ModelSerializer):
    availability_book = BookAvailabilitySerializer(many=True, read_only=True)

    class Meta:
        model = BookModel
        fields = [
            "id",
            "title",
            "author",
            "isbn",
            "language",
            "year",
            "description",
            "availability_book",
        ]
