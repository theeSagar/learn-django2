from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from .views import *

urlpatterns = [
    path(
        "know-your-approvals",
        KnowYourApprovalView.as_view(),
        name="know-your-approval",
    ),
    path(
        "get-sector-approvals",
        SectorApprovalView.as_view(),
        name="get-sector-approvals",
    ),
    path(
        "get-subsector-approvals",
        SubSectorApprovalView.as_view(),
        name="get-subsector-approvals",
    ),
    path(
        "get-exemption-approvals",
        ExemptionApprovalView.as_view(),
        name="get-exemption-approvals",
    ),
    path(
        "get-industrial-area",
        GetIndustrialAreaView.as_view(),
        name="get-industrial-area"
    ),
    path(
        "get-approval-by-question",
        GetApprovalByQuestionView.as_view(),
        name="get-approval-by-question"
    ),
    path(
        "save-user-approvals",
        UserApprovalView.as_view(),
        name="save-user-approvals"
    ),
    path(
        "service-list",
        UserCAFServiceView.as_view(),
        name="service-list"
    ),
    path(
        "approval-pdf",
        ApprovalPDFView.as_view(),
        name="approval-pdf"
    ),
    path(
        "common-approvals",
        CommonApprovalView.as_view(),
        name="common-approvals"
    ),
    path(
        "download-user-approvals",
        DownloadApprovalView.as_view(),
        name="download-user-approvals"
    )     
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
