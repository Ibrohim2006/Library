from django.db.models import Q
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import BookModel, SearchHistory
from .serializers import BookSerializer, SearchHistorySerializer


class BookViewSet(viewsets.ViewSet):
    @swagger_auto_schema(
        operation_summary="List books",
        operation_description=(
                "Returns a list of books.\n\n"
                "Available filters:\n"
                "- author: search by author name (matches author_uz/author_ru/author_en)\n"
                "- genre: search by genre name (matches Genre.name_uz/name_ru/name_en)\n"
                "- year: filter by publication year\n"
                "- language: filter by book language (BookModel.language: en/ru/uz)\n"
                "- search: full-text search across title_* and author_* fields\n"
                "- lang: controls the response language (used by modeltranslation in the serializer)"
        ),
        manual_parameters=[
            openapi.Parameter(
                name="author",
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description="Filter by author name (author_uz/author_ru/author_en).",
                required=False,
            ),
            openapi.Parameter(
                name="genre",
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description="Filter by genre name (Genre.name_uz/name_ru/name_en).",
                required=False,
            ),
            openapi.Parameter(
                name="year",
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_INTEGER,
                description="Filter by publication year.",
                required=False,
            ),
            openapi.Parameter(
                name="language",
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description="Filter by book language (BookModel.language: en/ru/uz).",
                required=False,
            ),
            openapi.Parameter(
                name="search",
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description="Full-text search across title_* and author_* fields.",
                required=False,
            ),
            openapi.Parameter(
                name="lang",
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description="Controls the response language (uz/ru/en).",
                required=False,
            ),
        ],
        responses={200: BookSerializer(many=True)},
        tags=["Books"],
    )
    def list(self, request):
        queryset = BookModel.objects.select_related("genre").all()
        search = request.query_params.get("search")
        author = request.query_params.get("author")
        genre = request.query_params.get("genre")
        year = request.query_params.get("year")
        language = request.query_params.get("language")
        if author:
            queryset = queryset.filter(
                Q(author_uz__icontains=author)
                | Q(author_ru__icontains=author)
                | Q(author_en__icontains=author)
            )

        if genre:
            queryset = queryset.filter(
                Q(genre__name_uz__icontains=genre)
                | Q(genre__name_ru__icontains=genre)
                | Q(genre__name_en__icontains=genre)
            )

        if year:
            queryset = queryset.filter(year=int(year))

        if language:
            queryset = queryset.filter(language=language)
        if search:
            search_queryset = (
                    Q(title_uz__icontains=search)
                    | Q(title_ru__icontains=search)
                    | Q(title_en__icontains=search)
                    | Q(author_uz__icontains=search)
                    | Q(author_ru__icontains=search)
                    | Q(author_en__icontains=search)
            )
            queryset = queryset.filter(search_queryset)
        queryset = queryset.distinct()
        serializer = BookSerializer(queryset, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_summary="Retrieve a book",
        operation_description="Get a single book by ID.",
        responses={
            200: BookSerializer(),
            404: "Not Found",
        },
        tags=["Books"],
    )
    def retrieve(self, request, pk=None):
        book = BookModel.objects.filter(id=pk).first()
        if not book:
            return Response(
                data={"message": "Book not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = BookSerializer(book, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class SearchHistoryViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Retrieve search history",
        operation_description="Get last 20 search queries of the current authenticated user.",
        responses={200: SearchHistorySerializer(many=True), },
        tags=["Search History"],
    )
    def list(self, request):
        queryset = SearchHistory.objects.filter(user=request.user).order_by("-created_at")[:20]
        serializer = SearchHistorySerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
