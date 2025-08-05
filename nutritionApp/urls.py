from django.contrib import admin
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import SignupView, OTPVerifyView, CustomLoginView,MultiFoodDetectionAPIView,ExtractAllInfoAPIView,SaveUserProfileAPIView,CheckEmailPasswordAPIView,MobileOTPAPIView,EmailOTPAPIView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('signup/', SignupView.as_view(),name='signup'),
    path('verify-otp/', OTPVerifyView.as_view(),name='verify_otp'),
    path('login/', CustomLoginView.as_view(),name='login'),
    path('api/token/refresh/', TokenRefreshView.as_view(),name='api_token_refresh'),
    path('multifooddetection/', MultiFoodDetectionAPIView.as_view(), name='multi_food_detection'),
    path('nutritioninfo/', ExtractAllInfoAPIView.as_view(), name='nutritioninfo'),
    path('emailpasswordverify/', CheckEmailPasswordAPIView.as_view(), name='emailpasswordverify'),
    path('userprofileinfo/', SaveUserProfileAPIView.as_view(), name='userprofileinfo'),
    path('mobileotp/', MobileOTPAPIView.as_view(), name='mobileotp'),
    path('emailotp/', EmailOTPAPIView.as_view(), name='mobileotp')
]
