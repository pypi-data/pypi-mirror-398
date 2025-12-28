from django.conf import settings
from libsv1.utils.base import BaseUtils
from django.utils.deprecation import MiddlewareMixin


class UpdateRequestMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request.client_ip = BaseUtils.get_client_ip(request)
        request.is_dev_ip = "*" in settings.DEV_IPS or request.client_ip in settings.DEV_IPS

        host = request.get_host()
        scheme = request.scheme

        request.base_host = host
        request.base_url = f"{scheme}://{host}"
        request.media_full_url = request.base_url + settings.MEDIA_URL
        request.static_full_url = request.base_url + settings.STATIC_URL

        settings.ALL_HOSTS.add(host)
        if settings.BASE_HOST_NAME in ['localhost', '127.0.0.1']:
            settings.BASE_URL = request.base_url
            settings.MEDIA_FULL_URL = request.base_url + settings.MEDIA_URL
            settings.STATIC_FULL_URL = request.base_url + settings.STATIC_URL

"""
```python
# settings.py
MIDDLEWARE = [
    # ...
    'libsv1.middlewares.update_request.UpdateRequestMiddleware',
    # ...
]
```
"""