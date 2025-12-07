from django.conf import settings
from rest_framework import serializers
from .models import (
    GenreModel,
    BookModel,
    SearchHistory,
    RatingModel,
    CommentModel,
    SavedBookModel,
    CommentLikeModel
)


def get_lang_from_request(request):
    """Get language from request"""
    default_lang = getattr(settings, "MODELTRANSLATION_DEFAULT_LANGUAGE", "en")
    lang_options = getattr(
        settings,
        "MODELTRANSLATION_LANGUAGES",
        [code for code, _ in getattr(settings, "LANGUAGES", [])]
    )

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


# ============================================================================
# GENRE SERIALIZER
# ============================================================================
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


# ============================================================================
# BOOK SERIALIZER
# ============================================================================
class BookSerializer(serializers.ModelSerializer):
    genre = GenreSerializer(read_only=True)
    avg_rating = serializers.DecimalField(
        max_digits=3,
        decimal_places=2,
        read_only=True
    )
    total_ratings = serializers.IntegerField(read_only=True)
    total_saves = serializers.IntegerField(read_only=True)
    total_comments = serializers.IntegerField(read_only=True)

    # User-specific fields (requires authentication)
    user_rating = serializers.SerializerMethodField()
    is_saved = serializers.SerializerMethodField()
    user_save_status = serializers.SerializerMethodField()

    class Meta:
        model = BookModel
        fields = [
            "id", "author", "title", "description", "genre",
            "year", "language", "image", "youtube_url",
            "library_url", "store_url",
            "avg_rating", "total_ratings", "total_saves", "total_comments",
            "user_rating", "is_saved", "user_save_status",
            "created_at", "updated_at"
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get("request")
        lang, lang_options = get_lang_from_request(request)

        # Translate fields
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

    def get_user_rating(self, obj):
        """Get current user's rating for this book"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            rating = RatingModel.objects.filter(
                user=request.user,
                book=obj,
                is_active=True
            ).first()
            return rating.stars if rating else None
        return None

    def get_is_saved(self, obj):
        """Check if current user saved this book"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return SavedBookModel.objects.filter(
                user=request.user,
                book=obj,
                is_active=True
            ).exists()
        return False

    def get_user_save_status(self, obj):
        """Get user's reading status for this book"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            saved = SavedBookModel.objects.filter(
                user=request.user,
                book=obj,
                is_active=True
            ).first()
            return saved.status if saved else None
        return None


# ============================================================================
# SAVED BOOK SERIALIZER
# ============================================================================
class SavedBookSerializer(serializers.ModelSerializer):
    book = BookSerializer(read_only=True)
    book_id = serializers.PrimaryKeyRelatedField(
        queryset=BookModel.objects.all(),
        source='book',
        write_only=True
    )
    user_email = serializers.CharField(source="user.email", read_only=True)

    class Meta:
        model = SavedBookModel
        fields = [
            "id", "book", "book_id", "user_email",
            "notes", "status", "is_active",
            "created_at", "updated_at"
        ]
        read_only_fields = ("user", "created_at", "updated_at")

    def create(self, validated_data):
        # user avtomatik views.py dan qo'shiladi (perform_create)
        return super().create(validated_data)


# ============================================================================
# COMMENT SERIALIZER
# ============================================================================
class CommentSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source="user.email", read_only=True)
    user_name = serializers.SerializerMethodField()
    book_title = serializers.CharField(source="book.title", read_only=True)
    replies_count = serializers.IntegerField(read_only=True)
    replies = serializers.SerializerMethodField()

    # User-specific fields
    user_liked = serializers.SerializerMethodField()

    class Meta:
        model = CommentModel
        fields = [
            "id", "book", "book_title", "text",
            "user_email", "user_name", "parent",
            "status", "likes_count", "is_active",
            "is_edited", "edited_at", "replies_count", "replies",
            "user_liked", "created_at", "updated_at"
        ]
        read_only_fields = ("user", "created_at", "updated_at", "likes_count")

    def get_user_name(self, obj):
        """Get user's full name or email"""
        if obj.user:
            full_name = f"{obj.user.first_name} {obj.user.last_name}".strip()
            return full_name if full_name else obj.user.email
        return "Anonymous"

    def get_replies(self, obj):
        """Get nested replies (only 1 level deep)"""
        if obj.parent is None:  # Only for top-level comments
            replies = obj.replies.filter(
                is_active=True,
                status='approved'
            )[:5]  # Limit to 5 replies
            return CommentSerializer(replies, many=True, context=self.context).data
        return []

    def get_user_liked(self, obj):
        """Check if current user liked this comment"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return CommentLikeModel.objects.filter(
                user=request.user,
                comment=obj,
                is_like=True
            ).exists()
        return False


# ============================================================================
# RATING SERIALIZER
# ============================================================================
class RatingSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source="user.email", read_only=True)
    user_name = serializers.SerializerMethodField()
    book_title = serializers.CharField(source="book.title", read_only=True)

    class Meta:
        model = RatingModel
        fields = [
            "id", "book", "book_title", "stars", "review_text",
            "user_email", "user_name", "previous_rating",
            "is_active", "created_at", "updated_at"
        ]
        read_only_fields = ("user", "created_at", "updated_at", "previous_rating")

    def get_user_name(self, obj):
        if obj.user:
            full_name = f"{obj.user.first_name} {obj.user.last_name}".strip()
            return full_name if full_name else obj.user.email
        return "Anonymous"

    def validate_stars(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5")
        return value


# ============================================================================
# COMMENT LIKE SERIALIZER
# ============================================================================
class CommentLikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommentLikeModel
        fields = ["id", "comment", "is_like", "created_at"]
        read_only_fields = ("user", "created_at")


# ============================================================================
# SEARCH HISTORY SERIALIZER
# ============================================================================
class SearchHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SearchHistory
        fields = ["id", "query", "created_at"]


# ============================================================================
# SEARCH REQUEST SERIALIZER
# ============================================================================
class SearchRequestSerializer(serializers.Serializer):
    query = serializers.CharField(max_length=255)
    language = serializers.ChoiceField(
        choices=[("uz", "Uzbek"), ("ru", "Russian"), ("en", "English")],
        default="uz"
    )