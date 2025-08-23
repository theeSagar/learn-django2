from rest_framework import serializers
from .models import *
from authentication.models import CustomUserProfile

class SessionEntityLockerSerializer(serializers.ModelSerializer):

    class Meta:
        model=SessionEntityLocker
        fields="__all__"

class CustomUserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model=CustomUserProfile
        fields = '__all__'

class EntityDocumentCenterSerializer(serializers.ModelSerializer):

    class Meta:
        model=EntityDocumentCenter
        # fields="__all__"
        exclude=("created_at","updated_at") # is used when need to exclude any feild better.

class DocumentEventBasedSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='document.name', read_only=True)
    title = serializers.CharField(source='document.tile', read_only=True)
    file_type = serializers.CharField(source='document.file_type', read_only=True)
    entity_doc_type = serializers.CharField(source='document.entity_doc_type', read_only=True)
    digi_doc_type = serializers.CharField(source='document.digi_doc_type', read_only=True)
    template_file_path = serializers.CharField(source='document.template_file_path', read_only=True)

    class Meta:
        model=DocumentEventBased
        fields= ['document','name', 'title', 'file_type', 'entity_doc_type', 'digi_doc_type','template_file_path','event']

class UserDocumentCenterSerializer(serializers.ModelSerializer):

    class Meta:
        model=UserDocumentCenter
        fields= ['document_name', 'file_type','entity_doc_type','digi_doc_type','document_id','minio_path','source']
