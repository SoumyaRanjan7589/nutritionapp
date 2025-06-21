from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import CustomUser, OTP
from .serializers import SignupSerializer, OTPVerifySerializer, LoginSerializer, UserSerializer, CustomTokenSerializer
import random
from django.contrib.auth import authenticate
from rest_framework_simplejwt.views import TokenObtainPairView
import requests
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


class MultiFoodDetectionAPIView(APIView):
    def post(self, request):
        image_file = request.FILES.get('image')
        # api_user_token = request.POST.get('api_user_token')
        api_user_token='eb2e800de7a802a5a284b4f6e1d8fa4ce243ca28'

        if not image_file or not api_user_token:
            return Response({'error': 'Missing image'}, status=status.HTTP_400_BAD_REQUEST)

        headers = {
            'Authorization': f'Bearer {api_user_token}'
        }

        api_url = 'https://api.logmeal.com/v2'
        endpoint = '/image/segmentation/complete'

        try:
            response = requests.post(
                api_url + endpoint,
                files={'image': image_file},
                headers=headers
            )

            if response.status_code != 200:
                return Response({'error': 'Failed to contact LogMeal API', 'details': response.text},
                                status=status.HTTP_502_BAD_GATEWAY)

            food_groups = response.json().get('foodFamily', [])
            return Response({'food_groups': food_groups}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        
        
class ProteinDetectionAPIView(APIView):
    # 🔐 Hardcoded API Token (or load securely from env)
    API_USER_TOKEN = 'eb2e800de7a802a5a284b4f6e1d8fa4ce243ca28'

    def post(self, request):
        image_file = request.FILES.get('image')

        if not image_file:
            return Response({'error': 'Missing image file'}, status=status.HTTP_400_BAD_REQUEST)

        headers = {
            'Authorization': f'Bearer {self.API_USER_TOKEN}'
        }

        api_url = 'https://api.logmeal.com/v2'

        try:
            # Step 1: Detect food dish to get imageId
            detect_endpoint = '/image/segmentation/complete'
            detect_response = requests.post(
                api_url + detect_endpoint,
                files={'image': image_file},
                headers=headers
            )

            if detect_response.status_code != 200:
                return Response({'error': 'Failed at image detection step', 'details': detect_response.text},
                                status=status.HTTP_502_BAD_GATEWAY)

            image_id = detect_response.json().get('imageId')
            print("imageid= ",image_id)
            if not image_id:
                return Response({'error': 'imageId not found in response'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # Step 2: Fetch nutritional info (including protein)
            nutrition_endpoint = '/nutrition/recipe/nutritionalInfo'
            nutrition_response = requests.post(
                api_url + nutrition_endpoint,
                json={'imageId': image_id},
                headers=headers
            )
            print("nutrition_response= ",nutrition_response)
            if nutrition_response.status_code != 200:
                return Response({'error': 'Failed at nutrition info step', 'details': nutrition_response.text},
                                status=status.HTTP_502_BAD_GATEWAY)

            nutrition_data = nutrition_response.json()
            protein = nutrition_data['nutritional_info']['totalNutrients']['PROCNT']['quantity']
            unit = nutrition_data['nutritional_info']['totalNutrients']['PROCNT']['unit']

            return Response({'protein_info': f'{protein} {unit}'}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
