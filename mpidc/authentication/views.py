import uuid, re
from datetime import timedelta
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db.models import Q, F
from django.utils import timezone
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import JSONParser
from rest_framework.authtoken.models import Token
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from .models import (
    CustomUserProfile,
    UserProfileStatus,
    DigiLockerSession,
    UserHasRole,
    Role,
    Country,
    WebAppointmentModel
)
from .serializers import (
    UserSignupSerializer,
    UserSignSerializer,
    DigiLockerSessionSerializer,
    UserSerializer,
    CustomUserProfileSerializer,
    WebAppointmentSerializer
)
from django.db import transaction
from django.conf import settings
from django.http import JsonResponse
global_err_message = settings.GLOBAL_ERR_MESSAGE  


class RegisterView(APIView):

    @swagger_auto_schema(
            request_body=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'name': openapi.Schema(type=openapi.TYPE_STRING, description="name"),
                    'password': openapi.Schema(type=openapi.TYPE_STRING, description="password"),
                    'mobile_no': openapi.Schema(type=openapi.TYPE_STRING, description="mobile_no"),
                    'email_id':openapi.Schema(type=openapi.TYPE_STRING, description="email_id"),
                    'confirm_password': openapi.Schema(type=openapi.TYPE_STRING, description="confirm_password")
                },
                required=['password','name','mobile_no','email_id','confirm_password']
            )
        )

    def post(self, request):
        data = request.data
        print("")

        required_fields = [
            "name",
            "mobile_no",
            "email_id",
            "password",
            "confirm_password",
        ]
        missing_fields = [field for field in required_fields if not data.get(field)]

        if missing_fields:
            return Response(
                {
                    "status": False,
                    "message": f"Missing required fields: {', '.join(missing_fields)}",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        mobile_no = data["mobile_no"]
        email_id = data["email_id"]
        country_code = data['country_code'] if 'country_code' in data else None

        if data["password"] != data["confirm_password"]:
            return Response(
                {
                    "status": False,
                    "message": "Password & confirm password is not matched",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if len(mobile_no) != 10:
            return Response(
                {"status": False, "message": "Mobile number must be of 10 digits."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not mobile_no.isdigit():
            return Response(
                {"status": False, "message": "Mobile number must contain only digits."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if int(mobile_no[0]) < 6:
            return Response(
                {"status": False, "message": "Invalid mobile number."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # this checks if the user with same mobile_no and email_id is present in db
        if (
            CustomUserProfile.objects.filter(email=email_id).exists()
            or CustomUserProfile.objects.filter(mobile_no=mobile_no).exists()
        ):
            return Response(
                {
                    "status": False,
                    "message": "User with this email or mobile number already exists.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        if "@" not in email_id:
            return Response(
                {
                    "status": False,
                    "message": "Email must contain '@'.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        # Validate the serializer
        serializer = UserSignupSerializer(data=data)
        if serializer.is_valid():

            try:
                
                with transaction.atomic():
                    country_code_obj=None
                    if country_code:
                        country_code_obj = Country.objects.filter(code=country_code).first()
                        if not country_code_obj:
                            return Response({"status": False, "message": f"Invalid country code: {country_code}"},status=400)

                    user = User.objects.create_user(
                        username=email_id,  # Use email as the username               
                        password=data["password"],
                    )
                    custom_user_profile = CustomUserProfile.objects.create(
                            user=user,  # Associate the created user
                            name=data["name"],
                            email=email_id,
                            mobile_no=mobile_no,
                            country_code = country_code_obj,
                            document_folder=str(uuid.uuid4())
                        )
                    UserProfileStatus.objects.create(user=user, is_profile_completed=False)
                        # assign the Investor role
                    try:
                        investor_role = Role.objects.get(role_name="Investor")
                        UserHasRole.objects.create(user=user, role=investor_role)
                    except Role.DoesNotExist:
                            return Response(
                                {"status": False, "message": "Investor role not found in the system."},
                                status=status.HTTP_400_BAD_REQUEST,
                            )

                    return Response(
                            {"status": True, "message": "User registered successfully"},
                            status=status.HTTP_201_CREATED,
                        )
            except Exception as e:
                # If their is any error while user creating this will rollback the craeted user in auth table.
                return Response(
                    {
                        "status": False,
                        "message": global_err_message,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        errors = serializer.errors
        formatted_errors = {
            field: errors[field][0] for field in errors
        }  # Extract the first error message
        return Response(
            {
                "status": False,
                "message": "Validation failed",
                "errors": formatted_errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )



class LoginView(APIView):

    @swagger_auto_schema(
            request_body=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'password': openapi.Schema(type=openapi.TYPE_STRING, description="Password"),
                    'username': openapi.Schema(type=openapi.TYPE_STRING, description="Username")
                },
                required=['password','username']
            )
        )

    def post(self, request):
        try:
            serializer = UserSignSerializer(data=request.data)

            if not serializer.is_valid():
                errors = serializer.errors
                if "username" in errors:
                    return Response(
                        {"status": False, "message": "Username is required."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                if "password" in errors:
                    return Response(
                        {"status": False, "message": "Password is required."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                return Response(
                    {"status": False, "message": "Invalid input."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            username = serializer.validated_data["username"]
            password = serializer.validated_data["password"]

            is_user_registered = User.objects.filter(username=username).exists()

            if not is_user_registered:
                return Response(
                    {"status": False, "message": "User not registered."},
                    status=400
                )

            user = authenticate(request, username=username, password=password)
            if user is None:
                return Response(
                    {"status": False, "message": "Invalid credentials."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            custom_profile_satus = UserProfileStatus.objects.filter(user=user).first()
            profile_status = False
            if custom_profile_satus:
                profile_status = custom_profile_satus.is_profile_completed

            refresh = RefreshToken.for_user(user)

            return Response(
                {
                    "status": True,
                    "message": "Login successful",
                    "access_token": str(refresh.access_token),
                    "refresh_token": str(refresh),
                    "is_profile_completed": profile_status,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {"status": False, "message": global_err_message},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class UserProfileView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        try:
            custom_profile = CustomUserProfile.objects.get(user=user)

            roles = UserHasRole.objects.filter(user=user).select_related('role')
            primary_role = {}
            secondary_roles = []
            role_list = {}

            for role in roles:
                if role.role_type == "primary":
                    primary_role['role_name'] = role.role.role_name
                elif role.role_type == "secondary":
                    secondary_roles.append({"role_name": role.role.role_name})
            role_list['primary'] = primary_role
            role_list['secondary'] = secondary_roles

            user_data = {
                "user_id": custom_profile.user_id,
                "name": custom_profile.name,
                "email_id": custom_profile.email,
                "mobile_no": custom_profile.mobile_no,
                "role": role_list,
                "folder_name": custom_profile.document_folder if custom_profile.document_folder else str(custom_profile.user_id)
            }

            return Response({
                "status": True,
                "message": "",
                "data": user_data
                }, status=status.HTTP_200_OK)

        except CustomUserProfile.DoesNotExist:
            return Response(
                {
                    "status": False,
                    "message": "User profile not found.",
                    "data": {}
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

class OTPView(APIView):
    parser_classes = [JSONParser]

    @swagger_auto_schema(
            request_body=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'email_id': openapi.Schema(type=openapi.TYPE_STRING, description="email")
                },
                required=['email_id']
            )
        )

    def post(self, request):
        email_id = request.data.get("email_id")

        if not email_id:
            return Response(
                {"status": False, "message": "Email is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if "@" not in email_id:
            return Response(
                {
                    "status": False,
                    "message": "Email must contain '@'",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        if not re.match(email_regex, email_id):
            return Response(
                {"status": False, "message": "Invalid email address"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(username=email_id)
            user_profile = CustomUserProfile.objects.get(user=user)
        except CustomUserProfile.DoesNotExist:
            return Response(
                {"status": False, "message": "User not found"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        # otp static as per now.
        otp = "123456"

        # Saving opt and expiry time in db
        user_profile.otp = otp
        user_profile.otp_expiry = timezone.now() + timedelta(minutes=15)
        user_profile.save()

        mobile_no = user_profile.mobile_no
        try:
            send_mail(
                subject="Your OTP for Password Reset",  # Email subject
                message=f"Your OTP for password reset is: {otp} and valid for 15 minutes.",
                from_email=settings.DEFAULT_FROM_EMAIL,  # Sender email address
                recipient_list=[email_id],
                fail_silently=False,
            )
        except Exception as e:
            return Response(
                {"status": global_err_message},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        return Response(
            {
                "status": True,
                "message": f"OTP sent successfully to your registered mobile number ending with XXXXXXX{mobile_no[-3:]} and email {email_id}",
            },
            status=status.HTTP_200_OK,
        )


class ForgotPasswordVerifyView(APIView):
    parser_classes = [JSONParser]

    @swagger_auto_schema(
            request_body=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'email_id': openapi.Schema(type=openapi.TYPE_STRING, description="Email"),
                    'otp': openapi.Schema(type=openapi.TYPE_STRING, description="OTP"),
                    'new_password':openapi.Schema(type=openapi.TYPE_STRING, description="New Password")
                },
                required=['email_id','otp','new_password']
            )
        )

    def post(self, request):
        email_id = request.data.get("email_id")
        otp = request.data.get("otp")
        new_password = request.data.get("new_password")
        # need to encrypt password from the front end
        fields = {"email_id": email_id, "otp": otp, "new_password": new_password}

        for key, value in fields.items():
            if not value:
                return Response(
                    {"status": False, "message": f"{key} is missing."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        if not re.match(email_regex, email_id):
            return Response(
                {"status": False, "message": "Invalid email address"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(username=email_id)
        except User.DoesNotExist:
            return Response(
                {"status": False, "message": "User not found."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            user_profile = CustomUserProfile.objects.get(user=user)
        except CustomUserProfile.DoesNotExist:
            return Response(
                {"status": False, "message": "User profile not found."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check OTP validity
        if user_profile.otp != otp:
            return Response(
                {"status": False, "message": "Invalid OTP"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if timezone.now() > user_profile.otp_expiry:
            return Response(
                {"status": False, "message": "OTP has expired"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Update password
        user = user_profile.user
        user.set_password(new_password)
        user.save()

        # Clear OTP fields
        user_profile.otp = None
        user_profile.otp_expiry = None
        user_profile.save()

        return Response(
            {
                "status": True,
                "message": "Password reset successful now login with your new password.",
            },
            status=status.HTTP_200_OK,
        )

class SaveSessionView(APIView):
    def post(self, request):
        try:
            data = request.data
            session_id = data.get("session_id")

            if not session_id:
                return Response({"status": False, "message": "session_id is required."}, status=status.HTTP_400_BAD_REQUEST)

            session_data = {"session_id": session_id}
            serializer = DigiLockerSessionSerializer(data=session_data)

            if serializer.is_valid():
                serializer.save()
                return Response({"status": True, "message": "Session created successfully"}, status=status.HTTP_201_CREATED)
            else:
                return Response({"status": False, "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"error": global_err_message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class UserDataView(APIView):
    def post(self, request):
        try:
            required_fields = [
                "digilockerid", "name", "dob", "gender",
                "reference_key", "mobile", "picture", "email", "mimeType", "session_id"
            ]
            data = request.data
            email_id = data.get("email")
            mobile = data.get("mobile")
            name = data.get("name")
            session_id = data.get("session_id")
            digilockerid = data.get("digilockerid")
            if not (email_id or mobile or digilockerid):
                return Response({
                    "status": False,
                    "message": "Either email, mobile, or digilockerid is required."
                }, status=status.HTTP_400_BAD_REQUEST)

            username = email_id if email_id else mobile if mobile else digilockerid

            user = User.objects.filter(username=username).first()

            if user:
                
                investor_role = Role.objects.get(role_name="Investor")
                user_role_data = UserHasRole.objects.filter(user=user, role=investor_role).first()
                if not user_role_data:
                    UserHasRole.objects.create(user=user, role=investor_role)
                
                CustomUserProfile.objects.filter(user=user).update(
                    session_id=session_id,
                    email=email_id if email_id else F('email')
                )

                existing_session = DigiLockerSession.objects.filter(session_id=session_id).first()

                if existing_session:
                    existing_session.user = user
                    existing_session.save()
                else:
                    DigiLockerSession.objects.update_or_create(
                        user=user,
                        defaults={"session_id": session_id}
                    )

                return Response({
                    "status": True,
                    "message": "User already exists, session updated!"
                }, status=status.HTTP_200_OK)

            password = data.get("password", "123456")
            user_serializer = UserSerializer(data={
                "username": username,                
                "password": password
            })

            if user_serializer.is_valid():
                user = user_serializer.save()
                user.set_password(password)
                user.save()

                profile_serializer = CustomUserProfileSerializer(data={
                    "user": user.id,
                    "name": name if name else digilockerid,
                    "mobile_no": mobile if mobile else None,
                    "email": email_id if email_id else None,
                    "user_type": "guest",
                    "session_id": session_id
                })

                if profile_serializer.is_valid():
                    user_profile = profile_serializer.save()
                    UserProfileStatus.objects.create(user=user, is_profile_completed=False)

                    DigiLockerSession.objects.update_or_create(
                        session_id=session_id,
                        defaults={"user": user}
                    )

                    return Response({"status": True, "message": "User created."})

                return Response({"status": False, "message": profile_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

            return Response({"status": False, "message": user_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"error": global_err_message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class GetUserBySessionId(APIView):
    def post(self, request):
        try:
            data = request.data
            session_id = data.get("session_id")

            if not session_id:
                return Response({"status": False, "message": "Session ID is required"}, status=status.HTTP_400_BAD_REQUEST)

            user_profile = CustomUserProfile.objects.filter(session_id=session_id).first()

            if not user_profile:
                return Response({"status": False, "message": "Invalid session ID"}, status=status.HTTP_400_BAD_REQUEST)

            user = user_profile.user

            refresh = RefreshToken.for_user(user)

            user_profile.session_id = None
            user_profile.save()

            DigiLockerSession.objects.filter(session_id=session_id).update(status=False)
            custom_profile_satus = UserProfileStatus.objects.filter(user=user).first()
            profile_status = False
            if custom_profile_satus:
                profile_status = custom_profile_satus.is_profile_completed

            return Response(
                {
                    "status": True,
                    "message": "Login successful",
                    "access_token": str(refresh.access_token),
                    "refresh_token": str(refresh),
                    "is_profile_completed": profile_status,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response({"status": False, "error": global_err_message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class el_userdata(APIView):
    authentication_classes = []
    # permission_classes = [AllowAny]

    def post (self, request):
        code = request.data.get("code")
        state = request.data.get("state")
        error = request.data.get("error")
        description = request.data.get("description")

        return Response({
            "status":True,
            "code":code,
            "state":state,
            "error":error,
            "description":description
        },status=status.HTTP_200_OK)
    
class WebAppointmentFormView(APIView):
    def post (self, request):

        try:
            data = request.data
            email = data.get("email")
            date_of_appointment = data.get("date_of_appointment")
            email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"

            if not re.match(email_regex, email):
                return Response(
                    {"status": False, "message": "Invalid email address"},
                    status=400,
                )

            is_user_exists = WebAppointmentModel.objects.filter(email=email, date_of_appointment=date_of_appointment).exists()

            if is_user_exists:
                return Response({"status":False,"message":"Appointment form already filled."},
                                status=200)

            serializer = WebAppointmentSerializer(data=data)

            if serializer.is_valid():
                serializer.save()

                return Response(
                    {"status": True, "message": "Appointment created successfully"},
                    status = 201
                )
        except Exception as e:
            return Response({"status":False,"message":global_err_message},
                            status=500)
        
# def index(request):
#     print("Index function called",request.GET)
#     return JsonResponse({"message":"Working fine func based views!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!."})
from django.shortcuts import render
import requests
from django.shortcuts import redirect


def IndexView(request):
    print("_________________________________++++++++++++++++++++++++++++++")
    return render(request, "index.html")

def GoogleApiView(request):
    print("___CALLED")
    return redirect("https://www.google.com/")

from rest_framework.parsers import MultiPartParser, FormParser
from .utils import *
class UploadDocAWSView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self,request):

        try:
            document = request.FILES.get('document')
            print(type(document),"703")
            uploaded_file_path=UploadDocAWS((document))
            return Response({
                "status":False,
                "message": "File uploaded👍",
                "data": uploaded_file_path
            },status=200)

        except Exception as e:
            return Response({
                "message":str(e)
            },status=500)

    

