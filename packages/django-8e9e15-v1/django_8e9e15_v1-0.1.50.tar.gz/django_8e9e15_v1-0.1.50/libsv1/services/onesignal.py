import json
import os
import re
import requests
from django.conf import settings


class OnesignalService:

    @staticmethod
    def send(onesignal_tokens=None, message='New message', data_to_send=None, title=None, request=None):

        if title is None:
            title = getattr(settings, 'PROJECT_NAME', os.getenv('PROJECT_NAME', ''))

        if not onesignal_tokens:
            return False
        if not isinstance(onesignal_tokens, list):
            onesignal_tokens = [onesignal_tokens]

        valid_onesignal_tokens = [
            token for token in onesignal_tokens if re.match(r'^[a-z0-9]{8}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{12}$', token)
        ]

        if not valid_onesignal_tokens:
            return False

        onesignal_app_id = getattr(settings, 'ONESIGNAL_APP_ID', os.getenv('ONESIGNAL_APP_ID', ''))
        onesignal_api_key = getattr(settings, 'ONESIGNAL_API_KEY', os.getenv('ONESIGNAL_API_KEY', ''))

        if not onesignal_app_id or not onesignal_api_key:
            return False

        data = {
            'app_id': onesignal_app_id,
            'include_player_ids': valid_onesignal_tokens,
            'data': data_to_send or {},
            'contents': {"en": message},
            'headings': {"en": title},
        }

        headers = {
            'Content-Type': 'application/json; charset=utf-8',
            'Authorization': f'Basic {onesignal_api_key}',
        }

        try:
            response = requests.post('https://onesignal.com/api/v1/notifications', headers=headers, data=json.dumps(data))
            response.raise_for_status()
            response_data = response.json()
            return True
        except requests.exceptions.RequestException as e:
            if request is not None:
                try:
                    from libsv1.apps.global_system_log.services import GlobalSystemLogAdd
                    from libsv1.utils.base import BaseUtils
                    GlobalSystemLogAdd(request=request, onesignal_logs={'OnesignalService': BaseUtils.log_response_error(locals().get('response'), e)})
                except Exception as e:
                    print(f"OnesignalService: {e}")

        return False


"""

OneSignalRepository.send(onesignal_tokens=user.onesignal_token, message=f"Subscription Request from {user.full_name}", data_to_send={
    'id': str(user.id),
    'action': 'sent_subscription_request',
}, request)
        
"""