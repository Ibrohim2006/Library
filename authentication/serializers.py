from django.contrib.auth import authenticate
from rest_framework import serializers
from .models import UserModel


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserModel
        fields = ("id", "email", "first_name", "last_name", "is_verified")


class GoogleAuthResponseSerializer(serializers.Serializer):
    message = serializers.CharField()
    token = serializers.CharField()
    user = UserSerializer()

class RegisterSeriliazer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm= serializers.CharField(write_only=True)
    class Meta:
        model= UserModel
        fields=['email','first_name','last_name','password','password_confirm']

    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({"password":"Passwords don't match"})
        return data

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user=UserModel.objects.create(
            username=validated_data['email'],
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            password=validated_data['password']
        )
        return user

class LoginSerializer(serializers.ModelSerializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    def validate(self, data):
        user =authenticate(username=data['email'], password=data['password'])
        if user is None:
            raise serializers.ValidationError("email yoki password xato")
        if not user.is_active:
            raise serializers.ValidationError("foydalanuvchi mavjud emas ")
        return {"user":user}

