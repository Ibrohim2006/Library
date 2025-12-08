from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from authentication.managers import UserManager
from core.base import BaseModel


class UserModel(AbstractUser, BaseModel):
    username = None
    email = models.EmailField(unique=True, blank=False, null=False)
    google = models.CharField(max_length=255, blank=True, null=True)

    is_verified = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email


# -------------------------------------------------------


class OTP(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="otps"
    )
    salt = models.CharField(max_length=64)
    otp_hash = models.CharField(max_length=64)  # sha256
    expires_at = models.DateTimeField()
    attempts = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"OTP for {self.user.email}"
