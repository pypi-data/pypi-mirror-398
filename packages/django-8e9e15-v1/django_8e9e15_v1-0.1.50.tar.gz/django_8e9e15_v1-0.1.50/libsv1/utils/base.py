from __future__ import annotations
from typing import Any
from collections import deque
from libsv1.utils.carbon import Carbon
from django.conf import settings


class BaseUtils:
    class DictToObject:
        def __init__(self, dictionary: dict[str, Any]) -> None:
            for key, value in dictionary.items():
                setattr(self, key, value)

    @staticmethod
    def is_unique(items: list) -> bool:
        return len(items) == len(set(items))

    @staticmethod
    def filter_dataset(dataset: dict[str, Any], include_dates: tuple[str, str], exclude_dates: tuple[str, str] | None = None, return_as_list: bool = False) -> list[Any] | dict[str, Any]:
        start_ts, end_ts = Carbon.parse(include_dates[0]).timestamp(), Carbon.parse(include_dates[1]).timestamp()

        exclude_ranges = []
        if exclude_dates:
            exclude_start, exclude_end = Carbon.parse(exclude_dates[0]).timestamp(), Carbon.parse(exclude_dates[1]).timestamp()
            exclude_ranges.append((exclude_start, exclude_end))

        filtered_items = {
            ts: data for ts, data in dataset.items()
            if start_ts <= int(ts) <= end_ts and not any(start <= int(ts) <= end for start, end in exclude_ranges)
        }

        return list(filtered_items.values()) if return_as_list else filtered_items

    @staticmethod
    def append_to_array(array: list[Any], value: Any, max_count: int = 10) -> None:
        if len(array) >= max_count:
            d = deque(array, maxlen=max_count)
            d.append(value)
            array.clear()
            array.extend(d)
        else:
            array.append(value)

    @staticmethod
    def generate_token() -> str:
        import secrets
        return secrets.token_urlsafe(100)

    @staticmethod
    def change_list_fields(fields: list[str], add_fields: list[str] | None = None, exclude_fields: list[str] | None = None) -> list[str]:
        field_set = set(fields)
        if add_fields:
            field_set.update(add_fields)
        if exclude_fields:
            field_set.difference_update(exclude_fields)
        return list(field_set)

    @staticmethod
    def decode_apple_jws(jws_token: str) -> dict[str, Any]:
        import jwt
        from cryptography.x509 import load_der_x509_certificate
        from cryptography.hazmat.backends import default_backend
        import base64

        headers = jwt.get_unverified_header(jws_token)
        if headers.get("alg") != "ES256":
            raise ValueError("Invalid algorithm: 'alg' must be 'ES256'")

        x5c_certs = headers.get("x5c")
        if not x5c_certs:
            raise ValueError("Certificate chain 'x5c' is missing from headers")

        cert_der = base64.b64decode(x5c_certs[0])
        cert = load_der_x509_certificate(cert_der, default_backend())
        public_key = cert.public_key()

        return jwt.decode(
            jws_token,
            public_key,
            algorithms=["ES256"],
            options={"verify_exp": True, "verify_aud": False}
        )

    @staticmethod
    def decode_base64(data: str) -> dict | str | None:
        import base64
        import json
        try:
            decoded_bytes = base64.b64decode(data)
            decoded_str = decoded_bytes.decode("utf-8")
            try:
                return json.loads(decoded_str)
            except json.JSONDecodeError:
                return decoded_str
        except (ValueError, TypeError, UnicodeDecodeError):
            return None

    @staticmethod
    def get_data_type(data: Any) -> str:
        if data is None: return "none"
        if isinstance(data, str): return "str"
        if isinstance(data, bool): return "bool"
        if isinstance(data, int): return "int"
        if isinstance(data, float): return "float"
        if isinstance(data, dict): return "dict"
        if isinstance(data, list):
            if not data:
                return "list"
            item_type = type(data[0])
            if all(isinstance(item, item_type) for item in data):
                return f"list_{item_type.__name__.lower()}"
            return "list"
        return "unknown"

    @staticmethod
    def get_client_ip(request: Any) -> str | None:
        if x_forwarded_for := request.META.get("HTTP_X_FORWARDED_FOR"):
            return x_forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR")

    @staticmethod
    def get_key_from_password(password, salt=b''):
        import base64
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key

    @staticmethod
    def encrypt_text(text, passwd=None, get_as_bytes=False):
        from cryptography.fernet import Fernet
        if passwd is None:
            passwd = getattr(settings, 'SECRET_KEY', 'SECRET_KEY')
        key = BaseUtils.get_key_from_password(passwd)
        cipher = Fernet(key)
        encrypted_text = cipher.encrypt(text.encode('utf-8'))
        if not get_as_bytes:
            encrypted_text = encrypted_text.decode('utf-8')
        return encrypted_text

    @staticmethod
    def decrypt_text(text, passwd=None):
        from cryptography.fernet import Fernet
        if passwd is None:
            passwd = getattr(settings, 'SECRET_KEY', 'SECRET_KEY')
        key = BaseUtils.get_key_from_password(passwd)
        cipher = Fernet(key)
        if isinstance(text, str):
            text = text.encode('utf-8')
        try:
            decrypted_text = cipher.decrypt(text).decode('utf-8')
            return decrypted_text
        except Exception as e:
            pass
        return None

    @staticmethod
    def log_response_error(response=None, e=None):
        log = {}

        if response is not None:
            log['global_error'] = str(response)
            log['url'] = str(response.url)
            log['body'] = str(response.request.body)

            try:
                log['response'] = str(response.json())
            except ValueError:
                log['response'] = str(response.text)

        if e:
            log['e'] = str(e)

        return log

