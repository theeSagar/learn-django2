"""
URL configuration for mpidc project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from .views import *


urlpatterns = [
    path("industry-type", IndustryTypeView.as_view(), name="industry-type"),
    path(
        "nature-of-business", NatureOfBusinessView.as_view(), name="nature-of-business"
    ),
    path("designation-list", DesignationList.as_view(), name="designation-list"),
    path("activity-data", GetIntentionDataView.as_view(), name="activity-data"),
    path("sectors-data", GetSectorsView.as_view(), name="sectors-data"),
    path(
        "sector-products", GetSectorProductsView.as_view(), name="get-sector-products"
    ),
    path(
        "pollution-types",
        GetPollutionTypeListCreateView.as_view(),
        name="pollution-type-list-create",
    ),
    path("district-data", DistrictDataList.as_view(), name="district-data"),
    path("intention-list", IntentionDetailsList.as_view(), name="intention-list"),
    path(
        "intention-details", IntentionDetailsListId.as_view(), name="intention-details"
    ),
    path(
        "caf-organization-details",
        CreateCAFView.as_view(),
        name="caf-organization-details",
    ),
    path(
        "caf-contact-details",
        CafContactDetailView.as_view(),
        name="caf-contact-details",
    ),
    path(
        "caf-investment-details",
        CAFInvestmentDetailsAPIView.as_view(),
        name="caf-investment-details",
    ),
    path(
        "filter-search", 
        FilterSearch.as_view(), 
        name="filter-search"
    ),
    path("district-list", DistrictData.as_view(), name="district-list"),
    path('state-list',StateDataView.as_view(),name='state-list'),
    path(
        'intention-form',
        IntentionFormView.as_view(),
        name='intention-form'
    ),
    path('caf-details',CAfDeatilsView.as_view(),name='caf-details'),
    path('sub-sector',SubSectorView.as_view(),name='sub-sector'),
    path('know-your-policies',SectorPolicyView.as_view(),name='know-your-policies'),
    path("user-caf-service", UserCafService.as_view(), name="user-caf-service"),
    path('district-landbank',DistrictLandBank.as_view(),name='district-landbank'),
    path("regional-office", RegionalOfficeListAPIView.as_view(), name="regional-office-list"),
    path("caf-submit",CAFSubmitAPIView.as_view(),name="caf-submit"),
    path("caf-preview", CAFSubmitAPIView.as_view(), name="caf-preview"),
    path("ro-district-data", RegionalOfficeDistrictView.as_view(), name="ro-district-data"),
    path("measurement-units", MeasurementUnitView.as_view(), name="measurement-units"),
    path("block-list", BlockListView.as_view(), name="block-list"),
    path("country", CountryView.as_view(), name="countries"),
    path("user-approvals", UserServiceView.as_view(), name="user-approvals"),
    path("helpdesk", HelpdeskView.as_view(), name = "helpdesk"),
    path("subscription", SubscriptionView.as_view(), name= "subscription"),
    path("add-on-service", UserCafAddOnService.as_view(), name="add-on-service"),
    path('update_signed_caf_pdf', UpdateSignedCAFView.as_view(), name='update_signed_service_caf'),
    path('block_priority', BlockPriorityAPIView.as_view(), name='block_priority'),
    path('tehsil',TehsilAPIView.as_view(), name="tehsil"),
    path("feedback-form",FeedbackFormView.as_view(), name="feedback-form"),
    path("auto-redirect-form", AutoRedirectFormView.as_view(), name="auto_redirect_form")

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
