from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from authentication.models import UserModel
from config.settings import GOOGLE_CLIENT_ID
from authentication.serializers import RegisterSerializer, LoginSerializer, LogoutSerializer, GoogleAuthSerializer
from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as google_requests


class AuthenticationViewSet(viewsets.ViewSet):
    @swagger_auto_schema(
        operation_summary="Register",
        operation_description="Register using email and password",
        request_body=RegisterSerializer,
        responses={
            201: openapi.Response(
                description="User created",
                schema=RegisterSerializer()
            ),
            400: openapi.Response(description="Validation error"),
        },
        tags=["Authentication"],
    )
    def register(self, request):
        serializer = RegisterSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        data = {
            "id": str(user.id),
            "email": user.email,
            "is_verified": getattr(user, "is_verified", False),
            "tokens": {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            },
        }
        return Response(data=data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        operation_summary="Login",
        operation_description="Login with email and password.",
        request_body=LoginSerializer,
        responses={
            200: openapi.Response(description="Logged in", schema=LoginSerializer),
            400: openapi.Response(description="Validation error"),
        },
        tags=["Authentication"],
    )
    @action(detail=False, methods=["post"], url_path="login")
    def login(self, request):
        ser = LoginSerializer(data=request.data, context={"request": request})
        ser.is_valid(raise_exception=True)
        user = ser.validated_data["user"]

        refresh = RefreshToken.for_user(user)
        data = {
            "user": {
                "id": str(user.id),
                "email": user.email,
                "is_verified": getattr(user, "is_verified", False),
            },
            "tokens": {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            },
        }
        return Response(data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_summary="Logout",
        operation_description="Blacklist the provided refresh token.",
        request_body=LogoutSerializer,
        responses={
            205: openapi.Response(description="Logged out (token blacklisted)"),
            400: openapi.Response(description="Validation error"),
        },
        tags=["Authentication"],
    )
    @action(detail=False, methods=["post"], url_path="logout", permission_classes=[permissions.IsAuthenticated])
    def logout(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_205_RESET_CONTENT)

    @swagger_auto_schema(
        operation_summary="Google Sign-In",
        operation_description="Accepts Google id_token, verifies it, upserts user, and returns JWT tokens.",
        request_body=GoogleAuthSerializer,
        responses={
            200: openapi.Response(
                description="OK",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "user": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "id": openapi.Schema(type=openapi.TYPE_STRING),
                                "email": openapi.Schema(type=openapi.TYPE_STRING, format="email"),
                                "first_name": openapi.Schema(type=openapi.TYPE_STRING),
                                "last_name": openapi.Schema(type=openapi.TYPE_STRING),
                                "image": openapi.Schema(type=openapi.TYPE_STRING),
                                "is_verified": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                            },
                        ),
                        "tokens": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                "refresh": openapi.Schema(type=openapi.TYPE_STRING),
                                "access": openapi.Schema(type=openapi.TYPE_STRING),
                            },
                        ),
                    },
                ),
            ),
            400: openapi.Response(description="Invalid token / validation error"),
        },
        tags=["Authentication"],
    )
    def google_signin(self, request):
        ser = GoogleAuthSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        raw_id_token = ser.validated_data["id_token"]
        client_id = GOOGLE_CLIENT_ID
        if not client_id:
            return Response({"detail": "GOOGLE_CLIENT_ID is not configured."},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            idinfo = google_id_token.verify_oauth2_token(
                raw_id_token,
                google_requests.Request(),
                client_id,
            )
            iss = idinfo.get("iss")
            if iss not in ("accounts.google.com", "https://accounts.google.com"):
                return Response({"detail": "Invalid issuer."}, status=status.HTTP_400_BAD_REQUEST)

            sub = idinfo["sub"]
            email = idinfo.get("email")
            email_verified = bool(idinfo.get("email_verified", False))
            given_name = idinfo.get("given_name") or ""
            family_name = idinfo.get("family_name") or ""
            picture = idinfo.get("picture") or ""

            if not email:
                return Response({"detail": "Google token does not contain email."},
                                status=status.HTTP_400_BAD_REQUEST)

        except Exception:
            return Response({"detail": "Invalid or expired id_token."},
                            status=status.HTTP_400_BAD_REQUEST)

        user = UserModel.objects.filter(google=sub).first()
        created = False

        if not user:
            user = UserModel.objects.filter(email__iexact=email).first()
            if user:
                if not user.google:
                    user.google = sub
            else:
                user = UserModel(
                    email=email,
                    google=sub,
                    first_name=given_name,
                    last_name=family_name,
                )
                created = True

        changed = False
        updates = {
            "first_name": given_name,
            "last_name": family_name,
        }

        if hasattr(user, "image") and picture and getattr(user, "image") != picture:
            setattr(user, "image", picture)
            changed = True

        for field, new_val in updates.items():
            if new_val and getattr(user, field, "") != new_val:
                setattr(user, field, new_val)
                changed = True

        if hasattr(user, "is_verified") and email_verified and user.is_verified is False:
            user.is_verified = True
            changed = True

        if created:
            user.set_unusable_password()
            user.save()
        elif changed:
            user.save()

        refresh = RefreshToken.for_user(user)
        data = {
            "user": {
                "id": str(user.id),
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "image": getattr(user, "image", ""),
                "is_verified": getattr(user, "is_verified", False),
            },
            "tokens": {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            },
        }
        return Response(data, status=status.HTTP_200_OK)
