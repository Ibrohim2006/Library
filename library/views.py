from django.db.models import Q
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import BookModel, BookAvailabilityModel
from .serializers import BookSerializer, BookAvailabilitySerializer


class BookViewSet(viewsets.ViewSet):
    @swagger_auto_schema(
        operation_summary="List books",
        operation_description="Get a list of all books with their availability.",
        responses={200: BookSerializer(many=True)},
        tags=["Books"],
    )
    def list(self, request):
        queryset = BookModel.objects.all()
        serializer = BookSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_summary="Retrieve a book",
        operation_description="Get a single book by ID with its availability information.",
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
        serializer = BookSerializer(book)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_summary="Search books",
        operation_description="Search books by title, ISBN or author.",
        manual_parameters=[
            openapi.Parameter(
                name="search",
                in_=openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                description="Search by book title, ISBN or author.",
                required=False,
            )
        ],
        responses={200: BookSerializer(many=True)},
        tags=["Books"],
    )
    @action(detail=False, methods=["get"], url_path="search")
    def search(self, request):
        search = request.query_params.get("search", "").strip()

        qs = BookModel.objects.all()

        if search:
            qs = qs.filter(
                Q(title__icontains=search)
                | Q(author__icontains=search)
                | Q(isbn__icontains=search)
            )

        qs = qs.distinct()

        serializer = BookSerializer(qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_summary="Get book availability",
        operation_description="Get a list of locations and services where this book is available.",
        responses={
            200: BookAvailabilitySerializer(many=True),
            404: "Not Found",
        },
        tags=["Books"],
    )
    def availability(self, request, pk=None):
        book = BookModel.objects.filter(id=pk).first()
        if not book:
            return Response(
                data={"message": "Book not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        availabilities = BookAvailabilityModel.objects.filter(
            book=book,
            is_available=True,
        )
        serializer = BookAvailabilitySerializer(availabilities, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
