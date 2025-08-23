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

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from .views import *


urlpatterns = [

    path(
        "states",
        StateView.as_view(),
        name="master-states",
    ),
    path("districts", DistrictView.as_view(), name="master-districts"),
    path("master_regional_offices", RegionalOfficeView.as_view(), name="regional_offices"),
    path("policy", KnowYourPolicyView.as_view(), name="policy"),
    path("industrial-areas", IndustrialAreaView.as_view(), name="industrial-areas"),
    path("regional-office-district-mappings", RegionalOfficeDistrictMappingView.as_view(), name="regional-office-district-mappings"),
    path("configurations", ConfigurationsAPIView.as_view(), name="configurations"),
    path("get-investor-users", InvestorUsersAPIView.as_view(), name="get-investor-users"),


] 