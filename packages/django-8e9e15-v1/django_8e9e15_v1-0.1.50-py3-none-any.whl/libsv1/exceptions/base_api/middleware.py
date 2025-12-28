import traceback
import platform
from django.conf import settings
from rest_framework import status
from django.http import JsonResponse, HttpResponse, Http404
from libsv1.utils.base import BaseUtils


class CustomExceptionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        if isinstance(exception, Http404):
            return None

        trace_error = traceback.format_exc()
        message_error = str(exception).strip()
        trace_error = trace_error.splitlines()

        if any(request.path.startswith(prefix) for prefix in settings.API_PREFIXES):
            response_error = {
                'title': 'Oops!',
                'message': 'A server error occurred.',
                'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR
            }

            try:
                from libsv1.apps.global_system_log.services import GlobalSystemLogAdd
                GlobalSystemLogAdd(request=request, trace_error=trace_error, message_error=message_error)
            except Exception as e:
                pass

            if request.is_dev_ip or settings.DEBUG:
                response_error = {
                    'title': 'Oops!',
                    'message': 'A server error occurred.',
                    'message_error': message_error,
                    'trace_error': trace_error,
                    'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR
                }

            return JsonResponse(response_error, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if not (settings.DEBUG and platform.system() != "Linux" and BaseUtils.get_client_ip(request) == "127.0.0.1"):
            if request.is_dev_ip or settings.DEBUG:
                html_trace = "<br>".join(trace_error)
                return HttpResponse(f"<h2>500 Error Occurred</h2><p>{message_error}</p><pre>{html_trace}</pre>", content_type="text/html", status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                return HttpResponse(f"<h2>500 Error Occurred</h2>", content_type="text/html", status=status.HTTP_500_INTERNAL_SERVER_ERROR)