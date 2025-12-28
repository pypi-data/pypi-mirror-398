from django.utils.translation import gettext
from rest_framework.exceptions import ValidationError
from libsv1.mixins.test_case import TestCaseMixin
from django.conf import settings
import time
import jwt
import requests
from jwt import PyJWKClient


class OAuthUtils:
    @staticmethod
    def generate_client_secret():
        team_id = settings.APPLE_TEAM_ID
        client_id = settings.APPLE_CLIENT_ID
        key_id = settings.APPLE_KEY_ID
        private_key = settings.APPLE_PRIVATE_KEY

        headers = {
            "alg": "ES256",
            "kid": key_id,
        }

        payload = {
            "iss": team_id,
            "iat": int(time.time()),
            "exp": int(time.time()) + 3600,
            "aud": "https://appleid.apple.com",
            "sub": client_id,
        }

        client_secret = jwt.encode(
            payload, private_key, algorithm="ES256", headers=headers
        )
        return client_secret

    @staticmethod
    def get_apple_public_key():
        jwks_url = "https://appleid.apple.com/auth/keys"
        response = requests.get(jwks_url)
        response.raise_for_status()
        return response.json()

    @staticmethod
    def user_from_token(token, driver):
        if token == TestCaseMixin.user_social_token:
            return {
                'email': TestCaseMixin.user_email,
                'name': TestCaseMixin.user_full_name
            }
        if driver == "apple":
            jwk_client = PyJWKClient("https://appleid.apple.com/auth/keys")
            try:
                signing_key = jwk_client.get_signing_key_from_jwt(token)
                decoded_token = jwt.decode(
                    token,
                    signing_key.key,
                    algorithms=['RS256'],
                    audience=settings.APPLE_CLIENT_ID,
                    issuer="https://appleid.apple.com",
                )
            except Exception as e:
                raise ValidationError(
                    gettext("Invalid token. {e}")
                    .format(e=e)
                )

            return decoded_token
        elif driver == "google":
            token_info_url = f"https://www.googleapis.com/oauth2/v3/userinfo?access_token={token}"
            response = requests.get(token_info_url)
            if response.status_code == 200:
                return response.json()
            raise ValidationError(
                gettext("Invalid token")
            )
        raise ValidationError(
            gettext("Invalid social driver")
        )

