import requests
from django.conf import settings
from document_center.models import *
from django.conf import settings
global_err_message = settings.GLOBAL_ERR_MESSAGE

def minio_func(path):
    url = settings.MINIO_API_URL
    payload = {"path": path}

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return True, response.json()
        # return True, path
    
    except requests.exceptions.RequestException as e:
        return False, global_err_message
    

def upload_files_to_minio(documents, url, document_folder):
    files = []
    for doc in documents:
        file_obj = doc["file"]
        files.append(
            ('files', (file_obj.name, file_obj.read(), file_obj.content_type))
        )

    data = {
        'bucketName': settings.MINIO_BUCKET,
        'folderName': document_folder,
    }

    try:
        res = requests.post(url, data=data, files=files )
        res.raise_for_status()
        return {
            "success": True,
            "data": res.json().get("data", [])  # adjust key if needed
        }
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": global_err_message,
            "response": getattr(e.response, 'text', '')
        }

    
def version_control_tracker(user_id, doc_url, module_name, doc_name=None, doc_id=None):

    version_no=0
    version_user_id=VersionControlTracker.objects.filter(user_id=user_id)
    if doc_id:
        queryset=version_user_id.filter(doc_id=doc_id)
    else:
        queryset=version_user_id.filter(doc_name=doc_name)

    if queryset.exists():
        latest_version_no=queryset.order_by('-version_no').first()
        version_no=latest_version_no.version_no + 1 if latest_version_no else 1
    else:
        version_no=1

    VersionControlTracker.objects.create(
        user_id=user_id,
        doc_url=doc_url,
        version_no=version_no,
        module_name=module_name,
        doc_name=doc_name,
        doc_id=doc_id
    )

