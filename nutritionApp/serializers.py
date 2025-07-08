from rest_framework import serializers
from .models import CustomUser, OTP
from django.contrib.auth import authenticate
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class SignupSerializer(serializers.Serializer):
    phone = serializers.CharField()
    password = serializers.CharField(write_only=True)

class OTPVerifySerializer(serializers.Serializer):
    phone = serializers.CharField()
    otp = serializers.CharField()

class LoginSerializer(serializers.Serializer):
    phone = serializers.CharField()
    password = serializers.CharField(write_only=True)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'phone']

class CustomTokenSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['phone'] = user.phone
        return token
    
class FoodImageUploadSerializer(serializers.Serializer):
    image = serializers.ImageField(required=True)
