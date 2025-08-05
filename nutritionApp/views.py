from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser
from .models import CustomUser, OTP,MobileOTP
from .serializers import SignupSerializer, OTPVerifySerializer, LoginSerializer, UserSerializer, CustomTokenSerializer,FoodImageUploadSerializer
import random
from django.contrib.auth import authenticate
from rest_framework_simplejwt.views import TokenObtainPairView
import requests
import os
from google import genai
from google.genai import types
from dotenv import load_dotenv
import re
import json
from pymongo import MongoClient
from bson.binary import Binary
import urllib.parse
from django.utils import timezone
api_user_token = os.getenv("LOGMEAL_API_TOKEN")
api_key=os.getenv("GEMINE_API_KEY")
client =  genai.Client(api_key=api_key)


def store_image_and_response_to_mongo(image_bytes, response_text):
    try:
        # MongoDB credentials
        username = "soumya-123"
        password = "Soumya"
        encoded_username = urllib.parse.quote_plus(username)
        encoded_password = urllib.parse.quote_plus(password)
        connection_string=f"mongodb+srv://soumya-123:{encoded_password}@cluster0.zaytioc.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
        # connection_string=f"mongodb+srv://soumya-123:{encoded_password}@cluster0.zaytioc.mongodb.net/"
        # Connect to MongoDB
        client = MongoClient(connection_string)
        db = client["Nutrition"]
        collection = db["img-store"]

        # Create document
        document = {
            "image": Binary(image_bytes),
            "response": response_text
        }

        # Insert document
        collection.insert_one(document)

    except Exception as e:
        # Raise to be handled by the calling view
        raise RuntimeError(f"MongoDB insert error: {e}")



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
    parser_classes = [MultiPartParser]  # To handle file upload

    def post(self, request):
        image_file = request.FILES.get('image')

        if not image_file:
            return Response({'error': 'Missing image file'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            image_bytes = image_file.read()

            prompt = (
                "List the different food items visible in this image. "
                "Return them as a comma-separated list only. No explanation."
            )

            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[
                    types.Part.from_bytes(
                        data=image_bytes,
                        mime_type='image/jpeg',
                    ),
                    prompt
                ]
            )

            raw_text = response.text
            food_names = [item.strip() for item in raw_text.split(',') if item.strip()]
            store_image_and_response_to_mongo(
                image_bytes=image_bytes,
                response_text=food_names
            )

            return Response({'food_groups': food_names}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)        
        
        
def parse_nutrition_json_from_raw_text(raw_text: str) -> dict:
    """
    Extract JSON object from Markdown-style response and return clean dict.
    """
    # Match the JSON block between ```json ... ```
    match = re.search(r'```json\n(.+?)\n```', raw_text, re.DOTALL)
    if match:
        json_str = match.group(1)
        try:
            data = json.loads(json_str)
            return {"nutrition_data": data}
        except json.JSONDecodeError:
            return {"error": "Failed to decode JSON."}
    else:
        return {"error": "No JSON block found in response."}


class ExtractAllInfoAPIView(APIView):
    parser_classes = [MultiPartParser]  # To handle file upload

    def post(self, request):
        image_file = request.FILES.get('image')

        if not image_file:
            return Response({'error': 'Missing image file'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            image_bytes = image_file.read()

            prompt = (
            "Analyze the image and return a JSON array of foods with nutritional values based on the actual quantity shown in the image. "
            "For each item, return: food_name, estimated_quantity, calories, protein_g, fats_g, carbs_g, vitamin_k, vitamin_c, fiber_g. "
            "Format the response as raw JSON inside triple backticks (```json ... ```)."
            )

            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[
                    types.Part.from_bytes(data=image_bytes, mime_type='image/jpeg'),
                    prompt
                ]
            )
           
            parsed_data = parse_nutrition_json_from_raw_text(response.text)
            store_image_and_response_to_mongo(
                image_bytes=image_bytes,
                response_text=response.text
            )
            return Response(parsed_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)        


def clean_gemini_raw_json(raw_text: str) -> dict:
    """
    Extract and parse a JSON object from a Markdown-style code block returned by Gemini.
    """
    try:
        # Remove code block markers and extract the inner JSON
        cleaned = re.sub(r'^```json|```$', '', raw_text.strip(), flags=re.MULTILINE).strip()
        return json.loads(cleaned)
    except Exception as e:
        return {"error": "Failed to parse JSON", "details": str(e), "raw_text": raw_text}
    
#for email password verification.
class CheckEmailPasswordAPIView(APIView):
    parser_classes = [MultiPartParser]

    def post(self, request):
        username = "soumya-123"
        password = "Soumya"
        encoded_username = urllib.parse.quote_plus(username)
        encoded_password = urllib.parse.quote_plus(password)
        connection_string=f"mongodb+srv://soumya-123:{encoded_password}@cluster0.zaytioc.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
        # connection_string=f"mongodb+srv://soumya-123:{encoded_password}@cluster0.zaytioc.mongodb.net/"
        # Connect to MongoDB
        client = MongoClient(connection_string)
        db = client["Nutrition"]
        collection = db["user-info"]
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return Response({"message": "Email and password are required."}, status=status.HTTP_400_BAD_REQUEST)

        user = collection.find_one({"email": email})

        if not user:
            return Response({"message": "No email present."}, status=status.HTTP_404_NOT_FOUND)

        # If password is hashed in DB, use check_password:
        # if check_password(password, user["password"]):
        if user["password"] == password:
            return Response({"message": True}, status=status.HTTP_200_OK)
        else:
            return Response({"message": False}, status=status.HTTP_200_OK)


#for saving user info in to db.
class SaveUserProfileAPIView(APIView):
    
    def post(self, request):
        try:
            username = "soumya-123"
            password = "Soumya"
            encoded_username = urllib.parse.quote_plus(username)
            encoded_password = urllib.parse.quote_plus(password)
            connection_string=f"mongodb+srv://soumya-123:{encoded_password}@cluster0.zaytioc.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
            # connection_string=f"mongodb+srv://soumya-123:{encoded_password}@cluster0.zaytioc.mongodb.net/"
            # Connect to MongoDB
            client = MongoClient(connection_string)
            db = client["Nutrition"]
            collection = db["user-info"]
        except Exception as e :
            return Response(
                {"message": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        try:
            data = request.data
            required_fields = [
                'gender', 'age', 'weight', 'height', 'primary_goal',
                'medical_condition', 'food_preference', 'mode_of_progress'
            ]

            # Check all required fields are present
            if not all(field in data for field in required_fields):
                return Response(
                    {"message": "Missing required fields."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            profile_data = {
                "gender": data.get("gender"),
                "age": int(data.get("age")),
                "weight": float(data.get("weight")),
                "height": float(data.get("height")),
                "primary_goal": data.get("primary_goal"),
                "medical_condition": data.get("medical_condition"),
                "food_preference": data.get("food_preference"),
                "mode_of_progress": data.get("mode_of_progress")
            }
            print("insert the data.")

            collection.insert_one(profile_data)

            return Response(
                {"message": "User profile saved successfully."},
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return Response(
                {"message": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

#otp generation and otp verification.
class MobileOTPAPIView(APIView):
    def post(self, request):
        mobile = request.data.get("mobile")
        otp = request.data.get("otp")
        username = "soumya-123"
        password = "Soumya"
        encoded_username = urllib.parse.quote_plus(username)
        encoded_password = urllib.parse.quote_plus(password)
        connection_string=f"mongodb+srv://soumya-123:{encoded_password}@cluster0.zaytioc.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
        # connection_string=f"mongodb+srv://soumya-123:{encoded_password}@cluster0.zaytioc.mongodb.net/"
        # Connect to MongoDB
        client = MongoClient(connection_string)
        db = client["Nutrition"]
        collection = db["otp-verification"]
        if not mobile:
            return Response({"error": "Mobile number is required"}, status=status.HTTP_400_BAD_REQUEST)

        if len(mobile) != 10 or not mobile.isdigit():
            return Response({"error": "Invalid mobile number"}, status=status.HTTP_400_BAD_REQUEST)

        if otp:
            # Verify OTP
            record = collection.find_one({"mobile": mobile})
            if not record:
                return Response({"error": "Mobile number not found"}, status=status.HTTP_404_NOT_FOUND)

            if record["otp"] == otp:
                return Response({"message": "OTP is valid"}, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)

        else:
            # Send OTP
            generated_otp = f"{random.randint(100000, 999999)}"
            # In real app, send OTP via SMS here
            collection.update_one(
                {"mobile": mobile},
                {"$set": {"otp": generated_otp}},
                upsert=True
            )
            return Response({"message": "OTP sent successfully", "otp": generated_otp}, status=status.HTTP_200_OK)
        

class EmailOTPAPIView(APIView):
    def post(self, request):
        email = request.data.get("email")
        otp = request.data.get("otp")
        username = "soumya-123"
        password = "Soumya"
        encoded_username = urllib.parse.quote_plus(username)
        encoded_password = urllib.parse.quote_plus(password)
        connection_string=f"mongodb+srv://soumya-123:{encoded_password}@cluster0.zaytioc.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
        # connection_string=f"mongodb+srv://soumya-123:{encoded_password}@cluster0.zaytioc.mongodb.net/"
        # Connect to MongoDB
        client = MongoClient(connection_string)
        db = client["Nutrition"]
        collection = db["otp-verification"]
        if not email:
            return Response({"error": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)


        if otp:
            # Verify OTP
            record = collection.find_one({"email": email})
            if not record:
                return Response({"error": "Email not found"}, status=status.HTTP_404_NOT_FOUND)

            if record["otp"] == otp:
                return Response({"message": "OTP is valid"}, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)

        else:
            # Send OTP
            generated_otp = f"{random.randint(100000, 999999)}"
            # In real app, send OTP via SMS here
            collection.update_one(
                {"email": email},
                {"$set": {"otp": generated_otp}},
                upsert=True
            )
            return Response({"message": "OTP sent successfully", "otp": generated_otp}, status=status.HTTP_200_OK)