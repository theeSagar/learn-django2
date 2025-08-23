from rest_framework import serializers
from .models import *

class OrganizationTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationType
        fields = ["id", "name", "status"]


class OrganizationAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationAddress
        fields = "__all__"

    def validate_addresses(self, value):
        """
        Validate that there is exactly one 'Registered' address and one 'Communication' address.
        """
        address_types = [address["address_type"] for address in value]

        if len(value) != 2:
            raise serializers.ValidationError("There must be exactly 2 addresses.")

        if "Registered" not in address_types or "Communication" not in address_types:
            raise serializers.ValidationError(
                "There must be one 'Registered' address and one 'Communication' address."
            )

        return value


class OrganizationDetailSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserOrgazination
        fields = "__all__"


class OrganizationUserSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=True)
    mobile_number = serializers.CharField(required=True)
    email_id = serializers.EmailField(required=True)
    contact_type = serializers.CharField(required=True)
    designation = serializers.PrimaryKeyRelatedField(queryset=Designation.objects.all())

    class Meta:
        model = OrganizationUserModel
        fields = '__all__'

class UserOrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserOrgazination
        fields = ['id','name','firm_registration_number','firm_pan_number','firm_gstin_number',"organization_type", "date_of_incorporation", "pan_verify"]

class UserBankDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserBankDetails
        fields = ['id', 'bank_name', 'bank_branch', 'bank_address', 'account_holder_name', 'bank_ifsc_code', 'account_number', 'status']


class UserServiceTrackerSerializer(serializers.ModelSerializer):

    class Meta:
        model = ServiceTracker
        fields = ['id', 'application_no', 'service_name', 'department_name', 'updated_at', 'status']

class UserCAFServiceSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    application_no = serializers.SerializerMethodField()
    service_name = serializers.CharField()
    department_name = serializers.CharField()
    updated_at = serializers.SerializerMethodField()
    status = serializers.CharField()

    def get_application_no(self, obj):
        return f"DIPIP{obj['id']:08d}" 

    def get_updated_at(self, obj):
        return obj["user_caf_updated_at"].strftime("%d-%m-%Y") if obj["user_caf_updated_at"] else None


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'user', 'title', 'message', 'is_read', 'created_at']


class OrganizationUserModelMDSerializer(serializers.ModelSerializer):
    class Meta:
        model=OrganizationUserModel
        fields=["name","mobile_number","email_id","designation","other_designation"]