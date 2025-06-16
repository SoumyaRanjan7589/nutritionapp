from django.contrib import admin
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import SignupView, OTPVerifyView, CustomLoginView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('signup/', SignupView.as_view()),
    path('verify-otp/', OTPVerifyView.as_view()),
    path('login/', CustomLoginView.as_view()),
    path('api/token/refresh/', TokenRefreshView.as_view())
]
