from django.urls import path
from .views import *

urlpatterns = [
    path(
        "permission",
        PermissionView.as_view(),
        name="permission",
    ),
    path("role", RoleView.as_view(), name="role"),
    path("designation", DesignationView.as_view(), name="designation"),
    path("activity",ActivityView.as_view(),name="activity"),
    path("subsector",SubSectorView.as_view(),name="SubSectorView"),
    path("department",DepartmentView.as_view(),name="department"),
    path("sector",SectorView.as_view(),name="sector"),
    path("user",UserView.as_view(),name="user"),
    path("user_module_permission",UserModulePermissionView.as_view(),name="user_module_permission")

]
