from django.urls import path
from .views import AuthenticationViewSet

urlpatterns = [
    path("register/", AuthenticationViewSet.as_view({"post": "register"}), name="register"),
    path("login/", AuthenticationViewSet.as_view({"post": "login"}), name="login"),
    path("logout/", AuthenticationViewSet.as_view({"post": "logout"}), name="logout"),
    path("google/", AuthenticationViewSet.as_view({"post": "google_signin"}), name="google"),
]
