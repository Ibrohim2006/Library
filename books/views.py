from django.shortcuts import render
from django.template.defaultfilters import title

# Create your views here.
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import *
from .serializers import *
@api_view(['GET'])
def get_books(request):
    search=request.GET.get("search","")
    if search:
        books=Book.objects.filter(title__icontains=search)
    else:
        books=Book.objects.all()
    serializer=BookSerializer(books, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def get_book(request,pk):
    book=Book.objects.get(id=pk)
    serializer=BookSerializer(book)
    return Response(serializer.data)

@api_view(['POST'])
def add_review(request,pk):
    data=request.data.copy()
    data['book']=pk
    serializer=ReviewSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def save_book(request,user_id,book_id):
    saved=Saved(user_id=user_id,book_id=book_id)
    saved.save()
    return Response({"massage":"Saved"})

@api_view(['GET'])
def get_saved(request,user_id):
    saved_items=Saved.objects.filter(user_id=user_id)
    books=[item.book for item in saved_items]
    serializer=BookSerializer(books, many=True)
    return Response(serializer.data)
