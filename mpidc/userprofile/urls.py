from django.urls import path
from .views import *

urlpatterns = [
    path(
        "organization-type",
        OrganizationTypeView.as_view(),
        name="get-organization-type",
    ),
    path(
        "organization-detail",
        CreateUserOrganizationView.as_view(),
        name="organization-detail",
    ),
    path(
        "organization-contact-details",
        OrganizationContactDetailView.as_view(),
        name="organization-contact-detail",
    ),
    path("user-bank-details", UserBankDetailsView.as_view(), name="user-bank-details"),
    path(
        "user-profile-status",
        UpdateUserProfileStatus.as_view(),
        name="user-profile-status",
    ),
    path(
        "user-service-tracker",
        UserServiceTrackerView.as_view(),
        name="user-service-tracker"
    ),
    path(
        "notification-list",
        NotificationListView.as_view(),
        name="notification-list"
    ),
    path("change-password",ChangePasswordView.as_view(),name="change-password")

]
