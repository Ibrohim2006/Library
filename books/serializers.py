from django.template.context_processors import request
from rest_framework import serializers
from .models import *

class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model=Review
        fields="__all__"

class BookSerializer(serializers.ModelSerializer):
    reviews =ReviewSerializer(many=True,read_only=True)
    class Meta:
        model=Book
        fields="__all__"


class SavedSerializer(serializers.ModelSerializer):
    class Meta:
        model=Saved
        fields="__all__"
