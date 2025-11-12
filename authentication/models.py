from django.contrib.auth.models import AbstractUser
from django.db import models
from authentication.managers import UserManager
from core.base import BaseModel


class UserModel(AbstractUser, BaseModel):
    username = None
    email = models.EmailField(unique=True, blank=False, null=False)
    google = models.CharField(max_length=255, unique=True, null=True, blank=True)

    is_verified = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email
