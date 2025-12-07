from django.shortcuts import get_object_or_404
from django.db.models import Q
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from .models import (
    BookModel,
    SearchHistory,
    RatingModel,
    SavedBookModel,
    CommentModel,
    CommentLikeModel
)
from .serializers import (
    BookSerializer,
    SearchHistorySerializer,
    SearchRequestSerializer,
    CommentSerializer,
    RatingSerializer,
    SavedBookSerializer,
    CommentLikeSerializer
)
from .utils import ai_search_books


# ============================================================================
# BOOK VIEWSET
# ============================================================================
class BookViewSet(viewsets.ViewSet):
    """
    ViewSet for books - list and detail
    """

    @swagger_auto_schema(
        operation_summary="List books",
        operation_description=(
                "Returns a list of books with filters.\n\n"
                "Available filters:\n"
                "- author: search by author name\n"
                "- genre: search by genre name\n"
                "- year: filter by publication year\n"
                "- language: filter by book language\n"
                "- search: full-text search\n"
                "- lang: controls the response language"
        ),
        manual_parameters=[
            openapi.Parameter("author", openapi.IN_QUERY, type=openapi.TYPE_STRING),
            openapi.Parameter("genre", openapi.IN_QUERY, type=openapi.TYPE_STRING),
            openapi.Parameter("year", openapi.IN_QUERY, type=openapi.TYPE_INTEGER),
            openapi.Parameter("language", openapi.IN_QUERY, type=openapi.TYPE_STRING),
            openapi.Parameter("search", openapi.IN_QUERY, type=openapi.TYPE_STRING),
            openapi.Parameter("lang", openapi.IN_QUERY, type=openapi.TYPE_STRING),
        ],
        responses={200: BookSerializer(many=True)},
        tags=["Books"],
    )
    def list(self, request):
        from django.utils import translation

        lang = request.GET.get("lang")
        if lang in ("uz", "en", "ru"):
            translation.activate(lang)

        queryset = BookModel.objects.select_related("genre").all()

        # Filters
        author = request.query_params.get("author")
        genre = request.query_params.get("genre")
        year = request.query_params.get("year")
        language = request.query_params.get("language")
        search = request.query_params.get("search")

        if author:
            queryset = queryset.filter(
                Q(author_uz__icontains=author) |
                Q(author_ru__icontains=author) |
                Q(author_en__icontains=author)
            )

        if genre:
            queryset = queryset.filter(
                Q(genre__name_uz__icontains=genre) |
                Q(genre__name_ru__icontains=genre) |
                Q(genre__name_en__icontains=genre)
            )

        if year:
            queryset = queryset.filter(year=int(year))

        if language:
            queryset = queryset.filter(language=language)

        if search:
            search_queryset = (
                    Q(title_uz__icontains=search) |
                    Q(title_ru__icontains=search) |
                    Q(title_en__icontains=search) |
                    Q(author_uz__icontains=search) |
                    Q(author_ru__icontains=search) |
                    Q(author_en__icontains=search)
            )
            queryset = queryset.filter(search_queryset)

        queryset = queryset.distinct()
        serializer = BookSerializer(queryset, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_summary="Retrieve a book",
        responses={200: BookSerializer(), 404: "Not Found"},
        tags=["Books"],
    )
    def retrieve(self, request, pk=None):
        book = get_object_or_404(BookModel, id=pk)
        serializer = BookSerializer(book, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)


# ============================================================================
# SAVED BOOKS VIEWSET
# ============================================================================
class SavedBookViewSet(viewsets.ModelViewSet):
    """
    ViewSet for saved books (user's reading list)
    """
    serializer_class = SavedBookSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return SavedBookModel.objects.active().for_user(self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def reading_now(self, request):
        """Get books currently reading"""
        books = SavedBookModel.objects.reading_now(request.user)
        serializer = self.get_serializer(books, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def want_to_read(self, request):
        """Get books user wants to read"""
        books = SavedBookModel.objects.want_to_read(request.user)
        serializer = self.get_serializer(books, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def finished(self, request):
        """Get finished books"""
        books = SavedBookModel.objects.finished(request.user)
        serializer = self.get_serializer(books, many=True)
        return Response(serializer.data)


# ============================================================================
# COMMENT VIEWSET
# ============================================================================
class CommentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for comments on books
    """
    serializer_class = CommentSerializer

    def get_queryset(self):
        queryset = CommentModel.objects.active().approved()

        # Filter by book if provided
        book_id = self.request.query_params.get('book')
        if book_id:
            queryset = queryset.filter(book_id=book_id)

        return queryset.select_related("user", "book", "parent")

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsAuthenticated()]
        return [AllowAny()]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def like(self, request, pk=None):
        """Like a comment"""
        comment = self.get_object()

        like_obj, created = CommentLikeModel.objects.get_or_create(
            user=request.user,
            comment=comment,
            defaults={'is_like': True}
        )

        if not created:
            # Toggle like
            like_obj.is_like = not like_obj.is_like
            like_obj.save()

        return Response({
            'liked': like_obj.is_like,
            'likes_count': comment.likes_count
        })


# ============================================================================
# RATING VIEWSET
# ============================================================================
class RatingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for book ratings
    """
    serializer_class = RatingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = RatingModel.objects.active()

        # Filter by book if provided
        book_id = self.request.query_params.get('book')
        if book_id:
            queryset = queryset.filter(book_id=book_id)

        return queryset.select_related("user", "book")

    def perform_create(self, serializer):
        user = self.request.user
        book = serializer.validated_data["book"]

        # Check if user already rated this book
        if RatingModel.objects.filter(user=user, book=book, is_active=True).exists():
            raise serializers.ValidationError(
                "You already rated this book. Use PUT/PATCH to update."
            )

        serializer.save(user=user)

    @action(detail=False, methods=["post"], permission_classes=[IsAuthenticated])
    def upsert(self, request):
        """Create or update rating"""
        user = request.user
        book_id = request.data.get("book_id")
        stars = int(request.data.get("stars", 0))
        review_text = request.data.get("review_text", "")

        if stars < 1 or stars > 5:
            return Response(
                {"error": "Stars must be between 1 and 5"},
                status=status.HTTP_400_BAD_REQUEST
            )

        book = get_object_or_404(BookModel, id=book_id)

        obj, created = RatingModel.objects.update_or_create(
            user=user,
            book=book,
            defaults={
                "stars": stars,
                "review_text": review_text,
                "is_active": True
            }
        )

        return Response(
            RatingSerializer(obj).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )


# ============================================================================
# SEARCH HISTORY VIEWSET
# ============================================================================
class SearchHistoryViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Retrieve search history",
        responses={200: SearchHistorySerializer(many=True)},
        tags=["Search"],
    )
    def list(self, request):
        queryset = SearchHistory.objects.filter(
            user=request.user
        ).order_by("-created_at")[:20]

        serializer = SearchHistorySerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


# ============================================================================
# AI SEARCH VIEWSET
# ============================================================================
class BookSearchViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Search books using AI",
        request_body=SearchRequestSerializer,
        responses={200: "Search results", 400: "Bad Request"},
        tags=["Search"]
    )
    def create(self, request, *args, **kwargs):
        serializer = SearchRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        query = serializer.validated_data["query"]
        language = serializer.validated_data["language"]

        try:
            keywords = ai_search_books(query=query, language=language) or []

            normalized_query = query.strip()
            if normalized_query and normalized_query not in keywords:
                keywords.insert(0, normalized_query)

            fields = [
                f"title_{language}",
                f"author_{language}",
                f"description_{language}",
                f"genre__name_{language}"
            ]

            q_obj = Q()
            for kw in keywords:
                kw_filter = Q()
                for field in fields:
                    kw_filter |= Q(**{f"{field}__icontains": kw})
                q_obj |= kw_filter

            books_qs = BookModel.objects.filter(q_obj).distinct()[:50]
            results = BookSerializer(books_qs, many=True, context={"request": request}).data

            # Save search history
            if request.user.is_authenticated:
                SearchHistory.objects.create(
                    user=request.user,
                    query=query,
                )

            return Response(
                {
                    "query": query,
                    "language": language,
                    "keywords": keywords,
                    "results": results,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {"detail": "Internal server error", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )