import os, re
from datetime import datetime
from django.conf import settings
from django.db import transaction
from django.db.models import Q, Max, OuterRef, Subquery, CharField, Value
from django.core.paginator import Paginator, EmptyPage
from django.template.defaultfilters import linebreaks
from django.utils.timezone import now
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework_simplejwt.authentication import JWTAuthentication
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from decouple import config
from .utils import generate_intention_form_pdf, generate_caf_pdf, get_industry_scale, create_service_url
from .natureofbusiness import BUSINESS_NATURE
from .models import *
from approval.models import (
    UserCAFService,
    SectorApprovalMapping,
    SubSectorApprovalMapping,
    UserApprovals,
    UserApprovalItems,
    ApprovalList,
    ApprovalDepartmentList,
    SectorCriteriaHideApproval,
    ApprovalConfigurationModel,
)
from authentication.models import CustomUserProfile, Country
from userprofile.models import UserOrgazination, OrganizationAddress
from incentive.models import IncentiveCAF
from .serializers import *
from approval.serializers import IAExemptionMapping, UserCAFServiceSerializer
from userprofile.serializers import (
    UserOrganizationSerializer,
    OrganizationAddressSerializer,
)
from authentication.serializers import CountrySerializer
from document_center.utils import *
from django.conf import settings
global_err_message = settings.GLOBAL_ERR_MESSAGE
from django.db.models.functions import Coalesce
from incentive.utils import count_page
from incentive.models import CcipIndustrialUnitGeneralInfo
from django.http import HttpResponse
from django.middleware.csrf import get_token

class IndustryTypeView(APIView):
    def post(self, request):
        serializer = IndustryTypeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "message": "Type of Industry created successfully!",
                    "data": serializer.data,
                    "status": True,
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class NatureOfBusinessView(APIView):
    def get(self, request):
        sector_query = request.GET.get("sector", "").strip().lower()
        nature_query = request.GET.get("nature", "").strip().lower()

        filtered_data = BUSINESS_NATURE

        # Apply filters
        if sector_query:
            filtered_data = [
                item
                for item in filtered_data
                if item.get("Sector of Business", "").lower() == sector_query
            ]

        if nature_query:
            filtered_data = [
                item
                for item in filtered_data
                if item.get("Nature of Business", "").lower() == nature_query
            ]

        return Response({"BUSINESS_NATURE": filtered_data}, status=status.HTTP_200_OK)


class DesignationList(APIView):
    def get(self, request):
        queryset = Designation.objects.all()  # Fetch all Designations
        serializer_class = DesignationSerializer(queryset, many=True)
        return Response(
            {"designation_list": serializer_class.data, "status": True},
            status=status.HTTP_200_OK,
        )


class DistrictDataList(APIView):

    @swagger_auto_schema(
        # method='get',
        manual_parameters=[
            openapi.Parameter(
                "district_id",
                openapi.IN_QUERY,
                description="District",
                type=openapi.TYPE_STRING,
                required=True,
            )
        ]
    )
    def get(self, request):
        user = request.user
        district_id = request.query_params.get("district_id")

        if not district_id:
            return Response(
                {"status": False, "message": "district_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            District.objects.get(id=district_id)
            plot_industrial_areas = list(
                PlotDetails.objects.filter(district_id=district_id)
                .values("ia_id", "industrial_area")
                .distinct()
                .order_by("industrial_area")
            )
            plot_industrial_areas = [
                {"id": plot["ia_id"], "industrial_area": plot["industrial_area"]}
                for plot in plot_industrial_areas
            ]

            return Response(
                {
                    "status": True,
                    "message": "Industrial data retrived successfully",
                    "data": list(plot_industrial_areas),
                },
                status=status.HTTP_200_OK,
            )
        except District.DoesNotExist:
            return Response(
                {"status": False, "message": "Invalid Parameter!", "data": []},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                {
                    "status": False,
                    "message": global_err_message,
                    "data": [],
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class GetIntentionDataView(APIView):
    authentication_classes = [JWTAuthentication]

    def get(self, request):
        try:
            activities = Activity.objects.filter(status=1).prefetch_related(
                "sectors__sector"
            )
            serializer = ActivityListSerializer(activities, many=True)

            return Response(
                {
                    "message": "Data retrieved successfully",
                    "data": serializer.data,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {
                    "message": global_err_message,
                    "data": [],
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class GetSectorsView(APIView):
    authentication_classes = [JWTAuthentication]

    # permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "activity_id",
                openapi.IN_QUERY,
                description="Activity id",
                type=openapi.TYPE_STRING,
                required=False,
            )
        ]
    )
    def get(self, request):
        activity_id = request.query_params.get("activity_id")
        request_type = request.query_params.get("request_type")

        # Base queryset based on request_type
        sectors = []
        if request_type == "KYA":
            if not activity_id:
                activity_id = 1
            sectors = Sector.objects.filter(show_in_kya=True, activity_id=activity_id, status=1).order_by("display_order")
        elif request_type:
            if not activity_id:
                activity_id = 1
            sectors = Sector.objects.filter(show_in_incentive_calc=True, activity_id=activity_id, status=1).order_by("display_order")
        else:
            if not activity_id:
                activity_id = 1
            sectors = Sector.objects.filter(show_in_kya=True, activity_id=activity_id, status=1).order_by("display_order")

        if sectors:
            serializer = SectorSerializer(sectors, many=True).data
            if request_type and request_type != 'KYA':
                for itm in serializer:
                    itm['name'] = itm['incentive_name']
            return Response(
                {
                    "success": True,
                    "message": "Sector data fetched successfully",
                    "data": serializer, 
                    "status": True
                }, status=status.HTTP_200_OK
            )
        return Response(
            {
                "success": True,
                "message": "No Data found",
                "data": [], 
                "status": True
            }, status=status.HTTP_200_OK
        )


class GetSectorProductsView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        # method='get',
        manual_parameters=[
            openapi.Parameter(
                "sector_id",
                openapi.IN_QUERY,
                description="Sector Id",
                type=openapi.TYPE_STRING,
                required=True,
            )
        ]
    )
    def get(self, request):
        sector_id = request.query_params.get("sector_id")

        if not sector_id:
            return Response(
                {"error": "sector_id is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        products = SectorProductDetails.objects.filter(sector_id=sector_id, status=1)
        serializer = SectorProductDetailsSerializer(products, many=True)
        return Response(
            {"data": serializer.data, "status": True}, status=status.HTTP_200_OK
        )


class GetPollutionTypeListCreateView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        pollution_types = PollutionType.objects.filter(status=1)
        serializer = PollutionTypeSerializer(pollution_types, many=True)
        return Response(
            {"data": serializer.data, "status": True}, status=status.HTTP_200_OK
        )

class IntentionDetailsList(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        # method='get',
        manual_parameters=[
            openapi.Parameter(
                "page",
                openapi.IN_QUERY,
                description="Page",
                type=openapi.TYPE_STRING,
                required=True,
            ),
            openapi.Parameter(
                "limit",
                openapi.IN_QUERY,
                description="Limit",
                type=openapi.TYPE_STRING,
                required=False,
            ),
        ]
    )
    def get(self, request):
        user = request.user
        query_type = request.query_params.get("type", "regular").strip().lower()
        page = int(request.query_params.get("page", 1))
        limit = int(request.query_params.get("limit", 10))
        caf_subquery = CAF.objects.filter(
            intention_id=OuterRef('pk')
        ).order_by('-id').values('status')[:1]

        incentive_caf_subquery = IncentiveCAF.objects.filter(
            intention_id=OuterRef('pk')
        ).order_by('-id').values('status')[:1]

        intentions = CustomerIntentionProject.objects.filter(user=user).filter(
            ~Q(status="Deleted")
        ).annotate(
            caf_status_annotated=Coalesce(Subquery(caf_subquery, output_field=CharField()), Value('Not Started')),
            incentive_caf_status_annotated=Coalesce(Subquery(incentive_caf_subquery, output_field=CharField()), Value('Not Started'))
        )
        intentions_ccip = CustomerIntentionProject.objects.filter(user=user)
        intention_ids = [i.intention_id for i in intentions_ccip]

        if query_type != "all":
            intentions = intentions.filter(intention_type="regular")

        intentions = intentions.order_by("-id")

        search_text = request.query_params.get("search_text", "").strip()
        if search_text:
            intentions = intentions.filter(
                Q(project_description__icontains=search_text)
                | Q(product_name__icontains=search_text)
                | Q(intention_id__icontains=search_text)
                | Q(product_proposed_date__icontains=search_text)
                | Q(status__icontains=search_text)
                | Q(sector__icontains=search_text)
                | Q(created_at__icontains=search_text)
                | Q(intention_type__icontains=search_text)
                | Q(caf_status_annotated__icontains=search_text)
                | Q(incentive_caf_status_annotated__icontains=search_text)

            )
        if intentions.exists():
            paginator = Paginator(intentions, limit)
            try:
                paginated_intentions = paginator.page(page)
            except EmptyPage:
                return Response(
                    {"status": False, "message": "Page out of range"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            serializer = IntentionListSerializer(paginated_intentions, many=True)
            ccip_intention_data =CcipIndustrialUnitGeneralInfo.objects.filter(intention_to_invest_number__in=intention_ids)

            ccip_status_map = {
                    row.intention_to_invest_number: row.status
                    for row in ccip_intention_data
                }
            intentions_data = list(serializer.data)
            for intention_data in intentions_data:
                intention_data["product_proposed_date"] = (
                    intention_data["product_proposed_date"]
                    if intention_data["product_proposed_date"]
                    else "NA"
                )
                caf = CAF.objects.filter(intention_id=intention_data["id"]).order_by("-id").first()
                intention_data["caf_status"] = caf.status if caf else "Not Started"
                intention_data["caf_id"] = caf.id if caf else 0

                if caf and UserCAFService.objects.filter(caf=caf).exists():
                    intention_data["view_service_status"] = True
                else:
                    intention_data["view_service_status"] = False

                intention_data["intention_type"] = intention_data.get(
                    "intention_type", "regular"
                )
                incentive_caf = IncentiveCAF.objects.filter(
                        intention_id=intention_data["id"]
                    ).order_by("-id").first()
                intention_data["incentive_caf_status"] = (
                    incentive_caf.status if incentive_caf else "Not Started"
                )
                intention_id = intention_data["intention_id"]
                
                ccip_status = ccip_status_map.get(intention_id)
                intention_data["ccip_status"] = ccip_status if ccip_status else "Not Started"
                intention_data["is_instruction_acknowledgement"] = (
                    incentive_caf.is_instruction_acknowledgement if incentive_caf else False
                )
                
                if query_type == "all":
                    intention_data["incentive_caf_id"] = (
                        incentive_caf.id if incentive_caf else 0
                    )
                    if incentive_caf:
                        slec_order = incentive_caf.incaf_slec_order.filter(status="Approved").order_by("-id").first()
                        intention_data["slec_order_id"] = slec_order.id if slec_order else 0
                    else:
                        intention_data["slec_order_id"] = 0

            response = Response(
                {
                    "status": True,
                    "limit": limit,
                    "page": page,
                    "total": paginator.count,
                    "data": intentions_data,
                },
                status=status.HTTP_200_OK,
            )
        else:
            response = Response(
            {
                "status": True,
                "limit": limit,
                "page": page,
                "total": 0,
                "data": [],
            },
            status=status.HTTP_200_OK,
        )
        return response


class IntentionDetailsListId(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        project_id = request.query_params.get("project_id")

        if not project_id:
            return Response(
                {"status": False, "message": "Project id is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            intention = CustomerIntentionProject.objects.get(id=project_id, user=user)
        except CustomerIntentionProject.DoesNotExist:
            return Response(
                {"status": False, "message": "Project not found or access denied"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = CustomerIntentionProjectSerializer(intention)
        project_data = serializer.data
        project_data["product_proposed_date"] = (
            project_data["product_proposed_date"]
            if project_data["product_proposed_date"]
            else "NA"
        )
        if project_data["preffered_district"]:
            district_pairs = project_data["preffered_district"].split("||")
            district_names = [pair.split(":")[1] for pair in district_pairs]
            project_data["preffered_district"] = ", ".join(district_names)
        caf = CAF.objects.filter(intention_id=project_id).first()
        project_data["caf_status"] = caf.status if caf else "Not Started"

        return Response(
            {
                "status": True,
                "message": "Project details retrieved successfully",
                "data": {"project": project_data},
            },
            status=status.HTTP_200_OK,
        )


class CreateCAFView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "name": openapi.Schema(type=openapi.TYPE_STRING, description="Name"),
                "activity": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Activity"
                ),
                "firm_registration_number": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Firm Registration Number"
                ),
                "scale_of_industry": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Scale Of Industry"
                ),
                "firm_pan_number": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Firm Pan Number"
                ),
                "firm_gstin_number": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Firm gstin Number"
                ),
                "website_url": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    default="In-Progress",
                    description="Website URL",
                ),
            },
        )
    )
    def post(self, request):
        try:
            with transaction.atomic():
                caf_data = request.data

                # Check if a CAF record already exists for the given intention
                caf_instance, created = CAF.objects.update_or_create(
                    intention_id=caf_data.get("intention"),
                    defaults={
                        "name": caf_data.get("name"),
                        "firm_registration_number": caf_data.get(
                            "firm_registration_number"
                        ),
                        "scale_of_industry": caf_data.get("scale_of_industry"),
                        "firm_pan_number": caf_data.get("firm_pan_number"),
                        "firm_gstin_number": caf_data.get("firm_gstin_number"),
                        "status": "In-Progress",
                    },
                )

                return Response(
                    {
                        "success": True,
                        "message": "CAF and Addresses saved/updated successfully.",
                        "data": {"caf_id": caf_instance.id},
                    },
                    status=status.HTTP_201_CREATED,
                )
        except Exception as e:
            return Response(
                {"success": False, "message": "Wait. There is some issues."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "itention_id",
                openapi.IN_QUERY,
                description="Itention Id",
                type=openapi.TYPE_STRING,
                required=True,
            )
        ]
    )
    def get(self, request):
        user = request.user
        itention_id = request.query_params.get("itention_id")
        message = "Intention ID is required"
        if itention_id:
            default_data = {
                "id": "",
                "name": "",
                "activity": "",
                "firm_registration_number": "",
                "scale_of_industry": "",
                "firm_pan_number": "",
                "firm_gstin_number": "",
                "status": "",
                "intention": "",
                "created_at": "",
                "updated_at": "",
            }
            intention_data = CustomerIntentionProject.objects.filter(user_id=user.id, id = itention_id).first()
            message = "Intention data issue"
            if intention_data:
                caf = CAF.objects.filter(intention_id=itention_id).first()
                if caf:
                    caf_serializer = CAFSerializer(caf).data
                    response_data = {**default_data, **caf_serializer}
                else:
                    user_org = UserOrgazination.objects.filter(
                        user_profile_id=user.id
                    ).first()

                    if user_org:
                        user_org_serializer = UserOrganizationSerializer(user_org)
                        response_data = {**default_data, **user_org_serializer.data}
                    else:
                        response_data = default_data
                    response_data['scale_of_industry'] = get_industry_scale(intention_data)

                return Response(
                    {
                        "status": True,
                        "message": "Data fetch successfully",
                        "data": response_data
                    },status=status.HTTP_200_OK,
                )
        return Response(
            {
                "status": False,
                "message": message,
                "data": {}
            },status=status.HTTP_400_BAD_REQUEST,
        )


class CafContactDetailView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "caf_id": openapi.Schema(
                    type=openapi.TYPE_INTEGER, description="CAF ID"
                ),
                "addresses": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    description="List of addresses",
                    items=openapi.Items(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "address_line": openapi.Schema(
                                type=openapi.TYPE_STRING, description="Address Line"
                            ),
                            "district": openapi.Schema(
                                type=openapi.TYPE_STRING, description="District"
                            ),
                            "pin_code": openapi.Schema(
                                type=openapi.TYPE_STRING, description="PIN Code"
                            ),
                            "state": openapi.Schema(
                                type=openapi.TYPE_STRING, description="State"
                            ),
                            "address_type": openapi.Schema(
                                type=openapi.TYPE_STRING,
                                description="Address Type (Registered/Communication)",
                            ),
                        },
                    ),
                ),
                "contact_details": openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    description="Contact details of the authorized person",
                    properties={
                        "name": openapi.Schema(
                            type=openapi.TYPE_STRING, description="Name"
                        ),
                        "designation": openapi.Schema(
                            type=openapi.TYPE_STRING, description="Designation"
                        ),
                        "mobile_number": openapi.Schema(
                            type=openapi.TYPE_STRING, description="Mobile Number"
                        ),
                        "email_id": openapi.Schema(
                            type=openapi.TYPE_STRING, description="Email ID"
                        ),
                        "contact_type": openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description="Contact Type (Authorized/Other)",
                        ),
                    },
                ),
            },
            required=["caf_id", "addresses", "contact_details"],
        )
    )
    def post(self, request):
        data = request.data
        caf_id = data.get("caf_id")
        contact_details = data.get("contact_details", {})
        address_data = data.get("addresses", [])

        if not caf_id or not contact_details or not address_data:
            return Response(
                {
                    "status": False,
                    "message": "Caf Id, contact details or address is missing",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            with transaction.atomic():
                caf = CAF.objects.get(id=caf_id)
                if not caf:
                    return Response(
                        {"status": False, "message": "Wrong caf id"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                allowed_contact_types = {"Authorized"}
                missing_fields = []
                contact_type = contact_details.get("contact_type")
                if not contact_type or contact_type not in allowed_contact_types:
                    return Response(
                        {
                            "status": False,
                            "message": f"Invalid contact_type: {contact_type}. Allowed values: {', '.join(allowed_contact_types)}",
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                required_fields = [
                    "name",
                    "designation",
                    "mobile_number",
                    "email_id",
                ]
                for field in required_fields:
                    if not contact_details.get(field):
                        missing_fields.append(field)

                if missing_fields:
                    return Response(
                        {
                            "status": False,
                            "message": f"Missing fields: {', '.join(missing_fields)}",
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                mobile_number = contact_details.get("mobile_number")
                if mobile_number:
                    if len(mobile_number) != 10:
                        return Response(
                            {
                                "status": False,
                                "message": "Mobile number must be 10 digits.",
                            },
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                    if not mobile_number.isdigit():
                        return Response(
                            {
                                "status": False,
                                "message": "Mobile number must contain only digits.",
                            },
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                    if int(mobile_number[0]) < 6:
                        return Response(
                            {"status": False, "message": "Invalid mobile number."},
                            status=status.HTTP_400_BAD_REQUEST,
                        )

                email_id = contact_details.get("email_id")
                if email_id:
                    if "@" not in email_id:
                        return Response(
                            {"status": False, "message": "Invalid email_id."},
                            status=status.HTTP_400_BAD_REQUEST,
                        )

                designation = contact_details.get("designation")
                other_designation = contact_details.get("other_designation") if contact_details.get("other_designation") else None
                try:
                    designation = int(designation)
                except (ValueError, TypeError):
                    designation = None
                designation_name = ""
                if designation:
                    designation_data = (
                        Designation.objects.filter(id=designation)
                        .values("name")
                        .first()
                    )
                    if designation_data:
                        designation_name = designation_data["name"]
                else:
                    designation = None

                contact_instance, created = CommonApplication.objects.update_or_create(
                    caf=caf,
                    contact_type=contact_details.get("contact_type"),
                    defaults={
                        "name": contact_details.get("name"),
                        "desig_id": designation,
                        "designation": designation_name,
                        "mobile_number": mobile_number,
                        "email_id": email_id,
                        "other_designation" : other_designation
                    },
                )

                if not isinstance(address_data, list) or len(address_data) != 2:
                    return Response(
                        {
                            "error": "Exactly two addresses (Registered & Communication) are required."
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                for addr in address_data:
                    state = addr.get("state")
                    try:
                        state = int(state)
                    except (ValueError, TypeError):
                        state = None
                    state_name = ""
                    if state:
                        state_data = (
                            State.objects.filter(id=state).values("name").first()
                        )
                        if state_data:
                            state_name = state_data["name"]
                    else:
                        state = None

                    district = addr.get("district")
                    try:
                        district = int(district)
                    except (ValueError, TypeError):
                        district = None
                    district_name = ""
                    if district:
                        disrict_data = (
                            District.objects.filter(id=district, state_id=state)
                            .values("name")
                            .first()
                        )
                        if disrict_data:
                            district_name = disrict_data["name"]
                    else:
                        district = None

                    address_instance, addr_created = Address.objects.update_or_create(
                        caf=caf,
                        address_type=addr.get("address_type"),
                        defaults={
                            "address_line": addr.get("address_line"),
                            "districts_id": district,
                            "district": district_name,
                            "state": state_name,
                            "states_id": state,
                            "pin_code": addr.get("pin_code"),
                        },
                    )
                addresses = Address.objects.filter(caf=caf)
                address_serializer = AddressSerializer(addresses, many=True)
                contact_details = CommonApplication.objects.filter(caf=caf).first()
                serializer = CommonApplicationSerializer(contact_details)

                return Response(
                    {
                        "status": True,
                        "message": "CAF Address Contact details added/updated successfully.",
                        "data": {
                            "caf_id": caf_id,
                            "contact_details": serializer.data,
                            "addressess": address_serializer.data,
                        },
                    },
                    status=status.HTTP_201_CREATED,
                )
        except Exception as e:
            return Response(
                {"success": False, "message": global_err_message},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "caf_id",
                openapi.IN_QUERY,
                description="Caf Id",
                type=openapi.TYPE_STRING,
                required=True,
            )
        ]
    )
    def get(self, request):
        caf_id = int(request.query_params.get("caf_id"))
        if not caf_id:
            return Response(
                {"status": False, "message": "caf_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            caf = CAF.objects.get(id=caf_id)
            if not caf:
                return Response(
                    {"status": False, "message": "Wrong caf id"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            contact_details = CommonApplication.objects.filter(caf=caf).first()
            addresses = Address.objects.filter(caf=caf)
            user_id = request.user.id
            # user_gmail=request
            if not contact_details:
                user_profile = {
                    "name": "",
                    "designation": 0,
                    "mobile_number": "",
                    "email_id": "",
                    "contact_type": "Authorized",
                    "caf": caf_id,
                }
                user_data = (
                    CustomUserProfile.objects.filter(user_id=user_id)
                    .values("email")
                    .first()
                )
                if user_data:
                    user_profile["email_id"] = user_data["email"]

                customer_profile = CustomUserProfile.objects.filter(
                    user=request.user
                ).first()
                if customer_profile:
                    if customer_profile.designation:
                        user_profile["designation"] = (
                            customer_profile.designation_id
                            if customer_profile.designation_id is not None
                            else 0
                        )

                    user_profile["name"] = customer_profile.name
                    user_profile["mobile_number"] = (
                        customer_profile.mobile_no
                        if customer_profile.mobile_no is not None
                        else ""
                    )
            else:
                user_profile = CommonApplicationSerializer(contact_details).data
                user_profile["designation"] = (
                    user_profile["desig"] if user_profile["desig"] is not None else 0
                )
                user_profile.pop("desig", None)

            if not addresses.exists():
                registered_address = {
                    "address_line": "",
                    "district": 0,
                    "state": 0,
                    "pin_code": "",
                    "address_type": "Registered",
                    "caf": caf_id,
                }
                communication_address = {
                    "address_line": "",
                    "district": 0,
                    "state": 0,
                    "pin_code": "",
                    "address_type": "Communication",
                    "caf": caf_id,
                }

                organization_details = UserOrgazination.objects.filter(
                    user_profile=request.user
                ).first()
                if organization_details:
                    organization_address = OrganizationAddress.objects.filter(
                        organization=organization_details
                    ).order_by("-address_type")
                    if organization_address.exists():
                        registered_address_data = next(
                            (
                                address
                                for address in organization_address
                                if address.address_type == "Registered"
                            ),
                            None,
                        )
                        communication_address_data = next(
                            (
                                address
                                for address in organization_address
                                if address.address_type == "Communication"
                            ),
                            None,
                        )
                        registered_address = OrganizationAddressSerializer(
                            registered_address_data
                        ).data
                        communication_address = OrganizationAddressSerializer(
                            communication_address_data
                        ).data
                        for key in ["created_at", "updated_at", "id", "organization"]:
                            communication_address.pop(key, None)
                            registered_address.pop(key, None)
            else:
                addresses = AddressSerializer(addresses, many=True).data
                for address in addresses:
                    address["district"] = (
                        address["districts"] if address["districts"] is not None else 0
                    )
                    address["state"] = (
                        address["states"] if address["states"] is not None else 0
                    )
                    address.pop("districts", None)
                    address.pop("states", None)
                    if address["address_type"] == "Communication":
                        communication_address = address
                    elif address["address_type"] == "Registered":
                        registered_address = address

            return Response(
                {
                    "status": True,
                    "message": "Data retrived successfully",
                    "data": {
                        "caf_id": caf_id,
                        "contact_details": user_profile,
                        "registered_addresses": registered_address,
                        "communication_addresses": communication_address,
                    },
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {"success": False, "message": global_err_message},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class CAFInvestmentDetailsAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "caf",
                openapi.IN_QUERY,
                description="Caf Id",
                type=openapi.TYPE_STRING,
                required=True,
            )
        ]
    )
    def get(self, request):
        try:
            caf_id = request.query_params.get("caf_id", None)
            if not caf_id:
                return Response(
                    {"status": False, "message": "caf_id is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            caf_data = CAF.objects.filter(id=caf_id).first()
            if not caf_data:
                return Response(
                    {"status": False, "message": "caf data is not available"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            investments = CAFInvestmentDetails.objects.filter(caf_id=caf_id).first()
            if investments:
                serializer = CAFInvestmentDetailsSerializer(investments).data
                serializer["activity"] = (
                    serializer["activities"]
                    if serializer["activities"] is not None
                    else 0
                )
                serializer.pop("activities", None)
                serializer["sector"] = (
                    serializer["sectors"] if serializer["sectors"] is not None else 0
                )
                serializer.pop("sectors", None)
                serializer["sub_sector"] = (
                    serializer["subsector"]
                    if serializer["subsector"] is not None
                    else 0
                )
                serializer.pop("subsector", None)
                serializer["industrial_area"] = (
                    serializer["land_ia"] if serializer["land_ia"] is not None else 0
                )
                serializer.pop("land_ia", None)
                serializer["land_district"] = (
                    serializer["district"] if serializer["district"] is not None else 0
                )
                serializer.pop("district", None)
                if serializer["preffered_districts"]:
                    district_pairs = serializer["preffered_districts"].split("||")
                    serializer["preffered_districts"] = [
                        int(pair.split(":")[0]) for pair in district_pairs
                    ]
                else:
                    serializer["preffered_districts"] = []

            else:
                serializer = {
                    "caf": int(caf_id),
                    "type_of_investment": "",
                    "project_name": "",
                    "activity": 0,
                    "sector": 0,
                    "sub_sector": 0,
                    "product_name": "",
                    "do_you_have_land": False,
                    "type_of_land": "",
                    "industrial_area": 0,
                    "land_district": 0,
                    "land_address": "",
                    "land_pincode": "",
                    "land_registry_number": "",
                    "total_land_area": 0,
                    "total_investment": "",
                    "plant_machinary_value": "",
                    "product_proposed_date": "",
                    "water_limit": "",
                    "power_limit": "",
                    "total_employee": 0,
                    "total_local_employee": 0,
                    "export_oriented_unit": False,
                    "export_percentage": "",
                    "preffered_districts": [],
                }

                intention_data = CustomerIntentionProject.objects.filter(
                    id=caf_data.intention_id
                ).first()
                if intention_data:
                    preffered_district = ""
                    if intention_data.preffered_district:
                        district_pairs = intention_data.preffered_district.split("||")
                        preffered_district = [
                            int(pair.split(":")[0]) for pair in district_pairs
                        ]
                    else:
                        preffered_district = []
                    serializer = {
                        "caf": int(caf_id),
                        "type_of_investment": intention_data.investment_type,
                        "project_name": intention_data.product_name,
                        "activity": (
                            intention_data.activities_id
                            if intention_data.activities_id is not None
                            else 0
                        ),
                        "sector": (
                            intention_data.sectors_id
                            if intention_data.sectors_id is not None
                            else 0
                        ),
                        "sub_sector": (
                            intention_data.subsectors_id
                            if intention_data.subsectors_id is not None
                            else 0
                        ),
                        "product_name": "",
                        "do_you_have_land": bool(intention_data.land_identified),
                        "type_of_land": intention_data.land_type,
                        "industrial_area": (
                            intention_data.land_ia_id
                            if intention_data.land_ia_id is not None
                            else 0
                        ),
                        "land_district": (
                            intention_data.districts_id
                            if intention_data.districts_id is not None
                            else 0
                        ),
                        "land_address": intention_data.address,
                        "land_pincode": intention_data.pincode,
                        "land_registry_number": "",
                        "preffered_districts": preffered_district,
                        "total_land_area": intention_data.total_land_required,
                        "total_investment": intention_data.total_investment,
                        "plant_machinary_value": intention_data.investment_in_pm,
                        "product_proposed_date": intention_data.product_proposed_date,
                        "water_limit": intention_data.water_required,
                        "power_limit": intention_data.power_required,
                        "total_employee": intention_data.employment,
                        "total_local_employee": 0,
                        "export_oriented_unit": False,
                        "export_percentage": "",
                    }

            return Response(
                {
                    "status": True,
                    "message": "CAF Investment data retrived successfully.",
                    "data": serializer,
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {"status": False, "message": global_err_message}, status=status.HTTP_400_BAD_REQUEST
            )

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "caf": openapi.Schema(type=openapi.TYPE_INTEGER, description="CAF ID"),
                "type_of_investment": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Type of Investment"
                ),
                "project_name": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Project Name"
                ),
                "land_district": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Land District"
                ),
                "activity": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Activity"
                ),
                "sector": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Sector"
                ),
                "sub_sector": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Sub Sector"
                ),
                "product_name": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Product Name"
                ),
                "do_you_have_land": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Do You Have Land?"
                ),
                "type_of_land": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Type of Land"
                ),
                "industrial_area": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Industrial Area"
                ),
                "land_district": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Land District"
                ),
                "land_address": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Land Address"
                ),
                "land_pincode": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Land Pincode"
                ),
                "land_registry_number": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Land Registry Number"
                ),
                "total_land_area": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Total Land Area"
                ),
                "total_investment": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Total Investment"
                ),
                "plant_machinary_value": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Plant Machinery Value"
                ),
                "product_proposed_date": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Product Proposed Date"
                ),
                "water_limit": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Water Limit"
                ),
                "power_limit": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Power Limit"
                ),
                "total_employee": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Total Employee"
                ),
                "total_local_employee": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Total Local Employee"
                ),
                "export_oriented_unit": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Export Oriented Unit"
                ),
                "export_percentage": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Export Percentage"
                ),
            },
        )
    )
    def post(self, request):
        data = request.data
        caf_id = data.get("caf")
        try:
            if not caf_id:
                return Response(
                    {"status": False, "message": "caf id is required."},
                    status=400,
                )

            caf = CAF.objects.filter(id=caf_id).first()
            if not caf:
                return Response(
                    {"status": False, "message": "caf id not found."},
                    status=400,
                )

            activity = data.get("activity")
            sector = data.get("sector")
            sub_sector = data.get("sub_sector")
            investment_details = CAFInvestmentDetails.objects.filter(caf=caf).first()

            data["activity"] = ""
            if activity:
                data["activities"] = activity
                activity_name = (
                    Activity.objects.filter(id=activity).values("name").first()
                )
                if activity_name:
                    data["activity"] = activity_name["name"]
            else:
                data["activities"] = None

            data["sector"] = ""
            if sector and activity:
                data["sectors"] = sector
                sector_name = (
                    Sector.objects.filter(id=sector, activity_id=activity)
                    .values("name")
                    .first()
                )
                if sector_name:
                    data["sector"] = sector_name["name"]
            else:
                data["sectors"] = None

            data["sub_sector"] = ""
            if sector and sub_sector:
                data["subsector"] = sub_sector
                sub_sector_name = (
                    SubSector.objects.filter(id=sub_sector, sector_id=sector)
                    .values("name")
                    .first()
                )
                if sub_sector_name:
                    data["sub_sector"] = sub_sector_name["name"]
            else:
                data["subsector"] = None

            land_industrial_area = data.get("industrial_area")

            data["industrial_area"] = ""
            if land_industrial_area:
                data["land_ia"] = land_industrial_area
                land_industrial_area_name = (
                    IndustrialAreaList.objects.filter(id=land_industrial_area)
                    .values("name")
                    .first()
                )
                if land_industrial_area_name:
                    data["industrial_area"] = land_industrial_area_name["name"]
            else:
                data["land_ia"] = None

            land_district = data.get("land_district")
            data["land_district"] = ""
            if land_district:
                data["district"] = land_district
                district_name = (
                    District.objects.filter(id=land_district).values("name").first()
                )
                if district_name:
                    data["land_district"] = district_name["name"]
            else:
                data["district"] = None

            get_preffered_district = data.get("preffered_districts", [])
            if get_preffered_district:
                if isinstance(get_preffered_district, list):
                    try:
                        get_preffered_district = list(map(int, get_preffered_district))
                    except ValueError:
                        return Response(
                            {
                                "message": "Preffered District data is not correct",
                                "status": False,
                                "data": [],
                            },
                            status=400,
                        )

                    # Query the database to check if all IDs exist
                    district_data = District.objects.filter(
                        id__in=get_preffered_district
                    ).values("id", "name")
                    if len(district_data) == len(get_preffered_district):
                        preffered_district = "||".join(
                            [f"{d['id']}:{d['name']}" for d in district_data]
                        )
                        data["preffered_districts"] = preffered_district
            else:
                data["preffered_districts"] = ""

            if investment_details:
                serializer = CAFInvestmentDetailsSerializer(
                    investment_details, data=data, partial=True
                )
            else:
                serializer = CAFInvestmentDetailsSerializer(data=data)

            if serializer.is_valid():
                serializer.save()
            else:
                first_field, errors = next(iter(serializer.errors.items()))
                first_error_message = errors[0] if isinstance(errors, list) else str(errors)

                friendly_field_names = {
                    "type_of_investment": "Type of Investment",
                    "project_name": "Project Name",
                    "project_category": "Project Category",
                    "product_name": "Product Name",
                    "activity": "Activity",
                    "sector": "Sector",
                    "sub_sector": "Sub Sector",
                    "do_you_have_land": "Do You Have Land",
                    "type_of_land": "Type of Land",
                    "industrial_area": "Industrial Area",
                    "land_district": "Land District",
                    "land_pincode": "Land Pincode",
                    "land_address": "Land Address",
                    "preffered_districts": "Preferred Districts",
                    "total_land_area": "Total Land Area",
                    "total_investment": "Total Investment",
                    "plant_machinary_value": "Plant & Machinery Value",
                    "product_proposed_date": "Product Proposed Date",
                    "water_limit": "Water Limit",
                    "power_limit": "Power Limit",
                    "total_employee": "Total Employees",
                    "total_local_employee": "Total Local Employees",
                    "direct_male_employee": "Direct Male Employees",
                    "direct_female_employee": "Direct Female Employees",
                    "indirect_male_employee": "Indirect Male Employees",
                    "indirect_female_employee": "Indirect Female Employees",
                    "export_oriented_unit": "Export Oriented Unit",
                    "export_percentage": "Export Percentage",
                    "caf": "CAF ID",
                    "land_registry_number": "Land Registry Number",
                }

                friendly_field = friendly_field_names.get(first_field, first_field.replace("_", " ").capitalize())
                final_message = f"{friendly_field} field is blank" if "may not be blank" in first_error_message else first_error_message

                return Response(
                    {
                        "status": False,
                        "message": final_message,
                        "data": [],
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            response_data = serializer.data
            if response_data["preffered_districts"]:
                district_pairs = response_data["preffered_districts"].split("||")
                response_data["preffered_districts"] = [
                    int(pair.split(":")[0]) for pair in district_pairs
                ]
            else:
                response_data["preffered_districts"] = []

            # Fetch related data
            common_applications = CommonApplication.objects.filter(caf=caf).first()
            org_addresses = Address.objects.filter(caf=caf)
            investment_details = CAFInvestmentDetails.objects.filter(caf=caf).first()
            intention_data = CustomerIntentionProject.objects.filter(caf=caf).first()
            customer_data = CustomUserProfile.objects.filter(user=request.user).first()
            addresses = {}
            if org_addresses.exists():
                addresses["reg_address"] = next(
                    (
                        address
                        for address in org_addresses
                        if address.address_type == "Registered"
                    ),
                    None,
                )
                addresses["comm_address"] = next(
                    (
                        address
                        for address in org_addresses
                        if address.address_type == "Communication"
                    ),
                    None,
                )

            # Generate PDF, passing all the necessary data
            pdf_url = generate_caf_pdf(
                caf,
                investment_details,
                common_applications,
                addresses,
                intention_data,
                customer_data,
            )
            user_id=request.user.id
            data=minio_func(pdf_url)
            version_control_tracker(user_id,pdf_url,"sws","cad_investment_details")

            return Response(
                {
                    "status": True,
                    "message": "CAF Investment Details created successfully",
                    "data": response_data,
                    "pdf_url":data[1]["Fileurl"],
                },
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            return Response(
                {"status": False, "message": global_err_message}, status=status.HTTP_400_BAD_REQUEST
            )


class FilterSearch(APIView):
    authentication_classes = [JWTAuthentication]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "district": openapi.Schema(
                    type=openapi.TYPE_STRING, description="District"
                ),
                "region": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Region"
                ),
                "plot_status": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Plot Status"
                ),
                "pollution_status": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Pollution Status"
                ),
                "industry_developed_area": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Industry Developed Area"
                ),
                "industrial_area": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Industrial Area"
                ),
                "plot_type": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Plot Type"
                ),
            },
        )
    )
    def post(self, request):
        try:
            user_id = request.user.id
            data = request.data
            district = data.get("district")
            region = data.get("region")
            plot_status = data.get("plot_status")
            industrial_area = data.get("industrial_area")

            filters = Q()

            if district:
                filters &= Q(district=district)
            if region:
                filters &= Q(ro=region)
            if plot_status:
                filters &= Q(status=plot_status)
            else:
                filters &= Q(status="Vacant")
            if industrial_area:
                filters &= Q(ia=industrial_area)

            queryset = PlotDetails.objects.filter(filters).order_by("id")

            # Pagination logic
            try:
                page = int(request.query_params.get("page", 1))
                limit = int(request.query_params.get("limit", 10))
            except ValueError:
                return Response(
                    {"status": False, "message": "Invalid page or limit"},
                    status=400,
                )

            paginator = Paginator(queryset, limit)
            try:
                paginated_plots = paginator.page(page)
            except EmptyPage:
                return Response(
                    {"status": False, "message": "Page out of range"},
                    status=400,
                )

            serialized_data = PlotFilterSerializer(paginated_plots, many=True).data
            if serialized_data:
                for plot in serialized_data:
                    plot["water"] = False
                    plot["road"] = False
                    plot["electricity"] = False
                    plot["nearest_city"] = ""
                    plot["nearest_railway"] = ""
                    plot["nearest_airport"] = ""
                    plot["nearest_road"] = ""
                    plot["nearest_port"] = ""
                    industrial_area_data = IndustrialAreaList.objects.filter(
                        name=plot["industrial_area"]
                    ).first()
                    if industrial_area_data:
                        plot["water"] = industrial_area_data.water
                        plot["road"] = industrial_area_data.road
                        plot["electricity"] = industrial_area_data.electricity
                        plot["nearest_city"] = (
                            industrial_area_data.nearest_city
                            if industrial_area_data.nearest_city
                            else ""
                        )
                        plot["nearest_railway"] = (
                            industrial_area_data.nearest_railway
                            if industrial_area_data.nearest_railway
                            else ""
                        )
                        plot["nearest_airport"] = (
                            industrial_area_data.nearest_airport
                            if industrial_area_data.nearest_airport
                            else ""
                        )
                        plot["nearest_road"] = (
                            industrial_area_data.nearest_road
                            if industrial_area_data.nearest_road
                            else ""
                        )
                        plot["nearest_port"] = (
                            industrial_area_data.nearest_port
                            if industrial_area_data.nearest_port
                            else ""
                        )

            return Response(
                {
                    "status": True,
                    "limit": limit,
                    "page": page,
                    "total": paginator.count,
                    "data": serialized_data if serialized_data else [],
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {
                    "status": False,
                    "message": "An error occurred while processing the request.",
                    "error": global_err_message,
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class DistrictData(APIView):
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "state_id",
                openapi.IN_QUERY,
                description="State Id",
                type=openapi.TYPE_STRING,
                required=True,
            )
        ]
    )
    def get(self, request):
        state_id = request.query_params.get("state_id")

        if state_id:
            queryset = District.objects.filter(state_id=state_id)
        else:
            try:
                state_name = State.objects.get(name="Madhya Pradesh")
                queryset = District.objects.filter(state=state_name)
            except State.DoesNotExist:
                return Response(
                    {"status": False, "message": "State 'Madhya Pradesh' not found."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        serializer = DistrictListSerializer(queryset, many=True)
        return Response(
            {
                "status": True,
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )


class StateDataView(APIView):
    def get(self, request):
        queryset = State.objects.all()
        state_serializers = StateSerializer(queryset, many=True)

        return Response(
            {
                "status": True,
                "message": "State Data retrieved successfully",
                "data": state_serializers.data,
            }
        )


class IntentionFormView(APIView):

    authentication_classes = [JWTAuthentication]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "activity": openapi.Schema(
                    type=openapi.TYPE_STRING, description="activity"
                ),
                "email": openapi.Schema(type=openapi.TYPE_STRING, description="Email"),
                "sector": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Region"
                ),
                "product_name": openapi.Schema(
                    type=openapi.TYPE_STRING, description="Product Name"
                ),
                "product_proposed_date": openapi.Schema(
                    type=openapi.TYPE_STRING, description="product_proposed_date"
                ),
                "project_description": openapi.Schema(
                    type=openapi.TYPE_STRING, description="project_description"
                ),
                "total_investment": openapi.Schema(
                    type=openapi.TYPE_INTEGER, description="total_investment"
                ),
                "power_required": openapi.Schema(
                    type=openapi.TYPE_INTEGER, description="power_required"
                ),
                "water_required": openapi.Schema(
                    type=openapi.TYPE_INTEGER, description="water_required"
                ),
                "employment": openapi.Schema(
                    type=openapi.TYPE_STRING, description="employment"
                ),
                "company_name": openapi.Schema(
                    type=openapi.TYPE_STRING, description="company_name"
                ),
                "investment_type": openapi.Schema(
                    type=openapi.TYPE_STRING, description="investment_type"
                ),
                "sub_sector": openapi.Schema(
                    type=openapi.TYPE_STRING, description="sub_sector"
                ),
                "investment_in_pm": openapi.Schema(
                    type=openapi.TYPE_INTEGER, description="investment_in_pm"
                ),
                "total_land_required": openapi.Schema(
                    type=openapi.TYPE_INTEGER, description="total_land_required"
                ),
                "land_identified": openapi.Schema(
                    type=openapi.TYPE_STRING, description="land_identified"
                ),
                "preffered_district": openapi.Schema(
                    type=openapi.TYPE_STRING, description="preffered_district"
                ),
                "district": openapi.Schema(
                    type=openapi.TYPE_STRING, description="district"
                ),
                "address": openapi.Schema(
                    type=openapi.TYPE_STRING, description="address"
                ),
                "pincode": openapi.Schema(
                    type=openapi.TYPE_INTEGER, description="pincode"
                ),
                "land_industrial_area": openapi.Schema(
                    type=openapi.TYPE_STRING, description="land_industrial_area"
                ),
            },
        )
    )
    def post(self, request):
        try:
            data = request.data
            user = request.user if request.user.is_authenticated else None
            if not user:
                email = request.data.get("email", None)

                if not email:
                    return Response(
                        {
                            "status": False,
                            "message": "Email is required when not logged in",
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                user = User.objects.filter(email=email).first()

                if not user:
                    # Create a guest user
                    password = datetime.now().strftime(
                        "%Y-%m-%d"
                    )  # Set password as current date
                    user = User.objects.create(
                        username=email,
                        email=email,
                        first_name="Guest",
                        last_name="Guest",
                        is_staff=False,
                        is_active=True,
                        date_joined=datetime.now(),
                        last_login=None,
                    )
                    user.set_password(password)
                    user.save()

            activity = request.data.get("activity")
            sector = request.data.get("sector")
            sub_sector = request.data.get("sub_sector")
            product_name = request.data.get("product_name")
            product_proposed_date = request.data.get("product_proposed_date")
            project_description = request.data.get("project_description")
            total_investment = request.data.get("total_investment")
            power_required = request.data.get("power_required")
            water_required = request.data.get("water_required")
            employment = request.data.get("employment")
            company_name = request.data.get("company_name")
            investment_type = request.data.get("investment_type")
            investment_in_pm = request.data.get("investment_in_pm")
            total_land_required = request.data.get("total_land_required")
            land_identified = request.data.get("land_identified")
            land_industrial_area = None
            district = None
            address = ""
            pincode = None
            preffered_district = ""
            land_type = ""
            land_industrial_area_name = ""
            district_name = ""
            intention_type = request.data.get("intention_type")

            if land_identified:
                district = request.data.get("district")
                if district:
                    district_data = (
                        District.objects.filter(id=district).values("name").first()
                    )
                    if district_data:
                        district_name = district_data["name"] 
                land_type = request.data.get("land_type")
                if land_type in ["MSME", "MPIDC", "MPSEDC"]:
                    land_industrial_area = request.data.get("land_industrial_area")
                    land_industrial_data = (
                        IndustrialAreaList.objects.filter(
                            id=land_industrial_area, authority=land_type
                        )
                        .values("name")
                        .first()
                    )
                    if land_industrial_data:
                        land_industrial_area_name = land_industrial_data["name"]
                else:
                    address = request.data.get("address")
                    pincode = int(request.data.get("pincode"))
            else:
                get_preffered_district = request.data.get("preffered_district", "")
                if get_preffered_district:
                    get_preffered_district = get_preffered_district.split(",")
                    if isinstance(get_preffered_district, list):
                        try:
                            get_preffered_district = list(
                                map(int, get_preffered_district)
                            )
                        except ValueError:
                            return Response(
                                {
                                    "message": "Preffered District data is not correct",
                                    "status": False,
                                    "pdf_url": "",
                                    "data": [],
                                },
                                status=400,
                            )

                        # Query the database to check if all IDs exist
                        district_data = District.objects.filter(
                            id__in=get_preffered_district
                        ).values("id", "name")
                        if len(district_data) == len(get_preffered_district):
                            preffered_district = "||".join(
                                [f"{d['id']}:{d['name']}" for d in district_data]
                            )

            activity_name = Activity.objects.filter(id=activity).values("name").first()
            sector_name = (
                Sector.objects.filter(id=sector, activity_id=activity)
                .values("name")
                .first()
            )
            sub_sector_name = (
                SubSector.objects.filter(id=sub_sector, sector_id=sector)
                .values("name")
                .first()
            )

            if activity_name and sector_name and sub_sector_name:
                intention_id = self.generate_intention_id(total_investment)
                if product_proposed_date:
                    product_proposed_date = datetime.strptime(
                        product_proposed_date, "%Y-%m-%d"
                    ).date()

                created_intention = CustomerIntentionProject.objects.create(
                    user=user,
                    activities_id=activity,
                    activity=activity_name["name"],
                    sectors_id=sector,
                    sector=sector_name["name"],
                    subsectors_id=sub_sector,
                    sub_sector=sub_sector_name["name"],
                    product_name=product_name,
                    product_proposed_date=product_proposed_date,
                    project_description=project_description,
                    total_investment=total_investment,
                    power_required=power_required,
                    water_required=water_required,
                    employment=employment,
                    company_name=company_name,
                    investment_type=investment_type,
                    investment_in_pm=investment_in_pm,
                    total_land_required=total_land_required,
                    land_identified=str(land_identified).lower(),
                    land_type=land_type,
                    land_ia_id=land_industrial_area,
                    land_industrial_area=land_industrial_area_name,
                    districts_id=district,
                    district=district_name,
                    address=address,
                    pincode=pincode,
                    preffered_district=preffered_district,
                    intention_id=intention_id,
                    intention_type=intention_type,
                )

                intention_data = IntentionFormSerializer(
                    instance=CustomerIntentionProject.objects.get(
                        intention_id=intention_id
                    )
                )
                customer_data = CustomUserProfile.objects.filter(user=user).first()
                minio_pdf = ""
                if customer_data:
                    pdf_url = generate_intention_form_pdf(
                        intention_data.data, customer_data
                    )
                    version_control_tracker(customer_data.user_id,pdf_url,"sws","intention_form_pdf")
                    created_intention.intention_file_path = pdf_url
                    created_intention.save()
                    minio_pdf=minio_func(pdf_url)
                    
                    if minio_pdf[0]:
                        minio_pdf = minio_pdf[1]["Fileurl"]
                    else:
                        minio_pdf = ""
                else:
                    pdf_url = ""

                return Response(
                    {
                        "message": "Data Saved Successfully!",
                        "status": True,
                        "pdf_url": minio_pdf,
                        "data": intention_data.data,
                    },
                    status=status.HTTP_201_CREATED,
                )
            return Response(
                {
                    "status": False,
                    "message": "Some dynamic parameter are not correct",
                    "data": {},
                    "pdf_url": "",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                {"status": False, "message": "Error saving project", "error": global_err_message},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def generate_intention_id(self, investment_amount):
        today_date = datetime.now().strftime("%y%m%d")

        if isinstance(investment_amount, str):
            investment_amount = float(investment_amount)

        if investment_amount < 50:
            prefix = "MSME1"
        else:
            prefix = "DIPIP"

        existing_ids = IntentionIdGenerator.objects.filter(
            investment_id__startswith=f"{prefix}{today_date}"
        )
        count = existing_ids.count() + 1
        seq_num = str(count).zfill(4)
        intention_id = f"{prefix}{today_date}{seq_num}"

        IntentionIdGenerator.objects.create(
            investment_amount=investment_amount,
            investment_id=intention_id,
            created_at=datetime.now(),
        )

        return intention_id


class CAfDeatilsView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "caf_id",
                openapi.IN_QUERY,
                description="Caf Id",
                type=openapi.TYPE_STRING,
                required=True,
            )
        ]
    )
    def get(self, request):
        try:
            user = request.user
            caf_id = request.query_params.get("caf_id")

            if not caf_id:
                return Response(
                    {"status": False, "message": "caf_id is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            caf = CAF.objects.filter(id=caf_id).first()
            if not caf:
                return Response(
                    {"status": False, "message": "CAF not found."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            intention_id = caf.intention_id

            if not intention_id:
                return Response(
                    {"status": False, "message": "No intention_id found for this CAF."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            intention_project = CustomerIntentionProject.objects.filter(
                id=intention_id, user_id=user.id
            ).first()
            intention_project = CustomerIntentionProject.objects.filter(
                id=intention_id, user_id=user.id
            ).first()
            addresses = Address.objects.filter(caf=caf)
            address_serializer = AddressSerializer(addresses, many=True)
            if not addresses.exists():
                return Response(
                    {
                        "status": False,
                        "message": "No Addresses found for the specified CAF.",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if not intention_project:
                return Response(
                    {
                        "status": False,
                        "message": "Unauthorized: You cannot access this CAF.",
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            caf_serializer = CAFSerializer(caf)
            contact_details = CommonApplication.objects.filter(caf=caf).first()
            investments = CAFInvestmentDetails.objects.filter(caf_id=caf_id)
            # if investments:
            #    for invest in investments:
            #        invest.dpr_document_path = config("BASE_URL") + invest.dpr_document_path

            contact_serializer = (
                CommonApplicationSerializer(contact_details)
                if contact_details
                else None
            )
            investment_serializer = CAFInvestmentDetailsSerializer(
                investments, many=True
            )

            return Response(
                {
                    "status": True,
                    "data": {
                        "intention_id": intention_project.intention_id,
                        "caf_details": caf_serializer.data,
                        "addresses": address_serializer.data,
                        "contact_details": (
                            contact_serializer.data if contact_serializer else None
                        ),
                        "investments": investment_serializer.data,
                    },
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {"status": False, "message": global_err_message},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class SubSectorView(APIView):
    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "sector_id",
                openapi.IN_QUERY,
                description="Sector Id",
                type=openapi.TYPE_STRING,
                required=True,
            )
        ]
    )
    def get(self, request):
        sector_id = request.query_params.get("sector_id")
        message = "Parameter missing!"
        if sector_id:
            request_type = request.query_params.get("request_type")
            if request_type and request_type == 'KYA':
                subsectors = SubSector.objects.filter(sector_id=sector_id, show_in_kya=True).order_by("display_order")
            else:
                subsectors = SubSector.objects.filter(sector_id=sector_id).order_by("display_order")
            message = "No SubSectors found for this Sector"
            if subsectors.exists():
                serializer = SubSectorSerializer(subsectors, many=True)
                return Response({
                        "status": True,
                        "data": serializer.data,
                        "message": "Data retrived successfully"
                    }, status=status.HTTP_200_OK
                )
        return Response({
                "status": False,
                "message": message,
                "data": []
            },status=status.HTTP_400_BAD_REQUEST,
        )


def is_html(content):
    """Check if the content already contains HTML tags."""
    return bool(re.search(r"<[a-z][\s\S]*>", content))


class SectorPolicyView(APIView):
    @swagger_auto_schema(
        operation_description="Retrieve all active Know Your Policy documents with search functionality",
        manual_parameters=[
            openapi.Parameter(
                "search_key",
                openapi.IN_QUERY,
                description="Search by policy title or content",
                type=openapi.TYPE_STRING,
                required=False,
            ),
            openapi.Parameter(
                "policies_type",
                openapi.IN_QUERY,
                description="Policy Type",
                type=openapi.TYPE_STRING,
                required=False,
            ),
            openapi.Parameter(
                "page",
                openapi.IN_QUERY,
                description="Page",
                type=openapi.TYPE_STRING,
                required=True,
            ),
            openapi.Parameter(
                "limit",
                openapi.IN_QUERY,
                description="Limit",
                type=openapi.TYPE_STRING,
                required=False,
            ),
        ],
        responses={200: "Success Response"},
    )
    def get(self, request):
        page = int(request.query_params.get("page", 1))
        limit = int(request.query_params.get("limit", 10))
        try:
            search_key = request.query_params.get("search_key", "").strip()
            policies_type = request.query_params.get("policies_type", "").strip()
            if policies_type:
                policies = KnowYourPolicy.objects.filter(
                    policy_type=policies_type, status="active"
                )
            else:
                policies = KnowYourPolicy.objects.filter(status="active")

            if search_key:
                policies = policies.filter(
                    Q(title__icontains=search_key)
                    | Q(subtitle__icontains=search_key)
                    | Q(content__icontains=search_key)
                )

            if not policies.exists():
                return Response(
                    {
                        "success": False,
                        "message": f"No matching policies found for '{search_key}'.",
                        "limit": limit,
                        "page": page,
                        "total": 0,
                        "data": [],
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            policies = policies.order_by("title")
            paginator = Paginator(policies, limit)
            paginated_policy = paginator.page(page)
            serializer = KnowYourPolicySerializer(paginated_policy, many=True)
            policies_data = list(serializer.data)
            return Response(
                {
                    "success": True,
                    "message": "Data retrieved successfully",
                    "limit": limit,
                    "page": page,
                    "total": paginator.count,
                    "data": policies_data,
                },
                status=status.HTTP_200_OK,
            )
        except EmptyPage:
            return Response(
                {
                    "status": False,
                    "message": "Page out of range",
                    "limit": limit,
                    "page": page,
                    "total": 0,
                    "data": [],
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                {
                    "success": False,
                    "message": global_err_message,
                    "limit": limit,
                    "page": page,
                    "total": 0,
                    "data": [],
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class DistrictLandBank(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        districts = (
            PlotDetails.objects.select_related("district")
            .values("district_id", "district__name")
            .distinct()
        )

        data = [
            {"id": item["district_id"], "name": item["district__name"]}
            for item in districts
        ]

        if not data:
            return Response(
                {"status": False, "message": "No districts found"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response({"status": True, "data": data}, status=status.HTTP_200_OK)


class UserCafService(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data
        user = request.user
        try:
            if "caf" not in data:
                return Response(
                    {"status": False, "message": "caf_id is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            caf = CAF.objects.filter(id=data["caf"]).first()
            if not caf:
                return Response(
                    {"status": False, "message": "Caf data is not exist"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if "service_details" not in data or not isinstance(
                data["service_details"], list
            ):
                return Response(
                    {"status": False, "message": "There is some issue with Service"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            created_services = []
    
            for service in data["service_details"]:
                if "approval_id" in service and service["approval_id"]:
                    approval = ApprovalList.objects.filter(
                        id=service["approval_id"]
                    ).first()
                    if approval:
                        user_service_check = UserCAFService.objects.filter(
                            approval_id=service["approval_id"], caf_id=data["caf"], status='New'
                        ).first()
                        if not user_service_check:
                            department_name = ""
                            department_id = None
                            all_approval_depatments_list = (
                                ApprovalDepartmentList.objects.filter(
                                    approval_id=service["approval_id"]
                                )
                            )
                            if all_approval_depatments_list.exists():
                                for appr in all_approval_depatments_list:
                                    department_id = appr.department_id
                                    if department_name == "":
                                        department_name = appr.department.name
                                    else:
                                        department_name = (
                                            department_name + "/" + appr.department.name
                                        )
                            
                            service_request_no = self.generate_service_request_number(data["caf"])
                            user_caf_service = UserCAFService.objects.create(
                                user=user,
                                caf=caf,
                                approval=approval,
                                service_name=approval.name,
                                department_name=department_name,
                                phase=approval.phase,
                                status="New",
                                request_number=service_request_no,
                                department_id = department_id
                            )
                            created_services.append(user_caf_service)

            serializer = UserCAFServiceSerializers(created_services, many=True)
            return Response(
                {
                    "status": True,
                    "message": "UserCAFService records created successfully",
                    "data": serializer.data,
                },
                status=status.HTTP_201_CREATED,
            )
        except Exception as e:
            return Response(
                {"status": False, "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
    
    
    def generate_service_request_number(self, caf_id):
        today = timezone.now().strftime("%Y%m%d")
        with transaction.atomic():
            last_request = ServiceRequestNumberModel.objects.filter(
                caf_id=caf_id,
                created_at__date=timezone.now().date()
            ).order_by("-id").first()
            if last_request:
                last_number = int(last_request.service_request_number[-4:])  # last 4 digits
                next_number = str(last_number + 1).zfill(4)
            else:
                next_number = "0001"
            sr_number = f"NEWSR{caf_id}{today}{next_number}"
            new_request = ServiceRequestNumberModel.objects.create(
                caf_id=caf_id,
                service_request_number=sr_number
            )

        return new_request.service_request_number


    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    def get(self, request):
        caf_id = request.query_params.get("caf_id")
        message = "Parameter missiong caf id"
        if caf_id:
            caf_data = CAF.objects.filter(id=caf_id).first()
            message = "CAF Data is not found"
            if caf_data:
                exemption = []
                caf_investment_data = CAFInvestmentDetails.objects.filter(
                    caf_id=caf_id
                ).first()
                message = "Investment data is not there for this caf"
                if caf_investment_data:
                    industrial_area = caf_investment_data.land_ia_id
                    if industrial_area:
                        exemptionData = IAExemptionMapping.objects.filter(
                            industrial_area=industrial_area
                        )
                        if exemptionData:
                            exemption = [ed.approval_id for ed in exemptionData]

                    sector_id = caf_investment_data.sectors_id
                    subsector_id = caf_investment_data.subsector_id

                    removeApprovals = []
                    findAllRemoveCriteria = SectorCriteriaHideApproval.objects.filter(
                        sector=sector_id
                    )
                    if findAllRemoveCriteria.exists():
                        for item in findAllRemoveCriteria:
                            if "||" in item.criteria:
                                criteria_list = item.criteria.split("||")
                                output_list = item.output.split("||")
                                result_dict = dict(zip(criteria_list, output_list))
                                pack_value = True
                                for ques in result_dict:
                                    if hasattr(caf_investment_data, ques) and result_dict[
                                        ques
                                    ] != getattr(caf_investment_data, ques):
                                        pack_value = False
                                if pack_value:
                                    removeApprovals.append(item.approval_id)
                            elif hasattr(
                                caf_investment_data, item.criteria
                            ) and item.output == getattr(
                                caf_investment_data, item.criteria
                            ):
                                removeApprovals.append(item.approval_id)

                    (
                        sector_man_service,
                        sector_opt_service,
                        sector_man_clearance,
                        sector_opt_clearance,
                    ) = ([], [], [], [])
                    subsector_man_clearance, subsector_opt_clearance, exempt_clearance = (
                        [],
                        [],
                        [],
                    )

                    # get common clearance
                    sector_approvals = SectorApprovalMapping.objects.filter(
                        Q(sector_id=sector_id) | Q(sector_id__isnull=True),
                    ).order_by("display_order")
                    if sector_approvals:
                        for sa in sector_approvals:
                            if sa.approval_id not in removeApprovals:
                                if sa.approval_id in exemption:
                                    exempt_clearance.append(sa.approval_id)
                                else:
                                    if sa.approval.approval_type == "service":
                                        if sa.approval_type == "optional":
                                            sector_opt_service.append(sa.approval_id)
                                        else:
                                            sector_man_service.append(sa.approval_id)
                                    else:
                                        if sa.approval_type == "optional":
                                            sector_opt_clearance.append(sa.approval_id)
                                        else:
                                            sector_man_clearance.append(sa.approval_id)

                    subsector_approvals = SubSectorApprovalMapping.objects.filter(
                         Q(subsector_id=subsector_id) | Q(subsector_id__isnull=True),
                    ).order_by("display_order")
                    if subsector_approvals:
                        for sa in subsector_approvals:
                            if sa.approval_id in exemption:
                                exempt_clearance.append(sa.approval_id)
                            else:
                                if sa.approval_type == "optional":
                                    subsector_opt_clearance.append(sa.approval_id)
                                else:
                                    subsector_man_clearance.append(sa.approval_id)

                    userexisting_clearance = []
                    user_existing_services = UserCAFService.objects.filter(caf_id=caf_id)
                    if user_existing_services.exists():
                        userexisting_clearance = [
                            ac.approval_id for ac in user_existing_services
                        ]

                    kya_final_approval = []
                    kya_user_approvals = UserApprovals.objects.filter(
                        user=request.user, sector_id=sector_id, subsector_id=subsector_id
                    ).first()
                    if kya_user_approvals:
                        kya_user_approval_items = UserApprovalItems.objects.filter(
                            user_approval_id=kya_user_approvals.id
                        )
                        if kya_user_approval_items.exists():
                            kya_final_approval = [
                                ac.approval_id for ac in kya_user_approval_items
                            ]
                    all_approvals = list(
                        set(
                            sector_man_service
                            + sector_opt_service
                            + sector_opt_clearance
                            + sector_man_clearance
                            + subsector_opt_clearance
                            + subsector_man_clearance
                            + exempt_clearance
                        )
                    )

                    all_approval_data = {}
                    all_depatment_data = {}
                    all_approval_data_list = ApprovalList.objects.filter(
                        id__in=all_approvals
                    )
                    all_approval_depatments_list = ApprovalDepartmentList.objects.filter(
                        approval_id__in=all_approvals
                    )
                    if all_approval_data_list.exists():
                        for appr in all_approval_data_list:
                            all_approval_data[appr.id] = appr

                        if all_approval_depatments_list.exists():
                            departmentList = []
                            for appr in all_approval_depatments_list:
                                if appr.approval_id in all_depatment_data:
                                    if appr.department.name not in departmentList:
                                        all_depatment_data[appr.approval_id] = (
                                            all_depatment_data[appr.approval_id]
                                            + "/"
                                            + appr.department.name
                                        )
                                else:
                                    all_depatment_data[appr.approval_id] = (
                                        appr.department.name
                                    )
                                    departmentList.append(appr.department.name)

                        finalApprovals = self.approval_filter(
                            mandatory_service=sector_man_service,
                            optional_service=sector_opt_service,
                            mandatory_approvals=sector_man_clearance,
                            optional_approvals=sector_opt_clearance,
                            subsector_man_approvals=subsector_man_clearance,
                            subsector_optional_approvals=subsector_opt_clearance,
                            exemption_approvals=exempt_clearance,
                            applied=userexisting_clearance,
                            wishlist=kya_final_approval,
                            all_approvals=all_approval_data,
                            department_data=all_depatment_data,
                        )

                        return Response(
                            {
                                "status": True,
                                "data": finalApprovals,
                                "message": "Data retrived successfully",
                            },
                            status=status.HTTP_200_OK,
                        )
        return Response(
            {
                "status": False,
                "message": message,
                "data": []
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    def approval_filter(self, *args, **kwargs):
        applied = kwargs["applied"]
        wishlist = kwargs["wishlist"]
        all_approval = kwargs["all_approvals"]
        department_data = kwargs["department_data"]

        mandatory_service = kwargs["mandatory_service"]
        optional_service = kwargs["optional_service"]
        mandatory_approvals = kwargs["mandatory_approvals"]
        optional_approvals = kwargs["optional_approvals"]
        subsector_man_approvals = kwargs["subsector_man_approvals"]
        subsector_optional_approvals = kwargs["subsector_optional_approvals"]
        exemption_approvals = kwargs["exemption_approvals"]

        mandatory_service = [item for item in mandatory_service if item not in applied]
        optional_service = [item for item in optional_service if item not in applied]
        mandatory_approvals = [
            item for item in mandatory_approvals if item not in applied
        ]
        optional_approvals = [
            item for item in optional_approvals if item not in applied
        ]
        subsector_man_approvals = [
            item for item in subsector_man_approvals if item not in applied
        ]
        subsector_optional_approvals = [
            item for item in subsector_optional_approvals if item not in applied
        ]
        exemption_approvals = [
            item for item in exemption_approvals if item not in applied
        ]

        preOps = {"mandatory": [], "optionals": [], "exemptions": []}
        postOps = {"mandatory": [], "optionals": [], "exemptions": []}
        preEstab = {"mandatory": [], "optionals": [], "exemptions": []}
        if mandatory_service:
            for appid in mandatory_service:
                if appid in all_approval:
                    finalApp = all_approval[appid]
                    department_name = (
                        department_data[appid] if appid in department_data else ""
                    )
                    approvalDict = {
                        "id": finalApp.id,
                        "name": finalApp.name,
                        "type": "Service",
                        "department": department_name,
                        "time_limit": finalApp.timelines,
                        "phase": finalApp.phase,
                        "instruction": finalApp.instruction,
                        "exemption": False,
                        "autoselect": False,
                    }

                    if finalApp.id in wishlist:
                        approvalDict["autoselect"] = True

                    if finalApp.phase == "Pre-Operation":
                        preOps["mandatory"].append(approvalDict)
                    elif finalApp.phase == "Pre-Establishment":
                        preEstab["mandatory"].append(approvalDict)
                    elif finalApp.phase == "Post-Operation":
                        postOps["mandatory"].append(approvalDict)
        if mandatory_approvals:
            for appid in mandatory_approvals:
                if appid in all_approval:
                    finalApp = all_approval[appid]
                    department_name = (
                        department_data[appid] if appid in department_data else ""
                    )
                    approvalDict = {
                        "id": finalApp.id,
                        "name": finalApp.name,
                        "type": "Approval",
                        "department": department_name,
                        "time_limit": finalApp.timelines,
                        "phase": finalApp.phase,
                        "instruction": finalApp.instruction,
                        "exemption": False,
                        "autoselect": False,
                    }

                    if finalApp.id in wishlist:
                        approvalDict["autoselect"] = True

                    if finalApp.phase == "Pre-Operation":
                        preOps["mandatory"].append(approvalDict)
                    elif finalApp.phase == "Pre-Establishment":
                        preEstab["mandatory"].append(approvalDict)
                    elif finalApp.phase == "Post-Operation":
                        postOps["mandatory"].append(approvalDict)
        if subsector_man_approvals:
            for appid in subsector_man_approvals:
                if appid in all_approval:
                    finalApp = all_approval[appid]
                    department_name = (
                        department_data[appid] if appid in department_data else ""
                    )
                    approvalDict = {
                        "id": finalApp.id,
                        "name": finalApp.name,
                        "type": "Sub-Sector Approval",
                        "department": department_name,
                        "time_limit": finalApp.timelines,
                        "phase": finalApp.phase,
                        "instruction": finalApp.instruction,
                        "exemption": False,
                        "autoselect": False,
                    }

                    if finalApp.id in wishlist:
                        approvalDict["autoselect"] = True

                    if finalApp.phase == "Pre-Operation":
                        preOps["mandatory"].append(approvalDict)
                    elif finalApp.phase == "Pre-Establishment":
                        preEstab["mandatory"].append(approvalDict)
                    elif finalApp.phase == "Post-Operation":
                        postOps["mandatory"].append(approvalDict)
        if optional_service:
            for appid in optional_service:
                if appid in all_approval:
                    finalApp = all_approval[appid]
                    department_name = (
                        department_data[appid] if appid in department_data else ""
                    )
                    approvalDict = {
                        "id": finalApp.id,
                        "name": finalApp.name,
                        "type": "Optional Service",
                        "department": department_name,
                        "time_limit": finalApp.timelines,
                        "phase": finalApp.phase,
                        "instruction": finalApp.instruction,
                        "exemption": False,
                        "autoselect": False,
                    }

                    if finalApp.id in wishlist:
                        approvalDict["autoselect"] = True

                    if finalApp.phase == "Pre-Operation":
                        preOps["optionals"].append(approvalDict)
                    elif finalApp.phase == "Pre-Establishment":
                        preEstab["optionals"].append(approvalDict)
                    elif finalApp.phase == "Post-Operation":
                        postOps["optionals"].append(approvalDict)
        if optional_approvals:
            for appid in optional_approvals:
                if appid in all_approval:
                    finalApp = all_approval[appid]
                    department_name = (
                        department_data[appid] if appid in department_data else ""
                    )
                    approvalDict = {
                        "id": finalApp.id,
                        "name": finalApp.name,
                        "type": "Optional Approval",
                        "department": department_name,
                        "time_limit": finalApp.timelines,
                        "phase": finalApp.phase,
                        "instruction": finalApp.instruction,
                        "exemption": False,
                        "autoselect": False,
                    }

                    if finalApp.id in wishlist:
                        approvalDict["autoselect"] = True

                    if finalApp.phase == "Pre-Operation":
                        preOps["optionals"].append(approvalDict)
                    elif finalApp.phase == "Pre-Establishment":
                        preEstab["optionals"].append(approvalDict)
                    elif finalApp.phase == "Post-Operation":
                        postOps["optionals"].append(approvalDict)

        if subsector_optional_approvals:
            for appid in subsector_optional_approvals:
                if appid in all_approval:
                    finalApp = all_approval[appid]
                    department_name = (
                        department_data[appid] if appid in department_data else ""
                    )
                    approvalDict = {
                        "id": finalApp.id,
                        "name": finalApp.name,
                        "type": "Sub-Sector Approval",
                        "department": department_name,
                        "time_limit": finalApp.timelines,
                        "phase": finalApp.phase,
                        "instruction": finalApp.instruction,
                        "exemption": False,
                        "autoselect": False,
                    }

                    if finalApp.id in wishlist:
                        approvalDict["autoselect"] = True

                    if finalApp.phase == "Pre-Operation":
                        preOps["mandatory"].append(approvalDict)
                    elif finalApp.phase == "Pre-Establishment":
                        preEstab["mandatory"].append(approvalDict)
                    elif finalApp.phase == "Post-Operation":
                        postOps["mandatory"].append(approvalDict)
        if exemption_approvals:
            for appid in exemption_approvals:
                if appid in all_approval:
                    finalApp = all_approval[appid]
                    department_name = (
                        department_data[appid] if appid in department_data else ""
                    )
                    approvalDict = {
                        "id": finalApp.id,
                        "name": finalApp.name,
                        "type": "",
                        "department": department_name,
                        "time_limit": finalApp.timelines,
                        "phase": finalApp.phase,
                        "instruction": finalApp.instruction,
                        "exemption": True,
                        "autoselect": False,
                    }

                    if finalApp.phase == "Pre-Operation":
                        preOps["exemptions"].append(approvalDict)
                    elif finalApp.phase == "Pre-Establishment":
                        preEstab["exemptions"].append(approvalDict)
                    elif finalApp.phase == "Post-Operation":
                        postOps["exemptions"].append(approvalDict)
        return {
            "Pre-Establishment": preEstab,
            "Pre-Operation": preOps,
            "Post-Operation": postOps,
        }


class RegionalOfficeListAPIView(APIView):
    @swagger_auto_schema(
        operation_description="Get a list of all regional offices",
        responses={200: RegionalOfficeSerializer(many=True)},
    )
    def get(self, request):
        try:
            regional_offices = RegionalOffice.objects.all().order_by("name")
            if regional_offices:
                serializer = RegionalOfficeSerializer(regional_offices, many=True)
                return Response(
                    {
                        "status": True,
                        "data": serializer.data,
                        "message": "Data Retrived Successfully",
                    },
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    {"status": False, "data": [], "message": "No data available"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
        except Exception as e:
            return Response(
                {
                    "status": False,
                    "message": global_err_message,
                    "data": [],
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class CAFSubmitAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "caf": openapi.Schema(type=openapi.TYPE_INTEGER, description="CAF ID"),
                "acknowledge": openapi.Schema(
                    type=openapi.TYPE_BOOLEAN, description="Acknowledgment"
                ),
            },
        )
    )
    def post(self, request):
        data = {}
        caf_id = request.data.get("caf")
        try:
            if not caf_id:
                return Response(
                    {"status": False, "message": "caf_id is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            caf = CAF.objects.filter(id=caf_id).first()
            if not caf:
                return Response(
                    {"status": False, "message": "caf id is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            investment_details = CAFInvestmentDetails.objects.filter(caf=caf).first()
            if investment_details:
                """
                file = request.FILES.get("dpr_document_path")
                if file:
                    # Path where we want to store the file
                    file_folder = os.path.join(settings.MEDIA_ROOT, "dpr_reports")

                    # Check if the directory exists, if not, create it
                    if not os.path.exists(file_folder):
                        os.makedirs(file_folder)

                    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                    new_file_name = f"{os.path.splitext(file.name)[0]}_{timestamp}{os.path.splitext(file.name)[1]}"

                    # Generate the full file path
                    file_path = os.path.join(file_folder, new_file_name)

                    # Save the file to the server
                    with open(file_path, "wb") as f:
                        for chunk in file.chunks():
                            f.write(chunk)

                    # Set the file path in the request data
                    data["dpr_document_path"] = f"{settings.MEDIA_URL}dpr_reports/{new_file_name}"
                """
                data["acknowledge"] = request.data.get("acknowledge")
                data["acknowledge_time"] = str(now())
                serializer = CAFSubmitSerializer(
                    investment_details, data=data, partial=True
                )

                if serializer.is_valid():
                    serializer.save()
                    caf.status = "Completed"
                    caf.save()
                else:
                    return Response(
                        {
                            "status": False,
                            "message": serializer.errors,
                            "data": [],
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                response_data = serializer.data

                return Response(
                    {
                        "status": True,
                        "message": "CAF Investment Details updated successfully",
                        "data": response_data,
                    },
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    {
                        "status": False,
                        "message": "Unable to find CAF",
                        "data": [],
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        except Exception as e:
            return Response(
                {"status": False, "message": global_err_message}, status=status.HTTP_400_BAD_REQUEST
            )

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        # method='get',
        manual_parameters=[
            openapi.Parameter(
                "caf_id",
                openapi.IN_QUERY,
                description="Caf Id",
                type=openapi.TYPE_STRING,
                required=True,
            )
        ]
    )
    def get(self, request):
        try:
            user_id = request.user.id
            caf_id = request.query_params.get("caf_id")
            message = "Missing Caf id"
            if caf_id:
                caf_data = CAF.objects.filter(id=caf_id).first()
                if caf_data:
                    intention_user_id = caf_data.intention.user_id
                    if intention_user_id == user_id:
                        pdf_data = (
                            CAFCreationPDF.objects.filter(caf_id=caf_id)
                            .order_by("-id")
                            .first()
                        )
                        message = "Data is not found"
                        pdf_url = ""
                        is_document_sign = False
                        total_pages = 0
                        if pdf_data:
                            serializers = CAFPDFSerializer(pdf_data).data
                            file_data=minio_func(serializers["pdf_url"])
                            if file_data[0]:
                                pdf_url = file_data[1]["Fileurl"]
                                is_document_sign = serializers["is_document_sign"]
                                total_pages = count_page(str(file_data[1]["Fileurl"][0]))
                            message = "Data Retrived successfully"
                        return Response(
                            {
                                "status": True,
                                "message": message,
                                "data": {
                                    "pdf_url":pdf_url,
                                    "is_document_sign": is_document_sign,
                                    "total_pages" : total_pages
                                },
                            },
                            status=status.HTTP_200_OK,
                        )
                    else:
                        message = "You don't have access to see the page"
                else:
                    message = "Caf Data not found"

            return Response(
                {
                    "status": False,
                    "message": message,
                    "data": {}
                },status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                {
                    "status": False,
                    "message": global_err_message,
                    "data": {},
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class RegionalOfficeDistrictView(APIView):

    def get(self, request):
        try:
            district_id = request.query_params.get("district_id")
            ro_id = request.query_params.get("ro_id")
            empty_data = True
            remove_list = ["id", "status", "display_order"]
            if district_id:
                district_data = RegionalOfficeDistrictMapping.objects.filter(
                    district_id=district_id
                ).first()
                if district_data:
                    regional_office_name = district_data.regional_office.name
                    data = RegionalOfficeDistrictSerializer(district_data).data
                    for item in remove_list:
                        data.pop(item)
                    data.pop("district")
                    data["regional_office_name"] = regional_office_name
                    empty_data = False
            elif ro_id:
                regional_office_data = RegionalOfficeDistrictMapping.objects.filter(
                    regional_office_id=ro_id
                )
                if regional_office_data:
                    data = []
                    for item in regional_office_data:
                        district_name = item.district.name
                        mainData = RegionalOfficeDistrictSerializer(item).data
                        mainData["district_name"] = district_name
                        for item in remove_list:
                            mainData.pop(item)
                        mainData.pop("regional_office")
                        data.append(mainData)
                    empty_data = False

            if empty_data:
                return Response(
                    {"status": True, "message": "Data not found", "data": []},
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    {
                        "status": True,
                        "message": "Data retrieved successfully",
                        "data": data,
                    },
                    status=status.HTTP_200_OK,
                )

        except Exception as e:
            return Response(
                {"status": False, "message": global_err_message, "data": []},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class BlockListView(APIView):

    def get(self, request):
        try:
            district_id = request.query_params.get("district_id")
            if district_id:
                district_data = DistrictBlockList.objects.filter(
                    district_id=district_id
                ).order_by("name")
            else:
                district_data = DistrictBlockList.objects.order_by("name")
            
            if district_data.exists():
                data = DistrictBlockListSerializer(district_data, many=True).data
                message = "Data retrieved successfully"
            else:
                data=[]
                message = "No data found"
            return Response(
                {
                    "status": True,
                    "message": message,
                    "data": data,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {"status": False, "message": global_err_message, "data": []},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class MeasurementUnitView(APIView):

    def get(self, request):
        try:
            measurement_units = MeasurementUnitList.objects.all().order_by("name")
            if measurement_units.exists():
                data = MeasurementUnitListSerializer(measurement_units, many=True).data

                return Response(
                    {
                        "status": True,
                        "message": "Data retrieved successfully",
                        "data": data,
                    },
                    status=status.HTTP_200_OK,
                )

            return Response(
                {"status": False, "message": "Data not found", "data": []},
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as e:
            return Response(
                {"status": False, "message": global_err_message, "data": []},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class CountryView(APIView):
    def get(self, request):
        try:
            country_data = Country.objects.all()
            if country_data.exists():
                data = CountrySerializer(country_data, many=True).data
                return Response(
                    {
                        "status": True,
                        "message": "Data retrieved successfully",
                        "data": data,
                    },
                    status=status.HTTP_200_OK,
                )

        except Exception as e:
            return Response(
                {"status": False, "message": global_err_message, "data": []},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class UserServiceView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            caf_id = request.query_params.get("caf_id")
            data = {"Pre-Establishment": [], "Pre-Operation": [], "Post-Operation": []}
            if caf_id:
                caf_data = CAF.objects.filter(id=caf_id).first()
                if caf_data:
                    message = "No data available"
                    usercafservices = UserCAFService.objects.filter(
                        user_id=user.id, caf_id=caf_id
                    )
                    approval_redirect_map = {
                        ac.approval_id: ac
                        for ac in ApprovalConfigurationModel.objects.all()
                    }
                    if usercafservices:
                        serialized_services = UserCAFServiceSerializer(
                            usercafservices, many=True
                        ).data
                        for service in serialized_services:
                            approval_id = service['approval']
                            if approval_id in approval_redirect_map:
                                service["redirect_url"] = create_service_url(approval_redirect_map[approval_id], service)
                            else:
                                service["redirect_url"] = ""
                            if service["phase"] in data:
                                data[service["phase"]].append(service)

                        message = "Data fetch successfully"

                    return Response(
                        {"status": True, "message": message, "data": data},
                        status=status.HTTP_200_OK,
                    )
            return Response(
                {"status": False, "message": "Data issue", "data": data},
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as e:
            return Response(
                {"status": False, "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        
class HelpdeskView(APIView):
    def post(self,request):
        try:
            data = request.data

            required_fields = [
                "name",
                "mobile_no",
                "email_id",
                "message",
                "acknowledgement"
            ]
            missing_fields = [field for field in required_fields if data.get(field) is None and field not in data]

            if missing_fields:
                return Response(
                    {
                        "status": False,
                        "message": f"Missing required fields: {', '.join(missing_fields)}",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            email_id = data.get("email_id")
            acknowledgement = data.get("acknowledgement")
            name = data.get("name")
            mobile_no = data.get("mobile_no")
            message = data.get("message")

            email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"

            if not re.match(email_regex, email_id):
                return Response(
                    {"status": False, "message": "Invalid email address"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if not acknowledgement:
                return Response({
                    "status": False,
                    "message": "Please acknowledge before submitting."
                },status=400)
            
            if not mobile_no.isdigit():
                return Response(
                    {"status": False, "message": "Mobile number must contain only digits."},
                    status=400,
                )
            
            if len(mobile_no) != 10:
                return Response(
                    {"status": False, "message": "Invalid mobile number."},
                    status=400,
                )
            
            
            CustomerHelpdesk.objects.create(
                name=name,
                email=email_id,
                mobile_no=mobile_no,
                message=message,
                acknowledgement=acknowledgement,
                status="Seen"
            )
            return Response({
                "status": True,
                "message": "Your query has been submited successfully."
            },status= 200)
        
        except Exception as e:
            return Response ({
                "status": False,
                "message": global_err_message
            },status=500)
        
class SubscriptionView(APIView):
    def post(self,request):
        try:
            data= request.data
            email_id= data.get("email_id")
            email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"

            message = ''
            if not email_id:
                message = "Email ID is required."

            elif not re.match(email_regex, email_id):
                message = "Invalid email address."

            if message:
                return Response({
                    "status": False,
                    "message": message
                }, status=status.HTTP_400_BAD_REQUEST)

            customer_email = CustomerSubscriptions.objects.filter(email=email_id).first()

            if customer_email:
                return Response({
                    "status": False,
                    "message": "Email ID already exists."
                }, status=status.HTTP_400_BAD_REQUEST)

            CustomerSubscriptions.objects.create(
                email = email_id,
                status= True
            )
            return Response ({
                "status": True,
                "message": "You have successfully subscribed"
            },status = 200)
        
        except Exception as e:
            return Response ({
                "status": False,
                "message": global_err_message
            },status=500)

class UserCafAddOnService(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        caf_id = request.query_params.get("caf_id")
        message = "Parameter missing: caf_id"
        if caf_id:
            caf_data = CAF.objects.filter(id=caf_id).first()
            message = "CAF Data is not found"
            if caf_data:
                exemption = []
                caf_investment_data = CAFInvestmentDetails.objects.filter(
                    caf_id=caf_id
                ).first()
                message = "Investment data is not there for this caf"
                if caf_investment_data:
                    industrial_area = caf_investment_data.land_ia_id
                    if industrial_area:
                        exemptionData = IAExemptionMapping.objects.filter(
                            industrial_area=industrial_area
                        )
                        if exemptionData:
                            exemption = [ed.approval_id for ed in exemptionData]

                    sector_id = caf_investment_data.sectors_id
                    subsector_id = caf_investment_data.subsector_id

                    removeApprovals = []

                    (
                        sector_man_service,
                        sector_opt_service,
                        sector_man_clearance,
                        sector_opt_clearance,
                    ) = ([], [], [], [])
                    subsector_man_clearance, subsector_opt_clearance, exempt_clearance = (
                        [],
                        [],
                        [],
                    )

                    sector_approvals = SectorApprovalMapping.objects.filter(
                        Q(sector_id=sector_id) | Q(sector_id__isnull=True)
                    ).order_by("display_order")

                    for sa in sector_approvals:
                        if sa.approval_id in exemption:
                            exempt_clearance.append(sa.approval_id)
                        else:
                            if sa.approval.approval_type == "service":
                                if sa.approval_type == "optional":
                                    sector_opt_service.append(sa.approval_id)
                                else:
                                    sector_man_service.append(sa.approval_id)
                            else:
                                if sa.approval_type == "optional":
                                    sector_opt_clearance.append(sa.approval_id)
                                else:
                                    sector_man_clearance.append(sa.approval_id)

                    subsector_approvals = SubSectorApprovalMapping.objects.filter(
                        Q(subsector_id=subsector_id) | Q(subsector_id__isnull=True)
                    ).order_by("display_order")

                    for sa in subsector_approvals:
                        if sa.approval_id in exemption:
                            exempt_clearance.append(sa.approval_id)
                        else:
                            if sa.approval_type == "optional":
                                subsector_opt_clearance.append(sa.approval_id)
                            else:
                                subsector_man_clearance.append(sa.approval_id)

                    userexisting_clearance = []
                    user_existing_services = UserCAFService.objects.filter(caf_id=caf_id)
                    if user_existing_services.exists():
                        userexisting_clearance = [
                            ac.approval_id for ac in user_existing_services
                        ]

                    kya_final_approval = []
                    kya_user_approvals = UserApprovals.objects.filter(
                        user=request.user, sector_id=sector_id, subsector_id=subsector_id
                    ).first()
                    if kya_user_approvals:
                        kya_user_approval_items = UserApprovalItems.objects.filter(
                            user_approval_id=kya_user_approvals.id
                        )
                        if kya_user_approval_items.exists():
                            kya_final_approval = [
                                ac.approval_id for ac in kya_user_approval_items
                            ]

                    all_approvals = list(
                        set(
                            sector_man_service
                            + sector_opt_service
                            + sector_opt_clearance
                            + sector_man_clearance
                            + subsector_opt_clearance
                            + subsector_man_clearance
                            + exempt_clearance
                            + userexisting_clearance 
                        )
                    )

                    all_approval_data = {}
                    all_depatment_data = {}
                    all_approval_data_list = ApprovalList.objects.filter(
                        id__in=all_approvals
                    )
                    all_approval_depatments_list = ApprovalDepartmentList.objects.filter(
                        approval_id__in=all_approvals
                    )
                    if all_approval_data_list.exists():
                        for appr in all_approval_data_list:
                            all_approval_data[appr.id] = appr

                        if all_approval_depatments_list.exists():
                            departmentList = []
                            for appr in all_approval_depatments_list:
                                if appr.approval_id in all_depatment_data:
                                    if appr.department.name not in departmentList:
                                        all_depatment_data[appr.approval_id] = (
                                            all_depatment_data[appr.approval_id]
                                            + "/"
                                            + appr.department.name
                                        )
                                else:
                                    all_depatment_data[appr.approval_id] = (
                                        appr.department.name
                                    )
                                    departmentList.append(appr.department.name)

                        finalApprovals = self.approval_filter_show_all(
                            mandatory_service=sector_man_service,
                            optional_service=sector_opt_service,
                            mandatory_approvals=sector_man_clearance,
                            optional_approvals=sector_opt_clearance,
                            subsector_man_approvals=subsector_man_clearance,
                            subsector_optional_approvals=subsector_opt_clearance,
                            exemption_approvals=exempt_clearance,
                            applied=[],  
                            wishlist=kya_final_approval,
                            all_approvals=all_approval_data,
                            department_data=all_depatment_data,
                        )

                        return Response(
                            {
                                "status": True,
                                "data": finalApprovals,
                                "message": "Data retrieved successfully",
                            },
                            status=status.HTTP_200_OK,
                        )

        return Response(
            {"status": False, "message": message, "data": []},
            status=status.HTTP_400_BAD_REQUEST,
        )
    def approval_filter_show_all(self, **kwargs):
        applied = kwargs["applied"]
        wishlist = kwargs["wishlist"]
        all_approval = kwargs["all_approvals"]
        department_data = kwargs["department_data"]

        mandatory_service = kwargs["mandatory_service"]
        optional_service = kwargs["optional_service"]
        mandatory_approvals = kwargs["mandatory_approvals"]
        optional_approvals = kwargs["optional_approvals"]
        subsector_man_approvals = kwargs["subsector_man_approvals"]
        subsector_optional_approvals = kwargs["subsector_optional_approvals"]
        exemption_approvals = kwargs["exemption_approvals"]

        preOps = {"mandatory": [], "optionals": [], "exemptions": []}
        postOps = {"mandatory": [], "optionals": [], "exemptions": []}
        preEstab = {"mandatory": [], "optionals": [], "exemptions": []}

        all_lists = [
            (mandatory_service, "Service", "mandatory"),
            (optional_service, "Optional Service", "optionals"),
            (mandatory_approvals, "Approval", "mandatory"),
            (optional_approvals, "Optional Approval", "optionals"),
            (subsector_man_approvals, "Sub-Sector Approval", "mandatory"),
            (subsector_optional_approvals, "Sub-Sector Approval", "optionals"),
        ]

        for approval_list, approval_type, category in all_lists:
            for appid in approval_list:
                if appid in all_approval:
                    finalApp = all_approval[appid]
                    department_name = department_data.get(appid, "")
                    approvalDict = {
                        "id": finalApp.id,
                        "name": finalApp.name,
                        "type": approval_type,
                        "department": department_name,
                        "time_limit": finalApp.timelines,
                        "phase": finalApp.phase,
                        "instruction": finalApp.instruction,
                        "exemption": False,
                        "autoselect": finalApp.id in wishlist,
                    }
                    if finalApp.phase == "Pre-Operation":
                        preOps[category].append(approvalDict)
                    elif finalApp.phase == "Pre-Establishment":
                        preEstab[category].append(approvalDict)
                    elif finalApp.phase == "Post-Operation":
                        postOps[category].append(approvalDict)

        for appid in exemption_approvals:
            if appid in all_approval:
                finalApp = all_approval[appid]
                department_name = department_data.get(appid, "")
                approvalDict = {
                    "id": finalApp.id,
                    "name": finalApp.name,
                    "type": "",
                    "department": department_name,
                    "time_limit": finalApp.timelines,
                    "phase": finalApp.phase,
                    "instruction": finalApp.instruction,
                    "exemption": True,
                    "autoselect": False,
                }
                if finalApp.phase == "Pre-Operation":
                    preOps["exemptions"].append(approvalDict)
                elif finalApp.phase == "Pre-Establishment":
                    preEstab["exemptions"].append(approvalDict)
                elif finalApp.phase == "Post-Operation":
                    postOps["exemptions"].append(approvalDict)

        return {
            "Pre-Establishment": preEstab,
            "Pre-Operation": preOps,
            "Post-Operation": postOps,
        }


class UpdateSignedCAFView(APIView):
    def post(self, request):
        user_id = request.data.get('userId') 
        caf_id = request.data.get('id')
        minio_url = request.data.get('minioUrl')
        message = "Missing 'id' field in request."
        if caf_id:
            message = "Missing 'minioUrl' field in request."
            if minio_url:
                caf_data = CAF.objects.filter(id=caf_id).first()
                caf_user_id = 0
                if caf_data:
                    caf_user_id = caf_data.intention.user_id
                message = f"IncentiveCAF with id={caf_id} not found for this user."
                if user_id == caf_user_id:
                    service_caf = CAFCreationPDF.objects.filter(caf_id=caf_id).first()
                    message = "Caf data not found"
                    if service_caf:
                        service_caf.pdf_url = minio_url
                        service_caf.is_document_sign= True
                        service_caf.save()

                        return Response({
                            "status": True,
                            "message": "CAF PDF URL updated successfully.",
                            "savedUrl": service_caf.pdf_url
                        }, status=status.HTTP_200_OK)
                
                return Response({
                    "success": False,
                    "message": message,
                }, status=status.HTTP_400_BAD_REQUEST)
        return Response({
            "status": False,
            "message": message,
          }, status=status.HTTP_400_BAD_REQUEST)

class BlockPriorityAPIView(APIView):
    def get(self, request):
        block_id = request.query_params.get("block_id")
        message = "Missing 'block_id' parameter",
        if block_id:
            try:
                block = DistrictBlockList.objects.get(id=block_id)
                is_priority = block.block_priority if block else 'Non Priority'

                return Response({
                    "success": True,
                    "message": "Data retrieved successfully",
                    "data": {
                        "priority_block": is_priority
                    }
                }, status=status.HTTP_200_OK)

            except DistrictBlockList.DoesNotExist:
                return Response({
                    "success": False,
                    "message": "Block not found",
                    "data": {}
                }, status=status.HTTP_400_BAD_REQUEST)
        return Response({
            "status": False,
            "message": message,
          }, status=status.HTTP_400_BAD_REQUEST)
    
class TehsilAPIView(APIView):
    def get(self, request):

        district_id = request.query_params.get("district_id")
        
        if not district_id:
            return Response(
                {"status": False, "message": "District id is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        qs = Tehsil.objects.filter(district_id=district_id)
        if not qs.exists():
            return Response({"status": True, "data": []}, status = 200)

        serializer = TehsilSerializer(qs, many=True)
        return Response({"status": True, "data": serializer.data}, status=200)
    

class FeedbackFormView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self,request):
        try:

            data = request.data
            email = data.get("email","")
            mobile_no = data.get("mobile_no")
            state_id = data.get("state_id")
            district_id = data.get("district_id")
            document = request.FILES.getlist("document",[])


            district_instance = District.objects.filter(id = district_id).first()

            state_instance = State.objects.filter(id = state_id).first()

            if not (state_instance and district_instance):
                return Response ({"status":False,"message":"Invalid district or state."},status =200)
            
            email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"

            if not re.match(email_regex, email):
                return Response(
                    {"status": False, "message": "Invalid email address"},
                    status=400,
                )

            upload_response = None

            if document:
                url = settings.MINIO_API_HOST + "/minio/uploads"
                document_folder = "feedback"
                files_to_upload = [{"file": doc} for doc in document]

                upload_response = upload_files_to_minio(files_to_upload, url, document_folder)

                if not upload_response["success"]:
                    return Response({
                        "status": False,
                        "message": "File upload failed",
                        "error": upload_response["error"],
                        "server_response": upload_response["response"]
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
                
            obj= FeedbackFormModel.objects.create(
                first_name = data.get("first_name"),
                last_name = data.get("last_name"),
                mobile_no = mobile_no,
                address=data.get("address"),
                email = email,
                state = state_instance,
                state_name = state_instance.name,
                district = district_instance,
                district_name = district_instance.name,
                organization=data.get("organization"),
                designation=data.get("designation"),
                request_type=data.get("request_type"),
                subject=data.get("subject"),
                details=data.get("details"),
                document_link = upload_response["data"][0]["path"] if upload_response else None,
            )
            return Response(
                {"status": True, "message": "Feedback form submitted successfully."},
                status=201
            )
        
        except Exception as e:
            return Response ({"status":False,"message": global_err_message},
                            status=500)      
    
class AutoRedirectFormView(APIView):
    def get(self, request):

        service_id = request.query_params.get("service_id")
        user_service = UserCAFService.objects.filter(id=service_id).first()
        if not user_service:
            return Response(
                {
                    "status": False,
                    "message": "Data is not correct"
                },
                status=status.HTTP_200_OK
            )
        approval_id = user_service.approval_id
        configurations = ApprovalConfigurationModel.objects.filter(approval_id=approval_id).first()
        if not configurations:
            return Response(
                {
                    "status": False,
                    "message": "Configuration is not correct"
                },
                status=status.HTTP_200_OK
            )
        redirect_url = configurations.signing_url 
        method = configurations.request_method

        config = configurations.request_params
        department_name = "Department Portal"
        if user_service.department_id:
            department_data = DepartmentList.objects.filter(id=user_service.department_id).first()
            department_name = department_data.name if department_data else "Department Portal"
        form_fields = {
        }
        if config:
            if 'caf_param' in config:
                form_fields[config['caf_param']] = user_service.caf_id
            if 'request_number_param' in config:
                form_fields[config['request_number_param']] = user_service.request_number
            if 'request_type_param' in config:
                form_fields[config['request_type_param']] = config['request_type_value']
            if 'mobileNumber' in config:
                caf_contact_data = CommonApplication.objects.filter(contact_type='Authorized', caf_id=user_service.caf_id).first()
                form_fields[config['mobileNumber']] = caf_contact_data.mobile_number if caf_contact_data else ""

        # Get a CSRF token for this request
        csrf_token = get_token(request)

        # Generate hidden inputs
        form_inputs = "".join(
            [f'<input type="hidden" name="{k}" value="{v}"/>' for k, v in form_fields.items()]
        )

        # Add CSRF token as hidden field
        form_inputs += f'<input type="hidden" name="CSRFToken" value="{csrf_token}"/>'
        html = f"""
        <html>
            <head><title>Redirecting...</title></head>
            <body onload="document.forms[0].submit()">
                <p id="countdown">Wait. Redirecting to {department_name}...</p>
                <form method="{method}" action="{redirect_url}">
                    {form_inputs}
                    <noscript>
                        <button type="submit">Click here if not redirected</button>
                    </noscript>
                </form>
            </body>
        </html>
        """

        return HttpResponse(html)

