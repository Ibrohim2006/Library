import logging
from django.urls import reverse
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework_simplejwt.tokens import RefreshToken

from .models import UserModel
from .oauth import oauth
from .serializers import UserSerializer, GoogleAuthResponseSerializer,LoginSerializer,RegisterSeriliazer
from .utils import create_jwt_token

logger = logging.getLogger(__name__)


class GoogleLoginAPIView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="Start Google login flow",
        operation_description=(
                "Redirects the user to the Google OAuth login/consent screen. "
                "When testing from Swagger, it will perform a real redirect."
        ),
        responses={
            302: openapi.Response(
                description="Redirect to Google OAuth consent screen"
            )
        },
    )
    def get(self, request, *args, **kwargs):
        redirect_uri = request.build_absolute_uri(
            reverse("authentication:google_callback")
        )

        django_request = request._request
        return oauth.google.authorize_redirect(django_request, redirect_uri)


class GoogleAuthCallbackAPIView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        operation_summary="Google OAuth callback",
        operation_description=(
                "Handles the callback from Google OAuth, creates or retrieves the user, "
                "then returns a JWT token together with user information."
        ),
        responses={
            200: GoogleAuthResponseSerializer,
            400: openapi.Response(description="Auth error / invalid request"),
        },
    )
    def get(self, request, *args, **kwargs):
        django_request = request._request

        try:
            token = oauth.google.authorize_access_token(django_request)

            user_info = token.get("userinfo")
            if not user_info:
                user_info = oauth.google.parse_id_token(django_request, token)

            if not user_info:
                logger.error("Google user info not found")
                return Response(
                    {"detail": "Failed to get user info from Google"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            email = user_info.get("email")
            if not email:
                return Response(
                    {"detail": "Email was not provided by Google"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            google_sub = user_info.get("sub")
            first_name = user_info.get("given_name", "")
            last_name = user_info.get("family_name", "")

            user, created = UserModel.objects.get_or_create(
                email=email,
                defaults={
                    "google": google_sub,
                    "first_name": first_name,
                    "last_name": last_name,
                    "is_verified": True,
                },
            )

            if not created and (not user.google) and google_sub:
                user.google = google_sub
                user.is_verified = True
                user.save(update_fields=["google", "is_verified"])

            jwt_token = create_jwt_token(user)
            user_data = UserSerializer(user).data

            return Response(
                {
                    "message": "Google auth success",
                    "token": jwt_token,
                    "user": user_data,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            logger.exception("Google auth error")
            return Response(
                {"detail": f"Auth error: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class RegisterAPIView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer=RegisterSeriliazer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                "message":"foydalanuvchi muvaffaqiyatli ro'yxatdan o'tdi",
                "user": UserSerializer(user).data,
                "refresh": str(refresh),
                "access": str(refresh.access_token),

            },status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginAPIView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer=LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data["user"]
            refresh = RefreshToken.for_user(user)
            return Response({
                'message':"login muvaffaqiyatli",
                'user': UserSerializer(user).data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),

            },status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)