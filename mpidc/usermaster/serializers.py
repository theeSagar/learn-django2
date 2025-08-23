from rest_framework import serializers
from authentication.models import *
from sws.models import *


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = "__all__"


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = "__all__"


class DesignationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Designation
        fields = ["name"]


class ActivitySerializer(serializers.ModelSerializer):

    class Meta:
        model = Activity
        fields = ["id", "name", "status"]


class SubsectorSerializar(serializers.ModelSerializer):

    class Meta:
        model = SubSector
        fields = "__all__"


class DepartmentSerializer(serializers.ModelSerializer):

    class Meta:
        model = DepartmentList
        fields = ["id", "name", "status", "code"]


class SectorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sector
        fields = ["name", "display_order", "icon_name", "status", "activity"]


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ["username", "is_active"]


class UserProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model = CustomUserProfile
        fields = [
            "user_id",
            "name",
            "mobile_no",
            "user_type",
            "mode_of_registration",
            "alternate_email_id",
            "status",
            "email",
        ]


class UserHasRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserHasRole
        fields = "__all__"

