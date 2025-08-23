import os,re
from django.db import connection, DatabaseError, transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from authentication.models import CustomUserProfile, UserProfileStatus
from sws.models import Designation
from .models import *
from .serializers import *
from sws.serializers import DesignationSerializer
from .utils import *
from sws.utils import generate_user_profile_pdf
from document_center.utils import *
from django.core.paginator import Paginator, EmptyPage
from django.conf import settings
import datetime
global_err_message = settings.GLOBAL_ERR_MESSAGE

class OrganizationTypeView(APIView):
    def get(self, request):
        try:
            organization_type = OrganizationType.objects.filter(status=1).order_by("id")
            serializer = OrganizationTypeSerializer(organization_type, many=True)
            return Response(
                getSuccessfulMessage(serializer.data, "Data Retrived Successfully"),
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                getOtherMessage({}, global_err_message),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

class OrganizationContactDetailView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            custom_profile = CustomUserProfile.objects.filter(user=user).first()
            if not custom_profile:
                return Response(
                    getErrorMessage("User id is not correct"),
                    status=status.HTTP_400_BAD_REQUEST,
                )
            designation_data = (
                DesignationSerializer(custom_profile.designation).data
                if custom_profile.designation
                else ""
            )
            if designation_data:
                designation_data = designation_data["id"]

            organization_details = UserOrgazination.objects.filter(
                user_profile=user
            ).first()
            if not organization_details:
                return Response(
                    getOtherMessage({}, "Organization details not found"),
                    status=status.HTTP_400_BAD_REQUEST,
                )
            organization_address = OrganizationAddress.objects.filter(
                organization=organization_details
            )
            md_user_details = {
                "name": "",
                "email_id": "",
                "country_code": "",
                "mobile_number": ""
            }
            md_user_data = OrganizationUserModel.objects.filter(organization=organization_details,
                    contact_type='Managing Director').first()
            if md_user_data:
                md_user_details = {
                    "name": md_user_data.name,
                    "email": md_user_data.email_id,
                    "country_code": md_user_data.country_code.id if md_user_data.country_code else None,
                    "mobile": md_user_data.mobile_number,
                    "designation": getattr(md_user_data,"designation",""),
                    "other_designation": getattr(md_user_data,"other_designation","")
                }
            
            user_details = {
                "name": custom_profile.name,
                "mobile": custom_profile.mobile_no,
                "email": custom_profile.email,
                "designation": designation_data,
                "alternate_email_id": custom_profile.alternate_email_id,
                "dob": custom_profile.dob,
                "pan_card_number": custom_profile.pan_card_number,
                "pan_verify": custom_profile.pan_verify,
            }            

            # If no organization or address found, return a message
            if not organization_address:
                return Response(
                    getOtherMessage({}, "Organization address details not found"),
                    status=status.HTTP_400_BAD_REQUEST,
                )

            registered_address = next(
                (
                    address
                    for address in organization_address
                    if address.address_type == "Registered"
                ),
                None,
            )
            communication_address = next(
                (
                    address
                    for address in organization_address
                    if address.address_type == "Communication"
                ),
                None,
            )

            # Serialize the organization and address details
            organization_serializer = OrganizationDetailSerializer(organization_details)
            registered_address_serializer = OrganizationAddressSerializer(
                registered_address
            )
            communication_address_serializer = OrganizationAddressSerializer(
                communication_address
            )

            response = {
                "org_id": organization_details.id,
                "org_registered_address": registered_address_serializer.data,
                "org_communication_address": communication_address_serializer.data,
                "user_details": user_details,
                "md_user_details": md_user_details
            }
            return Response(
                getSuccessfulMessage(response, "Data Retrived Successfully"),
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                getOtherMessage({}, global_err_message),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def post(self, request):
        try:
            user = request.user
            org_addresses = request.data.get("addresses")
            user_details = request.data.get("user_details")
            org_id = request.data.get("org_id")
            md_user_details = request.data.get("md_user_details")
            with transaction.atomic():
                communication_serializer = {}
                regiseterd_serializer = {}
                custom_profile = CustomUserProfile.objects.filter(user=user).first()
                if not custom_profile:
                    return Response(
                        getErrorMessage("User id is not correct"),
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                user_dob = user_details.get("dob") or None # if dob is None when "", as it is falsy value.
                user_num= user_details.get("mobile_no") or None
                alternate_email = user_details.get("alternate_email_id") or ""

                if user_num:
                    user_num_regex = (r"^[6-9]\d{9}$")

                    if not re.fullmatch(user_num_regex,user_num): # used fullmatch for exact length/format matching
                        return Response({
                            "status":False,
                            "message":"Invalid user mobile number."
                        },status=400)

                if user_dob:
                    if isinstance(user_dob, str):
                        user_dob = datetime.datetime.strptime(user_dob, "%Y-%m-%d").date()
                    is_user_eighteen = datetime.date.today() - datetime.timedelta(days=18*365)

                    if user_dob > is_user_eighteen:
                        return Response({
                            "status": False,
                            "message": "User must be 18 years or older."
                        }, status=400)
                    
                if alternate_email == custom_profile.email:
                    return Response({"status":False,"message":"Alternate email id should not be same as email id."},status=400)
                          
                custom_profile.alternate_email_id = alternate_email
                designation = Designation.objects.get(id=user_details["designation"])
                custom_profile.dob = user_dob
                custom_profile.father_name = user_details.get("father_name") or None
                custom_profile.pan_card_number = user_details.get("pan_card_number") or None
                custom_profile.pan_verify = user_details.get("pan_verify", False)                
                custom_profile.name = user_details.get("name", custom_profile.name)
                custom_profile.mobile_no = user_num

                if designation:
                    custom_profile.designation = designation
                custom_profile.save()
                org_instance = UserOrgazination.objects.filter(
                    id=org_id, user_profile=user.id
                ).first()
                if not org_instance:
                    return Response(
                        getErrorMessage("Organization Id is not belongs to user"),
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                for addr in org_addresses:
                    addr_instance = OrganizationAddress.objects.filter(
                        organization=org_id, address_type=addr["address_type"]
                    ).first()
                    if addr_instance:
                        addressSerializer = OrganizationAddressSerializer(
                            addr_instance, data=addr, partial=True
                        )
                    else:
                        addr["organization"] = org_id
                        addressSerializer = OrganizationAddressSerializer(data=addr)
                    if addressSerializer.is_valid():
                        addressSerializer.save()
                    else:
                        return Response(
                            getErrorMessage(addressSerializer.errors),
                            status=status.HTTP_400_BAD_REQUEST,
                        )

                addresses = OrganizationAddress.objects.filter(organization=org_id)
                address_serializer = OrganizationAddressSerializer(addresses, many=True)
                md_user_details_serializer = {}
                if md_user_details:
                    country_code = md_user_details.get("country_code") if md_user_details.get("country_code") else None
                    if country_code:
                        country_code = Country.objects.filter(id=country_code).first()
                    obj, created = OrganizationUserModel.objects.update_or_create(
                        organization=org_instance,
                        contact_type="Managing Director",
                        defaults={
                            "name": md_user_details.get("name", ""),
                            "mobile_number": md_user_details.get("mobile", ""),
                            "email_id": md_user_details.get("email", ""),
                            "country_code":  country_code,
                            "updated_at": timezone.now(),
                            "designation" : md_user_details.get("designation" ,""),
                            "other_designation": md_user_details.get("other_designation","")
                        }
                    )
                    md_user_details_serializer = OrganizationUserSerializer(obj).data
                response = {
                    "org_id": org_id,
                    "addresses": address_serializer.data,
                    "user_details": user_details,
                    "md_user_details": md_user_details_serializer
                }
                return Response(
                    getSuccessfulMessage(response, "Data updated successfully"),
                    status=status.HTTP_201_CREATED,
                )
        except Designation.DoesNotExist:
                    return Response(
                        {"status": False, "message": "Invalid Designation ID.", "data": {}},
                        status=400
                    )

        except Exception as e:
            return Response(
                getOtherMessage({}, global_err_message),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class CreateUserOrganizationView(APIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "addresses": openapi.Schema(
                type=openapi.TYPE_ARRAY,
                description="List of organization addresses",
                items=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "org_address_id": openapi.Schema(type=openapi.TYPE_STRING, description="Organization Address ID"),
                        "address_line": openapi.Schema(type=openapi.TYPE_STRING, description="Address Line"),
                        "district": openapi.Schema(type=openapi.TYPE_STRING, description="District"),
                        "city": openapi.Schema(type=openapi.TYPE_STRING, description="City"),
                        "pin_code": openapi.Schema(type=openapi.TYPE_STRING, description="PIN Code"),
                        "state": openapi.Schema(type=openapi.TYPE_STRING, description="State"),
                        "address_type": openapi.Schema(type=openapi.TYPE_STRING, description="Type of Address (e.g., Registered, Communication)"),
                    }
                ),
            ),
            "organization_details": openapi.Schema(
                type=openapi.TYPE_OBJECT,
                description="Organization Details",
                properties={
                    "user_org_id": openapi.Schema(type=openapi.TYPE_INTEGER, description="User Organization ID"),
                    "name": openapi.Schema(type=openapi.TYPE_STRING, description="Organization Name"),
                    "organization_type": openapi.Schema(type=openapi.TYPE_INTEGER, description="Type of Organization"),
                    "registered_under_msme": openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Registered under MSME"),
                    "msme_registration_number": openapi.Schema(type=openapi.TYPE_STRING, description="MSME Registration Number"),
                    "firm_registration_number": openapi.Schema(type=openapi.TYPE_STRING, description="Firm Registration Number"),
                    "registration_date": openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE, description="Registration Date"),
                    "scale_of_industry": openapi.Schema(type=openapi.TYPE_STRING, description="Scale of Industry"),
                    "firm_pan_number": openapi.Schema(type=openapi.TYPE_STRING, description="Firm PAN Number"),
                    "firm_gstin_number": openapi.Schema(type=openapi.TYPE_STRING, description="Firm GSTIN Number"),
                    "website_url": openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_URI, description="Organization Website URL"),
                    "helpdesk_number": openapi.Schema(type=openapi.TYPE_STRING, description="Helpdesk Contact Number"),
                    "firm_email_id": openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_EMAIL, description="Firm Email ID"),
                }
            ),
        }
    )
)

    def post(self, request):
        try:
            user = request.user
            data = request.data
            organization_type = None
            if "organization_type" in data:
                organization_type = OrganizationType.objects.filter(
                    id=data["organization_type"]
                ).first()

            organization, created = UserOrgazination.objects.update_or_create(
                user_profile=user,
                defaults={
                    "organization_type": organization_type,
                    "name": data.get("name", ""),
                    "firm_registration_number": data.get(
                        "firm_registration_number", ""
                    ),
                    "firm_pan_number": data.get("firm_pan_number", ""),
                    "firm_gstin_number": data.get("firm_gstin_number", ""),
                    "registered_under_msme": False,
                    "msme_registration_number": None,
                    "registration_date": timezone.now().date(),
                    "scale_of_industry": None,
                    "website_url": "",
                    "helpdesk_number": "",
                    "firm_email_id": "",
                    "date_of_incorporation": data.get("date_of_incorporation", None),
                    "pan_verify": data.get("pan_verify", False),
                    "updated_at": timezone.now(),  # Update timestamp
                },
            )

            return Response(
                {
                    "status": True,
                    "message": (
                        "Organization updated successfully"
                        if not created
                        else "Organization created successfully"
                    ),
                    "data": {"org_id": organization.id},
                },
                status=status.HTTP_200_OK if not created else status.HTTP_201_CREATED,
            )

        except Exception as e:
            return Response(
                {
                    "status": False,
                    "message": "Error saving organization",
                    "error": global_err_message,
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def get(self, request):
        try:
            user = request.user  # Get the logged-in user
            organizations = UserOrgazination.objects.filter(user_profile=user).first()
            if organizations:
                serializer = UserOrganizationSerializer(organizations)
                return Response(
                    {
                        "status": True, 
                        "data": serializer.data,
                        "message": "Organization fetch successfully"
                    },
                    status=status.HTTP_200_OK,
                )
            return Response(
                {
                    "status": False,
                    "message": "No organizations found for this user",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                {
                    "status": False,
                    "message": "Technical Issue!",
                    "data": {}
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

class UserBankDetailsView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            "bank_name": openapi.Schema(type=openapi.TYPE_STRING, description="Name of the bank"),
            "bank_branch": openapi.Schema(type=openapi.TYPE_STRING, description="Branch of the bank"),
            "bank_address": openapi.Schema(type=openapi.TYPE_STRING, description="Address of the bank branch"),
            "account_holder_name": openapi.Schema(type=openapi.TYPE_STRING, description="Name of the account holder"),
            "bank_ifsc_code": openapi.Schema(type=openapi.TYPE_STRING, description="IFSC code of the bank"),
            "account_number": openapi.Schema(type=openapi.TYPE_STRING, description="Account number"),
            "status": openapi.Schema(type=openapi.TYPE_STRING, description="Status of the account (default: active)"),
        }
    )
)

    def post(self, request):
        bank_details_data = {
            "bank_name": request.data.get("bank_name"),
            "bank_branch": request.data.get("bank_branch"),
            "bank_address": request.data.get("bank_address"),
            "account_holder_name": request.data.get("account_holder_name"),
            "bank_ifsc_code": request.data.get("bank_ifsc_code"),
            "account_number": request.data.get("account_number"),
            "status": request.data.get("status", "active"),
        }

        valid_statuses = ["active", "inactive", "blocked"]
        if bank_details_data["status"] not in valid_statuses:
            return Response(
                {"status": False, "message": "Invalid status. Choose from 'active', 'inactive', or 'blocked'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        existing_bank_details = UserBankDetails.objects.filter(user=request.user).first()

        if existing_bank_details:
            update_fields = {k: v for k, v in bank_details_data.items() if v is not None}
            serializer = UserBankDetailsSerializer(existing_bank_details, data=update_fields, partial=True)
            action = "updated"
        else:
            serializer = UserBankDetailsSerializer(data=bank_details_data)
            action = "created"

        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(
                {"status": True, "message": f"Bank details {action} successfully.", "data": serializer.data},
                status=status.HTTP_200_OK if existing_bank_details else status.HTTP_201_CREATED
            )

        return Response(
            {"status": False, "message": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    def get(self, request):
        bank_details = UserBankDetails.objects.filter(user=request.user, status='active')
        message = "No bank details found for the user."
        if bank_details.exists():
            message = "Bank Details fetch successfully"
            data = UserBankDetailsSerializer(bank_details, many=True).data
        else:
            data = [
                {
                    "bank_name": "",
                    "bank_branch": "",
                    "bank_address": "",
                    "account_holder_name": "",
                    "bank_ifsc_code": "",
                    "account_number": ""
                }
            ]
        return Response(
            {
                "status": True,
                "message": message,
                "data": data
            },
            status=status.HTTP_200_OK
        )


class UpdateUserProfileStatus(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def put(self, request):
        try:
            # ✅ Update user profile status
            user_profile, created = UserProfileStatus.objects.get_or_create(
                user=request.user, defaults={"is_profile_completed": True}
            )
            if not created:
                user_profile.is_profile_completed = True
                user_profile.save()

            # ✅ Generate PDF
            pdf_url = generate_user_profile_pdf(request.user)
            version_control_tracker(request.user.id,pdf_url,"user_profile_doc","user_profile")

            return Response(
                {
                    "status": True,
                    "message": "Profile status updated successfully.",
                    "pdf_url": pdf_url,  # ✅ Return the generated PDF URL
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {"status": False, "message": global_err_message},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class UserServiceTrackerView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    def get(self, request):
        try:
            raw_query = """
                SELECT 
                    ucs.id AS id,
                    ucs.service_name,
                    ucs.department_name,
                    ucs.status,
                    ucs.updated_at AS user_caf_updated_at
                FROM caf_user_services ucs
                JOIN kya_approval_lists al ON ucs.approval_id = al.id
                WHERE al.approval_type = 'service';
            """

            with connection.cursor() as cursor:
                cursor.execute(raw_query)
                columns = [col[0] for col in cursor.description]
                results = [dict(zip(columns, row)) for row in cursor.fetchall()]

            if not results:
                return Response(
                    {
                        "status": False, "message": "No service data found."    
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            serializer = UserCAFServiceSerializer(results, many=True)
            return Response(
                {
                    "status": True,
                    "data": serializer.data,
                    "message": "Service data retrived successfully"
                },
                status=status.HTTP_200_OK,
            )

        except DatabaseError as db_error:
            return Response(
                {"status": False, "message": f"Database error: {str(db_error)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        except Exception as e:
            return Response(
                {"status": False, "message": global_err_message},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class NotificationListView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            user_id = request.user.id
            page = int(request.query_params.get('page', 1))
            limit = int(request.query_params.get('limit', 10))

            notifications = Notification.objects.filter(user_id=user_id).order_by('-created_at')
            unread_count = notifications.filter(is_read=False).count()
            paginator = Paginator(notifications, limit)
            paginated_notifications = paginator.get_page(page)
            serializer = NotificationSerializer(paginated_notifications, many=True)

            return Response({
                "status": True,
                "message": "Notifications retrieved successfully.",
                "data": {
                    "results": serializer.data,
                    "unread_count": unread_count,
                        "total": paginator.count,
                        "page": page,
                        "limit": limit,
                        "total_pages": paginator.num_pages,
                }
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"status": False, "message": global_err_message},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
class ChangePasswordView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def put(self,request):
        user = request.user
        old_password = request.data.get("old_password")
        new_password = request.data.get("new_password")
        confirm_password = request.data.get("confirm_password")
        message= "Old, New & Confirm fields are required."
        if all([old_password, new_password, confirm_password]):
            message="New password and confirm password do not match."
            if new_password == confirm_password:
                message= "New password and old password can not be same." 
                if old_password != new_password:   
                    message='User not found.'
                    custom_profile = CustomUserProfile.objects.filter(user_id=user.id).first()
                    if custom_profile:
                        message= "Old password is incorrect." 
                        if user.check_password(old_password):
                            user.set_password(new_password)
                            user.save()
                            return Response(
                                {
                                    "status": True,
                                    "message": "Password changed successfully.",
                                    "data": {}
                                },status=status.HTTP_200_OK
                            )
        return Response(
                {
                "status":False,
                "message":message,
                "data": {}
            },status=status.HTTP_400_BAD_REQUEST
        )
            
