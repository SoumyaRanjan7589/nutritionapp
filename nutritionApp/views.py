from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import CustomUser, OTP
from .serializers import SignupSerializer, OTPVerifySerializer, LoginSerializer, UserSerializer, CustomTokenSerializer
import random
from django.contrib.auth import authenticate
from rest_framework_simplejwt.views import TokenObtainPairView

class SignupView(APIView):
    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        if serializer.is_valid():
            phone = serializer.validated_data['phone']
            password = serializer.validated_data['password']
            if CustomUser.objects.filter(phone=phone).exists():
                return Response({'message': 'Phone already exists'}, status=400)
            otp_code = str(random.randint(1000, 9999))
            OTP.objects.update_or_create(phone=phone, defaults={'otp': otp_code})
            request.session['signup_password'] = password
            print(f"[DEBUG] OTP sent to {phone}: {otp_code}")
            return Response({'message': 'OTP sent successfully (mocked)'})
        return Response(serializer.errors, status=400)

class OTPVerifyView(APIView):
    def post(self, request):
        serializer = OTPVerifySerializer(data=request.data)
        if serializer.is_valid():
            phone = serializer.validated_data['phone']
            otp = serializer.validated_data['otp']
            try:
                otp_record = OTP.objects.get(phone=phone, otp=otp)
                password = request.session.get('signup_password')
                user = CustomUser.objects.create_user(phone=phone, password=password)
                otp_record.delete()
                return Response({'message': 'Signup successful'})
            except OTP.DoesNotExist:
                return Response({'message': 'Invalid OTP'}, status=400)
        return Response(serializer.errors, status=400)

class CustomLoginView(TokenObtainPairView):
    serializer_class = CustomTokenSerializer
