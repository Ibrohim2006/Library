from rest_framework import serializers
from authentication.models import UserModel


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserModel
        fields = ("id", "email", "first_name", "last_name", "is_verified")


class GoogleAuthResponseSerializer(serializers.Serializer):
    message = serializers.CharField()
    token = serializers.CharField()
    user = UserSerializer()
