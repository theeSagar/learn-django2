from django.core.exceptions import ObjectDoesNotExist
from django.db.utils import IntegrityError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from sws.models import State
from .serializers import *
import json
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.db.models import Q
from authentication.models import Role, CustomUserProfile
from django.conf import settings
global_err_message = settings.GLOBAL_ERR_MESSAGE


class StateView(APIView):
    def get(self, request):
        try:
            states = State.objects.all().order_by('id')
            serializer = StateSerializer(states, many=True)
            return Response({
                "status": True,
                "message": "States fetched successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"status": False, "message": global_err_message, "data": []}, 
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        try:
            states = request.data.get("state", [])
            if not isinstance(states, list):
                return Response({
                    "status": False,
                    "message": "Invalid format. 'state' should be a list of dictionaries.",
                    "data": []
                }, status=status.HTTP_400_BAD_REQUEST)

            state_objects = []
            existing_states = set(State.objects.values_list('name', flat=True))

            for state_data in states:
                if not isinstance(state_data, dict) or "name" not in state_data:
                    return Response({
                        "status": False,
                        "message": "Each state must be a dictionary with a 'name' key.",
                        "data": []
                    }, status=status.HTTP_400_BAD_REQUEST)

                state_name = state_data["name"].strip()
                if state_name not in existing_states:
                    state_objects.append(State(name=state_name))

            if state_objects:
                State.objects.bulk_create(state_objects)

            all_states = State.objects.order_by("id").values_list('name', flat=True)

            return Response({
                "status": True,
                "message": "States added successfully",
                "data": list(all_states)
            }, status=status.HTTP_201_CREATED)

        except IntegrityError:
            return Response({
                "status": False,
                "message": "A state with this name already exists.",
                "data": []
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "status": False,
                "message": global_err_message,
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request):
        try:
            state_id = request.data.get("state_id")
            name = request.data.get("name")

            if not state_id or not name:
                return Response({
                    "status": False,
                    "message": "state_id and name are required.",
                    "data": []
                }, status=status.HTTP_400_BAD_REQUEST)

            state = get_object_or_404(State, id=state_id)
            state.name = name
            state.save()

            return Response({
                "status": True,
                "message": "State updated successfully",
                "data": {"state_id": state.id, "name": state.name}
            }, status=status.HTTP_200_OK)

        except IntegrityError:
            return Response({
                "status": False,
                "message": "A state with this name already exists.",
                "data": []
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "status": False,
                "message": global_err_message,
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request):
        try:
            state_id = request.data.get("state_id")

            if not state_id:
                return Response({
                    "status": False,
                    "message": "state_id is required.",
                    "data": []
                }, status=status.HTTP_400_BAD_REQUEST)

            state = get_object_or_404(State, id=state_id)
            state.delete()

            return Response({
                "status": True,
                "message": "State deleted successfully",
                "data": []
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "status": False,
                "message": global_err_message,
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class DistrictView(APIView):
    def get(self, request):
        try:
            districts = District.objects.all().order_by("id")
            serializer = DistrictSerializer(districts, many=True)
            return Response({
                "status": True,
                "message": "Districts fetched successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"status": False, "message": global_err_message, "data": []}, 
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        serializer = DistrictCreateSerializer(data=request.data)
        if serializer.is_valid():
            state = get_object_or_404(State, id=serializer.validated_data["state_id"])
            district_names = serializer.validated_data["district_names"]
            existing_districts = {name.lower() for name in District.objects.filter(state=state).values_list('name', flat=True)}

            new_districts = []
            for name in district_names:
                clean_name = name.strip()
                if clean_name.lower() not in existing_districts:
                    new_districts.append(District(state=state, name=clean_name))

            if new_districts:
                District.objects.bulk_create(new_districts)

            all_districts = District.objects.filter(state=state).order_by("id")
            return Response({
                "status": True,
                "message": "Districts added successfully",
                "data": DistrictSerializer(all_districts, many=True).data
            }, status=status.HTTP_201_CREATED)

        return Response({
            "status": False,
            "message": serializer.errors,
            "data": []
        }, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        district_id = request.data.get("district_id")
        new_name = request.data.get("name")

        if not district_id or not new_name:
            return Response({
                "status": False,
                "message": "district_id and name are required.",
                "data": []
            }, status=status.HTTP_400_BAD_REQUEST)

        district = get_object_or_404(District, id=district_id)
        district.name = new_name
        district.save()

        return Response({
            "status": True,
            "message": "District updated successfully",
            "data": {"district_id": district.id, "name": district.name}
        }, status=status.HTTP_200_OK)

    def delete(self, request):
        district_id = request.data.get("district_id")

        if not district_id:
            return Response({
                "status": False,
                "message": "district_id is required.",
                "data": []
            }, status=status.HTTP_400_BAD_REQUEST)

        district = get_object_or_404(District, id=district_id)
        district.delete()

        return Response({
            "status": True,
            "message": "District deleted successfully",
            "data": []
        }, status=status.HTTP_200_OK)


class RegionalOfficeView(APIView):
    def get(self, request):
        try:
            regional_offices = RegionalOffice.objects.all().order_by("id")
            serializer = RegionalCreatOfficeSerializer(regional_offices, many=True)
            return Response({
                "status": True,
                "message": "Regional Offices fetched successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "status": False,
                "message": global_err_message,
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        try:
            request_data = request.data.copy()
            request_data.pop("id", None)  

            name = request_data.get("name", "").strip()
            if RegionalOffice.objects.filter(name__iexact=name).exists():
                return Response({
                    "status": False,
                    "message": "A regional office with this name already exists.",
                    "data": []
                }, status=status.HTTP_400_BAD_REQUEST)

            serializer = RegionalCreatOfficeSerializer(data=request_data)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "status": True,
                    "message": "Regional Office created successfully",
                    "data": serializer.data
                }, status=status.HTTP_201_CREATED)

            return Response({
                "status": False,
                "message": serializer.errors,
                "data": []
            }, status=status.HTTP_400_BAD_REQUEST)

        except IntegrityError:
            return Response({
                "status": False,
                "message": "A regional office with this name already exists.",
                "data": []
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                "status": False,
                "message": global_err_message,
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request):
        try:
            regional_office_id = request.data.get("id")
            name = request.data.get("name")

            if not regional_office_id or not name:
                return Response({
                    "status": False,
                    "message": "id and name are required.",
                    "data": []
                }, status=status.HTTP_400_BAD_REQUEST)

            regional_office = get_object_or_404(RegionalOffice, id=regional_office_id)

            if RegionalOffice.objects.exclude(id=regional_office_id).filter(name__iexact=name).exists():
                return Response({
                    "status": False,
                    "message": "A Regional Office with this name already exists.",
                    "data": []
                }, status=status.HTTP_400_BAD_REQUEST)

            regional_office.name = name
            regional_office.save()

            return Response({
                "status": True,
                "message": "Regional Office updated successfully",
                "data": {"id": regional_office.id, "name": regional_office.name}
            }, status=status.HTTP_200_OK)

        except IntegrityError:
            return Response({
                "status": False,
                "message": "A Regional Office with this name already exists.",
                "data": []
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "status": False,
                "message": global_err_message,
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request):
        regional_office_id = request.data.get("id")
        if not regional_office_id:
            return Response({
                "status": False,
                "message": "id is required",
                "data": []
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            regional_office = get_object_or_404(RegionalOffice, id=regional_office_id)
            regional_office.delete()
            return Response({
                "status": True,
                "message": "Regional Office deleted successfully",
                "data": []
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "status": False,
                "message": global_err_message,
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




class KnowYourPolicyView(APIView):
    
    def get(self, request):
        try:
            policy_id = request.query_params.get("id")
            if policy_id:
                policy = get_object_or_404(KnowYourPolicy, id=policy_id)
                serializer = KnowYourPolicyCreateSerializer(policy)
                return Response({
                    "status": True,
                    "message": "Policy fetched successfully",
                    "data": serializer.data
                }, status=status.HTTP_200_OK)
            
            policies = KnowYourPolicy.objects.all()
            serializer = KnowYourPolicyCreateSerializer(policies, many=True)
            return Response({
                "status": True,
                "message": "Policies fetched successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({
                "status": False,
                "message": global_err_message,
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        try:
            request_data = request.data.copy()
            request_data.pop("id", None)
            
            if KnowYourPolicy.objects.filter(title=request_data.get("title")).exists():
                return Response({
                    "status": False,
                    "message": "Policy with this title already exists",
                    "data": []
                }, status=status.HTTP_400_BAD_REQUEST)

            serializer = KnowYourPolicyCreateSerializer(data=request_data)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "status": True,
                    "message": "Policy created successfully",
                    "data": serializer.data
                }, status=status.HTTP_201_CREATED)

            return Response({
                "status": False,
                "message": serializer.errors,
                "data": []
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                "status": False,
                "message": global_err_message,
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request):
        try:
            policy_id = request.data.get("id")
            if not policy_id:
                return Response({
                    "status": False,
                    "message": "id is required",
                    "data": []
                }, status=status.HTTP_400_BAD_REQUEST)

            policy = get_object_or_404(KnowYourPolicy, id=policy_id)

            new_title = request.data.get("title")
            if new_title and KnowYourPolicy.objects.filter(title=new_title).exclude(id=policy_id).exists():
                return Response({
                    "status": False,
                    "message": "Policy with this title already exists",
                    "data": []
                }, status=status.HTTP_400_BAD_REQUEST)

            serializer = KnowYourPolicyCreateSerializer(policy, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "status": True,
                    "message": "Policy updated successfully",
                    "data": serializer.data
                }, status=status.HTTP_200_OK)
            
            return Response({
                "status": False,
                "message": serializer.errors,
                "data": []
            }, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            return Response({
                "status": False,
                "message": global_err_message,
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request):
        try:
            policy_id = request.data.get("id")
            if not policy_id:
                return Response({
                    "status": False,
                    "message": "id is required",
                    "data": []
                }, status=status.HTTP_400_BAD_REQUEST)

            policy = get_object_or_404(KnowYourPolicy, id=policy_id)
            policy.delete()
            return Response({
                "status": True,
                "message": "Policy deleted successfully",
                "data": []
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "status": False,
                "message": global_err_message,
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class IndustrialAreaView(APIView):

    def get(self, request):
        try:
            industrial_area_id = request.query_params.get("id")
            if industrial_area_id:
                industrial_area = get_object_or_404(IndustrialAreaList, id=industrial_area_id)
                serializer = IndustrialAreaListSerializer(industrial_area)
                return Response({
                    "status": True,
                    "message": "Industrial area fetched successfully",
                    "data": serializer.data
                }, status=status.HTTP_200_OK)

            industrial_areas = IndustrialAreaList.objects.all()
            serializer = IndustrialAreaListSerializer(industrial_areas, many=True)
            return Response({
                "status": True,
                "message": "Industrial areas fetched successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "status": False,
                "message": global_err_message,
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        try:
            request_data = request.data.copy()
            request_data.pop("id", None) 

            serializer = IndustrialAreaListSerializer(data=request_data)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "status": True,
                    "message": "Industrial Area created successfully",
                    "data": serializer.data
                }, status=status.HTTP_201_CREATED)

            return Response({
                "status": False,
                "message": serializer.errors,
                "data": []
            }, status=status.HTTP_400_BAD_REQUEST)

        except IntegrityError as e:
            return Response({
                "status": False,
                "message": "Duplicate entry: This Industrial Area already exists.",
                "data": []
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "status": False,
                "message": global_err_message,
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request):
        try:
            industrial_area_id = request.data.get("id")
            if not industrial_area_id:
                return Response({
                    "status": False,
                    "message": "id is required",
                    "data": []
                }, status=status.HTTP_400_BAD_REQUEST)

            industrial_area = get_object_or_404(IndustrialAreaList, id=industrial_area_id)

            new_name = request.data.get("name")
            district_id = request.data.get("district")

            if new_name and district_id:
                if IndustrialAreaList.objects.filter(name=new_name, district_id=district_id).exclude(id=industrial_area_id).exists():
                    return Response({
                        "status": False,
                        "message": "An industrial area with this name already exists in the selected district.",
                        "data": []
                    }, status=status.HTTP_400_BAD_REQUEST)

            serializer = IndustrialAreaListSerializer(industrial_area, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    "status": True,
                    "message": "Industrial area updated successfully",
                    "data": serializer.data
                }, status=status.HTTP_200_OK)

            return Response({
                "status": False,
                "message": serializer.errors,
                "data": []
            }, status=status.HTTP_400_BAD_REQUEST)

        except ObjectDoesNotExist:
            return Response({
                "status": False,
                "message": "Industrial area not found.",
                "data": []
            }, status=status.HTTP_400_BAD_REQUEST)
        
        except IntegrityError:
            return Response({
                "status": False,
                "message": "Database integrity error occurred.",
                "data": []
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                "status": False,
                "message": global_err_message,
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    def delete(self, request):
        try:
            industrial_area_id = request.data.get("id")
            if not industrial_area_id:
                return Response({
                    "status": False,
                    "message": "id is required",
                    "data": []
                }, status=status.HTTP_400_BAD_REQUEST)

            industrial_area = get_object_or_404(IndustrialAreaList, id=industrial_area_id)
            industrial_area.delete()
            return Response({
                "status": True,
                "message": "Industrial area deleted successfully",
                "data": []
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "status": False,
                "message": global_err_message,
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RegionalOfficeDistrictMappingView(APIView):

    def get(self, request):
        try:
            mapping_id = request.query_params.get("id")
            if mapping_id:
                mapping = get_object_or_404(RegionalOfficeDistrictMapping, id=mapping_id)
                serializer = RegionalOfficeDistrictMapSerializer(mapping)
                return Response({
                    "status": True,
                    "message": "Regional office district mapping retrieved successfully",
                    "data": serializer.data
                }, status=status.HTTP_200_OK)

            mappings = RegionalOfficeDistrictMapping.objects.all()
            serializer = RegionalOfficeDistrictMapSerializer(mappings, many=True)
            return Response({
                "status": True,
                "message": "Regional office district mappings retrieved successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "status": False,
                "message": global_err_message,
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    def post(self, request):
        try:
            regional_office_id = request.data.get("regional_office")
            district_ids = request.data.get("districts", [])  
            display_order = request.data.get("display_order", 9999)
            status_value = request.data.get("status", "active")

            if not regional_office_id or not district_ids:
                return Response({
                    "status": False,
                    "message": "regional_office and districts are required",
                    "data": []
                }, status=status.HTTP_400_BAD_REQUEST)

            regional_office = get_object_or_404(RegionalOffice, id=regional_office_id)
            existing_mappings = RegionalOfficeDistrictMapping.objects.filter(
                regional_office=regional_office, district_id__in=district_ids
            )

            if existing_mappings.exists():
                return Response({
                    "status": False,
                    "message": "Some districts are already mapped to this regional office",
                    "data": []
                }, status=status.HTTP_400_BAD_REQUEST)

            created_mappings = []
            for district_id in district_ids:
                district = get_object_or_404(District, id=district_id)
                mapping = RegionalOfficeDistrictMapping.objects.create(
                    regional_office=regional_office,
                    district=district,
                    display_order=display_order,
                    status=status_value
                )
                created_mappings.append(mapping)

            serializer = RegionalOfficeDistrictMapSerializer(created_mappings, many=True)
            return Response({
                "status": True,
                "message": "Regional office district mappings created successfully",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)

        except IntegrityError:
            return Response({
                "status": False,
                "message": "Database integrity error occurred.",
                "data": []
            }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                "status": False,
                "message": global_err_message,
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request):
        try:
            mapping_id = request.data.get("id")
            if not mapping_id:
                return Response({
                    "status": False,
                    "message": "id is required",
                    "data": []
                }, status=status.HTTP_400_BAD_REQUEST)

            mapping = get_object_or_404(RegionalOfficeDistrictMapping, id=mapping_id)
            new_regional_office_id = request.data.get("regional_office")
            new_district_id = request.data.get("district")

            if not isinstance(new_district_id, int):
                return Response({
                    "status": False,
                    "message": "Invalid district format. Expected district ID (integer).",
                    "data": []
                }, status=status.HTTP_400_BAD_REQUEST)

            district_instance = get_object_or_404(District, id=new_district_id)

            mapping.district = district_instance
            mapping.regional_office_id = new_regional_office_id
            mapping.display_order = request.data.get("display_order", mapping.display_order)
            mapping.status = request.data.get("status", mapping.status)
            mapping.save()

            return Response({
                "status": True,
                "message": "Regional office district mapping updated successfully",
                "data": {
                    "id": mapping.id,
                    "regional_office": mapping.regional_office.id,
                    "district": mapping.district.id,
                    "display_order": mapping.display_order,
                    "status": mapping.status,
                }
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "status": False,
                "message": global_err_message,
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request):
        mapping_id = request.data.get("id")
        if not mapping_id:
            return Response({
                "status": False,
                "message": "id is required",
                "data": []
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            mapping = get_object_or_404(RegionalOfficeDistrictMapping, id=mapping_id)
            mapping.delete()
            return Response({
                "status": True,
                "message": "Regional office district mapping deleted successfully",
                "data": []
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "status": False,
                "message": global_err_message,
                "data": []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ConfigurationsAPIView(APIView):
    def get(self, request, *args, **kwargs):
        try:
            parameter_name = request.query_params.get('parameter_name')
            data = {}

            if parameter_name:
                try:
                    industry = ConfigurationsModel.objects.filter(parameter_name=parameter_name).first()
                    try:
                        parsed_data = json.loads(industry.value)
                        message = "Data retrieved successfully."
                        data = {
                            "parameter_name": industry.parameter_name,
                            "value": parsed_data,
                        }
                        return Response(
                            {"status": True, "message": message, "data": data},
                            status=status.HTTP_200_OK
                        )
                    except json.JSONDecodeError:
                        message = "Stored value is not valid JSON."
                except ConfigurationsModel.DoesNotExist:
                    message = "Industry not found for the provided parameter_name."
            else:
                industries = ConfigurationsModel.objects.all()
                all_data = []
                for item in industries:
                    try:
                        parsed = json.loads(item.value)
                    except json.JSONDecodeError:
                        parsed = "Invalid JSON"
                    all_data.append({
                        "parameter_name": item.parameter_name,
                        "value": parsed,
                    })
                return Response(
                    {
                        "status": True,
                        "message": "All records retrieved successfully.",
                        "data": all_data,
                    },
                    status=status.HTTP_200_OK
                )

            return Response(
                {"status": False, "message": message, "data": data},
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
        
class InvestorUsersAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        
        investor_role = Role.objects.filter(role_name__iexact='Investor').first()
        message = "Investor Role not exist"
        if investor_role:
            investor_users = CustomUserProfile.objects.filter(
                user__userhasrole__role=investor_role,
                user_type='regular'
            ).exclude(
                Q(email__isnull=True) | Q(email__exact="")
            ).values(
                'user_id', 'name', 'email'
            ).order_by("-user_id")
            message = "User not exist"
            if investor_users.exists():
                message = "All Investor records retrieved successfully."
                for investor in investor_users:
                    investor['email'] = investor['email'] if investor['email']  else ""

            return Response(
                {
                    "status": True,
                    "message": message,
                    "data": investor_users,
                },
                status=status.HTTP_200_OK,
            )    

        return Response(
            {
                "status": False,
                "message": message,
                "data": [],
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
