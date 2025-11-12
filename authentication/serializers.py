from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from authentication.models import UserModel
from rest_framework_simplejwt.tokens import RefreshToken, TokenError


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    confirm_password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = UserModel
        fields = ("email", "password", "confirm_password")

    def validate_email(self, value):
        if UserModel.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("This email is already registered.")
        return value

    def validate(self, attrs):
        password = attrs.get("password")
        confirm_password = attrs.get("confirm_password")

        if not attrs.get("email") or not password or not confirm_password:
            raise serializers.ValidationError({"detail": "email, password and confirm_password are required."})

        if password != confirm_password:
            raise serializers.ValidationError({"confirm_password": ["Passwords do not match."]})

        validate_password(password)
        return attrs

    def create(self, validated_data):
        validated_data.pop("confirm_password", None)
        password = validated_data.pop("password")
        user = UserModel.objects.create_user(password=password, **validated_data)
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        if not email or not password:
            raise serializers.ValidationError({"detail": "email and password are required."})

        user = authenticate(request=self.context.get("request"), email=email, password=password)
        if not user:
            raise serializers.ValidationError({"detail": "Invalid credentials."})

        if not user.is_active:
            raise serializers.ValidationError({"detail": "User account is disabled."})

        attrs["user"] = user
        return attrs


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField(write_only=True)

    def validate(self, attrs):
        token = attrs.get("refresh")
        if not token:
            raise serializers.ValidationError({"refresh": ["refresh token is required."]})
        self.token = token
        return attrs

    def save(self, **kwargs):
        try:
            RefreshToken(self.token).blacklist()
        except TokenError:
            pass
        return {}


class GoogleAuthSerializer(serializers.Serializer):
    id_token = serializers.CharField(write_only=True, required=True, help_text="Google ID token")

    def validate(self, attrs):
        if not attrs.get("id_token"):
            raise serializers.ValidationError({"id_token": ["id_token is required."]})
        return attrs
