import re
from pathlib import Path
from urllib.parse import urlparse
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import random
import time
import hashlib
import os
from io import BytesIO
from PIL import Image
import mimetypes
import qrcode
import logging
from django.conf import settings
from libsv1.utils.string import StringUtils


class FileUtils:
    @staticmethod
    def read_lines_backward(filename, encoding='utf-8'):
        with open(filename, 'rb') as f:
            f.seek(0, os.SEEK_END)
            buffer = bytearray()
            while f.tell() > 0:
                chunk_size = min(f.tell(), 4096)
                f.seek(-chunk_size, os.SEEK_CUR)
                chunk = f.read(chunk_size)
                buffer = chunk + buffer
                while b'\n' in buffer:
                    _, _, line_bytes = buffer.rpartition(b'\n')
                    buffer, _, _ = buffer.rpartition(b'\n')
                    yield line_bytes.decode(encoding, errors='ignore').strip()
            if buffer:
                yield buffer.decode(encoding, errors='ignore').strip()

    @staticmethod
    def delete_file(file_name=None):
        if file_name and not StringUtils.is_url(file_name):
            if file_name and not file_name.startswith('/'):
                file_name = '/' + file_name

            file_path = str(settings.MEDIA_ROOT) + str(file_name)
            if FileUtils.exists_file(file_path=file_path):
                if not "no_delete_" in str(file_name):
                    os.remove(file_path)
                return True
        return False

    @staticmethod
    def exists_file(file_name=None, file_path=None):
        if file_name and not file_name.startswith('/'):
            file_name = '/' + file_name

        if file_name:
            file_path = str(settings.MEDIA_ROOT) + str(file_name)
        if not file_path:
            return False
        if os.path.exists(file_path):
            return True
        return False

    @staticmethod
    def generate_qr_code(code, size=1000):
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=int(size / 25),
            border=1,
        )
        qr.add_data(code)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        return buffer

    @staticmethod
    def upload_files(path="", files=None, return_only_path=False):
        logging.getLogger("PIL").setLevel(logging.ERROR)
        if files is None:
            files = []

        path_files = []
        for file in files:
            original_ext = Path(file.name).suffix[1:].lower()

            if FileUtils.is_image(file) and original_ext in ['jpeg', 'jpg']:
                original_ext = 'jpeg'
                compressed_image = FileUtils.compress_image(file, 1280, 80, original_ext)

                file_name = FileUtils.generate_random_filename(file, original_ext)
                default_storage.save(f"{path}/{file_name}", ContentFile(compressed_image.read()))
                compressed_image.close()
            else:
                file_name = FileUtils.generate_random_filename(file, original_ext)
                default_storage.save(f"{path}/{file_name}", ContentFile(file.read()))

            if return_only_path:
                path_files.append(f"{path}/{file_name}")
            else:
                path_files.append(f"/media/{path}/{file_name}")

        return path_files

    @staticmethod
    def generate_random_filename(file, ext=None):
        timestamp = int(time.time())
        random_number = random.randint(100000, 999999)
        hash_input = f"{random_number}{timestamp}".encode()
        hashed_name = hashlib.sha256(hash_input).hexdigest()
        if ext:
            if ext == 'JPEG':
                ext = '.jpg'
            else:
                ext = f".{ext.lower()}"
        else:
            ext = os.path.splitext(file.name)[1]
        return f"{hashed_name}{ext}"

    @staticmethod
    def compress_image(image, max_width=1000, quality=60, ext='JPEG'):
        img = Image.open(image)
        img = img.convert("RGB")
        img.thumbnail((max_width, max_width))
        output = BytesIO()
        img.save(output, format=ext, quality=quality)
        output.seek(0)
        return output

    @staticmethod
    def is_image(file):
        mime_type, _ = mimetypes.guess_type(file.name)
        return mime_type and mime_type.startswith('image/')

    @staticmethod
    def get_media_path_from_allowed_url(url):
        if url is None:
            return None

        allowed_hosts = settings.ALLOWED_HOSTS
        if allowed_hosts == ['*']:
            allowed_hosts = list(settings.ALL_HOSTS)

        if allowed_hosts and url:
            origin_url = url
            allowed_hosts_pattern = '|'.join(re.escape(host) for host in allowed_hosts)
            if re.match(r'^http(s)?://(' + allowed_hosts_pattern + r')', url):
                url = urlparse(url).path
                url = url.replace(settings.MEDIA_URL, '')
            if not url:
                url = origin_url
        return url