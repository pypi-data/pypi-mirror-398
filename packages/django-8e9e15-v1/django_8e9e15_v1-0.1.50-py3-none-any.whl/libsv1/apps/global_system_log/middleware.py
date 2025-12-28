from .services import GlobalSystemLogAdd
from django.http import Http404
from rest_framework.response import Response
import uuid
from django.urls import get_resolver
from django.utils.module_loading import import_string
from django.views.defaults import page_not_found


class GlobalSystemLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def get_project_handler404(self):
        try:
            urlconf = get_resolver().urlconf_module
            handler = getattr(urlconf, 'handler404', None)

            if handler:
                if isinstance(handler, str):
                    return import_string(handler)
                return handler

            return page_not_found
        except Exception:
            return page_not_found

    def __call__(self, request):
        request.global_system_log_request_id = str(uuid.uuid4())
        GlobalSystemLogAdd(request=request)

        handler404_view = self.get_project_handler404()

        try:
            response = self.get_response(request)
        except Http404 as e:
            GlobalSystemLogAdd(request=request, response_error=str(e))
            return handler404_view(request, e)

        response_error = response.error_message if hasattr(response, 'error_message') else None
        GlobalSystemLogAdd(request=request, response=response, response_error=response_error)

        if response.status_code == 404:
            if isinstance(response, Response):
                return response
            return handler404_view(request, Http404('Page not found'))
        return response