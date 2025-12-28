import os
import requests
from django.conf import settings


class TwilioService:

    @staticmethod
    def send_sms(phone_number=None, msg=None, request=None):
        if not phone_number or not msg:
            return False

        twilio_account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', os.getenv('TWILIO_ACCOUNT_SID', ''))
        twilio_auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', os.getenv('TWILIO_AUTH_TOKEN', ''))
        twilio_phone_number = getattr(settings, 'TWILIO_PHONE_NUMBER', os.getenv('TWILIO_PHONE_NUMBER', ''))

        url = f"https://api.twilio.com/2010-04-01/Accounts/{twilio_account_sid}/Messages.json"
        data = {
            "To": phone_number,
            "From": twilio_phone_number,
            "Body": msg
        }
        auth = (twilio_account_sid, twilio_auth_token)

        try:
            response = requests.post(url, data=data, auth=auth)
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            if request is not None:
                try:
                    from libsv1.apps.global_system_log.services import GlobalSystemLogAdd
                    from libsv1.utils.base import BaseUtils
                    GlobalSystemLogAdd(request=request, additional_log={'TwilioService': BaseUtils.log_response_error(locals().get('response'), e)})
                except Exception as e:
                    print(f"TwilioService: {e}")

        return False
