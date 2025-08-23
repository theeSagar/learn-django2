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

from django.urls import path
from .views import *
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path("guest-incentive-calculator", GuestIncentiveCalculator.as_view(), name="guest-incentive-calculator"),
    path("user-incentive-calculator", UserIncentiveCalculator.as_view(), name="user-incentive-calculator"),
    path("get-intention-id",UserIncentiveId.as_view(),name="get-intention-id"),
    path("caf",IncentiveCAFView.as_view(),name="caf"),
    path("caf-incentive-detail",InCAFIncentiveView.as_view(),name="caf-incentive-detail"),
    path("caf-project-detail",CafProjectDetail.as_view(),name="caf-project-detail"),
    path("caf-other-detail",CafOtherDetailView.as_view(),name="caf-other-detail"),
    path("document-list",DocumentListView.as_view(),name="document-list"),
    path("upload-documents",UploadDocumentsView.as_view(),name="upload-documents"),
    path("caf-form-status",CheckCafFormStatusView.as_view(),name="caf-form-status"),
    path("caf-form-submission",CAFSubmissionView.as_view(),name="caf-form-submission"),
    path('incentive-agenda', IncentiveAgendaView.as_view(), name='incentive-agenda'),
    path('workflow', WorkflowActionView.as_view(), name='incentive-workflow'),
    path('caf-list', IncentiveCAFListView.as_view(), name='caf-list'),
    path('slec-order', SlecOrderView.as_view(),name='slec-order'),
    path('view-intention', IntentionDetailsListView.as_view(),name='view-intention'),
    path('view-caf-documents',ViewCafDocumentsView.as_view(),name='view-caf-documents'),
    path('audit_logs',IncentiveAuditLogListView.as_view(),name='audit_logs'),
    path('activity-history', IncentiveActivityHistoryListView.as_view(), name='incentive-activity-history'),
    path('calculator-dynamics',IncentiveCalculatorDynamicView.as_view(),name='calculator-dynamics'),
    path('create-incentive',IncentiveGenerateView.as_view(),name='create-incentive'),
    path('create-slec-year',IncentiveGenerateYearView.as_view(),name='create-slec-year'),
    path('create-claims',IncentiveClaimDataView.as_view(),name='create-claims'),
    path('offline-intention',OfflineIntentionDataView.as_view(),name='offline-intention'),
    path('offline-incentive-data',OfflineIncentiveDataView.as_view(),name='offline-incentive-data'),
    path('incentive-queries',IncentiveQueryDataView.as_view(),name='incentive-queries'),
    path('user-query-response',IncentiveQueryDetailView.as_view(),name='user-query-response'),
    path('upload-slec-document',InCAFSLECDocumentUploadView.as_view(),name='upload-slec-document'),
    path('slec-arrear',SLECArrearView.as_view(),name='slec-arrear'),
    path('update_signed_caf_pdf', UpdateSignedCAFView.as_view(), name='update_signed_caf_pdf'),
    path("agenda-pdf", AgendaPDFView.as_view(),name="agenda-pdf"),
    path("update-signed-agenda-pdf", UpdateSignedAgendaView.as_view(),name="update-signed-agenda-pdf")

]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

