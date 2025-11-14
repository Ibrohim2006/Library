from django.urls import path
from .views import GoogleLoginAPIView, GoogleAuthCallbackAPIView

app_name = 'authentication'

urlpatterns = [
    path("google/", GoogleLoginAPIView.as_view(), name="google_login"),
    path("google/callback/", GoogleAuthCallbackAPIView.as_view(), name="google_callback"),
]
