from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth.models import User
from rest_framework import serializers
from .models import CustomUserProfile, UserProfileStatus, DigiLockerSession, Country, WebAppointmentModel



class UserSignupSerializer(serializers.ModelSerializer):
    email_id = serializers.EmailField(write_only=True)
    password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUserProfile
        fields = ["name", "mobile_no", "email_id", "password"]

    def create(self, validated_data):
        """Hash password before saving to the database"""

        validated_data["password"] = make_password(validated_data["password"])
        return CustomUserProfile.objects.create(**validated_data)

    def create(self, validated_data):
        """Create the User and CustomUserProfile"""
        # Extract password and email_id
        password = validated_data.pop("password")
        email = validated_data.pop("email_id")

        # Create User object, password is automatically hashed by create_user
        user = User.objects.create_user(
            username=email,  # Use email as the username
            email=email,
            password=password,  # Password is hashed automatically
        )

        # Create the associated CustomUserProfile
        custom_user_profile = CustomUserProfile.objects.create(
            user=user,  # Associate the created user
            name=validated_data["name"],
            mobile_no=validated_data["mobile_no"],
        )

        return custom_user_profile


class UserSignSerializer(serializers.Serializer):
    username = serializers.EmailField()
    password = serializers.CharField(write_only=True)

class UserProfileStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model=UserProfileStatus
        feilds='__all__'
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username"]
class DigiLockerSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = DigiLockerSession
        fields = ["id", "user", "session_id", "created_at", "updated_at", "status"]
        extra_kwargs = {
            "created_at": {"read_only": True},
            "updated_at": {"read_only": True},
            "status": {"default": True},
        }
class CustomUserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUserProfile
        fields = ["id", "user", "name", "mobile_no", "user_type","session_id","email"]

class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = "__all__"

class WebAppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = WebAppointmentModel
        fields = "__all__"