import os
from decimal import Decimal
from datetime import datetime
from decouple import config
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework_simplejwt.authentication import JWTAuthentication
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.conf import settings
from django.db import transaction
from django.db.models import Q
from .models import *
from .serializers import *
from .utils import *  
from authentication.models import WorkflowList, CustomUserProfile
from userprofile.models import UserOrgazination
from userprofile.utils import NotificationMixin
from sws.models import CustomerIntentionProject, RegionalOfficeDistrictMapping
from document_center.utils import *
import json
from userprofile.serializers import OrganizationUserModelMDSerializer
from collections import defaultdict
from django.core.paginator import Paginator, EmptyPage
from django.conf import settings
global_err_message = settings.GLOBAL_ERR_MESSAGE
times = time.time()

class GuestIncentiveCalculator(APIView):
    def post(self, request):
        pass

    def get(self, request):
        try:
            investment = get_float_param(request, "investment", 0)
            if investment <= 0:
                return Response(
                    {
                        "success": False,
                        "message": "Investment Needed",
                        "data": []
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            
            yop = get_int_param(request, "yop", 1)
            if yop > 1:
                return Response(
                    {
                        "success": False,
                        "message": "Sorry! 2nd year onwards incentive can't be calculated here",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            sector_name = request.query_params.get("sector_name")
            yuc = get_int_param(request, "yuc", 100)
            cyp = get_int_param(request, "cyp", 40)
            total_employer = get_int_param(request, "total_employer", 100)
            is_company_exports = get_bool_param(request, "is_company_exports", False)
            export_per = get_float_param(request, "export_per", 0)
            is_back_area_company = get_bool_param(request, "is_back_area_company", False)
            is_cement_company = get_bool_param(request, "is_cement_company", False)
            is_company_fdi = get_bool_param(request, "is_company_fdi", False)
            fdi_per = get_float_param(request, "fdi_per", 0)
            
            bipa = calculateBipa(investment)
            if sector_name:
                sector_multiplier = sectorMultiplier(request, sector_name)
            else:
                sector_multiplier=1.0
            sector_specific_amount = calculate_sector_amount(
                    sector_multiplier, bipa
                )
            gsm_multiplier = calculate_gsm_multiplier(0.4, cyp, yuc)
            gsm_amount = gsm_multiplier * bipa
            final_gsm_amount = gsm_amount - bipa
            employee_multiple = calculate_employee_multiple(total_employer)
            employee_amount = employee_multiple * bipa - bipa
            export_multiple = 1
            if is_company_exports:
                export_multiple = calculate_export_percent(export_per)

            export_amount = export_multiple * bipa - bipa
            geo_multiple = 1
            if is_back_area_company and not is_cement_company:
                geo_multiple = 1.3

            geo_amount = geo_multiple * bipa - bipa

            fdi_multiple = 1
            if is_company_fdi:
                fdi_multiple = calculate_fdi_multiple(fdi_per)

            fdi_amount = fdi_multiple * bipa - bipa

            subsidy_amount = calculate_subsidy_amount(
                bipa,
                sector_specific_amount,
                final_gsm_amount,
                employee_amount,
                export_amount,
                geo_amount,
                fdi_amount,
            )

            message = "Data calculated successfully."

            # Return the result
            return Response(
                {
                    "success": True,
                    "message": message,
                    "data": {
                        "bipa": round(bipa, 2),
                        "sector_multiplier": round(sector_multiplier, 2),
                        "employee_multiple": round(employee_multiple, 2),
                        "export_multiple": round(export_multiple, 2),
                        "geo_multiple": round(geo_multiple, 2),
                        "fdi_multiple": round(fdi_multiple, 1),
                        "subsidy_amount": round(subsidy_amount, 2),
                    },
                },
                status=status.HTTP_200_OK,
            )
        except (ValueError, TypeError) as e:
            return Response(
                {"success": False, "message": global_err_message},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class UserIncentiveCalculator(APIView):
    def post(self, request):
        pass

    def get(self, request):
        try:
            investment = get_float_param(request, "investment", 0)
            if investment <= 0:
                return Response(
                    {
                        "success": False,
                        "message": "Investment Needed",
                        "data": []
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            
            yop = get_int_param(request, "yop", 1)
            if yop > 1:
                yop = 1

            sector_name = request.query_params.get("sector_name")
            yuc = get_float_param(request, "yuc", 100)
            cyp = get_float_param(request, "cyp", 40)
            total_employer = get_int_param(request, "total_employer", 100)
            is_company_exports = get_bool_param(request, "is_company_exports", False)
            export_per = get_float_param(request, "export_per", 0)
            is_back_area_company = get_bool_param(request, "is_back_area_company", False)
            is_cement_company = get_bool_param(request, "is_cement_company", False)
            is_company_fdi = get_bool_param(request, "is_company_fdi", False)
            fdi_per = get_float_param(request, "fdi_per", 0)
            
            bipa = calculateBipa(investment)
            sector_incentive = []
            if sector_name:
                sector_multiplier = sectorMultiplier(request, sector_name)
                sector_incentive = get_sector_specific_details(request, sector_name)
            else:
                sector_multiplier=1.0
                sector_incentive = get_general_incentive(request)
            sector_specific_amount = calculate_sector_amount(
                    sector_multiplier, bipa
                )
            gsm_multiplier = calculate_gsm_multiplier(0.4, cyp, yuc)
            gsm_amount = gsm_multiplier * bipa
            final_gsm_amount = gsm_amount - bipa
            employee_multiple = calculate_employee_multiple(total_employer)
            employee_amount = employee_multiple * bipa - bipa
            export_multiple = 1
            if is_company_exports:
                export_multiple = calculate_export_percent(export_per)

            export_amount = export_multiple * bipa - bipa
            geo_multiple = 1
            if is_back_area_company and not is_cement_company:
                geo_multiple = 1.3

            geo_amount = geo_multiple * bipa - bipa

            fdi_multiple = 1
            if is_company_fdi:
                fdi_multiple = calculate_fdi_multiple(fdi_per)

            fdi_amount = fdi_multiple * bipa - bipa

            subsidy_amount = calculate_subsidy_amount(
                bipa,
                sector_specific_amount,
                final_gsm_amount,
                employee_amount,
                export_amount,
                geo_amount,
                fdi_amount,
            )

            if sector_incentive:
                for key in sector_incentive:
                    subsidy_amount = subsidy_amount + sector_incentive[key]


            message = "Data calculated successfully."

            # Return the result
            return Response(
                {
                    "success": True,
                    "message": message,
                    "data": {
                        "bipa": round(bipa, 2),
                        "sector_multiplier": round(sector_multiplier, 2),
                        "gsm_multiplier": round(gsm_multiplier, 2),
                        "employee_multiple": round(employee_multiple, 2),
                        "export_multiple": round(export_multiple, 2),
                        "geo_multiple": round(geo_multiple, 2),
                        "fdi_multiple": round(fdi_multiple, 1),
                        "subsidy_amount": round(subsidy_amount, 2),
                        "sector_incentive": sector_incentive
                    },
                },
                status=status.HTTP_200_OK,
            )
        except (ValueError, TypeError) as e:
            return Response(
                {"success": False, "message": global_err_message},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    
class UserIncentiveId(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self,request):
            user = request.user
            customer_intention_projects = CustomerIntentionProject.objects.filter(Q(incentive_intention_id__isnull=True) | Q(incentive_intention_id__status="In-Progress"), user_id=user.id, ).order_by("-id")
            serializer = CustomerIntentionProjectSerializer(customer_intention_projects, many=True)
            return Response({
                "status":True,
                "data":serializer.data
            },status=status.HTTP_200_OK)
        
class IncentiveCAFView(APIView, ActivityHistoryMixin):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
        
    def post(self, request):
        intention_id = request.data.get("intention_id")
        user = request.user
        message = "intention_id is required."
        if intention_id:
            intention = CustomerIntentionProject.objects.filter(id=intention_id).first()
            message = "Invalid Intention Id"
            if intention:
                incentive_caf = IncentiveCAF.objects.filter(intention_id=intention.id, status="In-Progress").first()
                if incentive_caf:
                    created = False
                    message = "Existing In-Progress CAF returned."
                    http_status_code = status.HTTP_200_OK
                else:
                    # Create a new CAF
                    incentive_caf = IncentiveCAF.objects.create(
                        intention_id=intention.id,
                        user_id=user.id,
                        status="In-Progress",
                        is_instruction_acknowledgement = True
                    )

                    today = datetime.now()
                    date_part = today.strftime("%y%m%d")  
                    sequence = f"{incentive_caf.id:04d}"  
                    incentive_caf.incentive_caf_number = f"ICAF-{date_part}{sequence}"
                    incentive_caf.save()

                    created = True
                    message = "New In-Progress CAF created."
                    http_status_code = status.HTTP_201_CREATED

                self.create_activity_history(
                    caf_instance=incentive_caf,
                    user_name=str(request.user),
                    user_role=request.user.groups.first().name if request.user.groups.exists() else "",
                    ip_address=request.META.get("REMOTE_ADDR"),
                    activity_status="CAF_Id Created" if created else "CAF_Id Updated",
                    caf_status=incentive_caf.status,
                    status_remark="CAF_Id status changed",
                    activity_result="Success",
                )

                return Response(
                    {
                        "status": True,
                        "message": message,
                        "data": {
                            "id": incentive_caf.id,
                            "incentive_caf_number": incentive_caf.incentive_caf_number,
                            "status": incentive_caf.status,
                        },
                    },
                    status=http_status_code,
                )
            return Response(
                {
                    "status": False,
                    "message": message,
                    "data": {}
                },
                status=status.HTTP_400_BAD_REQUEST,
            )


    def get(self, request):
            intention_id = request.query_params.get("intention_id")
            message = "intention_id is required."
            if intention_id:
                incentive_caf = IncentiveCAF.objects.get(intention_id=intention_id)
                message = "Invalid Intention Id"
                if incentive_caf:
                    return Response(
                        {
                            "status": True,
                            "message": "Data retrieved successfully.",
                            "data": {"id": incentive_caf.id, "incentive_caf_number": incentive_caf.incentive_caf_number},
                        },
                        status=status.HTTP_200_OK,
                    )
            return Response(
                {
                    "status": False,
                    "message": message,
                    "data":{}
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        
# Safe date parsing helper
def parse_and_format_date(date_str):
    try:
        dt = datetime.fromisoformat(str(date_str))
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return ""        

class CafProjectDetail(APIView, ActivityHistoryMixin):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self,request):
            data = request.data
            caf_id = data.get("caf_id")
            message= "Caf id is required."
            if caf_id:
                caf_instance = IncentiveCAF.objects.filter(id=caf_id).first()
                message= "Invalid caf id."
                if caf_instance:
                    # for project in projects:
                    caf_instance = IncentiveCAF.objects.get(id=caf_id)

                    def get_instance_or_none(model, key):
                        return model.objects.filter(id=data.get(key)).first() if data.get(key) else None

                    district_obj = get_instance_or_none(District, "district")
                    regional_office_obj = get_instance_or_none(RegionalOffice, "regional_office")
                    block_obj = get_instance_or_none(DistrictBlockList, "block")
                    activity_obj = get_instance_or_none(Activity, "activity")
                    sector_obj = get_instance_or_none(Sector, "sector")
                    sub_sector_obj = get_instance_or_none(SubSector, "sub_sector")
                    constitution_type_obj = get_instance_or_none(OrganizationType, "constitution_type")
                    industrial_area_obj = get_instance_or_none(IndustrialAreaList, "industrial_area")
                    country_code_id=get_instance_or_none(Country,"country_code")
                    md_country_code_id=get_instance_or_none(Country,"md_country_code")

                    InCAFProject.objects.update_or_create(
                        caf=caf_instance,
                        defaults={
                            "unit_name": data.get("unit_name", ""),
                            "constitution_type": constitution_type_obj,
                            "constitution_type_name": constitution_type_obj.name if constitution_type_obj else "",
                            "intention_id": data.get("intention_id", ""),
                            "date_of_intention": data.get("date_of_intention"),
                            "district": district_obj,
                            "district_name": district_obj.name if district_obj else "",
                            "regional_office": regional_office_obj,
                            "regional_office_name": regional_office_obj.name if regional_office_obj else "",
                            "block": block_obj,
                            "block_name": block_obj.name if block_obj else "",
                            "land_type": data.get("land_type", ""),
                            "industrial_area": industrial_area_obj,
                            "industrial_area_name": industrial_area_obj.name if industrial_area_obj else "",
                            "industrial_plot": data.get("industrial_plot", ""),
                            "address_of_unit": data.get("address_of_unit", ""),
                            "activity": activity_obj,
                            "activity_name": activity_obj.name if activity_obj else "",
                            "sector": sector_obj,
                            "sector_name": sector_obj.incentive_name if sector_obj else "",
                            "sub_sector": sub_sector_obj,
                            "sub_sector_name": sub_sector_obj.name if sub_sector_obj else "",
                            "contact_person_name": data.get("contact_person_name", ""),
                            "contact_email": data.get("contact_email", ""),
                            "contact_mobile_no": data.get("contact_mobile_no", ""),
                            "contact_landline_no": data.get("contact_landline_no", None),
                            "company_address": data.get("company_address", ""),
                            "company_address_pincode": data.get("company_address_pincode", ""),
                            "iem_a_number": data.get("iem_a_number", ""),
                            "iem_a_date": data.get("iem_a_date"),
                            "iem_b_number": data.get("iem_b_number", ""),
                            "iem_b_date": data.get("iem_b_date"),
                            "gstin": data.get("gstin", ""),
                            "gstin_issue_date": data.get("gstin_issue_date"),
                            "unit_type": data.get("unit_type", ""),
                            "country_code_id":country_code_id,
                            "country_code_name":country_code_id.name if country_code_id else "",
                            "md_contact_email":data.get("md_contact_email",""),
                            "md_country_code_id":md_country_code_id,
                            "md_country_code_name":md_country_code_id.name if md_country_code_id else "",
                            "md_contact_mobile_no":data.get("md_contact_mobile_no",""),
                            "md_person_name":data.get("md_person_name",""),
                            "is_ccip": data.get("is_ccip",False),
                            "dipip_type" : data.get("dipip_type",""),
                            "plot_type": data.get("plot_type",""),
                            "designation":data.get("designation",""),
                            "other_designation":data.get("other_designation","")
                        }
                    )
                    turnover=data.get("turnover") if data.get("turnover") else 0
                    is_fdi = data.get("is_fdi") if data.get("is_fdi") else False

                    fdi_percentage= 0
                    if is_fdi:
                        fdi_percentage = data.get("fdi_percentage") if data.get("fdi_percentage") else 0

                    csr= data.get("csr") if data.get("csr") else None
                    is_export_unit = data.get("is_export_unit") if data.get("is_export_unit") else False
                    promoters_equity_amount = data.get ("promoters_equity_amount") if data.get("promoters_equity_amount") else 0
                    term_loan_amount = data.get ("term_loan_amount") if data.get("term_loan_amount") else 0
                    fdi_amount = data.get ("fdi_amount") if data.get("fdi_amount") else 0
                    total_finance_amount = data.get ("total_finance_amount") if data.get("total_finance_amount") else 0
                    is_csr = data.get("is_csr",False)

                    created = InCAFInvestment.objects.update_or_create(
                        caf=caf_instance,
                        defaults={ 
                            "comm_production_date": data.get("comm_production_date"),
                            "turnover":turnover,
                            "fdi_percentage" : fdi_percentage,
                            "is_fdi" : is_fdi,
                            "csr" : csr,
                            "is_export_unit" : is_export_unit,
                            "promoters_equity_amount": promoters_equity_amount,
                            "term_loan_amount" : term_loan_amount,
                            "fdi_amount" : fdi_amount,
                            "total_finance_amount" : total_finance_amount,
                            "is_csr": is_csr
                        }
                    )
                    
                    self.create_activity_history(
                        caf_instance=caf_instance,
                        user_name=request.user.get_full_name() if request.user.is_authenticated else "Anonymous",
                        user_role=getattr(request.user, 'role', 'Unknown'),
                        ip_address=request.META.get("REMOTE_ADDR"),
                        activity_status="Caf project Details Submitted",
                        caf_status=caf_instance.status,
                        status_remark="Caf project Details captured successfully.",
                        activity_result="Success",
                    )                                        

                    return Response({"status": True, "data": [], "message": "Caf project details inserted successfully."})
            return Response(
                {
                    "status": False,
                    "message": message,
                    "data":{}
                },
                status=status.HTTP_400_BAD_REQUEST,
            )                


    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    def get(self, request):
            user = request.user
            caf_id = request.query_params.get("caf_id")
            request_type=request.query_params.get("request_type","")
            message= "CAF ID is required."

            if caf_id:
                # Fetch CAF data
                caf_data = IncentiveCAF.objects.filter(id=caf_id).first()
                message= "CAF not found."
                expansion_count=0
                if caf_data:
                    # Access Control for Investor Role
                    user_roles = UserHasRole.objects.filter(user=user).select_related('role')
                    investor_role = Role.objects.filter(role_name="Investor").first()
                    is_investor = investor_role in [ur.role for ur in user_roles]

                    if is_investor and caf_data.user != user:

                        return Response({
                            "status": False,
                            "message": "You are not authorized to view this CAF project details."
                        }, status=status.HTTP_403_FORBIDDEN)

                    # Retrieve related project & investment data
                    inproject = InCAFProject.objects.filter(caf_id=caf_id).first()
                    incafinvestment = InCAFInvestment.objects.filter(caf_id=caf_id).first()
                    data = {}
                    default_data = {
                            "unit_name": "",
                            "intention_id": "",
                            "date_of_intention": "",
                            "land_type": "",
                            "industrial_plot": "",
                            "address_of_unit": "",
                            "contact_person_name": "",
                            "contact_email": "",
                            "contact_mobile_no": "",
                            "contact_landline_no": "",
                            "company_address": "",
                            "company_address_pincode": "",
                            "iem_a_number": "",
                            "iem_a_date": "",
                            "iem_b_number": "",
                            "iem_b_date": "",
                            "gstin": "",
                            "gstin_issue_date": "",
                            "unit_type": "",
                            "caf": int(caf_id),
                            "constitution_type": "",
                            "constitution_type_name": "",
                            "district": "",
                            "district_name": "",
                            "regional_office": "",
                            "regional_office_name": "",
                            "block": "",
                            "block_name": "",
                            "industrial_area": "",
                            "industrial_area_name": "",
                            "activity": "",
                            "activity_name": "",
                            "sector": "",
                            "sector_name": "",
                            "comm_production_date": "",
                            "md_person_name":"",
                            "md_contact_email":"",
                            "md_country_code_name":"",
                            "md_contact_mobile_no":"",
                            "previous_caf":[],
                            "is_ccip":False,
                            "dipip_type":"",
                            "plot_type":"",                  
                            "designation": "",
                            "other_designation": "",
                            "total_investment_land": 0,
                            "investment_land_before_expansion": 0,
                            "investment_in_plant_machinery":0,
                            "investment_in_plant_machinery_before_expansion": 0,
                            "investment_in_building": 0,
                            "investment_in_building_before_expansion": 0,
                            "total_investment_other_asset": 0,
                            "investment_other_asset_before_expansion" : 0,
                            "total_investment_amount": 0,
                            "total_investment_amount_before_expansion": 0,
                            "investment_in_house_before_expansion":0,
                            "investment_in_house": 0,
                            "investment_captive_power_before_expansion": 0, 
                            "investment_captive_power": 0,
                            "investment_energy_saving_devices_before_expansion": 0,
                            "investment_energy_saving_devices": 0,
                            "investment_imported_second_hand_machinery_before_expansion":0,
                            "investment_imported_second_hand_machinery": 0,
                            "investment_refurbishment_before_expansion": 0,
                            "investment_refurbishment": 0                        
                        }
                    organization_details = UserOrgazination.objects.filter(user_profile=user).first()
                    org_user_contact_detail=OrganizationUserModel.objects.filter(organization_id=organization_details)
                    org_user_contact_detail_serializer=OrganizationUserModelMDSerializer(org_user_contact_detail,many=True)
                    data_=org_user_contact_detail_serializer.data
                    previous_caf_projects = []
                    if inproject and incafinvestment:
                        data = InCAFProjectSerializer(inproject).data
                        if org_user_contact_detail:
                                data['md_person_name']=data_[0]["name"] if data_[0]["mobile_number"] else ""
                                data['md_contact_mobile_no']=data_[0]["mobile_number"] if data_[0]["mobile_number"] else ""
                                data['md_contact_email']=data_[0]["email_id"] if data_[0]["email_id"] else ""
                                data["designation"] = data_[0]["designation"] if data_[0]["designation"] else ""
                                data["other_designation"] = data_[0]["other_designation"]  if data_[0]["other_designation"]  else ""

                        investment_caf = InCAFInvestmentPreviousSerializer(incafinvestment).data
                        data.update(investment_caf)
                        data['industrial_area'] = data['industrial_area'] if data['industrial_area'] else ""
                        if request_type=="all":
                            previous_caf_ids = IncentiveCAF.objects.filter(
                                intention_id=caf_data.intention_id
                                    ).exclude(id=caf_id).values_list("id", flat=True)
                            if previous_caf_ids.exists():
                                for caf_id_item in previous_caf_ids:
                                    project = InCAFProject.objects.filter(caf_id=caf_id_item).first()
                                    investment = InCAFInvestment.objects.filter(caf_id=caf_id_item).first()

                                    if project or investment:
                                        merged_data = {}

                                        if project:
                                            merged_data.update(InCAFProjectSerializer(project).data)

                                        if investment:
                                            investment_data = InCAFInvestmentPreviousSerializer(investment).data
                                            merged_data.update(investment_data)
                                        previous_caf_projects.append(merged_data)
                    else:
                        # Default values if not found
                        data=default_data
                                               
                        # Fill from user's organization data
                        organization_details = UserOrgazination.objects.filter(user_profile=user).first()
                        if organization_details:
                            data['constitution_type'] = organization_details.organization_type_id
                            data['constitution_type_name'] = organization_details.name
                            data['unit_name'] = organization_details.name
                            if organization_details.firm_gstin_number:
                                data['gstin'] = organization_details.firm_gstin_number
                            
                            organization_address = OrganizationAddress.objects.filter(
                                organization=organization_details, address_type="Registered"
                            ).first()
                            if organization_address:
                                data['company_address'] = organization_address.address_line
                                data['company_address_pincode'] = organization_address.pin_code

                            org_user_contact_detail=OrganizationUserModel.objects.filter(organization_id=organization_details)
                            org_user_contact_detail_serializer=OrganizationUserModelMDSerializer(org_user_contact_detail,many=True)
                            data_=org_user_contact_detail_serializer.data
                            if org_user_contact_detail:
                                data['md_person_name']=data_[0]["name"] if data_[0]["mobile_number"] else ""
                                data['md_contact_mobile_no']=data_[0]["mobile_number"] if data_[0]["mobile_number"] else ""
                                data['md_contact_email']=data_[0]["email_id"] if data_[0]["email_id"] else ""
                                data["designation"] = data_[0]["designation"] if data_[0]["designation"] else ""
                                data["other_designation"] = data_[0]["other_designation"]  if data_[0]["other_designation"]  else ""

                        # Fill from user's profile
                        user_profile_data = CustomUserProfile.objects.filter(user=user).first()
                        if user_profile_data:
                            data['contact_person_name'] = user_profile_data.name
                            data['contact_email'] = user_profile_data.email
                            data['contact_mobile_no'] = user_profile_data.mobile_no

                        # Fill from intention project
                        intention_data = CustomerIntentionProject.objects.filter(id=caf_data.intention_id).first()
                        if intention_data:
                            data['intention_id'] = intention_data.intention_id
                            data['land_type'] = intention_data.land_type or ""
                            data['industrial_area'] = intention_data.land_ia_id or ""
                            data['industrial_area_name'] = intention_data.land_industrial_area or ""
                            data['activity'] = intention_data.activities_id or ""
                            data['activity_name'] = intention_data.activity or ""
                            data['sector'] = intention_data.sectors_id or ""
                            data['sector_name'] = intention_data.sector or ""
                            data['district'] = intention_data.districts_id or ""
                            data['district_name'] = intention_data.district or ""
                            data['unit_type'] = intention_data.investment_type
                            data['total_investment_amount'] = intention_data.total_investment or 0
                            data['investment_in_plant_machinery'] = intention_data.investment_in_pm or 0
                            data['investment_in_building'] = 0

                            if intention_data.districts_id:
                                ro_data = RegionalOfficeDistrictMapping.objects.filter(district_id=intention_data.districts_id).first()
                                if ro_data:
                                    data['regional_office'] = ro_data.regional_office_id
                                    data['regional_office_name'] = ro_data.regional_office.name

                            # Format dates
                            if intention_data.created_at:
                                data['date_of_intention'] = parse_and_format_date(intention_data.created_at)

                            if intention_data.product_proposed_date:
                                data['comm_production_date'] = parse_and_format_date(intention_data.product_proposed_date)
                        
                        data["full_investment_land"] = float(data['total_investment_land'])+float(data['investment_land_before_expansion'])
                        data["full_investment_plant_machinery"]= float(data['investment_in_plant_machinery'])+float(data['investment_in_plant_machinery_before_expansion'])
                        data["full_investment_building"]= float(data['investment_in_building'])+float(data['investment_in_building_before_expansion'])
                        data["full_investment_other_asset"] = float(data['total_investment_other_asset'])+float(data['investment_other_asset_before_expansion'])
                        data["full_investment"]= float(data['total_investment_amount'])+float(data['total_investment_amount_before_expansion'])
                        data["full_investment_in_house"] = float(data.get('investment_in_house_before_expansion') or 0) + float(data.get('investment_in_house') or 0)
                        data["full_investment_captive_power"] = float(data.get('investment_captive_power_before_expansion') or 0) + float(data.get('investment_captive_power') or 0)
                        data["full_investment_energy_saving_devices"] = float(data.get('investment_energy_saving_devices_before_expansion') or 0) + float(data.get('investment_energy_saving_devices') or 0)
                        data["full_investment_imported_second_hand_machinery"] = float(data.get('investment_imported_second_hand_machinery_before_expansion') or 0) + float(data.get('investment_imported_second_hand_machinery') or 0)
                        data["full_investment_refurbishment"] = float(data.get('investment_refurbishment_before_expansion') or 0) + float(data.get('investment_refurbishment') or 0)
                                            
                    data['previous_caf'] = previous_caf_projects
                    return Response({
                        "status": True,
                        "message": "CAF project details retrieved successfully.",
                        "data": data
                    })
            return Response(
                {
                    "status": False,
                    "message": message,
                    "data":{}
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

class InCAFIncentiveView(APIView, ActivityHistoryMixin):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]    

    def clean_value(self, value):
        return value if value not in ["", None] else None

    def clean_decimal(self, value):
        try:
            return float(value) if value not in ["", None] else 0.0
        except (ValueError, TypeError):
            return 0.0 

    def post(self, request):
            caf_id = request.data.get("caf_id")
            if not caf_id:
                return Response ({
                    "status": False,
                    "message" : "caf_id is required.",
                    "data": {}
                },status=400)

            if caf_id:
                caf_instance = IncentiveCAF.objects.filter(id=caf_id).first()
                if not caf_instance:
                    return Response ({
                        "status": False,
                        "message" : "Invalid caf_id.",
                        "data": {}
                    },status=400)
                
                if caf_instance:
                    my_data = {
                        "ida_road": self.clean_value(request.data.get("ida_road", "")),
                        "wms_expenditure": self.clean_decimal(request.data.get("wms_expenditure", "")),
                        "power_expenditure": self.clean_decimal(request.data.get("power_expenditure", "")),
                        "gas_expenditure": self.clean_decimal(request.data.get("gas_expenditure", "")),
                        "drainage_expenditure": self.clean_decimal(request.data.get("drainage_expenditure", "")),
                        "sewage_expenditure": self.clean_decimal(request.data.get("sewage_expenditure", "")),
                        "detail_ipr": self.clean_value(request.data.get("detail_ipr", "")),
                        "date_ipr": self.clean_value(request.data.get("date_ipr", "")),
                        "fee_paid_ipr": self.clean_decimal(request.data.get("fee_paid_ipr", "")),
                        "amount_claimed": self.clean_decimal(request.data.get("amount_claimed", "")),
                        "ipr_type": request.data.get("ipr_type", []),
                        "goods_transport": self.clean_value(request.data.get("goods_transport", "")),
                        "mode_transportation": self.clean_value(request.data.get("mode_transportation", "")),
                        "distance_location_unit": self.clean_decimal(request.data.get("distance_location_unit", "")),
                        "is_id" : request.data.get("is_id", False),
                        "is_ipr" : request.data.get("is_ipr", False),
                        "is_efs" : request.data.get("is_efs", False),
                        "is_sfu" : request.data.get ("is_sfu", False),
                        "is_ipp": request.data.get("is_ipp", False),
                        "is_gia": request.data.get("is_gia", False),
                        "is_mandifee": request.data.get("is_mandifee", False),
                        "is_employment_generation": request.data.get("is_employment_generation", False),
                        "is_interest_subsidy" : request.data.get("is_interest_subsidy", False),
                        "is_concession_development_charges" : request.data.get("is_concession_development_charges", False),
                        "is_training_skill_development" : request.data.get("is_training_skill_development", False),
                        "comm_proudction_date": self.clean_value(request.data.get("comm_proudction_date")),
                        "first_purchase_date": self.clean_value(request.data.get("first_purchase_date")),
                        "first_sales_date": self.clean_value(request.data.get("first_sales_date")),
                        "incentive_year": self.clean_value(request.data.get("incentive_year")),
                        "type_of_wms": self.clean_value(request.data.get("type_of_wms")),
                        "wms_total_expenditure": self.clean_decimal(request.data.get("wms_total_expenditure")),
                        "mandi_license": self.clean_value(request.data.get("mandi_license")),
                        "mandi_license_date": self.clean_value(request.data.get("mandi_license_date")),
                        "total_investment_plant_machinery": self.clean_value(request.data.get("total_investment_plant_machinery")),
                        "investment_in_main_manufacturing_process": self.clean_decimal(request.data.get("investment_in_main_manufacturing_process")),
                        "total_sanctioned_term_loan_bank_wise":self.clean_decimal(request.data.get("total_sanctioned_term_loan_bank_wise")),
                        "term_loan_main_process_bank_wise":self.clean_decimal(request.data.get("term_loan_main_process_bank_wise")),
                        "loan_disbursed_with_dates": self.clean_decimal(request.data.get("loan_disbursed_with_dates")),
                        "rate_of_interest_by_bank": self.clean_decimal(request.data.get("rate_of_interest_by_bank")),
                        "land_area_acres": self.clean_decimal(request.data.get("land_area_acres")),
                        "land_premium_inr": self.clean_decimal(request.data.get("land_premium_inr")),
                        "development_charges_inr": self.clean_decimal(request.data.get("development_charges_inr")),
                        "other_charges_inr": self.clean_decimal(request.data.get("other_charges_inr")),
                        "total_cost_of_land_inr": self.clean_decimal(request.data.get("total_cost_of_land_inr")),
                        "stamp_duty_paid_inr": self.clean_decimal(request.data.get("stamp_duty_paid_inr")),
                        "registration_charges_paid_inr": self.clean_decimal(request.data.get("registration_charges_paid_inr")),
                        "total_employees_in_project": self.clean_value(request.data.get("total_employees_in_project")),
                        "mp_domicile_employees_trained_till_cod": self.clean_value(request.data.get("mp_domicile_employees_trained_till_cod")),
                        "investment_year_cod": self.clean_value(request.data.get("investment_year_cod")),
                        "number_newly_employed_worker_code" : self.clean_value(request.data.get("number_newly_employed_worker_code"))
                    }
                    #field addeded for investment
                    my_data["investment_in_plant_machinery"] = self.clean_decimal(request.data.get("investment_in_plant_machinery"))
                    my_data["investment_in_building"] = self.clean_decimal(request.data.get("investment_in_building"))
                    my_data["total_investment_land"] = self.clean_decimal(request.data.get("total_investment_land"))
                    my_data["investment_furniture_fixtures"] = self.clean_decimal(request.data.get("investment_furniture_fixtures"))
                    my_data["total_investment_other_asset"] = self.clean_decimal(request.data.get("total_investment_other_asset"))
                    my_data["investment_in_house"] = self.clean_decimal(request.data.get("investment_in_house"))
                    my_data["investment_captive_power"] = self.clean_decimal(request.data.get("investment_captive_power"))
                    my_data["investment_energy_saving_devices"] = self.clean_decimal(request.data.get("investment_energy_saving_devices"))
                    my_data["investment_imported_second_hand_machinery"] = self.clean_decimal(request.data.get("investment_imported_second_hand_machinery"))
                    my_data["investment_refurbishment"] = self.clean_decimal(request.data.get("investment_refurbishment"))
                    my_data["other_assets_remark"] = self.clean_value(request.data.get("other_assets_remark", ""))
                    my_data["total_investment"] = self.clean_decimal(request.data.get("total_investment"))
                   
                    incentive_instance, created = InCAFIncentive.objects.update_or_create(
                        caf=caf_instance,
                        defaults={
                            "incentive_json": my_data
                        },
                    )

                self.create_activity_history(
                    caf_instance=caf_instance,
                    user_name=request.user.get_full_name() if request.user.is_authenticated else "Anonymous",
                    user_role=getattr(request.user, 'role', 'Unknown'),
                    ip_address=request.META.get("REMOTE_ADDR"),
                    activity_status="Incentive Details Submitted",
                    caf_status=caf_instance.status,
                    status_remark="Incentive Details captured successfully.",
                    activity_result="Success",
                )
                
                message = "Incentive Details Created successfully." if created else "Incentive Details Updated successfully."
                return Response({"status": True, "message": message, "data": my_data}, status=status.HTTP_200_OK)
            return Response(
                {
                    "status": False,
                    "message": message,
                    "data":{}
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

    def get(self, request):
        try:
            caf_id = request.query_params.get("caf_id")
            if not caf_id:
                return Response ({
                    "status": False,
                    "message" : "caf_id is required.",
                    "data": {}
                },status=400)
            if caf_id:
                is_incentive_caf = IncentiveCAF.objects.filter(id=caf_id).first()
                if not is_incentive_caf:
                    return Response({
                        "status": False,
                        "message":"Invalid caf_id.",
                        "data": {}
                    },status= 400)
                InCAFInvestment_instance=InCAFInvestment.objects.filter(caf_id=caf_id).first()
                incentive_instance = InCAFIncentive.objects.filter(caf_id=caf_id).first()
                incentive_sector=InCAFProject.objects.filter(caf_id=caf_id).first()
                ida = IncentiveTypeMasterModel.objects.filter(incentive_type='is_id').first()
                efs = IncentiveTypeMasterModel.objects.filter(incentive_type='is_efs').first()
                inCafInstance = InCAFEmployment.objects.filter(caf=caf_id).first()
                add_ida = False
                add_export_fright = False
                type_of_unit = ""  
                if incentive_sector and incentive_sector.is_ccip:
                    qs = IncentiveTypeSectorModel.objects.filter(
                        incentive_type__status='active', show_in_incentive=True
                    ).distinct("incentive_type_id").order_by("incentive_type_id","display_order")
                    qs = sorted(qs, key=lambda x: x.display_order)
                    add_ida, add_export_fright = True, True
                    type_of_unit = incentive_sector.unit_type
                elif incentive_sector:
                    type_of_unit = incentive_sector.unit_type
                    if incentive_sector.land_type == 'Private land':
                        add_ida = True
                    incentive_sector = incentive_sector.sector
                    qs = IncentiveTypeSectorModel.objects.filter(
                        Q(sector_id=incentive_sector) | Q(sector_id__isnull=True),
                        incentive_type__status='active', show_in_incentive=True
                    ).order_by("display_order")
                else:
                    qs = IncentiveTypeSectorModel.objects.filter(sector_id__isnull=True,
                        incentive_type__status='active' , show_in_incentive=True
                    ).order_by("display_order")

                if InCAFInvestment_instance and InCAFInvestment_instance.is_export_unit:
                    add_export_fright = True

                serializer = IncentiveTypeSectorModelSerializer(qs, many=True)
                if incentive_instance and incentive_instance.incentive_json:
                    incentive_policy_data = serializer.data
                    if add_ida and ida:
                        incentive_policy_data.append({
                            "input_tag": ida.incentive_type,
                            "title": ida.title
                        })
                    if add_export_fright and efs:
                        incentive_policy_data.append({
                            "input_tag": efs.incentive_type,
                            "title": efs.title
                        })
                    data = {
                        "caf_id": incentive_instance.caf.id,
                        "incentive_type": incentive_policy_data
                    }
                    incentive_instance.incentive_json["comm_proudction_date"] = InCAFInvestment_instance.comm_production_date if InCAFInvestment_instance else ""
                    incentive_instance.incentive_json["total_employement_generation_in_project"] = inCafInstance.total_employee if inCafInstance else ""
                    incentive_instance.incentive_json["mp_domicile_employee"] = inCafInstance.employees_from_mp if inCafInstance else ""
                    data.update(incentive_instance.incentive_json)
                    if not add_ida:
                        data.pop('is_id')
                    if not add_export_fright:
                        data.pop('is_efs')
                else:
                    incentive_generate_json = {}
                    incentive_policy_data = serializer.data
                    if add_ida and ida:
                        incentive_policy_data.append({
                            "input_tag": ida.incentive_type,
                            "title": ida.title
                        })
                    if add_export_fright and efs:
                        incentive_policy_data.append({
                            "input_tag": efs.incentive_type,
                            "title": efs.title
                        })
                    data = {
                                "caf_id": int(caf_id),
                                "incentive_type": incentive_policy_data,
                                "is_sfu": False,
                                "comm_proudction_date": "",
                                "incentive_year": "",
                                "type_of_wms": "",
                                "wms_total_expenditure": "",
                                "first_purchase_date": "",
                                "mandi_license": "",
                                "mandi_license_date": "",
                                "ida_road": "",
                                "wms_expenditure": "",
                                "power_expenditure": "",
                                "gas_expenditure": "",
                                "drainage_expenditure": "",
                                "sewage_expenditure": "",
                                "date_ipr": "",
                                "fee_paid_ipr": "",
                                "amount_claimed": "",
                                "ipr_type": [],
                                "detail_ipr" : "",
                                "goods_transport": "",
                                "mode_transportation": "",
                                "distance_location_unit": "",
                                "total_investment_plant_machinery": "",
                                "investment_in_main_manufacturing_process": "",
                                "total_sanctioned_term_loan_bank_wise": "",
                                "term_loan_main_process_bank_wise": "",
                                "loan_disbursed_with_dates": "",
                                "rate_of_interest_by_bank": "",
                                "total_employees_in_project": "",
                                "mp_domicile_employees_trained_till_cod": "",
                                "land_area_acres": "",
                                "land_premium_inr": "",
                                "development_charges_inr": "",
                                "other_charges_inr": "",
                                "total_cost_of_land_inr": "",
                                "stamp_duty_paid_inr": "",
                                "registration_charges_paid_inr": "",
                                "investment_year_cod": "",
                                "first_sales_date": "",
                                "number_newly_employed_worker_code":""                               
                            }
                    data["comm_proudction_date"] = InCAFInvestment_instance.comm_production_date if InCAFInvestment_instance else ""
                    data["total_employement_generation_in_project"] = inCafInstance.total_employee if inCafInstance else ""
                    data["mp_domicile_employee"] = inCafInstance.employees_from_mp if inCafInstance else ""
                    if incentive_policy_data:
                        for ipd in incentive_policy_data:
                            incentive_generate_json[ipd['input_tag']] = True
                    
                    if incentive_generate_json:
                        data.update(incentive_generate_json)

                    
                    incentive_fields = {
                        "investment_in_plant_machinery": 0,
                        "investment_in_building": 0,
                        "total_investment_land": 0,
                        "investment_furniture_fixtures": 0,
                        "total_investment_other_asset": 0,
                        "investment_in_house" :0,
                        "investment_captive_power" : 0,
                        "investment_energy_saving_devices" : 0,
                        "investment_imported_second_hand_machinery" : 0,
                        "investment_refurbishment" : 0,
                        "other_assets_remark": "",
                        "total_investment_amount": 0
                    }
                    if InCAFInvestment_instance:
                        incentive_fields['investment_in_plant_machinery'] = InCAFInvestment_instance.investment_in_plant_machinery or 0
                        incentive_fields['investment_in_building'] = InCAFInvestment_instance.investment_in_building or 0
                        incentive_fields['total_investment_land'] = InCAFInvestment_instance.total_investment_land or 0
                        incentive_fields['investment_furniture_fixtures'] = InCAFInvestment_instance.investment_furniture_fixtures or 0
                        incentive_fields['total_investment_other_asset'] = InCAFInvestment_instance.total_investment_other_asset or 0
                        incentive_fields['investment_in_house'] = InCAFInvestment_instance.investment_in_house or 0
                        incentive_fields['investment_captive_power'] = InCAFInvestment_instance.investment_captive_power or 0
                        incentive_fields['investment_energy_saving_devices'] = InCAFInvestment_instance.investment_energy_saving_devices or 0
                        incentive_fields['investment_imported_second_hand_machinery'] = InCAFInvestment_instance.investment_imported_second_hand_machinery or 0
                        incentive_fields['investment_refurbishment'] = InCAFInvestment_instance.investment_refurbishment or 0
                        incentive_fields['other_assets_remark'] = InCAFInvestment_instance.other_assets_remark or ""
                        incentive_fields['total_investment_amount'] = InCAFInvestment_instance.total_investment_amount or 0
                    else:
                        intention_data = CustomerIntentionProject.objects.filter(id=is_incentive_caf.intention_id).first()
                        if intention_data:
                            incentive_fields['total_investment_amount'] = intention_data.total_investment or 0
                            incentive_fields['investment_in_plant_machinery'] = intention_data.investment_in_pm or 0
                    data.update(incentive_fields)
                return Response(
                        {"status": True, "message": "Incentive Details fetched successfully.","data":data},
                        status=status.HTTP_200_OK
                    )
        except Exception as e:
            return Response(
                {
                    "status": False,
                    "message": str(e),
                    "data": {}
                },
                status=status.HTTP_400_BAD_REQUEST,
            )


class DocumentListView(APIView):

    def get(self,request):
            caf_id = request.query_params.get("caf_id")
            message = "caf_id is required."

            if caf_id:
                incentivecafid = IncentiveCAF.objects.filter(id=caf_id).first()
                message = "Invalid caf_id."
                if incentivecafid:
                    project_details = InCAFProject.objects.filter(caf_id=caf_id).first()
                    if project_details:
                        checked_incentive = []
                        all_approval_type = ['common']
                        all_incentive = IncentiveTypeMasterModel.objects.filter(status='active')
                        incentive_details = InCAFIncentive.objects.filter(caf_id=caf_id).first()
                        if incentive_details:
                            user_incentive = incentive_details.incentive_json
                            if all_incentive.exists():
                                for inc in all_incentive:
                                    if inc.incentive_type in user_incentive and user_incentive[inc.incentive_type]:
                                        checked_incentive.append(inc.incentive_type)

                        if project_details.is_ccip:
                            all_approval_type = all_approval_type + ['is_ccip']
                        
                        if checked_incentive:
                            all_approval_type = checked_incentive + all_approval_type
                        
                        documentlist = SectorDocumentList.objects.filter(
                            Q(sector_id=project_details.sector_id) | Q(sector__isnull=True),
                            status='active',
                            doc_type__in=all_approval_type
                        )
                            
                        if documentlist:
                            serializers=SectorDocumentSerializer(documentlist,many=True).data

                            return Response({
                                "status":True,
                                "message":"Documents fetched successfully.",
                                "data":serializers
                            },status=status.HTTP_200_OK)
                
                    documentlist=SectorDocumentList.objects.filter( sector_id__isnull=True, status='active')
                    if documentlist:
                        serializers=SectorDocumentSerializer(documentlist,many=True).data
                        return Response({
                            "status":True,
                            "message":"Documents fetched successfully.",
                            "data":serializers
                        },status=status.HTTP_200_OK)
                    else:
                        return Response({
                            "status":False,
                            "message":"Documents not available.",
                            "data":[]
                        },status=status.HTTP_400_BAD_REQUEST)
                
            return Response(
                {
                    "status": False,
                    "message": message,
                    "data":{}
                },
                status=status.HTTP_400_BAD_REQUEST,
            )                


class UploadDocumentsView(APIView, ActivityHistoryMixin):
    
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)
    
    def post(self, request):
        try:
            user = request.user            
            caf_id = request.data.get("caf_id")
            if not caf_id:
                return Response({"status": False, "message": "caf_id is required."}, status=status.HTTP_400_BAD_REQUEST)

            incentive_caf = IncentiveCAF.objects.filter(id=caf_id).first()
            if not incentive_caf:
                return Response({"status": False, "message": "Invalid caf_id."}, status=status.HTTP_400_BAD_REQUEST)
            
            intention_data = CustomerIntentionProject.objects.filter(id=incentive_caf.intention_id).first()
            file_folder_name = str(user.id)
            if intention_data:
                file_folder_name = intention_data.intention_id
            
            documents = []
            documents_to_upload = []
            uploaded_files = []
            document_files = [key for key, file in request.FILES.items()]
            text_fields = [item for item in request.data if item not in document_files]
            doc_type_ids = []

            if document_files:

                file_path = "incentive_doc/"+file_folder_name+"/"
                file_folder = os.path.join(settings.MEDIA_ROOT, file_path)
                os.makedirs(file_folder, exist_ok=True)
                
                doc_id_map = {}  
                original_keys=[]                    

                for key, file in request.FILES.items():
                    if key.startswith("document_"):
                        doc_id = key.split("_")[-1]
                        document_instance = DocumentList.objects.filter(id=doc_id).first()

                        if document_instance:
                            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                            new_file_name = f"{os.path.splitext(file.name)[0]}_{timestamp}{os.path.splitext(file.name)[1]}"

                            documents_to_upload.append({
                                "file": file,
                                "file_name": new_file_name,
                                "file_type": file.content_type,
                                "doc_id": int(doc_id)
                            })
                            doc_id_map[new_file_name] = document_instance

                            doc_type_ids.append(int(doc_id))
                            original_keys.append(key)

                if documents_to_upload:
                    minio_url = settings.MINIO_API_HOST + "/minio/uploads"
                    upload_response = upload_files_to_minio(documents_to_upload, minio_url, file_folder_name)


                    for i, j in zip(upload_response["data"], doc_type_ids):
                            document_instance = DocumentList.objects.filter(id=j).first()
                            version_control_tracker(user.id,i["path"],"document_center",doc_id=document_instance)


                    if not upload_response.get("success"):
                        return Response({
                            "status": False,
                            "message": "File upload failed",
                            "error": upload_response.get("error"),
                            "server_response": upload_response.get("response")
                        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)  
                    uploaded_files = upload_response.get("data", [])                  
                    
               
                all_docs = DocumentList.objects.in_bulk(doc_type_ids)

                ordered_documents = [all_docs.get(doc_id) for doc_id in doc_type_ids]

                if uploaded_files:

                    for idx, uploaded_file in enumerate(uploaded_files):
                        file_path = uploaded_file.get("path")
                        doc_id = documents_to_upload[idx]["doc_id"]
                        document_instance = DocumentList.objects.filter(id=doc_id).first()
                        if not document_instance:
                            continue

                        document_obj,created  = InCAFDocuments.objects.update_or_create(
                            caf=incentive_caf,
                            document=document_instance,
                            document_name=document_instance.name,
                            defaults={"document_path": file_path}
                        )                                    
                           

                        serializer = InCAFDocumentsSerializer(document_obj)
                        documents.append(serializer.data)
                                                                   
                    
            if text_fields:
                for param in text_fields:
                    param_data = request.data.get(param)
                    if param.startswith("document_"):
                        doc_id = param.split("_")[-1]
                        document_instance = DocumentList.objects.filter(id=doc_id).first()
                        if document_instance:
                            document_obj, created = InCAFDocuments.objects.update_or_create(
                                caf=incentive_caf,
                                document=document_instance,
                                document_name=document_instance.name,
                                defaults={
                                    "document_path": param_data
                                }
                            )
                            serializer = InCAFDocumentsSerializer(document_obj)
                            documents.append(serializer.data)

            self.create_activity_history(
                caf_instance=incentive_caf,
                user_name=request.user.get_full_name() if request.user.is_authenticated else "Anonymous",
                user_role=getattr(request.user, 'role', 'Unknown'),
                ip_address=request.META.get("REMOTE_ADDR"),
                activity_status="Documents uploaded Submitted",
                caf_status=incentive_caf.status,
                status_remark="Documents uploaded captured successfully.",
                activity_result="Success",
            )

            #Create CAF PDF here:
            caf_all_data = {}
            caf_all_data['caf_project'] = InCAFProject.objects.filter(caf_id=caf_id).order_by("-id").first()
            caf_all_data['incaf_investment'] = InCAFInvestment.objects.filter(caf_id=caf_id).order_by("-id").first()
            caf_all_data['incaf_power'] = InCAFPower.objects.filter(caf_id=caf_id).order_by("-id").first()
            caf_all_data['incaf_employment'] = InCAFEmployment.objects.filter(caf_id=caf_id).order_by("-id").first()
            caf_all_data['incaf_products'] = InCAFProduct.objects.filter(caf_id=caf_id).order_by("-id")
            caf_all_data['incaf_incentive'] = InCAFIncentive.objects.filter(caf_id=caf_id).order_by("-id").first()
            caf_all_data['incaf_submeter'] = InCAFSubMeter.objects.filter(caf_id=caf_id).order_by("-id")
            caf_all_data['incaf_power_load'] = InCAFPowerLoad.objects.filter(caf_id=caf_id).order_by("-id")
            caf_all_data['expansion_unit'] = InCAFExpansion.objects.filter(caf_id=caf_id).order_by("-id")
            caf_all_data['incaf_power_load'] = InCAFPowerLoad.objects.filter(caf_id=caf_id).order_by("-id")
            # caf_all_data['expansion_products'] = InCAFExpansionProduct.objects.filter(expansion_id=caf_id).order_by("-id")
            # Get expansions related to the CAF
            custom_profile = CustomUserProfile.objects.filter(user=user).first()
            organization_profile = None

            if custom_profile:
                user_organization = UserOrgazination.objects.filter(user_profile=user).first()
                if user_organization:
                    organization_profile = OrganizationUserModel.objects.filter(
                        organization=user_organization
                    ).first()

            expansions = InCAFExpansion.objects.filter(caf_id=caf_id).order_by("-id")
            expansion_products = InCAFExpansionProduct.objects.filter(expansion__in=expansions)
            grouped_data = defaultdict(list)
            comm_date_dict = {}

            for product in expansion_products:
                comm_date_dict[product.expansion_id] = product.expansion.date_of_production
                grouped_data[product.expansion_id].append({
                    "product_name": product.product_name,
                    "total_annual_capacity": product.total_annual_capacity,
                    "measurement_unit": product.measurement_unit_id,
                    "annual_capacity_before_expansion": product.annual_capacity_before_expansion,
                    "annual_capacity_during_expansion": product.annual_capacity_during_expansion,
                    "other_measurement_unit_name": product.other_measurement_unit_name,
                })

            caf_all_data['expansion_products'] = [
                {
                    "expansion_id": expansion_id,
                    "comm_production_date": comm_date_dict[expansion_id],
                    "products": product_list
                }
                for expansion_id, product_list in grouped_data.items()
            ]
            
            customer_data =  CustomUserProfile.objects.filter(user=request.user).first()
        
            pdf_url = generate_incentive_caf_pdf(
                intention_data,
                caf_all_data,
                customer_data,
                custom_profile,
                organization_profile
            )
            version_control_tracker(user.id,pdf_url,"incentive","incentive_caf")

            return Response({
                "status": True,
                "message": "Documents uploaded successfully.",
                "data": documents,
                "pdf_url": pdf_url
            }, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            return Response({"status": False, "message": global_err_message},
                                    status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def get(self,request):
            caf_id =request.query_params.get("caf_id")
            message= "caf_id is required."
            if caf_id:            
                incafdocuments=InCAFDocuments.objects.filter(caf_id=caf_id)
                message= "No data found!"
                data = []
                if incafdocuments:
                    data=InCAFDocumentsSerializer(incafdocuments,many=True).data
                    message = "Documents retrived successfully."
                return Response({
                    "status":True,
                    "message": message,
                    "data": data
                },status=200)
            return Response(
                {
                    "status": False,
                    "message": message,
                    "data":{}
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

class CheckCafFormStatusView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
            caf_id = request.query_params.get("caf_id")
            message= "caf_id is required."
            if caf_id:
                caf_instance = IncentiveCAF.objects.filter(id=caf_id).first()
                message= "Invalid caf_id."
                if caf_instance:

                    form_status = {
                        "is_project_filled": InCAFProject.objects.filter(caf_id=caf_id).exists(),
                        "is_investment_filled": InCAFInvestment.objects.filter(caf_id=caf_id).exists(),
                        "is_power_filled": InCAFPower.objects.filter(caf_id=caf_id).exists(),
                        "is_employement_filled": InCAFEmployment.objects.filter(caf_id=caf_id).exists(),
                        "is_product_filled": InCAFProduct.objects.filter(caf_id=caf_id).exists(),
                        "is_incentive_filled": InCAFIncentive.objects.filter(caf_id=caf_id).exists(),
                        "is_document_filled": InCAFDocuments.objects.filter(caf_id=caf_id).exists(),
                    }

                    return Response({
                        "status": True,
                        "message": "Data retrieved successfully.",
                        "data": form_status
                    }, status=status.HTTP_200_OK)
            return Response(
                {
                    "status": False,
                    "message": message,
                    "data":{}
                },
                status=status.HTTP_400_BAD_REQUEST,
            )            

class CAFSubmissionView(APIView, IncentiveApprovalMixin, NotificationMixin):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            caf_id = request.data.get("caf_id")
            if not caf_id:
                return Response({"status": False, "message": "caf_id is required."}, status=status.HTTP_400_BAD_REQUEST)

            incentive_caf = IncentiveCAF.objects.filter(id=caf_id).first()
            if not incentive_caf:
                return Response({"status": False, "message": "Invalid caf_id."}, status=status.HTTP_400_BAD_REQUEST)

            # updating the status of the instance not directly of the model.
            incentive_workflow = WorkflowList.objects.filter(flow_type="incentive-agenda", level_no=0).first()
            if incentive_workflow:
                sla_due_date = get_sla_date(incentive_workflow.sla_period)
                incentive_caf.status = incentive_workflow.current_status
                incentive_caf.acknowledgement =  request.data.get("acknowledgement")
                incentive_caf.acknowledgement_date = timezone.now()
                incentive_caf.sla_due_date = sla_due_date
                incentive_caf.sla_days = incentive_workflow.sla_period
                incentive_caf.current_approver_role = incentive_workflow.current_role
                incentive_caf.save() #save() needs an instance, not the class  
                user = request.user
                user_profile = CustomUserProfile.objects.filter(user_id = user.id).first()
                

                self.create_incentive_approval_log(
                    caf=incentive_caf,
                    user_name=user_profile.name,
                    user_designation= "investor",
                    action= incentive_workflow.current_status, 
                    document_path= None,  
                    remark=None,
                    next_approval_role= incentive_workflow.current_role,
                    sla_days=incentive_workflow.sla_period,
                    sla_due_date=sla_due_date
                )

                user_ids = self.get_user_ids_by_role(incentive_workflow.current_role)
                notification_response = self.send_notification(
                    user_ids = user_ids,
                    title="New CAF Created",
                    message=f"CAF ID {caf_id} has been updated by {user_profile.name} with action {incentive_workflow.current_status}."
                )

                if notification_response.status_code != status.HTTP_200_OK:
                    return notification_response 

            return Response({
                "status": True,
                "message": "Data updated successfully",
                "data": []
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "status": False,
                "message": global_err_message
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request):
        try:
            caf_id = request.query_params.get("caf_id")
            message ="Missing Caf id"
            data = {}
            if caf_id:
                caf_data = IncentiveCAF.objects.filter(id=caf_id).first()
                if caf_data:
                    data=minio_func(caf_data.caf_pdf_url)
                    total_pages = count_page(str(data[1]["Fileurl"][0]))

                    return Response({
                        "status": True,
                        "message": "Data Retrived successfully",
                        "data": {"pdf_url":data[1]["Fileurl"],
                                "is_document_sign":caf_data.is_document_sign,"total_pages":total_pages}
                    }, status=status.HTTP_200_OK)
                else:
                    message ="Caf Data not found"
                
            return Response({
                    "status": False,
                    "message": message,
                    "data": {}
                },
                status=status.HTTP_400_BAD_REQUEST,
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

class IncentiveAgendaView(APIView, ActivityHistoryMixin, IncentiveAuditLogMixin):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_instance_or_none(self, model, key, data):
        return model.objects.filter(id=data.get(key)).first() if data.get(key) else None

    def post(self, request, *args, **kwargs):
        agenda_data = request.data.get("agenda_data")
        products_data = request.data.get("products_data")
        incentive_data = request.data.get("incentive_data")
        try:
            message = "Invalid caf"
            check_caf = IncentiveCAF.objects.filter(id=agenda_data.get("caf")).first()
            if check_caf:
                user_profile = CustomUserProfile.objects.filter(user=request.user).first()
                agenda_data["created_user_name"] = user_profile.name if user_profile else ""
                agenda_data["created_by"] = user_profile.id if user_profile else None
                agenda_data["status"] = "Created"
                fk_fields = {
                    "block": DistrictBlockList,
                    "district": District,
                    "regional_office": RegionalOffice,
                    "industrial_area": IndustrialAreaList,
                    "activity": Activity,
                    "sector": Sector
                }

                for key, value in fk_fields.items():
                    if agenda_data.get(key):
                        model = fk_fields[key]
                        related_obj = model.objects.filter(id=agenda_data.get(key)).first()
                        if related_obj:
                            agenda_data[key+"_name"] = related_obj.name
                if 'id' in agenda_data:
                    existing_agenda = IncentiveAgenda.objects.filter(id=agenda_data.get('id')).first()
                    agenda_serializer = IncentiveAgendaSerializer(instance=existing_agenda, data=agenda_data)
                else:
                    existing_agenda = IncentiveAgenda.objects.filter(caf=agenda_data.get("caf")).order_by("-id").first()
                    agenda_serializer = IncentiveAgendaSerializer(instance=existing_agenda, data=agenda_data)
                
                if agenda_serializer.is_valid():
                    agenda_instance = agenda_serializer.save()
                    agenda_id = agenda_instance.id
                    if products_data:
                        IncentiveAgendaProduct.objects.filter(agenda_id=agenda_id).delete()
                        for product in products_data:
                            product["agenda"] = agenda_id
                            serializer = IncentiveAgendaProductSerializer(data=product)
                            if serializer.is_valid():
                                serializer.save()
                    if incentive_data:
                        incentive_instance, created = AgendaIncentiveModel.objects.update_or_create(
                            agenda=agenda_instance,
                            defaults={
                                "incentive_json": incentive_data
                            }
                        )

                    existing_agenda_incentive = AgendaInvestmentModel.objects.filter(agenda=agenda_instance).first()
                    agenda_data['agenda'] = agenda_id
                    agenda_incentive_serializer = AgendaInvestmentSerializer(instance=existing_agenda_incentive, data=agenda_data)
                    if agenda_incentive_serializer.is_valid():
                        agenda_investment_instance = agenda_incentive_serializer.save()
                        self.create_activity_history(
                            caf_instance=check_caf, 
                            user_name=request.user.username,  
                            user_role=request.user.groups.first().name if request.user.groups.exists() else "",
                            ip_address=request.META.get('REMOTE_ADDR'),  
                            activity_status="Agenda Created",  
                            caf_status=agenda_instance.status,  
                            status_remark="Agenda and products created successfully",
                            activity_result="Success"
                        )
                        log_api_timing(agenda_data["caf"],"Agenda and products created successfully.","Success", times)

                        self.create_incentive_audit_log(
                            caf_instance=check_caf,
                            module="Incentive Agenda", 
                            user_name=request.user.username, 
                            user_role=request.user.groups.first().name if request.user.groups.exists() else "",
                            action_type="Agenda Create", 
                            old_value=None,  
                            new_value=str(agenda_instance)  
                        )
                        pdf = generate_agenda_pdf(agenda_instance, products_data, user_profile, existing_agenda_incentive)
                        log_api_timing(agenda_data["caf"],"PDF created.","Success", times)

                        version_control_tracker(user_profile.user_id,pdf,"incentive","incentive_agenda")
                        data=minio_func(pdf)
                        total_pages = 0
                        pdf_url = ""

                        if data[0]:
                            total_pages =count_page(data[1]["Fileurl"][0])
                            pdf_url = data[1]["Fileurl"]
                            log_api_timing(agenda_data["caf"],"File recived from minio","Success", times)
                        else:
                            log_api_timing(agenda_data["caf"],"File not found","UnSuccess", times)
                    
                        return Response({
                                "success": True,
                                "message": "Incentive agenda along with its products has been saved successfully.",
                                "pdf_url": pdf_url,
                                "total_pages":total_pages
                            },status=status.HTTP_201_CREATED)
                    else:
                        message = str(agenda_incentive_serializer.errors)
                else:
                    message = str(agenda_serializer.errors)

            return Response({
                "success": False,
                "message": message,
                "data": []
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            log_api_timing(agenda_data["caf"],global_err_message,"UnSuccess", times)
            return Response({
                "success": False,
                "message": str(e),
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request):
        caf_id = request.query_params.get('caf_id')
        message = "caf_id is required."
        if caf_id:
            caf = IncentiveCAF.objects.filter(id=caf_id).first()
            message = "Caf data is invalid"
            if caf:
                data = {}
                investment_data = {
                    "is_ccip":False,
                    "turnover":0,
                    "is_export_unit":False,
                    "is_csr":False,
                    "csr":"",
                    "is_fdi":False,
                    "promoters_equity_amount":0,
                    "term_loan_amount":0,
                    "fdi_amount":0,
                    "fdi_percentage":0,
                    "total_finance_amount":0,
                    "investment_building":0,
                    "eligible_investment_building":0,
                    "investment_plant_machinery":0,
                    "eligible_investment_plant_machinery":0,
                    "investment_inhouse_rnd":0,
                    "eligible_investment_inhouse_rnd":0, 
                    "investment_captive_power":0,
                    "eligible_investment_captive_power":0,
                    "investment_energy_saving_devices":0,
                    "eligible_investment_energy_saving_devices":0,
                    "investment_imported_second_hand_machinery":0,
                    "eligible_investment_imported_second_hand_machinery":0,
                    "investment_refurbishment":0,
                    "eligible_investment_refurbishment":0,
                    "investment_furniture_fixtures":0
                }
                agenda = IncentiveAgenda.objects.filter(caf=caf).order_by("-id").first()
                if agenda:
                    data = IncentiveAgendaSerializer(agenda).data
                    product_queryset = agenda.agenda_product.all()
                    data["products_data"] = []
                    if product_queryset:
                        for product in product_queryset:
                            data["products_data"].append({
                                "product_name": product.product_name or "",
                                "measurement_unit": product.measurement_unit.id if product.measurement_unit else None,
                                "measurement_unit_name": product.measurement_unit_name or "",
                                "total_annual_capacity": product.total_annual_capacity or "",
                                "comm_production_date": product.comm_production_date.strftime("%Y-%m-%d") if product.comm_production_date else ""
                            })
                    incentive_details = AgendaIncentiveModel.objects.filter(agenda=agenda).first()
                    data["incentive_data"] = {}
                    if incentive_details:
                        incentive_agenda_data = AgendaIncentiveSerializer(incentive_details).data
                        data["incentive_data"] = incentive_agenda_data['incentive_json']
                    investment_details = AgendaInvestmentModel.objects.filter(agenda=agenda).first()
                    if investment_details:
                        investment_agenda_data = AgendaInvestmentSerializer(investment_details).data
                        data.update(investment_agenda_data)
                    else:
                        data.update(investment_data)     
                else:
                    data = {
                        "status": "In-Progress", 
                        "unit_name": "",
                        "constitution_type_name": "", 
                        "constitution_type": "", 
                        "gstin_and_date": "",
                        "iem_a_number": "",
                        "iem_a_date": "", 
                        "iem_b_number": "",
                        "iem_b_date": "",
                        "block_name": "",
                        "address_of_unit": "",
                        "category_of_block": "",
                        "activity": "", 
                        "activity_name": "", 
                        "sector": "", 
                        "sector_name": "", 
                        "sub_sector": "", 
                        "sub_sector_name": "", 
                        "first_production_year": "", 
                        "comm_production_date": "",
                        "unit_type": "", 
                        "ht_contract_demand": "", 
                        "saction_power_load": "", 
                        "investment_in_plant_machinery": "", 
                        "eligible_investment_plant_machinery": "", 
                        "bipa": "", 
                        "yearly_bipa": "", 
                        "ipp": "", 
                        "eligible_period": "", 
                        "employee_of_mp": "",
                        "employee_outside_mp": "",
                        "total_employee": "", 
                        "percentage_in_employee": "", 
                        "fact_about_case": "", 
                        "recommendation": "", 
                        "slec_proposal": "",
                        "agenda_file": "", 
                        "products_data": [],
                        "block": "",
                        "district":"",
                        "regional_office":"",
                        "land_type":"",
                        "industrial_area":"",
                        "industrial_plot":"",
                        "plot_type":"",
                        "incentive_data": []
                    }
                    data.update(investment_data)
                    caf_project = InCAFProject.objects.filter(caf=caf).first()
                    if caf_project:
                        gstin = caf_project.gstin
                        gstin_date = caf_project.gstin_issue_date.strftime("%d-%m-%Y")
                        data["gstin_and_date"] = f"{gstin} {gstin_date}" if gstin or gstin_date else ""
                        data["unit_name"] = caf_project.unit_name
                        data["constitution_type_name"] = caf_project.constitution_type_name
                        data["constitution_type"] = caf_project.constitution_type_id or ""
                        data["iem_a_number"] = caf_project.iem_a_number
                        data["iem_a_date"] = caf_project.iem_a_date
                        data["iem_b_number"] = caf_project.iem_b_number
                        data["iem_b_date"] = caf_project.iem_b_date
                        data["block_name"] = caf_project.block_name
                        data["address_of_unit"] = caf_project.address_of_unit
                        data["activity"] = caf_project.activity_id or ""
                        data["activity_name"] = caf_project.activity_name
                        data["sector"] = caf_project.sector_id or ""
                        data["sector_name"] = caf_project.sector_name
                        data["sub_sector"] = caf_project.sub_sector_id or ""
                        data["sub_sector_name"] = caf_project.sub_sector_name
                        data["unit_type"] = caf_project.unit_type
                        data["block"] = caf_project.block_id
                        data["district"] = caf_project.district_id
                        data["regional_office"] = caf_project.regional_office_id or ""
                        data["land_type"] = caf_project.land_type
                        data["industrial_area"] = caf_project.industrial_area_id or ""
                        data["industrial_plot"] = caf_project.industrial_plot
                        data["plot_type"] = caf_project.plot_type
                        data["is_ccip"]=caf_project.is_ccip
                    
                    investment = InCAFInvestment.objects.filter(caf=caf).first()
                    if investment:
                        data["investment_in_plant_machinery"] = investment.investment_in_plant_machinery
                        data["comm_production_date"] = investment.comm_production_date
                        data["turnover"]=investment.turnover
                        data["is_export_unit"]=investment.is_export_unit
                        data["is_csr"]=investment.is_csr
                        data["csr"]=investment.csr
                        data["is_fdi"]=investment.is_fdi
                        data["promoters_equity_amount"]=investment.promoters_equity_amount or 0
                        data["term_loan_amount"]=investment.term_loan_amount or 0
                        data["fdi_amount"]=investment.fdi_amount
                        data["fdi_percentage ="]=investment.fdi_percentage
                        data["total_finance_amount"]=investment.total_finance_amount or 0
                        data["investment_building"]=investment.investment_in_building or 0
                        data["eligible_investment_building"]=investment.investment_in_building or 0
                        data["investment_plant_machinery"]=investment.investment_in_plant_machinery or 0
                        data["eligible_investment_plant_machinery"]=investment.investment_in_plant_machinery or 0
                        data["investment_inhouse_rnd"]=investment.investment_in_house or 0
                        data["eligible_investment_inhouse_rnd"]=investment.investment_in_house or 0 
                        data["investment_captive_power"]=investment.investment_captive_power or 0
                        data["eligible_investment_captive_power"]=investment.investment_captive_power or 0
                        data["investment_energy_saving_devices"]=investment.investment_energy_saving_devices or 0
                        data["eligible_investment_energy_saving_devices"]=investment.investment_energy_saving_devices or 0
                        data["investment_imported_second_hand_machinery"]=investment.investment_imported_second_hand_machinery or 0
                        data["eligible_investment_imported_second_hand_machinery"]=investment.investment_imported_second_hand_machinery or 0
                        data["investment_refurbishment"]=investment.investment_refurbishment or 0
                        data["eligible_investment_refurbishment"]=investment.investment_refurbishment or 0
                        data["investment_furniture_fixtures"]=investment.investment_furniture_fixtures or 0

                    incaf_power = InCAFPower.objects.filter(caf=caf).first()
                    if incaf_power:
                        data["ht_contract_demand"] = incaf_power.ht_contract_demand
                        data["saction_power_load"] =  incaf_power.load_consumption if incaf_power.connection_type == 'New' else incaf_power.existing_load

                    employment = InCAFEmployment.objects.filter(caf=caf).first()
                    if employment:
                        data["total_employee"] = employment.total_employee
                        data["employee_of_mp"] = employment.employees_from_mp
                        data["employee_outside_mp"] = employment.employees_outside_mp
                        data["percentage_in_employee"] = employment.employee_domicile_percentage or 0
                        data["employee_of_mp_before_expansion"] = employment.employee_from_mp_before_expansion or 0
                        data["employee_outside_mp_before_expansion"] = employment.employees_outside_mp_before_expansion or 0
                        data["total_employee_before_expansion"] = employment.total_employee_before_expansion or 0
                        data["employee_domicile_percentage_before_expansion"] = employment.employee_domicile_percentage_before_expansion or 0
                        data["number_of_differently_abled_employees"] = employment.number_of_differently_abled_employees or 0
                        data["percentage_of_differently_abled_employees"] = employment.percentage_of_differently_abled_employees or 0

                    incentive_details = InCAFIncentive.objects.filter(caf=caf).first()
                    if incentive_details:
                        data['incentive_data'] = incentive_details.incentive_json

                    incentive_products = InCAFProduct.objects.filter(caf=caf)
                    if incentive_products:
                        for product in incentive_products:
                            data["products_data"].append({
                                "product_name": product.product_name or "",
                                "measurement_unit": product.measurement_unit.id if product.measurement_unit else None,
                                "measurement_unit_name": product.measurement_unit_name or "",
                                "total_annual_capacity": product.total_annual_capacity or "",
                                "comm_production_date": investment.comm_production_date or "",
                            })
                    else:
                        data["products_data"].append({
                            "product_name": "",
                            "measurement_unit": "",
                            "measurement_unit_name": "",
                            "total_annual_capacity": "",
                            "comm_production_date": ""
                        })                
                
                data["caf"] = caf_id
                data["application_filling_date"] = (
                    caf.acknowledgement_date.strftime("%Y-%m-%d") if caf and caf.acknowledgement_date else ""
                )
                user_profile = CustomUserProfile.objects.filter(user=request.user).first()
                data["created_user_name"] = user_profile.name if user_profile else ""
                data["created_by"] = user_profile.id if user_profile else None

                return Response(
                    {
                        "status": True,
                        "message": "Data retrieved successfully.",
                        "data": data,
                    },
                    status=status.HTTP_200_OK,
                )                

        return Response({
                "status": False,
                "message": message,
                "data": []
            }, status=status.HTTP_400_BAD_REQUEST)      

            
        
class WorkflowActionView(APIView, ActivityHistoryMixin, IncentiveAuditLogMixin, IncentiveApprovalMixin):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        try:
            caf_id = request.data.get('caf_id')
            user = request.user
            action_type = request.data.get('action_type')
            flow_type = request.data.get('flow_type')
            user_role = request.data.get('role')
            remark = request.data.get('remark')
            document = request.FILES.get('document')
            sanctionID = request.data.get('sanctionID')
            user_profile = CustomUserProfile.objects.filter(user_id = user.id).first()

            if caf_id:
                caf_data = IncentiveCAF.objects.filter(id=caf_id).first()
                if caf_data:
                    role_data = Role.objects.filter(role_name=user_role).first()
                    if role_data:
                        workflow_obj = WorkflowList.objects.filter(current_role_id = role_data.id, flow_type=flow_type).first()
                        if workflow_obj:
                            is_file_upload = False
                            file_path = ""
                            documents_to_upload = []
                            if document:
                                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                                new_file_name = f"{os.path.splitext(document.name)[0].replace(' ', '_')}_{timestamp}{os.path.splitext(document.name)[1]}"
                                documents_to_upload.append({
                                    "file": document,
                                    "file_name": new_file_name,
                                    "file_type": document.content_type
                                })
                                if documents_to_upload:
                                    intention_data = CustomerIntentionProject.objects.filter(id=caf_data.intention_id).first()
                                    file_folder_name = str(user.id)
                                    if intention_data:
                                        file_folder_name = intention_data.intention_id
                                    minio_url = settings.MINIO_API_HOST + "/minio/uploads"
                                    upload_response = upload_files_to_minio(documents_to_upload, minio_url, file_folder_name)
                                    if upload_response.get("success"):   
                                        uploaded_files = upload_response.get("data", [])                  
                                        if uploaded_files:
                                            is_file_upload = True
                                            file_path = uploaded_files[0]['path']
                                            
                            next_role = None
                            wfitem = WorkflowItemList.objects.filter(workflow = workflow_obj, action_type=action_type).first()

                            if wfitem:
                                caf_status = wfitem.status
                                next_role = wfitem.next_role
                                nextworkflow =  WorkflowList.objects.filter(current_role_id = wfitem.next_role, flow_type=wfitem.next_flow_type).first()
                                if nextworkflow:
                                    caf_data.sla_days=nextworkflow.sla_period
                                    caf_data.sla_due_date=get_sla_date(nextworkflow.sla_period)
                                    caf_data.current_approver_role = wfitem.next_role
                                else:
                                    caf_data.sla_days=None
                                    caf_data.sla_due_date=None
                                    caf_data.current_approver_role = None
                                if flow_type == 'sanction-order':
                                    if sanctionID:
                                        sanction_data = IncentiveSanctionOrder.objects.filter(id=sanctionID).first()
                                        if sanction_data and sanction_data.incentive_claim_id:
                                            if wfitem.action_type == 'Approve Sanction Order':
                                                sanction_data.status = 'Approved'
                                                sanction_data.save()
                                            claim_data = IncentiveClaimBasic.objects.filter(id=sanction_data.incentive_claim_id).first()
                                            if claim_data:
                                                if wfitem.action_type == 'Approve Sanction Order':
                                                    claim_data.status= 'Approved'
                                                else:
                                                    claim_data.status= caf_status
                                                claim_data.save()
                                else:
                                    caf_data.status = caf_status
                                    caf_data.save()
                                if wfitem.action_type == "SLEC Order Verified":
                                    incentiveSlec = IncentiveSlecOrder.objects.filter(caf_id=caf_id, status="Created").first()
                                    if incentiveSlec:
                                        incentiveSlec.status = "Approved"
                                        incentiveSlec.save()
                                if wfitem.action_type == "Approve Agenda":
                                    incentiveAgenda = IncentiveAgenda.objects.filter(caf_id=caf_id, status="Created").first()
                                    if incentiveAgenda:
                                        incentiveAgenda.status = "Approved"
                                        incentiveAgenda.save()
                                if action_type == "Raise Query":
                                    caf_data.status = caf_status
                                    caf_data.save()
                                    target_user_id = caf_data.intention.user.id if caf_data.intention.user else None
                                    user_name = ""
                                    if target_user_id:
                                        target_user_profile = CustomUserProfile.objects.filter(user_id = target_user_id).first()
                                        user_name = target_user_profile.name
                                    query_raise = IncentiveDepartmentQueryModel.objects.create(
                                        intention = caf_data.intention,
                                        query_type = flow_type,
                                        status = "In-Progress",
                                        user = caf_data.intention.user if caf_data.intention.user else None,
                                        user_name = user_name,
                                        depratment_user = user,
                                        department_user_name = user_profile.name if user_profile else "",
                                        department_remark = remark,
                                        department_user_role = role_data,
                                        caf = caf_data
                                    )
                                if wfitem.action_type == "Send SLEC Order" and is_file_upload:
                                    name = os.path.basename(file_path)
                                    document_obj,created  = InCAFSLECDocument.objects.update_or_create(
                                        caf=caf_data,
                                        defaults={
                                            "slec_doc_name": name,
                                            "slec_doc_path": file_path,
                                            "slec_order": None
                                        }
                                    )
                                # Create log
                                self.create_activity_history(
                                    caf_instance=caf_data, 
                                    user_name=user_profile.name,  
                                    user_role=role_data.role_name,
                                    ip_address=request.META.get('REMOTE_ADDR'),  
                                    activity_status= action_type + " performed by "+ user_role,  
                                    caf_status=caf_status,  
                                    status_remark=remark,
                                    activity_result="Success"
                                )

                                self.create_incentive_audit_log(
                                    caf_instance=caf_data,
                                    module="Incentive Agenda", 
                                    user_name=user_profile.name,
                                    user_role=role_data.role_name,
                                    action_type=action_type, 
                                    old_value=None,  
                                    new_value=str(request.data)  
                                )
                                
                                is_overdue = False
                                if caf_data.sla_due_date:
                                    if date.today() > caf_data.sla_due_date:
                                        is_overdue = True

                                self.create_incentive_approval_log(
                                    caf=caf_data,
                                    user_name=user_profile.name,
                                    user_designation=user_profile.designation.name if user_profile.designation else "",
                                    action=action_type, 
                                    document_path=file_path,  
                                    remark=remark,
                                    next_approval_role= next_role,
                                    sla_days=caf_data.sla_days or 0,
                                    sla_due_date=caf_data.sla_due_date,
                                    is_overdue = is_overdue,
                                    resolved_at = timezone.now()
                                )

                                return Response({"success": True,
                                    "message": "Data Submitted Successfully",
                                    "data": {}},
                                status=status.HTTP_200_OK)
            
            return Response({
                "success": False,
                "message": "Bad Data.",
                "data": {}},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response({
                "success": False,
                "message": global_err_message,
                "data": {}},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request):        
        try:
            caf_id = request.query_params.get("caf_id", "").strip()
            if caf_id:
                finding_caf_id = IncentiveCAF.objects.filter(id=caf_id).first()
                if finding_caf_id:
                    approval_history = IncentiveApprovalHistory.objects.filter(caf_id = caf_id).order_by("created_at")
                    data = []
                    if approval_history.exists():
                        data = IncentiveApprovalHistorySerializer(approval_history, many=True).data

                    return Response({
                        "status": True,
                        "data": data,
                        "message": "Approval History Logs fetch successfully"
                    }, status=status.HTTP_200_OK)
            
            return Response({
                "status": False,
                "message": "Data Issue!",
                "data": []
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                "status": False,
                "message": global_err_message
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class IncentiveCAFListView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
        
    def get(self, request, *args, **kwargs):
        response_data = {
            "success": False,
            "message": "Something went wrong",
            "data": {}
        }

        try:
            limit = int(request.query_params.get("limit", 10))
            page = int(request.query_params.get("page", 1))
            search_text = request.query_params.get("search_text", "").strip()
            queryset = IncentiveCAF.objects.select_related('intention').prefetch_related("caf_project").exclude(status="In-Progress").order_by("-updated_at")

            if search_text:
                queryset = queryset.filter(
                    Q(incentive_caf_number__icontains=search_text) |
                    Q(intention__intention_id__icontains=search_text) |
                    Q(caf_project__unit_name__icontains=search_text)
                )
            total_count = queryset.count()
            start = (page - 1) * limit
            end = start + limit
            paginated_queryset = queryset[start:end]

            serializer = IncentiveCAFListSerializer(paginated_queryset, many=True).data
            if serializer:
                for itm in serializer:
                    itm['is_agenda'] = False
                    itm['agenda_id'] = ""
                    project_data = InCAFProject.objects.filter(caf=itm['id']).order_by("-id").first()
                    agenda_data = IncentiveAgenda.objects.filter(caf=itm['id']).order_by("-id").first()
                    if agenda_data:
                        itm['is_agenda'] = True
                        itm['agenda_id'] = agenda_data.id
                    itm['unit_name'], itm['contact_person_name'] = "", ""
                    if project_data:
                        itm['unit_name'] = project_data.unit_name
                        itm['contact_person_name'] = project_data.contact_person_name
                    pdf_file = minio_func(itm['caf_pdf_url'])
                    if pdf_file[0]:
                        itm['caf_pdf_url'] = pdf_file[1]["Fileurl"]

            response_data.update({
                "success": True,
                "message": "Data fetched successfully.",
                "data": {
                    "results": serializer,
                    "pagination": {
                        "total": total_count,
                        "page": page,
                        "limit": limit,
                        "total_pages": (total_count + limit - 1) // limit
                    }
                }
            })
            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            response_data["message"] = global_err_message
            return Response(response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SlecOrderView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self,request):
        data=request.data
        caf_id=data.get("caf_id")
        slec_order_data = data.get("slec_order", {})
        product_data_list = data.get("product", []) 
        financial_year_data_list = data.get("finacial_year", [])
        message = "Caf id parameter is missing"
        if caf_id:
            message = "No CAF or Agenda found for this caf_id."
            caf_data=IncentiveCAF.objects.filter(id=caf_id).first()
            if caf_data:
                with transaction.atomic():
                    constitution_obj = OrganizationType.objects.filter(id=slec_order_data.get("constitution_type")).first()
                    activity_obj = Activity.objects.filter(id=slec_order_data.get("activity")).first()
                    sector_obj = Sector.objects.filter(id=slec_order_data.get("sector")).first()
                    sub_sector_obj = SubSector.objects.filter(id=slec_order_data.get("sub_sector")).first()                
                    order_data, created = IncentiveSlecOrder.objects.update_or_create(
                        caf=caf_data,
                        defaults={
                                "unit_name": slec_order_data.get("unit_name", ""),
                                "constitution_type": constitution_obj if constitution_obj else None,
                                "constitution_type_name": constitution_obj.name if constitution_obj else None,
                                "unit_type": slec_order_data.get("unit_type", ""),
                                "activity": activity_obj if activity_obj else None,
                                "activity_name": activity_obj.name if activity_obj else None,
                                "sector": sector_obj if sector_obj else None,
                                "sector_name": sector_obj.incentive_name if sector_obj else None,
                                "sub_sector": sub_sector_obj if sub_sector_obj else None,
                                "sub_sector_name": sub_sector_obj.name if sub_sector_obj else None,
                                "category_of_block": slec_order_data.get("category_of_block", ""),
                                "date_of_slec_meeting": slec_order_data.get("date_of_slec_meeting"),
                                "slec_meeting_number": slec_order_data.get("slec_meeting_number", ""),
                                "eligible_investment_plant_machinery": slec_order_data.get("eligible_investment_plant_machinery"),
                                "bipa": slec_order_data.get("bipa"),
                                "yearly_bipa": slec_order_data.get("yearly_bipa"),
                                "eligibility_from": slec_order_data.get("eligibility_from"),
                                "eligibility_to": slec_order_data.get("eligibility_to"),
                                "remark": slec_order_data.get("remark", ""),
                                "name_of_authority": slec_order_data.get("name_of_authority", ""),
                                "authority_designation": slec_order_data.get("authority_designation", ""),
                                "status": "Created",
                                "commencement_date": slec_order_data.get("commencement_date") if slec_order_data.get("commencement_date") else None,
                            })
                    order_slec_serializer = IncentiveSlecOrderSerializer(order_data)

                    for product in product_data_list:
                        unit_obj = MeasurementUnitList.objects.filter(id=product.get("measurement_unit")).first()
                        slec_product=IncentiveSlecProduct.objects.update_or_create(
                            product_name=product.get("product_name", ""),
                            slec_order=order_data,
                            defaults={
                            "measurement_unit_id":unit_obj.id if unit_obj else None,
                            "measurement_unit_name":unit_obj.name if unit_obj else None,
                            "total_annual_capacity":product.get("total_annual_capacity"),
                            "comm_production_date":product.get("comm_production_date")
                            }
                        )
                  
                    # Save Financial Year List
                    for year in financial_year_data_list:
                        amount = float(year.get("amount")) if year.get("amount") else 0.00
                        slec_year=IncentiveSlecYealy.objects.update_or_create(
                            slec_order=order_data,
                            incentive_year=year.get("incentive_year"),
                            defaults={                        
                            "status":year.get("status"),
                            "claim_year_serial_number":year.get("claim_year_serial_number"),
                            "amount": amount,
                            "remark":year.get("remark")
                            }
                        )
            
                    caf_data.status = "SLEC order created"
                    caf_data.save()

                    slec_pdf = InCAFSLECDocument.objects.filter(caf=caf_data).first()
                    if slec_pdf:
                        slec_pdf.slec_order = order_data
                        slec_pdf.save()

                    return Response({
                        "status": True,
                        "message": "Slec Order and associated data saved successfully."
                    }, status=status.HTTP_201_CREATED)
                
        return Response(
            {
                "status":False,
                "message":message,
                "data": []
            },status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
    def generate_incentive_data(self,number_of_years=7):
        today = date.today()
        current_year = today.year
        current_month = today.month

        # Fiscal year starts in April (month 4)
        if current_month >= 4:
            start_year = current_year
        else:
            start_year = current_year - 1

        incentive_data = []
        for i in range(number_of_years):
            fy_start = start_year + i
            fy_end = fy_start + 1
            incentive_data.append({
                "incentive_year": f"{fy_start}-{str(fy_end)[-2:]}",
                "status": "",
                "claim_year_serial_number": "",
                "amount": "",
                "remark": ""
            })
        return incentive_data
        
    def get(self, request):        
        caf_id = request.query_params.get("caf_id")
        message = "Caf id is not found"
        if caf_id:
            finding_caf_id = IncentiveCAF.objects.filter(id=caf_id).first()
            message = "Caf data is not found"
            if finding_caf_id:
                order = IncentiveSlecOrder.objects.filter(caf_id=caf_id).order_by("-date_of_slec_meeting").first()
                message = "SLEC order is not found"
                if order:
                    intention_number = finding_caf_id.intention.intention_id if finding_caf_id.intention else ""
                    intention_date = finding_caf_id.intention.created_at if finding_caf_id.intention else ""
                    if intention_date:
                        intention_date = intention_date.strftime("%Y-%m-%d")
                    products = IncentiveSlecProduct.objects.filter(slec_order_id=order)
                    financial_years = IncentiveSlecYealy.objects.filter(slec_order_id=order).order_by("claim_year_serial_number")
                    
                    if not financial_years.exists():
                        year_serializer = self.generate_incentive_data(7)
                    else:
                        year_serializer = IncentiveSlecYealySerializer(financial_years, many=True).data
                    
                    order_serializer = IncentiveSlecOrderSerializer(order).data
                    if order_serializer:
                        order_serializer['intention_number'] = intention_number
                        order_serializer['intention_date'] = intention_date
                        order_serializer['is_arrear'] = False
                        arrear_data = IncentiveSLECArrearModel.objects.filter(slec_order_id=order).first()
                        if arrear_data:
                            order_serializer['is_arrear'] = True
                    products_serializer = IncentiveSlecProductSerializer(products, many=True)
                    agenda = IncentiveAgenda.objects.filter(caf_id=caf_id).first()
                    minio_agenda_file = ""
                    if agenda.agenda_file:
                        agenda_file_data=minio_func(agenda.agenda_file)
                        if agenda_file_data[0]:
                            minio_agenda_file = agenda_file_data[1]["Fileurl"]
                    
                    slec_pdf = InCAFSLECDocument.objects.filter(slec_order=order).first()
                    main_slec_file = ""
                    if slec_pdf and slec_pdf.slec_doc_path:
                        slec_file_data=minio_func(slec_pdf.slec_doc_path)
                        if slec_file_data[0]:
                            main_slec_file = slec_file_data[1]["Fileurl"]
                    
                    check_other_caf = IncentiveCAF.objects.filter(intention_id=finding_caf_id.intention_id).exclude(id=caf_id)
                    old_slec_order = []
                    if check_other_caf:
                        for itm in check_other_caf:
                            old_slec_order_data = IncentiveSlecOrder.objects.filter(caf_id=itm.id).first()
                            if old_slec_order_data:
                                old_slec_data = IncentiveSlecOrderSerializer(old_slec_order_data).data
                                intention_number = itm.intention.intention_id if itm.intention else ""
                                intention_date = itm.intention.created_at if itm.intention else ""
                                if intention_date:
                                    intention_date = intention_date.strftime("%Y-%m-%d")
                                old_slec_data['intention_number'] = intention_number
                                old_slec_data['intention_date'] = intention_date
                                slec_pdf = InCAFSLECDocument.objects.filter(slec_order=old_slec_order_data).first()
                                slec_file = ""
                                if slec_pdf and slec_pdf.slec_doc_path:
                                    slec_file_data=minio_func(slec_pdf.slec_doc_path)
                                    if slec_file_data[0]:
                                        slec_file = slec_file_data[1]["Fileurl"]
                                old_slec_data['slec_pdf_file'] = slec_file
                                old_slec_order.append(old_slec_data)
                            
                        
                    return Response({
                        "status": True,
                        "message": "Data Fetch Successfully",
                        "data": {
                            "order": order_serializer,
                            "products": products_serializer.data,
                            "financial_years": year_serializer,
                            "agenda_file":minio_agenda_file,
                            "slec_file": main_slec_file,
                            "old_slec_order": old_slec_order
                        }
                    }, status=status.HTTP_200_OK)
                else:
                    agenda = IncentiveAgenda.objects.filter(caf_id=caf_id).first()
                    product_data = []
                    if agenda:
                        agenda_product_data=IncentiveAgendaProduct.objects.filter(agenda=agenda)
                        if agenda_product_data:
                            for prod in agenda_product_data:
                                product_data.append({
                                    "product_name": prod.product_name,
                                    "measurement_unit": prod.measurement_unit_id,
                                    "total_annual_capacity": prod.total_annual_capacity,
                                    "comm_production_date": prod.comm_production_date
                                })
                    year_serializer = self.generate_incentive_data(7)
                    agenda_data = {}
                    minio_agenda_file = ""
                    if agenda:
                        agenda_data = {
                            "caf": caf_id,
                            "unit_name": agenda.unit_name or "",
                            "constitution_type_name": agenda.constitution_type_name or "",
                            "constitution_type": agenda.constitution_type_id,
                            "activity_name": agenda.activity_name or "",
                            "activity": agenda.activity_id,
                            "sector": agenda.sector_id,
                            "sub_sector": agenda.sub_sector_id,
                            "sector_name": agenda.sector_name or "",
                            "unit_type": agenda.unit_type or "",
                            "sub_sector_name": agenda.sub_sector_name or "",
                            "category_of_block": agenda.category_of_block or "",
                            "date_of_slec_meeting": "",
                            "slec_meeting_number": "",
                            "eligible_investment_plant_machinery": agenda.eligible_investment_plant_machinery or "",
                            "bipa": agenda.bipa or "",
                            "yearly_bipa": agenda.yearly_bipa or "",
                            "eligibility_from": "",
                            "eligibility_to": "",
                            "remark": "",
                            "name_of_authority": "",
                            "authority_designation": "",
                            "status": agenda.status or "",
                            "commencement_date": agenda.comm_production_date or ""
                        }
                        minio_agenda_file = ""
                        if agenda.agenda_file:
                            agenda_file_data=minio_func(agenda.agenda_file)
                            if agenda_file_data[0]:
                                minio_agenda_file = agenda_file_data[1]["Fileurl"]

                    return Response({
                        "status": True,
                        "message": "Data Fetch Successfully",
                        "data": {
                            "order": agenda_data,
                            "products": product_data,
                            "financial_years": year_serializer,
                            "agenda_file": minio_agenda_file
                        }
                    }, status=status.HTTP_200_OK)
                
        return Response({
                "status": False,
                "message": message
            }, status=status.HTTP_400_BAD_REQUEST)

    def put(self,request):
        data=request.data
        slec_order_id=data.get("id")
        message = "Slec Order parameter is missing"
        if slec_order_id:
            message = "No SLEC Found"
            slec_order_data=IncentiveSlecOrder.objects.filter(id=slec_order_id).first()
            if slec_order_data:
                with transaction.atomic():
                    restricted_fields = {"id", "caf", "sub_sector","status"}
                    update_fields = {}
                    fk_fields = {
                        "constitution_type": OrganizationType,
                        "activity": Activity,
                        "sector": Sector,
                    }

                    for key, value in data.items():
                        if key in restricted_fields:
                            continue

                        if key in fk_fields:
                            model = fk_fields[key]
                            related_obj = model.objects.filter(id=value).first()
                            update_fields[key] = related_obj
                            if related_obj and key == "constitution_type":
                                update_fields["constitution_type_name"] = related_obj.name
                            elif related_obj and key == "activity":
                                update_fields["activity_name"] = related_obj.name
                            elif related_obj and key == "sector":
                                update_fields["sector_name"] = related_obj.incentive_name
                        else:
                            update_fields[key] = value

                    for key, value in update_fields.items():
                        setattr(slec_order_data, key, value)
                    slec_order_data.save()
                    serialized = IncentiveSlecOrderSerializer(slec_order_data)
                    return Response({
                        "status": True,
                        "message": "Slec Order updated successfully.",
                        "data": serialized.data
                    }, status=status.HTTP_200_OK)
        return Response(
            {
                "status":False,
                "message":message,
                "data": []
            },status=status.HTTP_400_BAD_REQUEST
        )
    

from collections import defaultdict

class CafOtherDetailView(APIView, ActivityHistoryMixin):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

     # Helper functions defined as FE passing "" in case of expansion, can be assess anywhere in this class.

    def to_decimal(self, value):
        try:
            return Decimal(str(value))
        except:
            return 0
        
    def to_date(self, value):
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except (TypeError, ValueError):
            return None
        
    def to_int(self, value):
        try:
            return int(value)
        except:
            return 0

    def get(self,request):
            user = request.user
            caf_id=request.query_params.get("caf_id")
            request_type = request.query_params.get("request_type")
            message = "caf_id is required."
            if caf_id:
                caf_data = IncentiveCAF.objects.filter(id=caf_id).first()
                message = "No product details found with this caf."
                if caf_data:
                    # Role-based access check
                    user_roles = UserHasRole.objects.filter(user=user).select_related('role')
                    investor_role = Role.objects.filter(role_name="Investor").first()
                    is_investor = investor_role in [ur.role for ur in user_roles]

                    if is_investor and caf_data.user != user:
                        return Response({
                            "status": False,
                            "message": "You are not authorized to view this CAF's details."
                        }, status=status.HTTP_403_FORBIDDEN)
                    def get_caf_details(caf_obj):
                        # Employment details
                        employment_instance = InCAFEmployment.objects.filter(caf_id=caf_obj.id).first()
                        employment_data = {
                            "employees_from_mp": getattr(employment_instance, "employees_from_mp", 0),
                            "employees_outside_mp": getattr(employment_instance, "employees_outside_mp", 0),
                            "total_employee": getattr(employment_instance, "total_employee", 0),
                            "employees_from_mp_before_expansion": getattr(employment_instance, "employee_from_mp_before_expansion", 0),
                            "employees_outside_mp_before_expansion": getattr(employment_instance, "employees_outside_mp_before_expansion", 0),
                            "total_employee_before_expansion": getattr(employment_instance, "total_employee_before_expansion", 0),
                            "employee_domicile_percentage": getattr(employment_instance, "employee_domicile_percentage", 0),
                            "employee_domicile_percentage_before_expansion" : getattr(employment_instance, "employee_domicile_percentage_before_expansion", 0),
                            # "employees_from_mp_before_expansion" : getattr(employment_instance, "employee_from_mp_before_expansion")
                            "number_of_differently_abled_employees" : getattr(employment_instance,"number_of_differently_abled_employees",0),
                            "percentage_of_differently_abled_employees" : getattr(employment_instance,"percentage_of_differently_abled_employees",0)
                        }
                        
                        # Product details of new
                        incaf_products = InCAFProduct.objects.filter(caf_id=caf_obj.id,product_type="New")
                        product_details = [
                            {
                                "id": product.id,                               
                                "measurement_unit_name": product.measurement_unit_name,
                                "custom_measurement_unit": product.other_measurement_unit_name,
                                "product_name": product.product_name,
                                "total_annual_capacity": str(product.total_annual_capacity),
                                "caf": product.caf_id,
                                "measurement_unit": product.measurement_unit.id if product.measurement_unit else None,
                                "ime_before_expansion": product.ime_before_expansion or 0,
                                "avg_production_before_expansion": product.avg_production_before_expansion or 0,
                                "annual_capacity_before_expansion": product.annual_capacity_before_expansion or 0,
                                "product_type": getattr(product,"product_type","New")
                            }
                            for product in incaf_products
                        ]

                        # Product details of existing_products
                        incaf_existing_products = InCAFProduct.objects.filter(caf_id=caf_obj.id,product_type="Existing")
                        existing_products = [
                            {
                                "id": incaf_existing_product.id,                               
                                "measurement_unit_name": incaf_existing_product.measurement_unit_name,
                                "custom_measurement_unit": incaf_existing_product.other_measurement_unit_name,
                                "product_name": incaf_existing_product.product_name,
                                "total_annual_capacity": str(incaf_existing_product.total_annual_capacity),
                                "caf": incaf_existing_product.caf_id,
                                "measurement_unit": incaf_existing_product.measurement_unit.id if incaf_existing_product.measurement_unit else None,
                                "ime_before_expansion": incaf_existing_product.ime_before_expansion or 0,
                                "avg_production_before_expansion": incaf_existing_product.avg_production_before_expansion or 0,
                                "annual_capacity_before_expansion": incaf_existing_product.annual_capacity_before_expansion or 0,
                                "product_type": getattr(incaf_existing_product,"product_type","Existing")
                            }
                            for incaf_existing_product in incaf_existing_products
                        ]

                        # Power details
                        power = InCAFPower.objects.filter(caf=caf_obj).first()
                        power_details = {
                            "connection_type": power.connection_type if power else "",
                            "ht_contract_demand": power.ht_contract_demand if power else "",
                            "date_of_connection": power.date_of_connection if power else "",
                            "load_consumption": str(power.load_consumption) if power and power.load_consumption else None,
                            "existing_load": str(power.existing_load) if power and power.existing_load else None,
                            "additional_load": str(power.additional_load) if power and power.additional_load else None,
                            "date_additional_load": power.date_additional_load if power else None,
                            "connection_type_before_expansion": str (power.connection_type_before_expansion) if power and power.connection_type_before_expansion else "",
                            "power_load_before_expansion" : power.power_load_before_expansion if power and power.power_load_before_expansion else None,
                            "date_of_connection_before_expansion": power.date_of_connection_before_expansion if power and power.date_of_connection_before_expansion else "",
                            "meter_before_expansion" : power.meter_before_expansion if power  and power.meter_before_expansion else "",
                            "meter_details" : getattr(power,"meter_details",""),
                            "enhancement_load_date": getattr(power,"enhancement_load_date","")
                        }

                        power_loads = InCAFPowerLoad.objects.filter(caf=caf_obj)
                        is_supplementary_load = (InCAFPowerLoad.objects.filter(caf=caf_obj).first())
                        is_supplementary_load_exits = getattr(is_supplementary_load,"is_supplementary_load",False)
                        employment_data["is_supplementary_load"] = is_supplementary_load_exits

                        power_load_details = []
                        if is_supplementary_load_exits:
                            if power_loads.exists():
                                power_load_details = [
                                    {
                                        "supplementary_load": str(load.supplementary_load),
                                        "supplementary_load_date": load.supplementary_load_date,
                                    } for load in power_loads
                                ]

                        submeters = InCAFSubMeter.objects.filter(caf=caf_obj)
                        submeter_details = [{"meter_number": meter.meter_number} for meter in submeters]

                        incafinvestment = InCAFInvestment.objects.filter(caf_id=caf_obj.id).first()
                        if incafinvestment:
                            investment_caf = InCAFInvestmentSerializer(incafinvestment).data
                            investment_caf["full_investment_land"] = float(investment_caf.get('total_investment_land') or 0) + float(investment_caf.get('investment_land_before_expansion') or 0)
                            investment_caf["full_investment_plant_machinery"] = float(investment_caf.get('investment_in_plant_machinery') or 0) + float(investment_caf.get('investment_in_plant_machinery_before_expansion') or 0)
                            investment_caf["full_investment_building"] = float(investment_caf.get('investment_in_building') or 0) + float(investment_caf.get('investment_in_building_before_expansion') or 0)
                            investment_caf["full_investment_other_asset"] = float(investment_caf.get('total_investment_other_asset') or 0) + float(investment_caf.get('investment_other_asset_before_expansion') or 0)
                            investment_caf["full_investment"] = float(investment_caf.get('total_investment_amount') or 0) + float(investment_caf.get('total_investment_amount_before_expansion') or 0)
                            investment_caf["full_investment_in_house"] = float(investment_caf.get('investment_in_house_before_expansion') or 0) + float(investment_caf.get('investment_in_house') or 0)
                            investment_caf["full_investment_captive_power"] = float(investment_caf.get('investment_captive_power_before_expansion') or 0) + float(investment_caf.get('investment_captive_power') or 0)
                            investment_caf["full_investment_energy_saving_devices"] = float(investment_caf.get('investment_energy_saving_devices_before_expansion') or 0) + float(investment_caf.get('investment_energy_saving_devices') or 0)
                            investment_caf["full_investment_imported_second_hand_machinery"] = float(investment_caf.get('investment_imported_second_hand_machinery_before_expansion') or 0) + float(investment_caf.get('investment_imported_second_hand_machinery') or 0)
                            investment_caf["full_investment_refurbishment"] = float(investment_caf.get('investment_refurbishment_before_expansion') or 0) + float(investment_caf.get('investment_refurbishment') or 0)
                        else:
                            investment_caf = {
                                "investment_land_before_expansion": 0,
                                "investment_in_plant_machinery_before_expansion": 0,
                                "investment_in_building_before_expansion": 0,
                                "investment_other_asset_before_expansion": 0,
                                "total_investment_amount_before_expansion": 0,
                                "total_investment_amount": 0,
                                "investment_in_plant_machinery": 0,
                                "investment_in_building": 0,
                                "total_investment_land": 0,
                                "total_investment_other_asset": 0,
                                "full_investment_land": 0,
                                "full_investment_plant_machinery": 0,
                                "full_investment_building": 0,
                                "full_investment_other_asset": 0,
                                "full_investment": 0,
                                "investment_furniture_fixtures": 0,
                                "investment_in_house_before_expansion" : 0,
                                "full_investment_in_house" : 0,
                                "investment_in_house" :0,
                                "investment_captive_power_before_expansion" : 0,
                                "full_investment_captive_power" : 0,
                                "investment_captive_power" : 0,
                                "investment_energy_saving_devices_before_expansion" : 0,
                                "full_investment_energy_saving_devices" : 0,
                                "investment_energy_saving_devices" : 0,
                                "investment_imported_second_hand_machinery_before_expansion" : 0,
                                "full_investment_imported_second_hand_machinery" : 0,
                                "investment_imported_second_hand_machinery" : 0,
                                "investment_refurbishment_before_expansion" : 0,
                                "full_investment_refurbishment" : 0,
                                "investment_refurbishment" : 0,
                                "other_assets_remark": ""
                            }

                            # Fill from intention project
                            intention_data = CustomerIntentionProject.objects.filter(id=caf_obj.intention_id).first()
                            if intention_data:
                                investment_caf['total_investment_amount'] = intention_data.total_investment or 0
                                investment_caf['investment_in_plant_machinery'] = intention_data.investment_in_pm or 0
                                investment_caf['investment_in_building'] = 0

                        response = {
                            "caf_id": caf_obj.id,
                            "status": caf_obj.status,
                            "created_at": caf_obj.created_at,
                            "updated_at": caf_obj.updated_at,
                            "user": caf_obj.user.id if caf_obj.user else None,
                            **employment_data,
                            "product_details": product_details,                            
                            "existing_products":existing_products,
                            "power_details": power_details,
                            "power_load_details": power_load_details,
                            "submeter_details": submeter_details
                        }
                        response.update(investment_caf)
                        return response

                    # Main CAF details
                    current_data = get_caf_details(caf_data)
                    print("--",current_data)

                    # Previous CAFs
                    current_data["previous_caf"] = []
                    if request_type == "all" and caf_data.intention_id:
                        previous_cafs = IncentiveCAF.objects.filter(intention_id=caf_data.intention_id).exclude(id=caf_data.id)
                        current_data["previous_caf"] = [get_caf_details(prev) for prev in previous_cafs]

            return Response({
                "status": True,
                "message": "Caf other details fetched successfully.",
                "data": current_data
            })
                    
            
        
    def post(self, request):
                            
            data = request.data
            caf_id = data.get("caf_id")
            message = "caf_id is required."

            if caf_id:
                incentivecafid = IncentiveCAF.objects.filter(id=caf_id).first()
                message= "Invalid caf id."
                if incentivecafid:
                    employees_from_mp = request.data.get("employees_from_mp")
                    employees_outside_mp = request.data.get("employees_outside_mp")
                    total_employee = request.data.get("total_employee")
                    if total_employee > 0:
                        employee_domicile_percentage = (employees_from_mp * 100) / total_employee
                    else:
                        employee_domicile_percentage = 0 
                    existing_products = request.data.get("existing_products",[])

                    employees_from_mp_before_expansion = self.to_int(request.data.get("employees_from_mp_before_expansion"))
                    employees_outside_mp_before_expansion = self.to_int(request.data.get("employees_outside_mp_before_expansion"))
                    total_employee_before_expansion = self.to_int(request.data.get("total_employee_before_expansion"))
                    if total_employee_before_expansion > 0:
                        employee_domicile_percentage_before_expansion = (employees_from_mp_before_expansion * 100) / total_employee_before_expansion
                    else:
                        employee_domicile_percentage_before_expansion = 0    
                    number_of_differently_abled_employees = self.to_int(request.data.get("number_of_differently_abled_employees"))
                    if total_employee > 0:
                        percentage_of_differently_abled_employees = (number_of_differently_abled_employees * 100) / total_employee
                    else:
                        percentage_of_differently_abled_employees = 0 
                    #investment fields
                    total_investment_land=data.get("total_investment_land") if data.get("total_investment_land") else 0
                    total_investment_other_asset=data.get("total_investment_other_asset") if data.get("total_investment_other_asset") else 0
                    total_investment_amount=data.get("total_investment_amount") if data.get("total_investment_amount") else 0
                    investment_in_building=data.get("investment_in_building") if data.get("investment_in_building") else 0
                    investment_in_plant_machinery=data.get("investment_in_plant_machinery") if data.get("investment_in_plant_machinery") else 0
                    investment_land_before_expansion = data.get ("investment_land_before_expansion") if data.get("investment_land_before_expansion") else 0
                    investment_in_plant_machinery_before_expansion = data.get ("investment_in_plant_machinery_before_expansion") if data.get("investment_in_plant_machinery_before_expansion") else 0
                    investment_in_building_before_expansion = data.get ("investment_in_building_before_expansion") if data.get("investment_in_building_before_expansion") else 0
                    investment_other_asset_before_expansion = data.get ("investment_other_asset_before_expansion") if data.get("investment_other_asset_before_expansion") else 0
                    total_investment_amount_before_expansion = data.get ("total_investment_amount_before_expansion") if data.get("total_investment_amount_before_expansion") else None
                    investment_furniture_fixtures = data.get ("investment_furniture_fixtures") if data.get("investment_furniture_fixtures") else None
                    investment_in_house_before_expansion = data.get ("investment_in_house_before_expansion") if data.get("total_investment_amount_before_expansion") else None
                    investment_in_house= data.get ("investment_in_house") if data.get("investment_in_house") else None
                    investment_captive_power_before_expansion = data.get ("investment_captive_power_before_expansion") if data.get("investment_captive_power_before_expansion") else None
                    investment_captive_power = data.get ("investment_captive_power") if data.get("investment_captive_power") else None
                    investment_energy_saving_devices_before_expansion = data.get ("investment_energy_saving_devices_before_expansion") if data.get("investment_energy_saving_devices_before_expansion") else None
                    investment_energy_saving_devices = data.get ("investment_energy_saving_devices") if data.get("investment_energy_saving_devices") else None
                    investment_imported_second_hand_machinery_before_expansion = data.get ("investment_imported_second_hand_machinery_before_expansion") if data.get("investment_imported_second_hand_machinery_before_expansion") else None
                    investment_imported_second_hand_machinery = data.get ("investment_imported_second_hand_machinery") if data.get("investment_imported_second_hand_machinery") else None
                    investment_refurbishment_before_expansion = data.get ("investment_refurbishment_before_expansion") if data.get("investment_refurbishment_before_expansion") else None
                    investment_refurbishment=data.get ("investment_refurbishment") if data.get("investment_refurbishment") else None
                    other_assets_remark = data.get("other_assets_remark") if data.get("other_assets_remark") else None

                    if employees_from_mp and employees_outside_mp and total_employee:
                        employment_instance, created = InCAFEmployment.objects.update_or_create(
                            caf=incentivecafid,
                            defaults={
                                "employees_from_mp": employees_from_mp,
                                "employees_outside_mp": employees_outside_mp,
                                "total_employee": total_employee,
                                "employee_from_mp_before_expansion": employees_from_mp_before_expansion,
                                "employees_outside_mp_before_expansion": employees_outside_mp_before_expansion,
                                "total_employee_before_expansion": total_employee_before_expansion,
                                "employee_domicile_percentage": employee_domicile_percentage,
                                "employee_domicile_percentage_before_expansion" : employee_domicile_percentage_before_expansion,
                                "number_of_differently_abled_employees" : number_of_differently_abled_employees,
                                "percentage_of_differently_abled_employees" : percentage_of_differently_abled_employees
                            }
                        )
                    
                    power_details = request.data.get("power_details", {})
            
                    if power_details:

                        load_consumption = self.to_decimal(power_details.get("load_consumption"))
                        existing_load = self.to_decimal(power_details.get("existing_load"))
                        additional_load = self.to_decimal(power_details.get("additional_load"))
                        date_additional_load = power_details.get("date_additional_load") or None

                        incaf_power, created = InCAFPower.objects.update_or_create(
                            caf=incentivecafid,
                            defaults={
                                "connection_type": power_details.get("connection_type", ""),
                                "ht_contract_demand": power_details.get("ht_contract_demand", ""),
                                "date_of_connection": power_details.get("date_of_connection"),
                                "load_consumption": load_consumption,
                                "existing_load": existing_load,
                                "additional_load": additional_load,
                                "date_additional_load": date_additional_load,
                                "date_of_connection_before_expansion" : self.to_date(power_details.get("date_of_connection_before_expansion", None)),
                                "connection_type_before_expansion": power_details.get("connection_type_before_expansion", None),
                                "power_load_before_expansion" : self.to_decimal(power_details.get("power_load_before_expansion", None)),
                                "meter_before_expansion" : power_details.get("meter_before_expansion", None),
                                "meter_details": power_details.get("meter_details",None),
                                "enhancement_load_date": self.to_date(power_details.get("enhancement_load_date", None))
                            }
                        )

                        is_supplementary_load = request.data.get("is_supplementary_load")
                        power_load_details = request.data.get("power_load_details", [])


                        if power_load_details:
                                InCAFPowerLoad.objects.filter(caf_id=incentivecafid.id).delete()
                                for load in power_load_details:

                                    supplementary_load = self.to_decimal(load.get("supplementary_load"))
                                    supplementary_load_date = self.to_date(load.get("supplementary_load_date"))

                                    InCAFPowerLoad.objects.create(
                                            caf=incentivecafid,
                                            supplementary_load=supplementary_load,
                                            supplementary_load_date=supplementary_load_date,
                                            is_supplementary_load = is_supplementary_load

                                        )                        

                        else:
                            InCAFPowerLoad.objects.filter(caf=incentivecafid).delete()

                        submeter_details = request.data.get("submeter_details", [])
                        if submeter_details:
                            InCAFSubMeter.objects.filter(caf_id=incentivecafid.id).delete()
                            for meter in submeter_details:
                                InCAFSubMeter.objects.create(
                                    caf=incentivecafid,
                                    meter_number=meter.get("meter_number")
                                )
                        else:
                            InCAFSubMeter.objects.filter(caf=incentivecafid).delete()
                    
                    created = InCAFInvestment.objects.update_or_create(
                        caf=incentivecafid,
                        defaults={ 
                            "investment_in_building": investment_in_building,
                            "total_investment_amount": total_investment_amount,
                            "total_investment_land": total_investment_land,
                            "investment_in_plant_machinery": investment_in_plant_machinery,
                            "total_investment_other_asset":total_investment_other_asset,
                            "investment_land_before_expansion": investment_land_before_expansion,
                            "investment_in_plant_machinery_before_expansion": investment_in_plant_machinery_before_expansion,
                            "investment_in_building_before_expansion": investment_in_building_before_expansion,
                            "investment_other_asset_before_expansion": investment_other_asset_before_expansion,
                            "total_investment_amount_before_expansion": total_investment_amount_before_expansion,
                            "investment_furniture_fixtures": investment_furniture_fixtures,
                            "investment_in_house_before_expansion": investment_in_house_before_expansion,
                            "investment_in_house": investment_in_house,
                            "investment_captive_power_before_expansion":investment_captive_power_before_expansion,
                            "investment_captive_power":investment_captive_power,
                            "investment_energy_saving_devices_before_expansion":investment_energy_saving_devices_before_expansion,
                            "investment_energy_saving_devices": investment_energy_saving_devices,
                            "investment_imported_second_hand_machinery_before_expansion":investment_imported_second_hand_machinery_before_expansion,
                            "investment_imported_second_hand_machinery": investment_imported_second_hand_machinery,
                            "investment_refurbishment_before_expansion":investment_refurbishment_before_expansion,
                            "investment_refurbishment": investment_refurbishment,
                            "other_assets_remark": other_assets_remark
                        }
                    )
                    products = data.get("products", [])
                    if products or existing_products:
                        if products:
                            InCAFProduct.objects.filter(caf_id=incentivecafid.id).delete()

                            if isinstance(products, dict):
                                products = [products]

                            product_instances = []
                            # InCAFExpansionProduct.objects.filter(caf_id=incentivecafid.id).delete()
                            for product in products:
                                product["caf"] = incentivecafid.id

                                measurement_unit_id = product.get("measurement_unit")
                                measurementUnitList = MeasurementUnitList.objects.filter(id=measurement_unit_id).first()

                                if measurement_unit_id:
                                    product["measurement_unit"] = measurement_unit_id
                                    product["measurement_unit_name"] = ""
                                    if measurementUnitList:
                                        product["measurement_unit_name"] = measurementUnitList.name

                                custom_measurement_unit = product.get("custom_measurement_unit")
                                if custom_measurement_unit:
                                    product["other_measurement_unit_name"] = custom_measurement_unit
                                else:
                                    product["other_measurement_unit_name"] = None

                                product_type = product.get("product_type", "New")
                                product["product_type"] = product_type
                        
                                serializer = InCAFProductSerializer(data=product)
                                if serializer.is_valid():
                                    product_instances.append(serializer.save())
                                else:
                                    return Response({"status": False, "message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
                                
                        if existing_products:
                            if isinstance(existing_products, dict):
                                existing_products = [existing_products]

                            existing_products_instances = []
                            # InCAFProduct.objects.filter(caf_id=incentivecafid.id).delete()
                            for existing_product in existing_products:
                                if existing_product.get("product_name"):
                                    existing_product["caf"] = incentivecafid.id

                                    measurement_unit_id = existing_product.get("measurement_unit")

                                    if measurement_unit_id:
                                        measurementUnitList = MeasurementUnitList.objects.filter(id=measurement_unit_id).first()
                                        existing_product["measurement_unit"] = measurement_unit_id
                                        existing_product["measurement_unit_name"] = ""
                                        if measurementUnitList:
                                            existing_product["measurement_unit_name"] = measurementUnitList.name

                                    custom_measurement_unit = existing_product.get("custom_measurement_unit")
                                    if custom_measurement_unit:
                                        existing_product["other_measurement_unit_name"] = custom_measurement_unit
                                    else:
                                        existing_product["other_measurement_unit_name"] = None

                                    product_type = existing_product.get("product_type", "New")
                                    existing_product["product_type"] = product_type
                            
                                    serializer = InCAFProductSerializer(data=existing_product)
                                    if serializer.is_valid():
                                        existing_products_instances.append(serializer.save())
                                    else:
                                        return Response({"status": False, "message": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

                            
                            # Handle Expansion Products
                    expansion_product = data.get("expansion_product", [])

                    if expansion_product:
                        with transaction.atomic():
                            for item in expansion_product:
                                item_product = item.get("products", [])
                                expansion_id = item.get("expansion_id")
                                if item_product and expansion_id:
                                    expansion_instance = InCAFExpansion.objects.filter(id=expansion_id).first()
                                    if not expansion_instance:
                                        continue
                                    InCAFExpansionProduct.objects.filter(expansion=expansion_instance).delete()
                                    for exp_product in item_product:
                                        product_name = exp_product.get("product_name")
                                        exp_measurement_unit_id = exp_product.get("measurement_unit")
                                        exp_unit = MeasurementUnitList.objects.filter(id=exp_measurement_unit_id).first()
                                        InCAFExpansionProduct.objects.update_or_create(
                                            expansion=expansion_instance,
                                            product_name=product_name,
                                            defaults={
                                                "total_annual_capacity": exp_product.get("total_annual_capacity"),
                                                "annual_capacity_before_expansion": exp_product.get("annual_capacity_before_expansion"),
                                                "annual_capacity_during_expansion": exp_product.get("annual_capacity_during_expansion"),
                                                "other_measurement_unit_name": exp_product.get("other_measurement_unit_name"),
                                                "measurement_unit_id": exp_product.get("measurement_unit"),
                                                "measurement_unit_name": exp_unit.name if exp_unit else "",
                                            }
                                        )   
                    else:
                        expansions = InCAFExpansion.objects.filter(caf=incentivecafid)
                        InCAFExpansionProduct.objects.filter(expansion__in=expansions).delete()

                    self.create_activity_history(
                        caf_instance=incentivecafid,
                        user_name=request.user,
                        user_role=getattr(request.user, 'role', 'Unknown'),
                        ip_address=request.META.get("REMOTE_ADDR"),
                        activity_status="Other Details Submitted",
                        caf_status=incentivecafid.status,
                        status_remark="All other Details captured successfully.",
                        activity_result="Success",
                    )
                    return Response({"status": True, "message": "Products Details Created Successfully."})
            return Response(
                {
                    "status": False,
                    "message": message,
                    "data":{}
                },
                status=status.HTTP_400_BAD_REQUEST,
            )


class IntentionDetailsListView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            user_roles = UserHasRole.objects.filter(user=user).select_related('role')

            investor_role = Role.objects.filter(role_name="Investor").first()
            is_investor = investor_role in [ur.role for ur in user_roles]

            if is_investor:
                return Response({
                    "status": False,
                    "message": "You are not authorized to view this Intention Details."
                }, status=status.HTTP_400_BAD_REQUEST)

            caf_id = request.query_params.get("caf_id")
            
            if caf_id:
                caf_instance = IncentiveCAF.objects.filter(id=caf_id).first()
                intention_instance = caf_instance.intention

            if not intention_instance:
                return Response({
                    "status": False,
                    "message": "CustomerIntentionProject not found for this CAF."
                }, status=status.HTTP_400_BAD_REQUEST)

            serializer = CustomerIntentionProjectListSerializer(intention_instance).data
            serializer['is_agenda_filled'] = False
            is_agenda_data = IncentiveAgenda.objects.filter(caf_id=caf_id).first()
            if is_agenda_data:
                serializer['is_agenda_filled'] = True

            return Response({
                "status": True,
                "message": "Customer Intention Details fetched successfully.",
                "data": serializer
            })
        
        except Exception as e:
            return Response({
                "status": False,
                "message": global_err_message
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class ViewCafDocumentsView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self,request):       

        try:
            user = request.user
            caf_id =request.query_params.get("caf_id")
            if not caf_id:
                return Response({"status": False, "message": "caf_id is required."}, status=status.HTTP_400_BAD_REQUEST)
            
            is_investor = UserHasRole.objects.filter(user=user, role__role_name="Investor").exists()
            caf_instance = IncentiveCAF.objects.filter(id=caf_id).first()
            if is_investor and caf_instance.intention and caf_instance.intention.user and caf_instance.intention.user_id != user.id:
                return Response({
                    "status":False,
                    "message":"You are not authorized to view this."
                },status=status.HTTP_400_BAD_REQUEST)
            
            
            incafdocuments=InCAFDocuments.objects.filter(caf_id=caf_id)
            Incentivecaf=IncentiveCAF.objects.filter(id=caf_id).first()

            serializers=InCAFDocumentsPdfSerializer(incafdocuments,many=True)
            IncentiveCAF_serializers=IncentiveCAFPdfSerializer(Incentivecaf,many=False)

            CAFCreationpdf=CAFCreationPDF.objects.filter(caf_id=caf_id).first()
            CAFCreationPDF_serializer=CAFCreationPDFSerializer(CAFCreationpdf,many=False)  
            caf_pdf_data = IncentiveCAF_serializers.data.get("caf_pdf_url") if Incentivecaf else ""
            intention_pdf_data = CAFCreationPDF_serializer.data.get("pdf_url") if CAFCreationpdf else ""
            minio_caf_pdf_url=""
            if (caf_pdf_data != ""):
                pdf_file = minio_func(caf_pdf_data)
                if pdf_file[0]:
                    minio_caf_pdf_url = pdf_file[1]["Fileurl"]
                
            intention_pdf_url=""
            if (intention_pdf_data != ""):
                minio_intention_pdf_url=minio_func(intention_pdf_data)
                if minio_intention_pdf_url[0]:
                    intention_pdf_url=pdf_file[1]["Fileurl"]
               
            for item in serializers.data:
                if item["document_path"]:
                    doc_=item["document_path"]
                    minio_url=minio_func(doc_)
                    if minio_url[0]:
                        item["document_path"] = minio_url[1]["Fileurl"]
              
            return Response({
                "status":True,
                "message":"Documents retrived successfully.",
                "data":{"documents":serializers.data,
                        "caf_pdf_url": minio_caf_pdf_url,
                        "intention_pdf_url":intention_pdf_url}
                
                
            },status=200)
            
        except Exception as e:
            return Response({"status": False, "message": global_err_message},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class IncentiveAuditLogListView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            caf_id = request.query_params.get("caf_id")
            if not caf_id:
                return Response({
                    "status": False,
                    "message": "CAF ID is required."
                }, status=status.HTTP_400_BAD_REQUEST)

            logs = IncentiveAuditLog.objects.filter(caf_id=caf_id).order_by('-created_at')
            try:
                page = int(request.query_params.get("page", 1))
                limit = int(request.query_params.get("limit", 10))
            except ValueError:
                return Response({
                    "status": False,
                    "message": "Invalid page or limit."
                }, status=status.HTTP_400_BAD_REQUEST)

            paginator = Paginator(logs, limit)
            try:
                paginated_logs = paginator.page(page)
            except EmptyPage:
                return Response({
                    "status": False,
                    "message": "Page out of range."
                }, status=status.HTTP_400_BAD_REQUEST)

            serializer = IncentiveAuditLogSerializer(paginated_logs, many=True)
            return Response({
                "status": True,
                "message": "Audit logs fetched successfully.",
                "page": page,
                "limit": limit,
                "total": paginator.count,
                "data": serializer.data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "status": False,
                "message": "An error occurred while fetching audit logs.",
                "error": global_err_message,
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class IncentiveActivityHistoryListView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            caf_id = request.query_params.get("caf_id")

            if not caf_id:
                return Response({
                    "status": False,
                    "message": "CAF ID is required."
                }, status=status.HTTP_400_BAD_REQUEST)

            activity_logs = IncentiveActivityHistory.objects.filter(
                caf_id=caf_id
            ).order_by('-created_at')

            try:
                page = int(request.query_params.get("page", 1))
                limit = int(request.query_params.get("limit", 10))
            except ValueError:
                return Response({
                    "status": False,
                    "message": "Invalid page or limit."
                }, status=status.HTTP_400_BAD_REQUEST)

            paginator = Paginator(activity_logs, limit)
            try:
                paginated_logs = paginator.page(page)
            except EmptyPage:
                return Response({
                    "status": False,
                    "message": "Page out of range."
                }, status=status.HTTP_400_BAD_REQUEST)            

            serializer = IncentiveActivityHistorySerializer(paginated_logs, many=True)

            return Response({
                "status": True,
                "message": "Activity history fetched successfully.",
                "page": page,
                "limit": limit,
                "total": paginator.count,
                "data": serializer.data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "status": False,
                "message": global_err_message,
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class IncentiveCalculatorDynamicView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        sector_id = request.query_params.get("sector_id")
        message = "sector_id is required"
        if sector_id:
            records = SectorIncentiveList.objects.filter(
                sector_id=sector_id,
                status="active"
            ).order_by("display_order")

            header_mapping = {}
            message = "Data is not exists"
            data = []
            if records.exists():
                for record in records:
                    try:
                        input_options = json.loads(record.input_options) if record.input_options else []
                    except json.JSONDecodeError:
                        input_options = []

                    field_data = {
                        "input_tag": record.input_tag,
                        "input_type": record.input_type,
                        "title": record.title,
                        "input_options": input_options,
                        "placeholder": record.placeholder,
                        "display_options": record.display_options,
                    }

                    if record.main_header not in header_mapping:
                        header_mapping[record.main_header] = {
                            "main_header": record.main_header,
                            "fields": []
                        }

                    header_mapping[record.main_header]["fields"].append(field_data)
                    message = "Data fetch successfully"
                    data = list(header_mapping.values())
            return Response({
                "success": True,
                "message": message,
                "data": data,
            }, status=status.HTTP_200_OK)

        return Response({
            "success": False,
            "message": message,
            "data": []
        }, status=status.HTTP_400_BAD_REQUEST)
    

class IncentiveGenerateView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data
        department_user = request.user
        mandatory_fields = ['user','intention_id', 'intention_date', 'unit_name','unit_type', 'date_of_production',
                            'activity','sector','eligibility_start_date','eligibilty_end_date','products','bipa',
                            'block_priority','ybipa','eligible_investment','slec_meeting_date','slec_meeting_number']

        missing_fields = [field for field in mandatory_fields if not data.get(field)]
        if missing_fields:
            message = f"Missing required fields: {', '.join(missing_fields)}"
        else:
            intention_id = data.get("intention_id")
            intention_data = CustomerIntentionProject.objects.filter(intention_id = intention_id).first()
            message = "data inserted successfully"
            intention_date = parse_and_format_date(data.get("intention_date"))
            production_date = parse_and_format_date(data.get("date_of_production"))
            period_from = parse_and_format_date(data.get("eligibility_start_date"))
            period_to = parse_and_format_date(data.get("eligibilty_end_date"))
            products = data.get("products", [])
            unit_name = data.get("unit_name")
            unit_type = data.get("unit_type")
            block_priority = data.get("block_priority")
            eligible_investment = data.get("eligible_investment")
            bipa = data.get("bipa")
            ybipa = data.get("ybipa")
            slec_meeting_date = parse_and_format_date(data.get("slec_meeting_date")).strip()
            slec_meeting_number = data.get("slec_meeting_number").strip()
            user = User.objects.filter(id=data.get("user")).first()
            department_user = CustomUserProfile.objects.filter(user_id=department_user.id).first()
            if not user:
                user = None
            activity = Activity.objects.filter(id=data.get("activity")).first()
            if activity:
                sector =Sector.objects.filter(id=data.get("sector"), activity=activity).first()
                if not sector:
                    sector = None
            else:
                activity = None
                sector = None
            with transaction.atomic():
                if not intention_data:
                    intention_data = CustomerIntentionProject.objects.create(
                        intention_id=intention_id,
                        user= user,
                        created_at= intention_date,
                        product_name= unit_name,
                        company_name = unit_name,
                        investment_type=unit_type,
                        product_proposed_date= production_date,
                        sectors= sector,
                        activities=activity,
                        activity = activity.name if activity else "",
                        sector = sector.name if sector else "",
                        intention_type= "incentive",
                        status="new"
                    )
                slec_caf_data = True
                all_caf_data = IncentiveCAF.objects.filter(intention_id=intention_data.id).order_by("id")
                if all_caf_data.exists():
                    for caf in all_caf_data:
                        caf_slec_data = IncentiveSlecOrder.objects.filter(caf=caf, 
                            date_of_slec_meeting=slec_meeting_date,
                            slec_meeting_number=slec_meeting_number).first()
                        if caf_slec_data:
                            slec_caf_data = False
                            message = "slec exist with same date and meeting number"
                            break
                        else:
                            caf.status = "Approve Sanction Order"
                            caf.save()
                if slec_caf_data:
                    caf_data = IncentiveCAF.objects.create(
                        intention_id=intention_data.id,
                        user= user,
                        status="Completed",
                        acknowledgement=True,
                        acknowledgement_date=intention_date,
                        is_offline=True
                    )

                    caf_project_data = InCAFProject.objects.create(
                        unit_name=data.get("unit_name"),
                        intention_id=intention_id,
                        date_of_intention=intention_date,
                        address_of_unit=data.get("unit_name"),
                        sector= sector,
                        activity=activity,
                        activity_name = activity.name if activity else "",
                        sector_name = sector.incentive_name if sector else "",
                        unit_type=unit_type,
                        caf=caf_data
                    )

                    caf_investment_data = InCAFInvestment.objects.create(
                        comm_production_date=production_date,
                        caf=caf_data
                    )

                    caf_agenda_data = IncentiveAgenda.objects.create(
                        comm_production_date=production_date,
                        created_user_name=department_user.name,
                        unit_name=unit_name,
                        address_of_unit=unit_name,
                        category_of_block=block_priority,
                        sector= sector,
                        activity=activity,
                        activity_name = activity.name if activity else "",
                        sector_name = sector.name if sector else "",
                        application_filling_date=intention_date,
                        first_production_year = get_year_from_date(period_from),
                        unit_type = unit_type,
                        eligible_investment_plant_machinery=eligible_investment,
                        bipa=bipa,
                        yearly_bipa=ybipa,
                        ipp="IPA-2014",
                        caf=caf_data,
                        status="Approved"
                    )

                    caf_slec_data = IncentiveSlecOrder.objects.create(
                        commencement_date=production_date,
                        unit_name=unit_name,
                        unit_type=unit_type,
                        sector= sector,
                        activity=activity,
                        activity_name = activity.name if activity else "",
                        sector_name = sector.name if sector else "",
                        category_of_block=block_priority,
                        date_of_slec_meeting=slec_meeting_date,
                        slec_meeting_number=slec_meeting_number,
                        eligible_investment_plant_machinery=eligible_investment,
                        bipa=bipa,
                        yearly_bipa=ybipa,
                        eligibility_from=period_from,
                        eligibility_to=period_to,
                        caf=caf_data,
                        status="Approved"
                    )

                    if products:
                        for prod in products:
                            if prod['name']:
                                caf_product_data = InCAFProduct.objects.create(
                                    product_name=prod['name'],
                                    caf=caf_data
                                )

                                caf_agenda_product_data = IncentiveAgendaProduct.objects.create(
                                    product_name=prod['name'],
                                    agenda=caf_agenda_data,
                                    comm_production_date=production_date
                                )

                                caf_slec_product_data = IncentiveSlecProduct.objects.create(
                                    product_name=prod['name'],
                                    slec_order=caf_slec_data,
                                    comm_production_date=production_date
                                )
                current_financial_year = get_current_financial_year()
                if caf_slec_data:
                    claim_details = data.get("claim_details", [])
                    if claim_details:
                        cnt = 1
                        for cfy in claim_details:
                            if current_financial_year == cfy['financial_year']:
                                caf_data.status ="Pending For Request Claim"
                                caf_data.save()
                            sanction_data = cfy['sanction_details']
                            caf_slec_year_data = IncentiveSlecYealy.objects.filter(slec_order=caf_slec_data,incentive_year=cfy['financial_year']).first()
                            if not caf_slec_year_data:
                                caf_slec_year_data = IncentiveSlecYealy.objects.create(
                                    slec_order=caf_slec_data,
                                    incentive_year=cfy['financial_year'],
                                    claim_year_serial_number=cnt
                                )
                            
                            claim_basic_data = IncentiveClaimBasic.objects.filter(incentive_slec_year_id=caf_slec_year_data.id,
                                    year_of_claimed_assistance=cfy['financial_year']).first()
                            if not claim_basic_data:
                                claim_basic_data = IncentiveClaimBasic.objects.create(
                                    year_of_claimed_assistance=cfy['financial_year'],
                                    acknowledgement=True,
                                    acknowledgement_date=timezone.now(),
                                    status='Submitted',
                                    incentive_slec_year_id=caf_slec_year_data.id,
                                    action_date=timezone.now(),
                                    action_by_name = department_user.name,
                                    action_by_id = department_user.user_id,
                                    apply_date = timezone.now()
                                )
                            
                            if products:
                                for prod in products:
                                    if prod['name']:
                                        slec_product_data = IncentiveSlecProduct.objects.filter(
                                            product_name=prod['name'],
                                            slec_order=caf_slec_data
                                        ).first()
                                        if slec_product_data:
                                            claim_product_data = IncentiveClaimProductDetail.objects.filter(
                                                incentive_slec_product= slec_product_data,
                                                incentive_claim_basic=claim_basic_data
                                            )
                                            if not claim_product_data:
                                                claim_product_data= IncentiveClaimProductDetail.objects.create(
                                                    incentive_slec_product= slec_product_data,
                                                    incentive_claim_basic=claim_basic_data,
                                                    action_date=timezone.now(),
                                                    action_by_name = department_user.name,
                                                    action_by_id = department_user.user_id,
                                                    apply_date = timezone.now(),
                                                )

                            cnt = cnt + 1
                            if sanction_data:
                                for sanction in sanction_data:
                                    if sanction['sanction_date'] and sanction['sanction_amount']:
                                        sanction_date = parse_and_format_date(sanction['sanction_date']).strip()
                                        incentive_sanction_order = IncentiveSanctionOrder.objects.filter(
                                            incentive_claim=claim_basic_data,
                                            sanction_order_created_date=sanction_date,
                                            total_sanctioned_assistance_amount= sanction['sanction_amount'],
                                            intention = intention_data,
                                            year_of_claimed_assistance=cfy['financial_year'],
                                            incentive_caf=caf_data
                                        ).first()
                                        if not incentive_sanction_order:
                                            incentive_sanction_order = IncentiveSanctionOrder.objects.create(
                                                incentive_claim=claim_basic_data,
                                                sanction_order_created_date=sanction_date,
                                                unit_name = unit_name,
                                                total_sanctioned_assistance_amount= sanction['sanction_amount'],
                                                is_old_record = True,
                                                acknowledgement=True,
                                                acknowledgement_date=timezone.now(),
                                                status='Approved',
                                                action_date=timezone.now(),
                                                sanction_order_create_by_name = department_user.name,
                                                intention = intention_data,
                                                sanction_order_create_by = department_user.user_id,
                                                year_of_claimed_assistance = cfy['financial_year'],
                                                incentive_caf=caf_data
                                            )
                                        disbursement_data = sanction['disbursement_details']   
                                        if disbursement_data:
                                            for disbursement in disbursement_data:
                                                if disbursement['disbursement_date'] and disbursement['disbursement_amount']:
                                                    disbursement_date = parse_and_format_date(disbursement['disbursement_date']).strip()
                                                    sanction_disbursement_data = IncentiveDisbursement.objects.filter(
                                                        incentive_sanction_order=incentive_sanction_order,
                                                        disbursement_date=disbursement_date,
                                                        disbursed_amount= disbursement['disbursement_amount'],
                                                        intention = intention_data,
                                                        year_of_claimed_assistance=cfy['financial_year']
                                                    ).first()
                                                    if not sanction_disbursement_data:
                                                        incentive_sanction_order = IncentiveDisbursement.objects.create(
                                                            incentive_sanction_order=incentive_sanction_order,
                                                            disbursement_date=disbursement_date,
                                                            disbursed_amount= disbursement['disbursement_amount'],
                                                            intention = intention_data,
                                                            year_of_claimed_assistance=cfy['financial_year'],
                                                            action_date=timezone.now(),
                                                            action_by_name = department_user.name,
                                                            action_by = department_user.user_id,
                                                        )

                return Response({
                    "success": True,
                    "message": message,
                    "data": data,
                }, status=status.HTTP_200_OK)
        return Response({
            "success": False,
            "message": message,
            "data": []
        }, status=status.HTTP_400_BAD_REQUEST)


def get_year_from_date(date):
    try:
        dt = datetime.fromisoformat(str(date))
        return dt.strftime("%Y")
    except Exception:
        return None 

def generate_financial_years(period_from: str, period_to: str, request_type: str):
    from_date = datetime.strptime(period_from, "%Y-%m-%d")

    # Determine financial year starting from 1-April
    start_year = from_date.year if from_date.month >= 4 else from_date.year - 1

    financial_years = []

    if request_type == "all":
        for i in range(7):
            fy = f"{start_year + i}-{str(start_year + i + 1)[-2:]}"
            financial_years.append(fy)
    else:
        # Optional logic if not "all" (keep previous behavior)
        current_year = datetime.now().year
        limit_year = current_year - 1 if datetime.now().month >= 4 else current_year - 2

        for year in range(start_year, limit_year + 1):
            fy = f"{year}-{str(year + 1)[-2:]}"
            financial_years.append(fy)

    return financial_years


class IncentiveGenerateYearView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        start_date = request.query_params.get("eligibility_start_date")
        end_date = request.query_params.get("eligibilty_end_date")
        request_type = request.query_params.get("request_type")
        message = "start_date and end_date  is required"
        if start_date and end_date:
            slec_year_create = generate_financial_years(start_date, end_date, request_type)
            message = "Data required successfully"
            return Response({
                "success": True,
                "message": message,
                "data": slec_year_create,
            }, status=status.HTTP_200_OK)

        return Response({
            "success": False,
            "message": message,
            "data": []
        }, status=status.HTTP_400_BAD_REQUEST)


class IncentiveClaimDataView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self,request):
        data=request.data
        intention_id=data.get("intention_id")
        claim_data = data.get("claim_details", [])
        department_user = request.user
        department_user = CustomUserProfile.objects.filter(user_id=department_user.id).first()
        message = "Intention and claim details is needed"
        if intention_id and claim_data:
            intention_data = CustomerIntentionProject.objects.filter(intention_id = intention_id).first()
            message = "Intention data is not found"
            if intention_data:
                latest_caf = IncentiveCAF.objects.filter(intention_id=intention_data.id).order_by("-id")
                message = "No CAF Found"
                if latest_caf.exists():
                    new_slec = {}
                    for caf in latest_caf:
                        current_slec = IncentiveSlecOrder.objects.filter(caf=caf).first()
                        if not new_slec:
                            new_slec = current_slec
                        elif new_slec.date_of_slec_meeting < current_slec.date_of_slec_meeting:
                            new_slec = current_slec
                    with transaction.atomic():
                        get_slec_product = IncentiveSlecProduct.objects.filter(slec_order=new_slec)
                        if get_slec_product.exists():
                            slec_ids = get_slec_product.values_list('id', flat=True)
                            IncentiveClaimProductDetail.objects.filter(incentive_slec_product_id__in=slec_ids).delete()
                            get_slec_product.delete()
                        for claim in claim_data:
                            year = claim['financial_year']
                            employees_outside_of_mp = claim['employees_outside_of_mp']
                            employees_permanent_resident_of_mp = claim['employees_permanent_resident_of_mp']
                            total_employees = claim['total_employees']
                            products = claim['product_details']
                            get_slec_year = IncentiveSlecYealy.objects.filter(
                                incentive_year=year,
                                slec_order=new_slec
                            ).first()
                            if get_slec_year:
                                get_claim = IncentiveClaimBasic.objects.filter(
                                    year_of_claimed_assistance=year,
                                    incentive_slec_year=get_slec_year,
                                ).first()
                                if get_claim:
                                    get_claim.employees_permanent_resident_of_mp = employees_permanent_resident_of_mp
                                    get_claim.employees_outside_of_mp = employees_outside_of_mp
                                    get_claim.total_employees = total_employees
                                    get_claim.action_by_id = department_user.user_id
                                    get_claim.action_by_name = department_user.name
                                    get_claim.action_date = timezone.now()
                                    get_claim.save()
                                else:
                                    get_claim = IncentiveClaimBasic.objects.create(
                                        year_of_claimed_assistance=year,
                                        incentive_slec_year=get_slec_year,
                                        employees_permanent_resident_of_mp = employees_permanent_resident_of_mp,
                                        employees_outside_of_mp = employees_outside_of_mp,
                                        total_employees = total_employees,
                                        action_by_id = department_user.user_id,
                                        action_by_name = department_user.name,
                                        action_date = timezone.now(),
                                        apply_date=timezone.now()
                                    )
                                if products:
                                    for prod in products:
                                        prod_name = prod['product_name']
                                        annual_capacity = prod['annual_capacity']
                                        export_quantity = prod['export_quantity']
                                        production_quantity = prod['production_quantity']
                                        measurement_unit_id = prod['measurement_unit_id']
                                        unit_obj = MeasurementUnitList.objects.filter(id=measurement_unit_id).first() 
                                        if prod_name:
                                            get_slec_product = IncentiveSlecProduct.objects.filter(product_name=prod_name,
                                                slec_order=new_slec).first()
                                            if not get_slec_product:
                                                get_slec_product = IncentiveSlecProduct.objects.create(
                                                    product_name=prod_name,
                                                    slec_order=new_slec,
                                                    total_annual_capacity=annual_capacity,
                                                    measurement_unit = unit_obj if unit_obj else None,
                                                    measurement_unit_name = unit_obj.name if unit_obj else None,
                                                )
                                            if get_slec_product:
                                                get_claim_product = IncentiveClaimProductDetail.objects.create(
                                                    incentive_slec_product = get_slec_product,
                                                    incentive_claim_basic = get_claim,
                                                    production_quantity = production_quantity,
                                                    export_quantity = export_quantity,
                                                    total_annual_capacity = annual_capacity,
                                                    measurement_unit = unit_obj if unit_obj else None,
                                                    measurement_unit_name = unit_obj.name if unit_obj else None,
                                                    action_by_id = department_user.user_id,
                                                    action_by_name = department_user.name,
                                                    action_date = timezone.now()
                                                )

                        return Response({
                            "status": True,
                            "message": "Claim data saved successfully."
                        }, status=status.HTTP_201_CREATED)
                
        return Response(
            {
                "status":False,
                "message":message,
                "data": []
            },status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    def get(self,request):
        intention_id=request.query_params.get("intention_id")
        department_user = request.user
        department_user = CustomUserProfile.objects.filter(user_id=department_user.id).first()
        message = "Parameter is needed"
        if intention_id:
            intention_data = CustomerIntentionProject.objects.filter(intention_id = intention_id).first()
            message = "Intention data is not found"
            data = []
            empty_product =  {
                "product_name": "",
                "annual_capacity": "",
                "export_quantity": "",
                "production_quantity": "",
                "measurement_unit_id": ""
            }
            if intention_data:
                latest_caf = IncentiveCAF.objects.filter(intention_id=intention_data.id).order_by("-id")
                message = "No CAF Found"
                if latest_caf.exists():
                    new_slec = {}
                    for caf in latest_caf:
                        current_slec = IncentiveSlecOrder.objects.filter(caf=caf).first()
                        if not new_slec:
                            new_slec = current_slec
                        elif new_slec.date_of_slec_meeting < current_slec.date_of_slec_meeting:
                            new_slec = current_slec
                    get_slec_year = IncentiveSlecYealy.objects.filter(
                        slec_order=new_slec
                    ).order_by("incentive_year")
                    if get_slec_year.exists():
                        for slec_year in get_slec_year:
                            claims = IncentiveClaimBasic.objects.filter(incentive_slec_year=slec_year).first()
                            claim_data = {}
                            if claims:
                                claim_data['financial_year'] = claims.year_of_claimed_assistance
                                claim_data["employees_outside_of_mp"]= claims.employees_outside_of_mp
                                claim_data["employees_permanent_resident_of_mp"]= claims.employees_permanent_resident_of_mp
                                claim_data["total_employees"] = claims.total_employees
                                claim_data["employee_percentage"] = round((claims.employees_permanent_resident_of_mp/claims.total_employees) * 100, 2) if claims.employees_permanent_resident_of_mp and claims.employees_outside_of_mp else None
                                claim_product_data = IncentiveClaimProductDetail.objects.filter(incentive_claim_basic=claims)
                                claim_data['product_details'] = []
                                if claim_product_data.exists():
                                    for claim_product in claim_product_data:
                                        claim_prod = {
                                            "product_name": claim_product.incentive_slec_product.product_name if claim_product.incentive_slec_product else "",
                                            "annual_capacity": claim_product.total_annual_capacity if claim_product.total_annual_capacity else 0,
                                            "export_quantity": claim_product.export_quantity if claim_product.export_quantity else 0,
                                            "production_quantity": claim_product.production_quantity if claim_product.production_quantity else 0,
                                            "measurement_unit_id": claim_product.measurement_unit.id if claim_product.measurement_unit else "",
                                        }
                                        claim_data["product_details"].append(claim_prod)
                                else:
                                    claim_data['product_details'].append(empty_product)
                                data.append(claim_data)
                                message="Data retrived successfully"
        
        if not data:
            empty_obj = {
                'financial_year': "",
                "employees_outside_of_mp": "",
                "employees_permanent_resident_of_mp": "",
                "total_employees": "",
                "employee_percentage": "",
                "product_details": []
            }
            empty_obj['product_details'].append(empty_product)
            data.append(empty_obj)
                
        return Response({
            "status": True,
            "message": message,
            "data":data 
        }, status=status.HTTP_200_OK)


class OfflineIntentionDataView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        data = []
        distinct_intention_ids = IPAUnitDataMaster.objects.order_by('intention_id').distinct('intention_id')
        message = "Data retrived successfully"
        if distinct_intention_ids.exists():
            data = IPAIntentionSerializer(distinct_intention_ids, many=True).data
        return Response({
            "success": True,
            "message": message,
            "data": data,
        }, status=status.HTTP_200_OK)

class OfflineIncentiveDataView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        intention_id = request.query_params.get("intention_id")
        message = "Parameter missing"
        result = {}
        if intention_id:
            
            data = IPAUnitDataMaster.objects.filter(intention_id=intention_id).order_by("-slec_meeting_date").first()
            message = "Data not found"
            if data:
                result = IPAUnitDataMasterSerializer(data).data
                result['slec_meeting_number'] = result['slec_meeting_no']
                result.pop('slec_meeting_no')
                message = "Data retrived successfully"
        if not result:
            result = {
                "intention_id": intention_id,
                "intention_date": "",
                "unit_name": "",
                "date_of_production": "",
                "unit_type": "",
                "activity": "",
                "sector": "",
                "block_priority": "",
                "slec_meeting_date": "",
                "eligible_investment": "",
                "bipa": "",
                "ybipa": "",
                "eligibility_start_date": "",
                "eligibility_end_date": "",
                "slec_meeting_number": ""
            }
        return Response({
            "success": True,
            "message": message,
            "data": result,
        }, status=status.HTTP_200_OK)
        
class IncentiveQueryDataView(APIView, IncentiveApprovalMixin):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        intention_id = request.query_params.get("intention_id")
        query_type = request.query_params.get("type")
        message = "Parameter missing"
        result = []

        if intention_id and query_type:
            message = "Data not found"
            data = IncentiveDepartmentQueryModel.objects.filter(
                intention_id=intention_id,
                user_id=user.id,
                query_type=query_type,
                status="In-Progress"
            ).order_by("-updated_at")  

            if data.exists():
                result = IncentiveDepartmentQuerySerializer(data, many=True).data
                message = "Data retrieved successfully"

            return Response({
                "success": True,
                "message": message,
                "data": result,
            }, status=status.HTTP_200_OK)

        return Response({
            "success": False,
            "message": message,
            "data": result,
        }, status=status.HTTP_400_BAD_REQUEST)

    
    def put(self,request):
        try:
            user = request.user
            data = request.data

            query_id = data.get("id")
            remark = data.get("remark", "")
            documents = request.FILES.getlist("documents")
            message=''
            
            verify_query_id=IncentiveDepartmentQueryModel.objects.filter(id=query_id).first()
            message= "Invalid id"
            if verify_query_id and verify_query_id.user_id == user.id:
                user_profile = CustomUserProfile.objects.filter(user=user).first()
                verify_query_id.user_remark= remark
                verify_query_id.save()
                caf = verify_query_id.caf
                if documents:
                    file_folder_name = f"incentive_queries"
                    if user_profile:
                        file_folder_name = user_profile.document_folder if user_profile.document_folder else file_folder_name
                    minio_url = settings.MINIO_API_HOST + "/minio/uploads"
                    documents_to_upload = []
                    for file in documents:
                        documents_to_upload.append({
                            "file": file,
                            "document_name": file.name
                        })
                        upload_response = upload_files_to_minio(documents_to_upload, minio_url, file_folder_name)

                    if upload_response:
                        uploaded_files = upload_response["data"]

                        for i, file_info in enumerate(documents_to_upload):
                            IncentiveQueryDocumentModel.objects.create(
                                    query_id=verify_query_id.id,
                                    document_name=file_info["document_name"],
                                    document_path=uploaded_files[i]["path"]
                                )
                        incentive_workflow = WorkflowList.objects.filter(flow_type=verify_query_id.query_type, level_no=0).first()
                        if incentive_workflow:
                            sla_due_date = get_sla_date(incentive_workflow.sla_period)
                            caf.status = incentive_workflow.current_status
                            caf.sla_due_date = sla_due_date
                            caf.sla_days = incentive_workflow.sla_period
                            caf.current_approver_role = incentive_workflow.current_role
                            caf.save() 

                            self.create_incentive_approval_log(
                                caf=caf,
                                user_name=user_profile.name,
                                user_designation= "investor",
                                action= incentive_workflow.current_status, 
                                document_path= None,
                                remark=None,
                                next_approval_role= incentive_workflow.current_role,
                                sla_days=incentive_workflow.sla_period,
                                sla_due_date=sla_due_date
                            )
                        return Response({"status": True, "message": "Incentive query updated successfully."},
                            status=200)
                    else:
                        message= "Document failed saving in MinIO"
            return Response({"status": False, "message": message},
                            status=400)
            


        except Exception as e:
            return Response({
                "status": False,
                "message":global_err_message,
            }, status=500)
class IncentiveQueryDetailView(APIView):
    def get(self, request):
        query_type = request.query_params.get("query_type")
        caf_id = request.query_params.get("caf_id")

        if not query_type or not caf_id:
            return Response(
                {
                    "status": False,
                    "message": "query_type and caf_id are required.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Fetch all matching queries
        queries = IncentiveDepartmentQueryModel.objects.filter(
            query_type=query_type,
            caf_id=caf_id
        ).order_by("-updated_at")

        if queries.exists():
            serializer = IncentiveDepartmentQueryListSerializer(queries, many=True)
            data = serializer.data

            for query_item in data:
                documents = query_item.get("documents", [])
                for doc in documents:
                    doc_path = doc.get("document_path")
                    if doc_path and doc_path != "null":
                        minio_url = minio_func(doc_path)
                        if minio_url[0]:
                            doc["document_path"] = minio_url[1]["Fileurl"]

            return Response(
                {
                    "status": True,
                    "message": "Data retrieved successfully.",
                    "data": data,
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {
                "status": True,
                "message": "Data not found",
                "data": [],
            },
            status=status.HTTP_200_OK,
        )


def get_current_financial_year():
    today = date.today()
    year = today.year
    if today.month >= 4:
        start_year = year
        end_year = year + 1
    else:  # Jan, Feb, Mar
        start_year = year - 1
        end_year = year
    return f"{start_year}-{str(end_year)[-2:]}"

class InCAFSLECDocumentUploadView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
            
            user = request.user
            data = request.data

            slec_order_id = data.get('slec_order_id')
            documents = request.FILES.getlist('documents')
            message = ''

            slec_order = IncentiveSlecOrder.objects.filter(id=slec_order_id).first()
            message = 'Invalid slec_order_id.'
            if slec_order:
                caf = slec_order.caf
                file_folder_name = f"slec_docs_caf_{caf.id}"
                user_id = caf.intention.user
                if user_id:
                    user_profile = CustomUserProfile.objects.filter(user_id=user_id).first()
                    if user_profile:
                        file_folder_name = user_profile.document_folder if user_profile.document_folder else file_folder_name

                if documents:
                    minio_url = settings.MINIO_API_HOST + "/minio/uploads"
                    documents_to_upload = []

                    for file in documents:
                        documents_to_upload.append({
                            "file": file,
                            "document_name": file.name
                        })

                    upload_response = upload_files_to_minio(documents_to_upload, minio_url, file_folder_name)

                    if upload_response and upload_response.get("data"):
                        uploaded_files = upload_response["data"]

                        for i, file_info in enumerate(documents_to_upload):
                            existing_doc = InCAFSLECDocument.objects.filter(
                                caf=caf,
                                slec_order=slec_order,
                            ).first()

                            if existing_doc:
                                existing_doc.slec_doc_name = file_info["document_name"]
                                existing_doc.slec_doc_path = uploaded_files[i]["path"]
                                existing_doc.save()
                            else:
                                InCAFSLECDocument.objects.create(
                                    caf=caf,
                                    slec_order=slec_order,
                                    slec_doc_name=file_info["document_name"],
                                    slec_doc_path=uploaded_files[i]["path"]
                                )

                    else:
                        message = "Document failed to save in MinIO"                    
                        return Response(
                            {
                                "status": False,
                                "message": message,
                            },
                            status=status.HTTP_400_BAD_REQUEST,
                        )                    

                return Response(
                    {
                        "status": True,
                        "message": "Documents uploaded/updated successfully.",
                    },
                    status=status.HTTP_201_CREATED,
                )
            
class SLECArrearView(APIView):
    def post(self, request):
        user = request.user
        department_user = CustomUserProfile.objects.filter(user_id=user.id).first()
        slec_order_id = request.data.get("slec_order_id")
        remark = request.data.get("remark")
        role = request.data.get("role")
        user_role = None
        if role:
            user_role = Role.objects.filter(role_name=role).first()
        message = "Parameters are required."
        if slec_order_id:
            message = "SLEC Data not found"
            slec_order_data = IncentiveSlecOrder.objects.filter(id=slec_order_id).first()
            if slec_order_data:
                intention =  slec_order_data.caf.intention
                all_claims = []
                caf_ids = IncentiveCAF.objects.filter(intention=intention).values_list('id', flat=True)
                if caf_ids:
                    all_slec_order = IncentiveSlecOrder.objects.filter(caf_id__in=caf_ids).values_list('id', flat=True)
                    if all_slec_order:
                        get_slec_year = IncentiveSlecYealy.objects.filter(slec_order_id__in = all_slec_order).values_list('id', flat=True)
                        if get_slec_year:
                            get_all_claims = IncentiveClaimBasic.objects.filter(incentive_slec_year_id__in = get_slec_year).values_list('year_of_claimed_assistance', flat=True)
                            if get_all_claims:
                                all_claims = list(get_all_claims)
                message = "No Previous Claims found"
                final_year = []
                if all_claims:
                    get_current_slec_year = IncentiveSlecYealy.objects.filter(slec_order_id = slec_order_data).values_list('incentive_year', flat=True)
                    if get_current_slec_year:
                        message = "Arrear will be given for these years"
                        current_years = list(get_current_slec_year)
                        final_year = [year for year in all_claims if year in current_years]
                        if final_year:
                            for year in final_year:
                                data_exist = IncentiveSLECArrearModel.objects.filter(
                                    slec_order=slec_order_data,
                                    incentive_year=year
                                ).first()
                                if not data_exist:
                                    created = IncentiveSLECArrearModel.objects.create(
                                        slec_order=slec_order_data,
                                        incentive_year=year,
                                        status="In-Progress",
                                        depratment_user= user,
                                        department_user_name=department_user.name,
                                        department_user_role=user_role if user_role else None,
                                        department_remark=remark
                                    )                
                return Response(
                    {
                        "status": True,
                        "message": message,
                        "data": final_year
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

class UpdateSignedCAFView(APIView):

    def post(self, request):
        user_id = request.data.get('userId') 
        caf_id = request.data.get('id')
        minio_url = request.data.get('minioUrl')
        message = "Missing 'id' field in request."
        if caf_id:
            message = "Missing 'minioUrl' field in request."
            if minio_url:
                incentive_caf = IncentiveCAF.objects.filter(id=caf_id, user_id=user_id).first()
                if not incentive_caf:
                    return Response({
                        "message": f"IncentiveCAF with id={caf_id} not found for this user."
                    }, status=status.HTTP_404_NOT_FOUND)

                incentive_caf.caf_pdf_url = minio_url
                incentive_caf.is_document_sign= True
                incentive_caf.save()

                return Response({
                    "status": True,
                    "message": "CAF PDF URL updated successfully.",
                    "savedUrl": incentive_caf.caf_pdf_url
                }, status=status.HTTP_200_OK)
        return Response({
            "status": False,
            "message": message,
          }, status=status.HTTP_400_BAD_REQUEST)
    
class AgendaPDFView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            caf_id = request.query_params.get("caf_id")
            message ="Missing Caf id"
            data = {}
            if caf_id:
                agenda_data = IncentiveAgenda.objects.filter(caf_id=caf_id).first()
                message ="Data not found"
                file_url = ""
                total_pages = 0
                if agenda_data and agenda_data.agenda_file:
                    data=minio_func(agenda_data.agenda_file)
                    if data[0]:
                        total_pages = count_page(data[1]["Fileurl"][0])
                        file_url = data[1]["Fileurl"]
                        message = "Data Retrived successfully"
                return Response({
                    "status": True,
                    "message": message,
                    "data": {
                        "pdf_url": file_url,
                        "is_document_sign": agenda_data.is_document_sign,
                        "total_pages":total_pages
                    }
                }, status=status.HTTP_200_OK)
            return Response({
                    "status": False,
                    "message": message,
                    "data": {}
                },
                status=status.HTTP_400_BAD_REQUEST,
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
        
class UpdateSignedAgendaView(APIView):
    def post(self, request):
        caf_id = request.data.get('id')
        minio_url = request.data.get('minioUrl')
        message = "Missing 'id'/'minio url' field in request."
        if caf_id and minio_url:
            incentive_caf = IncentiveCAF.objects.filter(id=caf_id).first()
            message = "Caf data not found"
            if incentive_caf:
                agenda_data = IncentiveAgenda.objects.filter(caf_id=caf_id).first()
                message ="Data not found"
                if agenda_data:
                    agenda_data.agenda_file = minio_url
                    agenda_data.is_document_sign= True
                    agenda_data.save()
                    return Response({
                        "status": True,
                        "message": "Agenda PDF URL updated successfully.",
                        "savedUrl": agenda_data.agenda_file
                    }, status=status.HTTP_200_OK)
        return Response({
            "status": False,
            "message": message,
          }, status=status.HTTP_400_BAD_REQUEST)
            
