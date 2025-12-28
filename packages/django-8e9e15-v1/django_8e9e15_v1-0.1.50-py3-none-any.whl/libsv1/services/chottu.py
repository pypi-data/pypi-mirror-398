import os
import requests
from django.conf import settings
from urllib.parse import urlencode, urljoin

class ChottuService:

    @staticmethod
    def create_deeplink_url(action, params=None, request=None):
        base_url = getattr(settings, 'BASE_URL', 'http://127.0.0.1:8000')

        params = params or {}
        params.update({'action': action})
        query_string = urlencode(params) if params else ""

        headers = {
            "API-KEY": getattr(settings, 'CHOTTULINK_API_KEY', os.getenv('CHOTTULINK_API_KEY', '')),
            "Content-Type": "application/json"
        }
        payload = {
            "destination_url": f"{base_url}?{query_string}" if query_string else base_url,
            "domain": getattr(settings, 'CHOTTULINK_DOMAIN', os.getenv('CHOTTULINK_DOMAIN', '')),
            "link_name": action,
            "ios_behavior": 2,
            "android_behavior": 2,
        }

        try:
            response = requests.post('https://api2.chottulink.com/chotuCore/pa/v1/create-link', json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data.get('short_url')
        except requests.exceptions.RequestException as e:
            if request is not None:
                try:
                    from libsv1.apps.global_system_log.services import GlobalSystemLogAdd
                    from libsv1.utils.base import BaseUtils
                    GlobalSystemLogAdd(request=request, additional_log={'ChottuService': BaseUtils.log_response_error(locals().get('response'), e)})
                except Exception as e:
                    print(f"ChottuService: {e}")

        return None
