from rest_framework_simplejwt.tokens import RefreshToken


def create_jwt_token(user) -> dict:
    refresh = RefreshToken.for_user(user)
    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    }
# -------------------------------------------------


import secrets
import string
import hashlib
from django.core.mail import send_mail
from django.conf import settings

def generate_otp(length=6):
    alphabet = string.ascii_letters + string.digits + "!@#$%&*"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def hash_otp(otp, salt=None):
    if salt is None:
        salt = secrets.token_hex(16)
    hashed = hashlib.sha256((salt + otp).encode()).hexdigest()
    return hashed, salt


def send_otp_email(email, otp):
    subject = "Your verification code"
    message = f"Sizning kirish kodingiz: {otp}\nKod 10 daqiqa amal qiladi."
    return send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])
