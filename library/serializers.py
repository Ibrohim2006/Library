from django.conf import settings
from rest_framework import serializers
from .models import GenreModel, BookModel, SearchHistory


def get_lang_from_request(request):
    default_lang = getattr(settings, "MODELTRANSLATION_DEFAULT_LANGUAGE", "en")
    lang_options = getattr(settings, "MODELTRANSLATION_LANGUAGES",
                           [code for code, _ in getattr(settings, "LANGUAGES", [])])
    lang = default_lang
    if not request:
        return lang, lang_options
    query_lang = getattr(request, "query_params", {}).get("lang")
    if query_lang and query_lang in lang_options:
        return query_lang, lang_options
    header_lang = request.headers.get("Accept-Language")
    if header_lang and header_lang in lang_options:
        return header_lang, lang_options
    return lang, lang_options


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = GenreModel
        fields = ["id", "name"]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get("request")
        lang, lang_options = get_lang_from_request(request)
        translated = getattr(instance, f"name_{lang}", None)
        if translated:
            data["name"] = translated
        return data


class BookSerializer(serializers.ModelSerializer):
    genre = GenreSerializer(read_only=True)

    class Meta:
        model = BookModel
        fields = ["id", "author", "title", "description", "genre", "year", "language", "image", "youtube_url",
                  "library_url", "store_url",
                  ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get("request")
        lang, lang_options = get_lang_from_request(request)
        title_translated = getattr(instance, f"title_{lang}", None)
        author_translated = getattr(instance, f"author_{lang}", None)
        description_translated = getattr(instance, f"description_{lang}", None)
        if title_translated:
            data["title"] = title_translated
        if author_translated:
            data["author"] = author_translated
        if description_translated:
            data["description"] = description_translated
        return data

class SearchHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SearchHistory
        fields = ["id", "query", "created_at"]