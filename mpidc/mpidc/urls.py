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

import os
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import permissions
from rest_framework_simplejwt.authentication import JWTAuthentication
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from authentication.views import el_userdata
from .views import download_media_file

schema_view = get_schema_view(
   openapi.Info(
      title="MPIDC API Documentation",
      default_version='v1',
      description="MPIDC",
    #   terms_of_service="https://www.google.com/policies/terms/",
    #   contact=openapi.Contact(email="tushargoyal@primuspartners.in"),
    #   license=openapi.License(name="BSD License"),
   ),
    public=True,
    authentication_classes=[JWTAuthentication],
    permission_classes=[permissions.AllowAny]
)

urlpatterns = [
    path("mpidc/admin/", admin.site.urls),
    path("api/v1/auth/", include("authentication.urls")),
    path("api/v1/sws/", include("sws.urls")),
    path("api/v1/incentives/", include("incentive.urls")),
    path("api/v1/users/", include("userprofile.urls")),
    path("api/v1/", include("approval.urls")),
    path('mpidc-api-doc/', schema_view.with_ui('swagger', cache_timeout=0), name='mpidc-api-doc'),
    path("api/v1/master/", include("master.urls")),
    path("api/v1/usermaster/",include("usermaster.urls")),
    path('el-userdata',el_userdata.as_view(),name="user_data"),
    path("api/v1/document_center/",include("document_center.urls")),
    re_path(r'^media-file/(?P<file_path>.+)$', download_media_file, name='download_media'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
