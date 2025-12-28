import json
import re
from gettext import gettext
from django.db.models import QuerySet
from rest_framework.views import exception_handler
from rest_framework import status
from django.http import Http404
from django.shortcuts import _get_queryset
from rest_framework.exceptions import ErrorDetail
from libsv1.utils.string import StringUtils
from rest_framework.exceptions import PermissionDenied
from rest_framework.exceptions import ValidationError


def api_exception_handler(exc, context):
    print('')
    print('error_exc:')
    print(exc)
    print('')
    print('error_context:')
    print(context)
    print('')

    if isinstance(exc, ValueError):
        exc = ValidationError(str(exc))

    response = exception_handler(exc, context)
    if response is None:
        raise Exception(f"Unexpected error: {exc}")
    response.error_message = str(exc.default_detail) if hasattr(exc, 'default_detail') else None

    if isinstance(exc, CustomNotFound):
        response.data = {
            'title': 'Oops!',
            'message': exc.detail,
            'status_code': status.HTTP_404_NOT_FOUND
        }
    elif response is not None:
        if hasattr(exc, 'status_code'):
            if exc.status_code == status.HTTP_401_UNAUTHORIZED:
                response.data = {
                    'title': 'Oops!',
                    'message': 'Unauthorized',
                    'status_code': status.HTTP_401_UNAUTHORIZED
                }
            elif exc.status_code == status.HTTP_403_FORBIDDEN:
                if exc and re.findall(r'___', str(exc)):
                    message = re.sub(r'___', '', str(exc))
                else:
                    message = "Forbidden"
                response.data = {
                    'title': 'Oops!',
                    'message': message,
                    'status_code': status.HTTP_403_FORBIDDEN
                }
            elif exc.status_code == status.HTTP_404_NOT_FOUND:
                response.data = {
                    'title': 'Oops!',
                    'message': 'Not found',
                    'status_code': status.HTTP_404_NOT_FOUND
                }
            elif exc.status_code == status.HTTP_405_METHOD_NOT_ALLOWED:
                response.data = {
                    'title': 'Oops!',
                    'message': 'Method Not Allowed',
                    'status_code': status.HTTP_405_METHOD_NOT_ALLOWED
                }
            else:
                normalized_errors = normalize_errors(response.data)

                if normalized_errors:
                    first_error = extract_first_error(normalized_errors)

                    if isinstance(normalized_errors, list):
                        normalized_errors = normalize_errors_list(normalized_errors)

                    elif isinstance(normalized_errors, dict):
                        normalized_errors = normalize_errors_dict(normalized_errors)

                    response.data = {
                        'title': 'Oops!',
                        'message': first_error,
                        'errors': normalized_errors,
                        'status_code': status.HTTP_400_BAD_REQUEST
                    }
                else:
                    response.data = {
                        'title': 'Oops!',
                        'message': 'Undefined error',
                        'status_code': status.HTTP_400_BAD_REQUEST
                    }

        else:
            response.data = {
                'title': 'Oops!',
                'message': 'A server error occurred.',
                'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR
            }
    else:
        response.data = {
            'title': 'Oops!',
            'message': 'A server error occurred.',
            'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR
        }

    return response

def normalize_errors_dict(normalized_errors):
    new_normalized_errors = {}
    for k, v in normalized_errors.items():
        if isinstance(v, list):
            new_normalized_errors[k] = normalize_errors_list(v)
        elif isinstance(v, str):
            new_normalized_errors[k] = v.replace('___', '')
        elif isinstance(v, dict):
            new_normalized_errors[k] = normalize_errors_dict(v)
        else:
            new_normalized_errors[k] = v
    return new_normalized_errors

def normalize_errors_list(normalized_errors):
    updated_errors = []
    for error in normalized_errors:
        if isinstance(error, dict):
            updated_error = {
                key: (
                    value.replace('___', '') if isinstance(value, str)
                    else [v.replace('___', '') if isinstance(v, str) else v for v in value]
                    if isinstance(value, list)
                    else value
                )
                for key, value in error.items()
            }
            updated_errors.append(updated_error)
        elif isinstance(error, str):
            if 'non_field_errors' not in updated_errors:
                updated_errors = {}
                updated_errors['non_field_errors'] = []
            updated_errors['non_field_errors'].append(error.replace('___', ''))
    return updated_errors

def normalize_errors(errors):
    if isinstance(errors, dict):
        return {key: normalize_errors(value) for key, value in errors.items()}
    elif isinstance(errors, list):
        return [normalize_errors(error) for error in errors]
    elif isinstance(errors, ErrorDetail):
        return str(errors)
    elif isinstance(errors, str):
        try:
            parsed_errors = json.loads(errors.replace("'", '"'))
            return normalize_errors(parsed_errors)
        except json.JSONDecodeError:
            return errors
    return errors

def extract_first_error(errors, parent_field=None):
    if isinstance(errors, list):
        errors = [error for error in errors if error]
    elif isinstance(errors, dict):
        errors = {k: v for k, v in errors.items() if v}

    if isinstance(errors, dict):
        for field, value in errors.items():
            full_field = f"{parent_field}.{field}" if parent_field else field
            extracted = extract_first_error(value, full_field)
            if extracted:
                if isinstance(extracted, str):
                    return format_error(extracted)
                return extracted
    elif isinstance(errors, list):
        for error in errors:
            extracted = extract_first_error(error, parent_field)
            if extracted:
                if isinstance(extracted, str):
                    return format_error(extracted)
                return extracted
    elif isinstance(errors, ErrorDetail) or isinstance(errors, str):
        return format_error(str(errors), parent_field)
    return None

def format_error(error_message, parent_field=None):
    if parent_field and parent_field == 'non_field_errors':
        parent_field = None
    if parent_field and re.findall(r'error(?:_\d+)*$', parent_field):
        parent_field = None
    if parent_field and re.findall(r'error(?:_\d+)*\.non_field_errors', parent_field):
        parent_field = None
    if re.findall(r'___', error_message):
        parent_field = None
        error_message = re.sub(r'___', '', error_message)
    parent_field = re.sub(r'^error(?:_\d+)*\.', '', parent_field) if parent_field else None
    parent_field = format_key_name(parent_field) if parent_field else None
    parent_field = parent_field.strip() if parent_field else None

    if error_message == "This field is required." and parent_field:
        return f"{parent_field} is required"
    if error_message == "Enter a valid email address.":
        parent_field = None

    if parent_field:
        error_message = error_message.replace("This field", "").strip()
        error_message = error_message.replace("This", "").strip()
        if 'this value' in error_message:
            error_message = error_message.replace("this value", parent_field.lower()).strip()
            parent_field = None

    error_message = error_message.strip().rstrip(".")

    parent_field = StringUtils.capitalize_first_letter(parent_field)
    if not parent_field:
        error_message = StringUtils.capitalize_first_letter(error_message)

    return f"{parent_field} {error_message}" if parent_field else error_message

def format_key_name(key):
    cleaned_name = re.sub(r'_(id|ids)$', '', key)
    words = cleaned_name.split('_')
    formatted_name = ' '.join(words)
    return formatted_name

def get_object_or_404(klass, **kwargs):
    queryset = _get_queryset(klass)
    model = queryset.model if isinstance(queryset, QuerySet) else klass
    model_name = model._meta.verbose_name.title()
    try:
        return queryset.get(**kwargs)
    except model.DoesNotExist:
        raise CustomNotFound(f"{model_name} with the given ID does not exist.")

def get_object_or_403(klass, **kwargs):
    queryset = _get_queryset(klass)
    model = queryset.model if isinstance(queryset, QuerySet) else klass
    try:
        return queryset.get(**kwargs)
    except model.DoesNotExist:
        raise PermissionDenied('___' + gettext("Forbidden"))

def get_object_or_404_403(klass, **kwargs):
    main_filters = {key: value for key, value in kwargs.items() if not key.startswith("__")}
    access_filters = {key.lstrip("__"): value for key, value in kwargs.items() if key.startswith("__")}

    if access_filters:
        get_object_or_404(klass, **main_filters)
        combined_filters = {**main_filters, **access_filters}
        instance = get_object_or_403(klass, **combined_filters)
        return instance
    else:
        return get_object_or_404(klass, **main_filters)

def get_optional_object_or_404(klass, **kwargs):
    if kwargs.get('id'):
        return get_object_or_404(klass, **kwargs)
    return None

def get_optional_object_or_404_403(klass, **kwargs):
    if kwargs.get('id'):
        return get_object_or_404_403(klass, **kwargs)
    return None

class CustomNotFound(Http404):
    def __init__(self, detail=None, *args, **kwargs):
        self.detail = detail if detail is not None else "Not Found"
        super().__init__(*args, **kwargs)
