import os, requests
from collections import defaultdict
from django.conf import settings
from django.db import connection
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework_simplejwt.authentication import JWTAuthentication
from authentication.models import CustomUserProfile
from document_center.serializer import *
from incentive.models import SectorDocumentList
from .utils import minio_func, upload_files_to_minio
from document_center.utils import *
from django.conf import settings
global_err_message = settings.GLOBAL_ERR_MESSAGE
# Create your views here.
class SaveSessionView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post (self,request):
        try:
            data = request.data
            user_id = request.user.id

            user_exists = CustomUserProfile.objects.filter(user_id=user_id).exists()
            if not user_exists:
                return Response({"status":False,
                                "message": "Invalid user_id"},
                                status=status.HTTP_400_BAD_REQUEST)

            event_type = data.get("event_type")
            session_id = data.get("session_id")

            if not event_type or not session_id:
                return Response({"status":False,
                                "message": "Required event_type and session_id"},
                                status=status.HTTP_400_BAD_REQUEST)

            data = {
                "user":user_id,
                "event_type": event_type,
                "session_id": session_id
            }

            serializer = SessionEntityLockerSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response({"status":True,
                                "message": "Data saved successfully"}, status=status.HTTP_201_CREATED)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                "status": False,
                "message": global_err_message
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class SaveEntityDataView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self,request):
        try:
            data=request.data
            user=request.user
            user_id = user.id

            event_type = data.get("event_type")
            session_id = data.get("session_id")

            if not session_id:                
                doc_exists = EntityDocumentCenter.objects.filter(user_id=user_id, application_type=event_type)
     
                if doc_exists.exists():
                    # If docs exist, return them directly
                    serializer = EntityDocumentCenterSerializer(doc_exists, many=True)
                    return Response({
                        "status": True,
                        "message": "Documents already exist.",
                        "data": serializer.data
                    })

            ENTITY_LOCKER_INTEGRATION_API = settings.ENTITY_LOCKER_INTEGRATION_API # this gets api url from settings.py

            payload = {
            "event_type": event_type,
            "session_id": session_id
        }
            response_ext = requests.post(ENTITY_LOCKER_INTEGRATION_API, json=payload) # this calls the api and passes payload

            if response_ext.status_code != 200:
                return Response({
                    "status":False,
                    "message": "No data found.",
                    "error": response_ext.text
                }, status=response_ext.status_code)
            
            api_response_data = response_ext.json()
            
            document_list = api_response_data.get("Data", [])

            if not document_list:
                return Response ({
                    "status":True,
                    "message":"No data found.",
                    "data":[]
                },status=200)

            session_from_api = document_list[0].get("session_id")

            session_entry = SessionEntityLocker.objects.filter(session_id=session_from_api).first()
            

            if not session_entry:
                return Response({
                    "status": False,
                    "message": f"No user found for session_id: {session_id}"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            user_id = session_entry.user_id

            saved_docs = []

            for doc in document_list:
                    doc_data = {
                    "file_name": doc.get("file_name"),
                    "file_type": doc.get("file_type"),
                    "minio_path": doc.get("minio_path"),
                    "document_source": doc.get("document_source"),
                }
                    
                    obj, created = EntityDocumentCenter.objects.update_or_create(
                    user_id=user_id,
                    document_type=doc.get("document_type"),
                    application_type=doc.get("application_type"),
                    defaults=doc_data
                )

                    serializer = EntityDocumentCenterSerializer(obj)
                    saved_docs.append(serializer.data)
            
            return Response({
            "message": "Documents saved successfully",
            "data": saved_docs
        }, status=status.HTTP_201_CREATED)
                        
        except Exception as e:
            return Response({
                "status":False,
                "message":global_err_message
            },status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class MinioPathView(APIView):
    def post(self,request):

        try:
            data=request.data
            path=data.get("path")

            success , result=minio_func(path)

            file_url = result.get("Fileurl") # this will extraxt inside the data fileurl.

            if not success:
                return Response({
                    "status": False,
                    "error": result
                }, status=status.HTTP_400_BAD_REQUEST)

            return Response({
                "status":True,
                "data": file_url
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                "status":False,
                "message":global_err_message
            },status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DocumentListView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self,request):
        try:
            doctype=request.query_params.get("doctype")
            if doctype:
                document_list = DocumentEventBased.objects.select_related("document", "event").filter(event__name=doctype)
                if document_list.exists():
                    filedata = DocumentEventBasedSerializer(document_list, many=True).data
                    return Response({
                        "status":True,
                        "message": "Data type get fetched successfully",
                        "data": filedata
                    }, status=status.HTTP_200_OK)
            
            return Response({
                    "status":False,
                    "message": "No Data found",
                    "data": []
                }, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            return Response({
                "status":False,
                "message":global_err_message
            },status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class DocumentUploadView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def post(self,request):
        try:
            user = request.user
            user_profile = CustomUserProfile.objects.filter(user=user).first()
            if user_profile:
                document_folder = user_profile.document_folder if user_profile.document_folder else user.id 
                documents, doc_type_data = [], []
                i = 0
                url = settings.MINIO_API_HOST+"/minio/uploads"
                while f'documents[{i}][file]' in request.FILES:
                    doc_file = request.FILES.get(f'documents[{i}][file]')
                    doc_type = request.data.get(f'documents[{i}][type]')
                    documents.append({
                        "file": doc_file,
                        "file_name": doc_file.name,
                        "file_type": doc_file.content_type
                    })
                    doc_type_data.append(int(doc_type))
                    i += 1
                upload_response  = upload_files_to_minio(documents, url, document_folder)
                if not upload_response["success"]:
                    return Response({
                        "status": False,
                        "message": "File upload failed",
                        "error": upload_response["error"],
                        "server_response": upload_response["response"]
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

                # Store document records in the database
                document_list_data = DocumentList.objects.filter(id__in=doc_type_data)
                if document_list_data:
                    document_data = {
                        doc.id: {
                            "document_name": doc.name,
                            "file_type": doc.file_type,
                            "entity_doc_type": doc.entity_doc_type,
                            "digi_doc_type": doc.digi_doc_type
                        }
                        for doc in document_list_data
                    }
                for idx, result in enumerate(upload_response["data"]):
                    doc = documents[idx]
                    document_id = doc_type_data[idx]
                    document_name = document_data[document_id]["document_name"] if document_data else ""
                    file_type = document_data[document_id]["file_type"] if document_data else None
                    entity_doc_type = document_data[document_id]["entity_doc_type"] if document_data else None
                    digi_doc_type = document_data[document_id]["digi_doc_type"] if document_data else None
                    
                    doc_data = {
                        "minio_path":  result.get("path"),
                        "file_name": result.get("path").split("/")[-1],
                        "source": "manual"
                    }
                    UserDocumentCenter.objects.update_or_create(
                        user=user,
                        document_id=document_id,
                        document_name=document_name,
                        file_type=file_type,
                        entity_doc_type=entity_doc_type,
                        digi_doc_type=digi_doc_type,
                        defaults=doc_data
                    )

                return Response({
                    "status": True,
                    "message": "Files uploaded and saved successfully",
                    "data": upload_response['data']
                }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                "status":False,
                "message":global_err_message
            },status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class DocumentCenterView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self,request):
        filedata = []
        user = request.user
        message = "No data found for this user"
        document_list = UserDocumentCenter.objects.filter(user_id=user.id)
        if document_list.exists():
            filedata = UserDocumentCenterSerializer(document_list, many=True).data
            message = "Data type get fetched successfully"
        return Response(
            {
                "status": True,
                "message": message,
                "data": filedata
            }, status=status.HTTP_200_OK
        )    

        

class ELDocumentCenterView(APIView):
    def post(self,request):
        try:
            documents = request.data.get("data", [])
            if documents:
                session_obj = SessionEntityLocker.objects.filter(session_id=documents[0]['session_id']).first()
                if session_obj:
                    user = User.objects.filter(id=session_obj.user_id).first()
                    if user:
                        id_list = []
                        for doc in documents:
                            document_type = doc["document_type"]
                            source = doc["document_source"]
                            session_id = doc["session_id"]
                            minio_path = doc["minio_path"]
                            document_obj = DocumentList.objects.filter(entity_doc_type=document_type).first()
                            if document_obj:
                                doc_data = {
                                    "minio_path":  minio_path,
                                    "file_name": minio_path.split("/")[-1],
                                    "session_id": session_id,
                                    "source": source
                                }
                                doc_center_obj, created = UserDocumentCenter.objects.update_or_create(
                                    user=user,
                                    document_id=document_obj.id,
                                    document_name=document_obj.name,
                                    file_type=document_obj.file_type,
                                    entity_doc_type=document_obj.entity_doc_type,
                                    digi_doc_type=document_obj.digi_doc_type,
                                    defaults=doc_data
                                )
                                id_list.append(doc_center_obj.id)
                                version_control_tracker(user.id,minio_path,"document_center",doc_id=document_obj)

                        return Response({
                            "status": True,
                            "message": "Files uploaded and saved successfully",
                            "data": id_list
                        }, status=status.HTTP_200_OK)
            return Response({
                "status": False,
                "message": "Data is not there",
                "data": []
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({
                "status":False,
                "message":global_err_message
            },status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PurposeWiseDocumentView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self,request):
        try:
            user=request.user
            document_list = DocumentEventBased.objects.all()
            if document_list.exists():
                file_array = {}
                sector_doc_map = defaultdict(list)
                filter_doc, claim_document_ids = [], []
                table_name = 'incentive_claim_document_list'
                with connection.cursor() as cursor:
                    # Check if the table exists
                    cursor.execute("""
                        SELECT to_regclass(%s)
                    """, [table_name])
                    result = cursor.fetchone()

                    if result and result[0] == table_name:
                        # Table exists, now run the select query
                        cursor.execute(f"SELECT document_id FROM {table_name}")
                        rows = cursor.fetchall()
                        claim_document_ids = [row[0] for row in rows]
                
                sector_incentive_list = SectorDocumentList.objects.select_related('sector', 'document').all()

                if sector_incentive_list.exists():
                    for item in sector_incentive_list:
                        sector_name = item.sector.name if item.sector else "All Sectors"
                        sector_doc_map[item.document.id].append(sector_name)
                for doc in document_list:
                    if doc.document.id in file_array:
                        file_array[doc.document.id].append(doc.event.name)
                    else:
                        file_array[doc.document.id] = [doc.event.name]
                        filter_doc.append(doc)
                filedata = DocumentEventBasedSerializer(filter_doc, many=True).data
                user_document_data = UserDocumentCenter.objects.filter(user_id=user.id)
                user_doc_list = []
                if user_document_data:
                    user_doc_list = [item.document.id for item in user_document_data]

                for doc in filedata:
                    doc['purpose'] = []
                    if doc['document'] in claim_document_ids:
                        doc['purpose'].append("Claim")
                    doc['sector'] = []
                    if doc['document'] in sector_doc_map:
                        doc['purpose'].append("Incentive")
                        doc['sector'] = sector_doc_map[doc['document']]

                    doc['is_uploaded'] = True if doc["document"] in user_doc_list else False
                    if doc["document"] in file_array:
                        doc['event'] = file_array[doc["document"]]
                       
                return Response({
                    "status":True,
                    "message": "Data type get fetched successfully",
                    "data": filedata
                }, status=status.HTTP_200_OK)
        
            return Response({
                "status":False,
                "message": "No Data found",
                "data": []
            }, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            return Response({
                "status":False,
                "message":global_err_message
            },status=status.HTTP_500_INTERNAL_SERVER_ERROR)


