from django.contrib import admin
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import SignupView, OTPVerifyView, CustomLoginView,MultiFoodDetectionAPIView,ProteinDetectionAPIView

urlpatterns = [
    path('admin/', admin.site.urls,name='admin'),
    path('signup/', SignupView.as_view(),name='signup'),
    path('verify-otp/', OTPVerifyView.as_view(),name='verify_otp'),
    path('login/', CustomLoginView.as_view(),name='login'),
    path('api/token/refresh/', TokenRefreshView.as_view(),name='api_token_refresh'),
    path('multifooddetection/', MultiFoodDetectionAPIView.as_view(), name='multi_food_detection'),
    path('proteindetection/', ProteinDetectionAPIView.as_view(), name='protein_detection')
]
