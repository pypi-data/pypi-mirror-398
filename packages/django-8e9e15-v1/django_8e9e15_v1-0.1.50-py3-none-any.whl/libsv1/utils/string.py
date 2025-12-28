import ast
import csv
import datetime
import hashlib
import io
import json
import random
import re
import string
from typing import Any
from urllib.parse import urlparse


class StringUtils:
    @staticmethod
    def convert_to_csv_string(data_list: list[dict[str, Any]], fields_to_include: list[str] | None = None) -> str:
        if not data_list:
            return ""

        output = io.StringIO()
        available_headers = list(data_list[0].keys())

        headers = [h for h in fields_to_include if h in available_headers] if fields_to_include else available_headers

        writer = csv.DictWriter(output, fieldnames=headers, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(data_list)
        return output.getvalue()

    @staticmethod
    def parse_json_from_string(text: str, disable_strict: bool = False) -> Any:
        match = re.search(r'(\{.*\})', text, re.DOTALL)
        if not match:
            raise ValueError(f'Invalid JSON format: No JSON object found in string: {text}')

        json_string = match.group(1)
        try:
            return json.loads(json_string)
        except json.JSONDecodeError:
            if not disable_strict:
                raise ValueError(f'Invalid JSON format: {text}')
            try:
                return ast.literal_eval(json_string)
            except (ValueError, SyntaxError):
                raise ValueError(f'Invalid JSON format: {text}')

    @staticmethod
    def replace_data_string(data: Any, old_value: str, new_value: str) -> Any:
        if isinstance(data, list):
            return [StringUtils.replace_data_string(item, old_value, new_value) for item in data]
        if isinstance(data, dict):
            return {k: StringUtils.replace_data_string(v, old_value, new_value) for k, v in data.items()}
        if isinstance(data, str):
            return data.replace(old_value, new_value)
        return data

    @staticmethod
    def split_words(s: str) -> list[str]:
        return re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?![a-z])|\d+', s)

    @staticmethod
    def convert_case(text: str, case_type: str) -> str:
        words = StringUtils.split_words(text)
        if not words:
            return ""

        if case_type == 'PascalCase':
            return ''.join(word.capitalize() for word in words)
        if case_type == 'Sentence case':
            return ' '.join(words).capitalize()
        if case_type == 'Title Case':
            return ' '.join(word.capitalize() for word in words)
        if case_type == 'camelCase':
            return words[0].lower() + ''.join(word.capitalize() for word in words[1:])
        if case_type == 'dash-case':
            return '-'.join(word.lower() for word in words)
        if case_type == 'snake_case':
            return '_'.join(word.lower() for word in words)
        if case_type == 'separate words':
            return ' '.join(word.lower() for word in words)

        raise ValueError(f"Unsupported type: {case_type}")

    @staticmethod
    def crop_string(text: str, length: int, strong: bool = False) -> str:
        if not length:
            return text
        if strong:
            return text[:length]
        return text[:length] + "..." if len(text) > length else text

    @staticmethod
    def split_by_empty_lines(text: str) -> list[str]:
        text = re.sub(r'\n{2,}', '\n\n', text)
        lines = text.split("\n\n")
        return [line for line in lines if line.strip()]

    @staticmethod
    def remove_end_repetitions(text: str) -> str:
        words = re.split(r'\s+', text.strip())
        if len(words) <= 1:
            return StringUtils.clean_text(text)

        cleaned_words = [re.sub(r'[^\w-]', '', word) for word in words]

        for i in range(len(cleaned_words) - 2, -1, -1):
            if cleaned_words[i] != cleaned_words[i + 1]:
                if i + 2 < len(cleaned_words) and cleaned_words[i + 1] == cleaned_words[i + 2]:
                    text = " ".join(words[:i + 1]).strip()
                    return StringUtils.clean_text(text)
        return StringUtils.clean_text(text)

    @staticmethod
    def clean_text(text: str | None) -> str:
        if not text:
            return ''
        return text.strip().strip(",").strip()

    @staticmethod
    def clean_string(text: str | None) -> str:
        if not text:
            return ''
        text = StringUtils.clean_space(text)
        return text.strip(",").strip(".").strip()

    @staticmethod
    def clean_space(text: str | None) -> str:
        if not text:
            return ''
        text = text.replace("\n", " ")
        text = re.sub(r'\s{2,}', ' ', text)
        return text.strip()

    @staticmethod
    def is_like_substring(shorter: str, longer: str) -> bool:
        from difflib import SequenceMatcher
        return SequenceMatcher(None, shorter, longer).ratio() > 0.7

    @staticmethod
    def merge_strings(strings: list[str]) -> list[str]:
        cleaned_strings = sorted([StringUtils.clean_string(s) for s in strings], key=len, reverse=True)
        final_strings = []
        for s in cleaned_strings:
            if not any(s in fs for fs in final_strings):
                final_strings.append(s)
        return final_strings

    @staticmethod
    def is_url(text: str) -> bool:
        try:
            result = urlparse(text)
            return all([result.scheme, result.netloc])
        except (ValueError, AttributeError):
            return False

    @staticmethod
    def capitalize_first_letter(text: str, strip: bool = True) -> str:
        if text and str(text).strip():
            text = str(text)
            if strip:
                text = text.strip()
            return text[0].upper() + text[1:]
        return text

    @staticmethod
    def generate_simple_password(length: int = 16) -> str:
        set1 = 'abcdefghijklmnpqrstuvwxyz'
        set2 = '123456789'
        length = max(length, 3)
        password_list = [random.choice(set1), random.choice(set1)]
        for _ in range(length - 2):
            password_list.append(random.choice(set1) if random.randint(0, 1) else random.choice(set2))
        return "".join(password_list)

    @staticmethod
    def generate_unique_email(prefix: str = 'user', domain: str = 'example.com') -> str:
        timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')
        random_part = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
        local_part = f"{timestamp}_{random_part}"
        email_hash = hashlib.md5(local_part.encode()).hexdigest()
        return f"{prefix}_{email_hash}@{domain}"

    @staticmethod
    def clear_phone_number(phone_number: str, british_format: bool = False) -> str | None:
        phone_number = re.sub(r'[^\d]', '', phone_number)
        if british_format:
            if len(phone_number) == 11 and phone_number.startswith('0'):
                phone_number = f"0044{phone_number[1:]}"
            elif len(phone_number) == 12:
                phone_number = f"00{phone_number}"
            return phone_number if len(phone_number) == 14 else None

        return phone_number if 1 <= len(phone_number) <= 16 else None

    @staticmethod
    def slug_zh(text: str) -> str:
        slug = re.sub(r'[?|\p{P}|\s]+', '-', text.lower())
        return slug.strip('-')

    @staticmethod
    def slug(text: str, default: str | None = None, extension: str = '', max_length: int = 70, not_use_latin_and_cyrillic: bool = False) -> str:
        if text:
            text = text.replace('.', '-').replace('/', '-').replace('|', '-')
            text = re.sub(r'\b(\w+)\b(?=.*?\b\1\b)', ' ', text, flags=re.IGNORECASE | re.UNICODE)
            text = re.sub(r"[+'&@#/%?=~_$!:,.;_{}()\[\]«»“„\"~`*]", '', text)
            text = re.sub(r'-{2,}', '-', text).strip()
            text = text[:max_length]

        if text and text != '-':
            slug = StringUtils.slug_zh(text) if not_use_latin_and_cyrillic else re.sub(r'[^a-zA-Z0-9\-]', '', text).lower()
        else:
            slug = default if default is not None else f"{str(datetime.datetime.now().timestamp())[3:].replace('.', '')}{random.randint(111111, 999999)}"

        if extension and not slug.endswith(extension):
            slug = f"{slug}{extension}"

        return slug

