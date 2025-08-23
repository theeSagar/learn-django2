from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth.models import User
from .models import CustomUserProfile

class RegisterTestCase(APITestCase):
    def setUp(self):
        self.url = reverse('register') 
        self.valid_data = {
            "name": "Test User",
            "mobile_no": "9876543210",
            "email_id": "testuser@example.com",
            "password": "password123",
        }

    def test_missing_required_fields(self):
        # Test missing required fields
        data = self.valid_data.copy()
        del data["email_id"]
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Missing required fields", response.data["message"])

    def test_invalid_mobile_length(self):
        # Test mobile number that is not exactly 10 digits
        data = self.valid_data.copy()
        data["mobile_no"] = "98765432"
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Mobile number must be 10 digits", response.data["status"])

    def test_non_digit_mobile_number(self):
        # Test mobile number that contains non-digit characters
        data = self.valid_data.copy()
        data["mobile_no"] = "98765432AB"  # Invalid mobile number with letters
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Mobile number must contain only digits", response.data["message"])

    def test_invalid_mobile_start(self):
        # Test mobile number that starts with a digit less than 6
        data = self.valid_data.copy()
        data["mobile_no"] = "5876543210"  # Invalid mobile number starting with '5'
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Invalid mobile number", response.data["message"])

    def test_duplicate_email_or_mobile(self):
        # Test that user with same email or mobile number can't sign up
        existing_user = User.objects.create_user(
            username="existinguser@example.com",
            email="existinguser@example.com",
            password="password123",
        )
        CustomUserProfile.objects.create(
            user=existing_user,
            name="Existing User",
            mobile_no="9876543210",
        )

        data = self.valid_data.copy()
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("User with this email or mobile number already exists", response.data["message"])

    def test_invalid_email_format(self):
        data = self.valid_data.copy()
        data["email_id"] = "invalidemail.com"
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Email must contain '@'", response.data["message"])

    def test_successful_signup(self):
        data = self.valid_data.copy()
        data["email_id"] = "testuser@example.com"
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("User registered successfully", response.data["message"])
        self.assertEqual(response.data["mobile_no"], data["mobile_no"])
        self.assertEqual(response.data["username"], data["name"])

    def test_signup_with_invalid_serializer(self):
        data = self.valid_data.copy()
        del data["email_id"] 
        response = self.client.post(self.url, data, format='json')        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Missing required fields", response.data.get("message", ""))
