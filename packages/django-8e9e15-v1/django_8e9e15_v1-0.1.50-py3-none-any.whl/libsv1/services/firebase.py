import json
import requests
from django.conf import settings


class FirebaseService:
    @staticmethod
    def send(action, data=None, headers=None, request=None):
        if data is None:
            data = {}
        if headers is None:
            headers = {}

        url = f'https://identitytoolkit.googleapis.com/v1/{action}?key={settings.FIREBASE_AUTH_KEY}'
        default_headers = {
            'Content-Type': 'application/json',
        }
        all_headers = {**default_headers, **headers}

        try:
            response = requests.post(url, headers=all_headers, data=json.dumps(data))
            response_data = response.json()
            return response_data
        except Exception as e:
            if request is not None:
                try:
                    from libsv1.apps.global_system_log.services import GlobalSystemLogAdd
                    from libsv1.utils.base import BaseUtils
                    GlobalSystemLogAdd(request=request, firebase_logs={'FirebaseService': BaseUtils.log_response_error(locals().get('response'), e)})
                except Exception as e:
                    print(f"FirebaseService: {e}")

        return None

    @staticmethod
    def get_id_token(email, sign_up=True, request=None):
        id_token = FirebaseService.sign_in(email, request=request)
        if not id_token and sign_up:
            id_token = FirebaseService.sign_up(email, request=request)
        return id_token

    @staticmethod
    def sign_in_with_phone_number(phone_number, code, session_info, request=None):
        response = FirebaseService.send('accounts:signInWithPhoneNumber', {
            'phoneNumber': phone_number,
            'code': code,
            'sessionInfo': session_info,
        }, request=request)
        if response and 'idToken' in response:
            FirebaseService.id_token = response['idToken']
            return response['idToken']
        return False

    @staticmethod
    def send_verification_code(phone_number, request=None):
        response = FirebaseService.send('accounts:sendVerificationCode', {
            'phoneNumber': phone_number,
            'recaptchaSiteKey': '6LcMZR0UAAAAALgPMcgHwga7gY5p8QMg1Hj-bmUv',
        }, request=request)
        return response if response else False

    @staticmethod
    def sign_up(email, request=None):
        response = FirebaseService.send('accounts:signUp', {
            'email': email,
            'password': settings.FIREBASE_USER_PASSWORD,
            'returnSecureToken': True,
        }, request=request)
        if response and 'idToken' in response:
            return response['idToken']
        return False

    @staticmethod
    def sign_in(email, request=None):
        response = FirebaseService.send('accounts:signInWithPassword', {
            'email': email,
            'password': settings.FIREBASE_USER_PASSWORD,
            'returnSecureToken': True,
        }, request=request)
        if response and 'idToken' in response:
            return response['idToken']
        return False

    @staticmethod
    def get_account(email, request=None):
        id_token = FirebaseService.get_id_token(email, request=request)
        if id_token:
            response = FirebaseService.send('accounts:lookup', {
                'idToken': id_token,
            }, request=request)
            if response and 'users' in response and response['users']:
                return response['users'][0]
        return False

    @staticmethod
    def email_verification_send(email, request=None):
        id_token = FirebaseService.get_id_token(email, request=request)
        if id_token:
            response = FirebaseService.send('accounts:sendOobCode', {
                'requestType': "VERIFY_EMAIL",
                'idToken': id_token,
            }, {'X-Firebase-Locale': settings.LANGUAGE_CODE}, request=request)
            return True if response and 'kind' in response else False
        return False

    @staticmethod
    def email_verification_check(oob_code, request=None):
        response = FirebaseService.send('accounts:update', {
            'oobCode': oob_code,
        }, request=request)
        if response and 'email' in response:
            return response['email']
        return False

    @staticmethod
    def delete_account(email, request=None):
        id_token = FirebaseService.get_id_token(email, False, request=request)
        if id_token:
            response = FirebaseService.send('accounts:delete', {
                'idToken': id_token,
            }, request=request)
            return True if response and 'kind' in response else False
        return False

    @staticmethod
    def reset_password_verification_send(email, request=None):
        FirebaseService.get_id_token(email, request=request)
        response = FirebaseService.send('accounts:sendOobCode', {
            'requestType': 'PASSWORD_RESET',
            'email': email,
        }, {'X-Firebase-Locale': settings.LANGUAGE_CODE}, request=request)
        return True if response and 'kind' in response else False

    @staticmethod
    def reset_password_verification_check(oob_code, request=None):
        response = FirebaseService.send('accounts:resetPassword', {
            'oobCode': oob_code,
        }, request=request)
        if response and 'email' in response:
            return response['email']
        return False
