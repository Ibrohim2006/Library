from django.urls import path
from .views import *

app_name = 'authentication'

urlpatterns = [
    path("google/", GoogleLoginAPIView.as_view(), name="google_login"),
    path("google/callback/", GoogleAuthCallbackAPIView.as_view(), name="google_callback"),
    path('register/', RegisterAPIView.as_view(), name="register"),
    path('login/', LoginAPIView.as_view(), name="login"),
]

