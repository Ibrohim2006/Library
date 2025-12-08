import logging
from django.urls import reverse
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from authentication.models import UserModel
from authentication.oauth import oauth
from authentication.serializers import UserSerializer, GoogleAuthResponseSerializer
from authentication.utils import create_jwt_token

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
# ---------------------------------------------------------------

from datetime import datetime, timedelta
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from django.utils import timezone

from .models import UserModel, OTP
from .serializers import RegisterSerializer, VerifySerializer, MeSerializer
from .oauth import create_access_token
from .utils import generate_otp, hash_otp, send_otp_email


class RegisterView(APIView):
    def post(self, request):
        ser = RegisterSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        name = ser.validated_data["name"]
        email = ser.validated_data["email"]

        # User yaratish yoki mavjudini olish
        user, created = User.objects.get_or_create(email=email, defaults={"name": name})

        otp = generate_otp()
        otp_hash, salt = hash_otp(otp)
        expires = timezone.now() + timedelta(minutes=10)

        OTP.objects.create(
            user=user,
            otp_hash=otp_hash,
            salt=salt,
            expires_at=expires
        )

        # Email yuborish (dev yoki prod)
        send_otp_email(email, otp)

        return Response({"detail": "OTP emailingizga yuborildi"}, status=200)


class VerifyView(APIView):
    def post(self, request):
        ser = VerifySerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        email = ser.validated_data["email"]
        otp_input = ser.validated_data["otp"]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"detail": "User topilmadi"}, status=400)

        otp_obj = OTP.objects.filter(user=user).order_by("-created_at").first()
        if otp_obj is None:
            return Response({"detail": "OTP mavjud emas. Avval register qiling"}, status=400)

        if otp_obj.expires_at < timezone.now():
            return Response({"detail": "OTP muddati tugagan"}, status=400)

        if otp_obj.attempts >= 5:
            return Response({"detail": "Urinishlar cheklangan"}, status=429)

        # Tekshirish
        hashed, _ = hash_otp(otp_input, otp_obj.salt)

        if hashed != otp_obj.otp_hash:
            otp_obj.attempts += 1
            otp_obj.save()
            return Response({"detail": "OTP noto‘g‘ri"}, status=400)

        # To‘g‘ri → userni active qilamiz
        user.is_active = True
        user.save()

        otp_obj.delete()  # OTP-ni o'chiramiz

        token = create_access_token(user.id)

        return Response({"access_token": token, "token_type": "bearer"})


class MeView(APIView):
    def get(self, request):
        # Tokenni DRF SimpleJWT o‘rniga o‘zimiz parse qilamiz
        auth = request.headers.get("Authorization")
        if not auth:
            return Response({"detail": "Token yo‘q"}, status=401)

        try:
            scheme, token = auth.split()
            import jwt
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        except:
            return Response({"detail": "Token noto‘g‘ri"}, status=401)

        user_id = payload.get("sub")
        user = User.objects.get(id=user_id)

        return Response(MeSerializer(user).data)
