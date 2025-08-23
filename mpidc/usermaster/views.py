from django.shortcuts import render
from django.db import transaction
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token
from rest_framework_simplejwt.authentication import JWTAuthentication
from .serializers import *
from django.conf import settings
global_err_message = settings.GLOBAL_ERR_MESSAGE

class PermissionView(APIView):
    def get(self, request):
        try:
            permission = Permission.objects.all()
            serializer = PermissionSerializer(permission, many=True)
            return Response(
                {
                    "status": True,
                    "message": "Permission fetched successfully",
                    "data": serializer.data,
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {"status": False, "message": global_err_message, "data": []},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def post(self, request):
        try:
            data = request.data

            if isinstance(data, dict) and "permission" in data:
                permissions_data = data["permission"]
            else:
                permissions_data = [data] if isinstance(data, dict) else data

            if not permissions_data:
                return Response(
                    {"status": False, "message": "No data provided"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            existing_permissions = set(
                Permission.objects.values_list("name", flat=True)
            )

            new_permissions = []
            for p in permissions_data:
                serializer = PermissionSerializer(data=p)
                if serializer.is_valid():
                    permission_name = p.get("name")
                    if permission_name and permission_name not in existing_permissions:
                        new_permissions.append(Permission(**serializer.validated_data))

            if new_permissions:
                Permission.objects.bulk_create(new_permissions)
                return Response(
                    {"status": True, "message": "Permissions added successfully"},
                    status=status.HTTP_201_CREATED,
                )

            return Response(
                {"status": False, "message": "All provided permissions already exist"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as e:
            return Response(
                {"status": False, "message": global_err_message},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def put(self, request):

        try:
            permission_id = request.data.get("id")
            permission_name = request.data.get("name")
            permission_status = request.data.get("status")

            if not all([permission_id, permission_name]):
                return Response(
                    {
                        "status": False,
                        "message": "Both permission id and tag are required.",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            permission = Permission.objects.filter(id=permission_id).first()
            if not permission:
                return Response(
                    {"status": False, "message": "Permission not found"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            update_data = {"name": permission_name}

            if permission_status:
                update_data["status"] = permission_status

            serializer = PermissionSerializer(
                permission, data=update_data, partial=True
            )
            if serializer.is_valid():
                serializer.save()
                return Response(
                    {"status": True, "message": "Updated successfully"},
                    status=status.HTTP_201_CREATED,
                )

            return Response(
                {"status": False, "message": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                {"status": False, "message": global_err_message},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def delete(self, request):
        try:
            permission_id = request.data.get("id")

            if not permission_id:
                return Response(
                    {"status": False, "message": "Permission Id is required."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            permission = Permission.objects.filter(id=permission_id).first()

            if not permission:
                return Response(
                    {"status": False, "message": "Permission not found"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            permission.delete()
            return Response(
                {"status": True, "message": "Permission deleted successfully."},
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {
                    "status": False,
                    "message": global_err_message,
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class RoleView(APIView):

    def post(self, request):
        try:
            roles_data = request.data.get("role", [])

            if not roles_data:
                return Response(
                    {"status": False, "message": "No data provided"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            role_names = [role["role_name"] for role in roles_data]
            existing_roles = set(
                Role.objects.filter(role_name__in=role_names).values_list(
                    "role_name", flat=True
                )
            )

            new_roles = [
                role for role in roles_data if role["role_name"] not in existing_roles
            ]

            if not new_roles:
                return Response(
                    {"status": False, "message": "All roles already exist"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            serializer = RoleSerializer(data=new_roles, many=True)
            if serializer.is_valid():
                serializer.save()
                return Response(
                    {"status": True, "message": "Roles added successfully"},
                    status=status.HTTP_201_CREATED,
                )

            return Response(
                {"status": False, "message": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as e:
            return Response(
                {"status": False, "message": global_err_message},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def get(self, request):
        try:
            role = Role.objects.all()
            serializers = RoleSerializer(role, many=True)
            return Response(
                {
                    "status": True,
                    "message": "Roles fetched successfully.",
                    "data": serializers.data,
                }
            )
        except Exception as e:
            return Response(
                {"status": False, "message": global_err_message},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def put(self, request):
        try:
            role_id = request.data.get("id")
            role_name = request.data.get("role_name")
            description = request.data.get("description")
            role_status = request.data.get("status")

            if not all([role_id, role_name, description, role_status]):
                return Response(
                    {"status": False, "message": "All fields are required."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            role = Role.objects.filter(id=role_id).first()
            if not role:
                return Response(
                    {"status": False, "message": "Role not found."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            serializer = RoleSerializer(role, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(
                    {
                        "status": True,
                        "message": "Role updated successfully.",
                        "data": serializer.data,
                    },
                    status=status.HTTP_200_OK,
                )

            return Response(
                {
                    "status": False,
                    "message": "Invalid data.",
                    "errors": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as e:
            return Response(
                {"status": False, "message": global_err_message},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def delete(self, request):
        try:
            role_id = request.data.get("id")

            if not role_id:
                return Response(
                    {"status": False, "message": "Role Id is required."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            role = Role.objects.filter(id=role_id).first()

            if role is None:
                return Response(
                    {"status": False, "message": "No role id found."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            role.delete()

            return Response(
                {"status": True, "message": "Role Deleted successfully."},
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {"status": False, "message": global_err_message},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class DesignationView(APIView):
    def get(self, request):
        try:
            designation = Designation.objects.all()
            serializers = DesignationSerializer(designation, many=True)
            return Response(
                {
                    "status": True,
                    "message": "Designation fetched successfully.",
                    "data": serializers.data,
                }
            )
        except Exception as e:
            return Response({}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        try:
            designations_data = request.data.get("designation", [])

            if not designations_data:
                return Response(
                    {"status": False, "message": "No data provided."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            for data in designations_data:
                if Designation.objects.filter(name=data["name"]).exists():
                    return Response(
                        {
                            "status": False,
                            "message": f"Designation '{data['name']}' already exists.",
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            serializer = DesignationSerializer(data=designations_data, many=True)
            if serializer.is_valid():
                serializer.save()
                return Response(
                    {
                        "status": True,
                        "message": "Designations added successfully.",
                        "data": serializer.data,
                    },
                    status=status.HTTP_201_CREATED,
                )

            return Response(
                {
                    "status": False,
                    "message": "Invalid data.",
                    "errors": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as e:
            return Response(
                {"status": False, "message": global_err_message},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def put(self, request):
        try:
            designation_id = request.data.get("id")
            name = request.data.get("name")

            if not (id and name):
                return Response(
                    {"status": False, "message": "Id and name are required."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            designation = Designation.objects.filter(id=designation_id).first()

            if not designation:
                return Response(
                    {"status": False, "message": "Designation not found."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            designation.name = name
            designation.save()

            return Response(
                {"status": True, "message": "Designation updated successfully."},
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {"status": False, "messgae": global_err_message},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def delete(self, request):
        try:
            id = request.data.get("id")

            if not id:
                return Response(
                    {"status": False, "message": "Id is required."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            designation = Designation.objects.filter(id=id).first()

            if not designation:
                return Response(
                    {"status": False, "message": "Designation not found."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            designation.delete()

            return Response(
                {"status": True, "message": "Designation deleted successfully."},
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {"status": False, "message": global_err_message},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ActivityView(APIView):
    def get(self, request):

        try:
            activity = Activity.objects.all()
            serializer = ActivitySerializer(activity, many=True)
            return Response(
                {"status": True, "data": serializer.data}, status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {"status": False, "message": global_err_message},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def post(self, request):
        try:
            activities = request.data.get(
                "activities", []
            )  # Expecting a list of activities

            if not activities or not isinstance(activities, list):
                return Response(
                    {"status": False, "message": "Invalid or empty data provided."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            valid_activities = []

            for activity in activities:
                name = activity.get("name")
                status_value = activity.get(
                    "status"
                )  # This is optional if no passed default will be 1.

                if not name:
                    return Response(
                        {"status": False, "message": "Name is required."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                if Activity.objects.filter(name=name).exists():
                    return Response(
                        {
                            "status": False,
                            "message": "Activity with this name already exists.",
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                activity_data = (
                    {"name": name, "status": status_value}
                    if status_value is not None
                    else {"name": name}
                )
                valid_activities.append(activity_data)

            if not valid_activities:
                return Response(
                    {
                        "status": False,
                        "message": "No valid activities to insert.",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            serializer = ActivitySerializer(data=valid_activities, many=True)
            if serializer.is_valid():
                serializer.save()
                return Response(
                    {"status": True, "message": "Activities added successfully."},
                    status=status.HTTP_201_CREATED,
                )

            return Response(
                {
                    "status": False,
                    "message": "Invalid data.",
                    "errors": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as e:
            return Response(
                {"status": False, "message": global_err_message},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def put(self, request):
        try:
            activity_id = request.data.get("id")
            name = request.data.get("name")
            activity_status = request.data.get("activity_status")

            if not (activity_id and name):
                return Response(
                    {"status": False, "message": "Name and ID is required."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            activity = Activity.objects.filter(id=activity_id).first()

            if not activity:
                return Response(
                    {"status": False, "message": "Activity not found."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
            if activity_status:
                activity.status = activity_status

            activity.name = name
            activity.save()
            return Response(
                {"status": True, "message": "Acitvity updated successfully."},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {"status": False, "message": global_err_message},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def delete(self, request):
        try:
            activity_id = request.data.get("id")
            if not activity_id:
                return Response(
                    {"status": False, "message": "ID is required."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            activity = Activity.objects.filter(id=activity_id).first()
            if not activity:
                return Response(
                    {"status": False, "message": "Activity not found."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            activity.delete()
            return Response(
                {"status": True, "message": "Activity deleted successfully."},
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {"status": False, "message": global_err_message},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class SubSectorView(APIView):
    def get(self, request):
        try:
            subsector = SubSector.objects.all()
            serializers = SubsectorSerializar(subsector, many=True)
            # if not subsector.exists():
            #     return Response({
            #     "status":False,
            #     "message":"No subsectors found."
            # },status=status.HTTP_400_BAD_REQUEST)
            return Response(
                {
                    "status": True,
                    "message": "Subsectors fetched successfully.",
                    "data": serializers.data,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {"status": False, "message": global_err_message},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def post(self, request):

        try:
            # Ensure request data exists
            if not request.data:
                return Response(
                    {"status": False, "message": "No data provided."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            subsectors_data = request.data.get(
                "subsector", request.data
            )  # Handle both cases

            # Convert single dictionary to a list
            if isinstance(subsectors_data, dict):
                subsectors_data = [subsectors_data]

            # Ensure it's a valid list
            if not isinstance(subsectors_data, list) or not subsectors_data:
                return Response(
                    {"status": False, "message": "No data provided."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            new_subsectors = []
            existing_names = set()

            for subsector in subsectors_data:
                # Validate mandatory fields
                if (
                    not isinstance(subsector, dict)
                    or "name" not in subsector
                    or "sector" not in subsector
                ):
                    return Response(
                        {
                            "status": False,
                            "message": "name and 'sector' are mandatory fields.",
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                name = subsector["name"].strip().lower()  # Normalize for comparison
                sector = subsector["sector"]

                # Check for duplicate name in DB
                if SubSector.objects.filter(
                    name__iexact=subsector["name"], sector=subsector["sector"]
                ).exists():
                    return Response(
                        {"status": False, "message": f"Subsector already exits."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                # Check for duplicate name within the request itself
                if (name, sector) in existing_names:
                    return Response(
                        {
                            "status": False,
                            "message": f"Duplicate name '{subsector['name']}' found in the request.",
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                existing_names.add((name, sector))

                # Convert display_order to integer if provided
                if "display_order" in subsector:
                    try:
                        subsector["display_order"] = int(subsector["display_order"])
                    except ValueError:
                        return Response(
                            {
                                "status": False,
                                "message": "display_order must be an integer.",
                            },
                            status=status.HTTP_400_BAD_REQUEST,
                        )

                new_subsectors.append(subsector)

            # Serialize and save data
            serializer = SubsectorSerializar(data=new_subsectors, many=True)

            if serializer.is_valid():
                serializer.save()
                return Response(
                    {"status": True, "message": "Subsectors added successfully."},
                    status=status.HTTP_201_CREATED,
                )

            return Response(
                {"status": False, "message": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as e:
            return Response(
                {"status": False, "message": global_err_message},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def put(self, request):
        try:
            subsector_id = request.data.get("id")
            name = request.data.get("name")
            sector = request.data.get("sector")

            if not all([subsector_id, name, sector]):
                return Response(
                    {"status": False, "message": "id, name, and sector are required."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            subsector = SubSector.objects.filter(id=subsector_id).first()
            if not subsector:
                return Response(
                    {"status": False, "message": "Subsector not found."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if (
                SubSector.objects.exclude(id=subsector_id)
                .filter(name__iexact=name)
                .exists()
            ):
                return Response(
                    {"status": False, "message": f"Subsector '{name}' already exists."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            subsector.name = name
            subsector.sector_id = sector
            subsector.display_order = request.data.get(
                "display_order", subsector.display_order
            )

            subsector.save()
            return Response(
                {"status": True, "message": "Subsector updated successfully."},
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {"status": False, "message": global_err_message},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def delete(self, request):
        try:
            subsector_id = request.data.get("id")

            if not subsector_id:
                return Response(
                    {"status": False, "message": "'id' is required."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            subsector = SubSector.objects.filter(id=subsector_id).first()
            if not subsector:
                return Response(
                    {"status": False, "message": "Subsector not found."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            subsector.delete()

            return Response(
                {"status": True, "message": "Subsector deleted successfully."},
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {"status": False, "message": global_err_message},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class DepartmentView(APIView):
    def get(self, request):
        try:
            department = DepartmentList.objects.all()
            serializers = DepartmentSerializer(department, many=True)
            return Response(
                {
                    "status": True,
                    "message": "Department Fetched successfully.",
                    "data": serializers.data,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {"status": False, "message": global_err_message},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def post(self, request):
        try:
            data = request.data

            departments_data = data.get(
                "department", [data] if isinstance(data, dict) else []
            )

            if not departments_data:
                return Response(
                    {"status": False, "message": "No data provided."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            existing_departments = set(
                DepartmentList.objects.values_list("name", flat=True)
            )

            new_departments = []
            for dept in departments_data:
                if dept.get("name") and dept["name"] not in existing_departments:
                    serializer = DepartmentSerializer(data=dept)
                    if serializer.is_valid():
                        validated_data = serializer.validated_data

                        new_departments.append(DepartmentList(**validated_data))

            if new_departments:
                DepartmentList.objects.bulk_create(new_departments)
                return Response(
                    {"status": True, "message": "Departments created successfully."},
                    status=status.HTTP_201_CREATED,
                )

            return Response(
                {
                    "status": False,
                    "message": "Provided department name already exists.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as e:
            return Response(
                {"status": False, "message": global_err_message},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def put(self, request):
        try:
            data = request.data
            department_id = data.get("id")
            department_name = data.get("name")

            # Validate mandatory fields
            if not department_id or not department_name:
                return Response(
                    {"status": False, "message": "Both 'id' and 'name' are required."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            try:
                department = DepartmentList.objects.get(id=department_id)
            except DepartmentList.DoesNotExist:
                return Response(
                    {"status": False, "message": "Department not found."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if "name" in data:
                department.name = department_name
            if "status" in data:
                department.status = data["status"]
            if "code" in data:
                department.code = data["code"]

            department.save()

            return Response(
                {"status": True, "message": "Department updated successfully."},
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {"status": False, "message": global_err_message},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def delete(self, request):
        try:
            data = request.data
            department_id = data.get("id")

            if not department_id:
                return Response(
                    {"status": False, "message": "Department id is required."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            department = DepartmentList.objects.filter(id=department_id).first()

            if not department:
                return Response({"status": False, "message": "No department found."})
            # Delete department
            department.delete()

            return Response(
                {"status": True, "message": "Department deleted successfully."},
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {"status": False, "message": global_err_message},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class SectorView(APIView):
    def get(self, request):
        try:
            sector = Sector.objects.all()
            serializer = SectorSerializer(sector, many=True)
            return Response(
                {
                    "status": True,
                    "message": "Sectors fetched successfully.",
                    "data": serializer.data,
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {
                    "status": False,
                    "message": global_err_message,
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def post(self, request):
        try:
            data = request.data
            sector_data = data.get("sectors", [data] if isinstance(data, dict) else [])

            existing_sectors = set(Sector.objects.values_list("name", flat=True))

            new_sectors = []
            for sector in sector_data:
                if not sector.get("name") or not sector.get("activity"):
                    return Response(
                        {
                            "status": False,
                            "message": "name and activity are mandatory.",
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                if sector["name"] in existing_sectors:
                    continue

                serializer = SectorSerializer(data=sector)
                if serializer.is_valid():
                    new_sectors.append(Sector(**serializer.validated_data))

            if new_sectors:
                Sector.objects.bulk_create(new_sectors)
                return Response(
                    {"status": True, "message": "Sectors created successfully."},
                    status=status.HTTP_201_CREATED,
                )

            return Response(
                {"status": False, "message": "Provided sector name already exists."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as e:
            return Response(
                {"status": False, "message": global_err_message},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def put(self, request):
        try:
            data = request.data
            sector_id = data.get("id")
            name = data.get("name")

            if not (sector_id and name):
                return Response(
                    {"status": False, "message": "id and name are required."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            sector = Sector.objects.filter(id=sector_id).first()
            if not sector:
                return Response(
                    {"status": False, "message": "Sector not found."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            serializer = SectorSerializer(sector, data=data, partial=True)

            if serializer.is_valid():
                if (
                    "name" in data
                    and Sector.objects.exclude(id=sector_id)
                    .filter(name=data["name"])
                    .exists()
                ):
                    return Response(
                        {
                            "status": False,
                            "message": "Sector with this name already exists.",
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                serializer.save()
                return Response(
                    {"status": True, "message": "Sector updated successfully."},
                    status=status.HTTP_200_OK,
                )

            return Response(
                {"status": False, "message": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as e:
            return Response(
                {"status": False, "message": global_err_message},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def delete(self, request):
        try:
            sector_id = request.data.get("id")
            if not sector_id:
                return Response(
                    {"status": True, "message": "Id is required."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            sector = Sector.objects.filter(id=sector_id).first()
            if sector == None:
                return Response(
                    {"status": False, "message": "No sector found."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            sector.delete()
            return Response(
                {"status": True, "message": "Sector deleted successfully."},
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {"status": False, "message": global_err_message},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class UserView(APIView):
    def get(self, request):
        try:
            page = int(request.query_params.get("page", 1))
            limit = int(request.query_params.get("limit", 10))
            userprofile = CustomUserProfile.objects.all()
            paginator = Paginator(userprofile, limit)
            if page > paginator.num_pages or page < 1:
                return Response(
                    {"status": False, "message": "Page out of range"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            paginated_profiles = paginator.page(page)
            serializer = UserProfileSerializer(paginated_profiles, many=True)

            return Response(
                {
                    "status": True,
                    "message": "User profile retrived successfully.",
                    "limit": limit,
                    "page": page,
                    "total": paginator.count,
                    "data": serializer.data,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {"status": False, "message": global_err_message},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def post(self, request):
        try:
            data = request.data
            user_data = data.get("user", {})

            email = user_data.get("email")
            if not email:
                return Response(
                    {"status": False, "message": "Email is mandatory"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            userProfile = CustomUserProfile.objects.filter(email=email).first()
            if userProfile:
                return Response(
                    {"status": False, "message": "Email already exists."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            roles = data.get("roles", [])
            permissions = data.get("permissions", [])

            existing_roles = set(
                Role.objects.filter(id__in=roles).values_list("id", flat=True)
            )
            existing_permissions = set(
                Permission.objects.filter(id__in=permissions).values_list(
                    "id", flat=True
                )
            )

            valid_roles = Role.objects.filter(id__in=roles).count()

            if valid_roles != len(roles):
                return Response(
                    {"status": False, "message": "Invalid role IDs"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            valid_permissions = Permission.objects.filter(id__in=permissions).count()
            if valid_permissions != len(permissions):
                return Response(
                    {"status": False, "message": "Invalid permission IDs"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            with transaction.atomic():
                user = User.objects.create(username=email)
                user.set_password("123456")
                user.save()

                user_profile = CustomUserProfile.objects.create(
                    user=user,
                    mobile_no=user_data.get("mobile_no", ""),
                    name=user_data.get("name", "").strip(),
                    email=email.strip(),
                )

                # This assign roles
                UserHasRole.objects.bulk_create(
                    [
                        UserHasRole(user=user, role=Role.objects.get(id=role_id))
                        for role_id in roles
                    ]
                )

                return Response(
                    {
                        "status": True,
                        # "message": "User created successfully",
                        # "user": {"id": user.id, "email": user.username},
                        # "roles": list(existing_roles),
                        # "permissions": list(existing_permissions)
                    },
                    status=status.HTTP_201_CREATED,
                )

        except Exception as e:
            return Response(
                {"status": False, "message": global_err_message},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def put(self, request):
        try:
            data = request.data
            user_id = data.get("user_id")

            if not user_id:
                return Response(
                    {"status": False, "message": "User ID is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            user = User.objects.filter(id=user_id).first()
            if not user:
                return Response(
                    {"status": False, "message": "User not found"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            user_profile = user.customuserprofile
            with transaction.atomic():
                user.username = data.get("email", user.username).strip()
                user.save()

                user_profile.name = data.get(
                    "name", user_profile.name
                ).strip()  # will keep the exiting values if no name provided.
                user_profile.mobile_no = data.get(
                    "mobile_no", user_profile.mobile_no
                ).strip()
                user_profile.email = data.get("email", user_profile.email).strip()
                user_profile.save()

                new_roles = set(data.get("roles", []))
            existing_roles = set(
                Role.objects.filter(id__in=new_roles).values_list("id", flat=True)
            )

            if new_roles - existing_roles:
                return Response(
                    {
                        "status": False,
                        "message": "Invalid role IDs",
                        "missing_roles": list(new_roles - existing_roles),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            user_has_roles = set(
                UserHasRole.objects.filter(user=user).values_list("role_id", flat=True)
            )

            roles_to_add = new_roles - user_has_roles
            UserHasRole.objects.bulk_create(
                [UserHasRole(user=user, role_id=role_id) for role_id in roles_to_add]
            )
            return Response(
                {
                    "status": True,
                    "message": "User details updated successfully",
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {"status": False, "message": global_err_message},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

class UserModulePermissionView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            requested_role_name = request.query_params.get('role')
            module_name = request.query_params.get('module_name')

            if not module_name:
                return Response({
                    "success": True,
                    "message": "Module not found",
                    "data": []
                }, status=status.HTTP_400_BAD_REQUEST)

            # Find module by name
            module = Module.objects.filter(module_name=module_name).first()
            if not module:
                return Response({
                    "success": True,
                    "message": "Module not found",
                    "data": []
                }, status=status.HTTP_400_BAD_REQUEST)

            # Determine current role (from query param or fallback to primary)
            current_role = None

            if requested_role_name:
                current_role = Role.objects.filter(role_name=requested_role_name).first()
            if not current_role:
                user_primary_role = UserHasRole.objects.filter(user=user, role_type="primary").first()
                if user_primary_role:
                    current_role = user_primary_role.role

            if not current_role:
                return Response({
                    "success": True,
                    "message": "No Valid Role",
                    "data": []
                }, status=status.HTTP_400_BAD_REQUEST)

            # Get permissions via role
            role_permissions = RoleModulePermission.objects.filter(role=current_role, module=module)

            # Get permissions directly assigned to the user
            user_permissions = UserModulePermission.objects.filter(user=user, module=module)

            # Combine permissions
            combined_permissions = set()

            for perm in role_permissions:
                combined_permissions.add(perm.permission.name)

            for perm in user_permissions:
                combined_permissions.add(perm.permission.name)

            all_permissions = Permission.objects.values_list('name', flat=True)
            permission_map = {
                perm.lower(): (perm.lower() in combined_permissions)
                for perm in all_permissions
            }

            return Response({
                "success": True,
                "message": "Data Retrived Successfully",
                "data": permission_map
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "success": True,
                "message": "Technical issue",
                "data": []
            }, status=status.HTTP_400_BAD_REQUEST)

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            user = request.user
            modules_requested = request.data.get("module", [])
            requested_role_name = request.data.get('role',"")

            if not modules_requested or not isinstance(modules_requested, list):
                return Response({
                    "success": False,
                    "message": "Invalid or missing 'module' list in request body",
                    "data": {}
                }, status=status.HTTP_400_BAD_REQUEST)

            # Determine current role (from query param or fallback to primary)
            current_role = None

            if requested_role_name:
                current_role = Role.objects.filter(role_name=requested_role_name).first()
            if not current_role:
                user_primary_role = UserHasRole.objects.filter(user=user, role_type="primary").first()
                if user_primary_role:
                    current_role = user_primary_role.role

            if not current_role:
                return Response({
                    "success": True,
                    "message": "No Valid Role",
                    "data": []
                }, status=status.HTTP_400_BAD_REQUEST)

            # Fetch all permissions once to build keys (optional, to ensure all are present)
            all_permission_names = set(Permission.objects.values_list("name", flat=True))

            response_data = {}

            # Loop through modules
            for mod_name in modules_requested:
                module = Module.objects.filter(module_name=mod_name).first()
                if not module:
                    continue  # Skip invalid module names

                permissions_set = set()

                # Role-based permissions
                role_perms = RoleModulePermission.objects.filter(role=current_role, module=module)
                permissions_set.update([rp.permission.name.lower() for rp in role_perms])

                # User-specific permissions
                user_perms = UserModulePermission.objects.filter(user=user, module=module)
                permissions_set.update([up.permission.name.lower() for up in user_perms])

                # Build permission map per module
                permission_map = {
                    perm_name.lower(): perm_name.lower() in permissions_set
                    for perm_name in all_permission_names
                }

                response_data[mod_name] = permission_map

            return Response({
                "success": True,
                "message": "data",
                "data": response_data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"status": False, "message": global_err_message, "data": ""},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )