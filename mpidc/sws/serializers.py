from datetime import datetime
from rest_framework import serializers
from .models import *
from approval.models import UserCAFService



class IndustryTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = IndustryType
        fields = "__all__"

class DesignationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Designation
        fields = ["id", "name"]


class StateSerializer(serializers.ModelSerializer):
    district=serializers.SerializerMethodField()
    def get_district(self, obj):
        district_mappings = District.objects.filter(state=obj).order_by("id")
        return DistrictSerializer(district_mappings, many=True).data
    class Meta:
        model = State
        fields = ["id", "name", "district"]


class DistrictSerializer(serializers.ModelSerializer):

    class Meta:
        model = District
        fields = ["id", "name"]


class IndustrialAreaSerializer(serializers.ModelSerializer):
    class Meta:
        model = IndustrialAreaList
        fields = "__all__"


class TehsilSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tehsil
        fields = "__all__"


class ActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Activity
        fields = "__all__"


class SectorSerializer(serializers.ModelSerializer):
    icon_name = serializers.SerializerMethodField() 
    class Meta:
        model = Sector
        fields = "__all__"

    def get_icon_name(self, obj):
        return obj.icon_name if obj.icon_name else ""

class SectorProductDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SectorProductDetails
        fields = "__all__"


class PollutionTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PollutionType
        fields = "__all__"


class CustomerIntentionProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerIntentionProject
        fields = "__all__"

class CAFStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = CAF
        fields = ["status"]


class CAFSerializer(serializers.ModelSerializer):
    class Meta:
        model = CAF
        fields = "__all__"


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = "__all__"


class IntentionIdGeneratorSerializer(serializers.ModelSerializer):
    class Meta:
        model = IntentionIdGenerator
        fields = "__all__"


class CommonApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommonApplication
        fields = "__all__"


class CAFInvestmentDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CAFInvestmentDetails
        fields = [
            "caf",
            "type_of_investment",
            "project_name",
            "activity",
            "activities",
            "sector",
            "sectors",
            "sub_sector",
            "subsector",
            "product_name",
            "do_you_have_land",
            "type_of_land",
            "land_ia",
            "industrial_area",
            "district",
            "land_district",
            "land_address",
            "land_pincode",
            "land_registry_number",
            "total_land_area",
            "total_investment",
            "plant_machinary_value",
            "product_proposed_date",
            "water_limit",
            "power_limit",
            "total_employee",
            "total_local_employee",
            "export_oriented_unit",
            "export_percentage",
            "preffered_districts"
        ]


class PlotFilterSerializer(serializers.ModelSerializer):
    district_name = serializers.CharField(source="district.name", read_only=True)

    class Meta:
        model = PlotDetails
        fields = [
            "id",
            "regional_office",
            "district_name",
            "industrial_area",
            "industrial_area_type",
            "total_land_area",
            "status",
            "latitude",
            "longitude",
            "extra_feature"
        ]


class DistrictListSerializer(serializers.ModelSerializer):

    class Meta:
        model = District
        fields = ["id", "name"]


class IntentionFormSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerIntentionProject
        fields = [
            "intention_id",
            "activity",
            "sector",
            "product_name",
            "product_proposed_date",
            "project_description",
            "total_investment",
            "power_required",
            "water_required",
            "employment",
            "company_name",
            "investment_type",
            "sub_sector",
            "investment_in_pm",
            "total_land_required",
            "land_identified",
            "land_type",
            "preffered_district",
            "district",
            "address",
            "pincode",
            "land_industrial_area",
            "intention_type"
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)

        # Base fields (same in both cases)
        base_fields = {
            "intention_id": data["intention_id"],
            "activity": data["activity"],
            "sector": data["sector"],
            "product_name": data["product_name"],
            "product_proposed_date": data["product_proposed_date"],
            "project_description": data["project_description"],
            "total_investment": data["total_investment"],
            "power_required": data["power_required"],
            "water_required": data["water_required"],
            "employment": data["employment"],
            "company_name": data["company_name"],
            "investment_type": data["investment_type"],
            "sub_sector": data["sub_sector"],
            "investment_in_pm": data["investment_in_pm"],
            "total_land_required": data["total_land_required"],
            "land_identified": data["land_identified"],
        }

        # Dynamic fields
        if instance.land_identified == 'True':
            if instance.land_type in ['MSME','MPIDC','MPSEDC']:
                base_fields.update(
                    {
                        "land_type": data["land_type"],
                        "land_industrial_area": data["land_industrial_area"],
                        "created_at": datetime.now(),
                    }
                )
            else:
                base_fields.update(
                    {
                        "land_type": data["land_type"],
                        "district": data["district"],
                        "address": data["address"],
                        "pincode": data["pincode"],
                        "created_at": datetime.now(),
                    }
                )
            
        else:  # land_identified == "yes"
            base_fields["preffered_district"] = data["preffered_district"]
            base_fields["created_at"] = datetime.now()

        return base_fields


class IntentionIdFormSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerIntentionProject
        fields = ["intention_id"]


class SubSectorSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubSector
        fields = ["id", "name", "sector"]

class UserCAFServiceSerializers(serializers.ModelSerializer):
    class Meta:
        model = UserCAFService
        fields = ['caf', 'approval', 'service_name', 'department_name', 'phase', 'status']

class RegionalOfficeDistrictMappingSerializer(serializers.ModelSerializer):
    district = DistrictSerializer()  # Nest District details inside response

    class Meta:
        model = RegionalOfficeDistrictMapping
        fields = ["district"]

class RegionalOfficeSerializer(serializers.ModelSerializer):
    district = serializers.SerializerMethodField()

    def get_district(self, obj):
        # Get the districts related to the regional office
        district_mappings = RegionalOfficeDistrictMapping.objects.filter(regional_office=obj).order_by("display_order")
        districts = [mapping.district for mapping in district_mappings]
        return DistrictSerializer(districts, many=True).data

    class Meta:
        model = RegionalOffice
        fields = ['id', 'name', 'district']

class KnowYourPolicyDocumentSerializer(serializers.ModelSerializer):
    document_title = serializers.CharField(source="document_name")
    document_url = serializers.CharField(source="document_link")

    class Meta:
        model = KnowYourPolicyDocument
        fields = ["document_title", "document_url"]

class KnowYourPolicySerializer(serializers.ModelSerializer):
    download = KnowYourPolicyDocumentSerializer(many=True, source="kyp_policy")

    class Meta:
        model = KnowYourPolicy
        fields = ["title", "subtitle", "content", "policy_img","policy_type", "download"]


class SubSectorListSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubSector
        fields = ["id", "name"]

class SectorListSerializer(serializers.ModelSerializer):
    subsector = SubSectorListSerializer(many=True, source="sector")  

    class Meta:
        model = Sector
        fields = ["id", "name", "subsector"]

class ActivityListSerializer(serializers.ModelSerializer):
    sector = SectorListSerializer(many=True, source="sectors")  

    class Meta:
        model = Activity
        fields = ["id", "name", "sector"]

class DepartmentListSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = DepartmentList
        fields = [ 'id', 'name']


class IntentionListSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerIntentionProject
        fields = ["id", "product_name", "product_proposed_date", "status","intention_id","sector","created_at", "intention_type"]

class CAFSubmitSerializer(serializers.ModelSerializer):
    class Meta:
        model = CAFInvestmentDetails
        fields = [
            "caf",
            "acknowledge",
            "acknowledge_time"
        ]

class CAFPDFSerializer(serializers.ModelSerializer):
    class Meta:
        model = CAFCreationPDF
        fields = ["pdf_url", 'is_document_sign']

class RegionalOfficeDistrictSerializer(serializers.ModelSerializer):

    class Meta:
        model = RegionalOfficeDistrictMapping
        fields = '__all__'

class DistrictBlockListSerializer(serializers.ModelSerializer):

    class Meta:
        model = DistrictBlockList
        fields = ["id", "name", "block_priority"]

class MeasurementUnitListSerializer(serializers.ModelSerializer):

    class Meta:
        model = MeasurementUnitList
        fields =  ["id", "name"]


