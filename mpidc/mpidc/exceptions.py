import traceback
from rest_framework.views import exception_handler
from django.core.exceptions import ObjectDoesNotExist
from userprofile.models import ExceptionLog

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    view = context.get('view', None)
    request = context.get('request', None)

    view_name = view.__class__.__name__ if view else "UnknownAPI"
    method = request.method if request else "UNKNOWN_METHOD"

    api_name = f"{view_name} [{method}]"
    error_message = str(exc)
    stack = traceback.format_exc()

    ExceptionLog.objects.create(
        api_name=api_name,
        error_message=error_message,
        stack_trace=stack
    )

    if response is not None:
        response.data = {
            "status": False,
            "message": "Sorry, we are facing some technical issue. Please try again later.",
            "data": {}
        }
    else:
        if isinstance(exc, ObjectDoesNotExist):
            from rest_framework.response import Response
            from rest_framework import status
            return Response({
                "status": False,
                "message": "Sorry, we are facing some technical issue. Please try again later.",
                "data": {}
            }, status=status.HTTP_400_BAD_REQUEST)

    return response
