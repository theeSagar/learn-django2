from django.conf import settings
from django.urls import path
from .views import *

urlpatterns = [
    path("save-session-id",SaveSessionView.as_view(),name="save-sesion-id"),
    path("save-data",SaveEntityDataView.as_view(),name="save-data"),
    path("get-minio-doc-path",MinioPathView.as_view(),name="get-minio-doc-path"),
    path("document-list",DocumentListView.as_view(),name="document-list"),
    path("document-upload",DocumentUploadView.as_view(),name="document-upload"),
    path("fetch-documents",DocumentCenterView.as_view(),name="fetch-upload"),
    path("save-el-data-in-dc", ELDocumentCenterView.as_view(),name="save-el-data-in-dc"),
    path("get-purpose-documents", PurposeWiseDocumentView.as_view(),name="get-purpose-documents") 
]
