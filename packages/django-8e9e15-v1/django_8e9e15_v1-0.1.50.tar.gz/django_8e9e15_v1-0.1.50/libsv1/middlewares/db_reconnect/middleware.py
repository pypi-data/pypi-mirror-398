from django.db import OperationalError
from .core import close_old_connections, should_reconnect


class DBConnectionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            return self.get_response(request)
        except OperationalError as e:
            if should_reconnect(e):
                close_old_connections()
                return self.get_response(request)
            else:
                raise