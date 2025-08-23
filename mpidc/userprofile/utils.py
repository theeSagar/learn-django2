import logging
from rest_framework import status
from rest_framework.response import Response
from .models import *
logger = logging.getLogger(__name__)
from django.conf import settings
global_err_message = settings.GLOBAL_ERR_MESSAGE


def getErrorMessage(errors):
    formatted_errors = {field: errors[field][0] for field in errors}
    return {"status": False, "message": formatted_errors}


def getSuccessfulMessage(data, message):
    return {"status": True, "message": message, "data": data}


def getOtherMessage(data, message):
    return {"status": False, "message": message, "data": data}


class NotificationMixin:
    def send_notification(self, *args, **kwargs):
        try:
           
            for user_id in kwargs['user_ids']:
                user = User.objects.get(id=user_id)
                Notification.objects.create(
                    user=user, 
                    title=kwargs['title'],
                    message=kwargs['message'], 
                    is_read=False 
                )
            
            return Response(
                {
                    "status": True,
                    "message": "Notifications sent successfully.",
                    "data": []
                },
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            logger.error(f"Failed to send notification: {global_err_message}", exc_info=True)
            return Response(
                {
                    "status": False,
                    "message": "Error while sending notification",
                    "error": global_err_message,
                    "data": {},
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def get_user_ids_by_role(self, role_name):  

        try:
            role = Role.objects.filter(role_name=role_name).first()
            user_ids = UserHasRole.objects.filter(role=role).values_list('user', flat=True)
            return list(user_ids)
        except Exception as e:
            logger.error(global_err_message, exc_info=True)
            return []
