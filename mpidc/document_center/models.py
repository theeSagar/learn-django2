from django.db import models
from authentication.models import User
from incentive.models import DocumentList

# Create your models here.

class TimeStampModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class SessionEntityLocker(TimeStampModel):
    user=models.ForeignKey(User, on_delete=models.CASCADE, null=False)
    event_type=models.CharField(max_length=100, null=True, blank=True)
    session_id = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = "session_entity_locker"

class EntityDocumentCenter(TimeStampModel):
    user=models.ForeignKey(User, on_delete=models.CASCADE, null=False)
    session_id = models.CharField(max_length=255, null=True, blank=True)
    file_name=models.CharField(max_length=100, null=True, blank=True)
    file_type=models.CharField(max_length=100, null=True, blank=True)
    minio_path=models.CharField(max_length=100, null=True, blank=True)
    document_type=models.CharField(max_length=100, null=True, blank=True)
    document_source=models.CharField(max_length=100, null=True, blank=True)
    application_type=models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        db_table= "entity_document_center"

class UserDocumentCenter(TimeStampModel):
    user=models.ForeignKey(User, on_delete=models.CASCADE, null=False)
    document = models.ForeignKey(DocumentList, on_delete=models.CASCADE, null=True, blank=True)
    document_name = models.CharField(max_length=255, null=True, blank=True)
    session_id = models.CharField(max_length=255, null=True, blank=True)
    source = models.CharField(max_length=50, null=True, blank=True, help_text="digilocker, entity, manual")
    file_name=models.CharField(max_length=100, null=True, blank=True)
    file_type=models.CharField(max_length=100, null=True, blank=True)
    entity_doc_type = models.CharField(max_length=50, null=True, blank=True, help_text="Document Type")
    digi_doc_type = models.CharField(max_length=50, null=True, blank=True, help_text="Digi doc Type")
    minio_path=models.TextField(null=True, blank=True)
    
    class Meta:
        db_table= "document_center"

class DocumentEvent(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        db_table= "document_events"

class DocumentEventBased(models.Model):
    document = models.ForeignKey(DocumentList, on_delete=models.CASCADE, null=True, related_name="event_docs")
    event = models.ForeignKey(DocumentEvent, on_delete=models.CASCADE, null=True, related_name="doc_events")

    class Meta:
        db_table= "document_based_on_event"

class VersionControlTracker(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    doc_url = models.CharField(max_length=255, null=False, blank=False)
    doc_name = models.CharField(max_length=50, null=True, blank=True)
    module_name = models.CharField(max_length=50, null=True, blank=True)
    doc_id = models.ForeignKey(DocumentList, on_delete=models.CASCADE, null=True, blank=True)
    version_no = models.SmallIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "version_control_tracker"
