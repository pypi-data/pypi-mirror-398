import json
from io import BytesIO
from django.conf import settings
from django.http import QueryDict
import logging

logger = logging.getLogger(__name__)

class RequestUtils:
    @staticmethod
    def normalize_request_params(request):
        api_prefixes = getattr(settings, 'API_PREFIXES', [])
        if not hasattr(request, 'is_request_params_converted') and any(request.path.startswith(prefix) for prefix in api_prefixes):
            if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
                request_data = RequestUtils.parse_request_data(request)
                converted_data = RequestUtils.convert_request(request_data)
                request._request_params = converted_data
                RequestUtils.update_request_data(request, converted_data)
            elif request.method in ['GET']:
                query_params = request.GET.copy()
                converted_data = RequestUtils.convert_request(query_params)
                request._request_params = converted_data
                request.GET = converted_data
            request.is_request_params_converted = True

    @staticmethod
    def convert_request(data):
        if not data:
            return QueryDict() if isinstance(data, QueryDict) else {}
        if isinstance(data, QueryDict):
            result = QueryDict(mutable=True)
            for key in data.keys():
                values = data.getlist(key)
                for value in values:
                    result.appendlist(key, RequestUtils.process_value(key, value))
            return result
        if isinstance(data, dict):
            return RequestUtils.convert_request_dict(data)
        return data

    @staticmethod
    def convert_request_dict(data):
        result = {}
        for key, value in data.items():
            if isinstance(value, list):
                processed_values = []
                for v in value:
                    if isinstance(v, dict):
                        processed_value = RequestUtils.convert_request_dict(v)
                    else:
                        processed_value = RequestUtils.process_value(key, v)

                    if processed_value is not None:
                        processed_values.append(processed_value)
                result[key] = processed_values
            else:
                result[key] = RequestUtils.process_value(key, value)
        return result

    @staticmethod
    def process_value(key, value):
        if isinstance(value, int) and not isinstance(value, bool) and value == 0 and (key.endswith('_id') or key == 'id'):
            return None
        if isinstance(value, str):
            value = value.replace('%20', ' ').strip()
            if key == 'email' and value:
                value = value.replace(' ', '').lower()
            elif (key.replace("]", "").endswith('id') or key == 'id') and (value == '0' or value == ''):
                return None
            elif value.lower() == 'null':
                return None
            elif value.lower() == 'true':
                return True
            elif value.lower() == 'false':
                return False
        return value

    @staticmethod
    def update_request_data(request, converted_data):
        if request.content_type == 'application/json':
            body = json.dumps(converted_data).encode('utf-8')
            request._body = body
            request._stream = BytesIO(body)

        elif request.content_type == 'multipart/form-data':
            request.POST = QueryDict('', mutable=True)
            request.POST.update(converted_data)

        elif request.content_type == 'application/x-www-form-urlencoded':
            new_post_data = QueryDict('', mutable=True)

            if isinstance(converted_data, QueryDict):
                for key in converted_data.keys():
                    for value in converted_data.getlist(key):
                        new_post_data.appendlist(key, value)
            else:
                for key, value in converted_data.items():
                    if isinstance(value, list):
                        for item in value:
                            new_post_data.appendlist(key, item)
                    else:
                        new_post_data.appendlist(key, value)
            request.POST = new_post_data

            json_data = {}
            for key in new_post_data:
                values = new_post_data.getlist(key)
                json_data[key] = values if len(values) > 1 or key == 'list' else values[0] if values else None
            encoded_body = json.dumps(json_data).encode('utf-8')
            request._stream = BytesIO(encoded_body)
            request._body = encoded_body
            request.META['CONTENT_TYPE'] = 'application/json'

    @staticmethod
    def parse_request_data(request):
        if request.GET:
            return request.GET
        elif request.POST or request.FILES:
            return request.POST
        else:
            request_body = request._stream.read()
            request._stream = BytesIO(request_body)

            if isinstance(request_body, bytes):
                if request_body:
                    try:
                        return json.loads(request_body.decode('utf-8'))
                    except json.JSONDecodeError as e:
                        logger.warning(f"JSONDecodeError: {e}", exc_info=True)
                        return {}
                else:
                    return {}
            elif isinstance(request_body, str):
                if request_body and request_body != '':
                    try:
                        return json.loads(request_body)
                    except json.JSONDecodeError as e:
                        logger.warning(f"JSONDecodeError: {e}", exc_info=True)
                        return {}
                else:
                    return {}
            else:
                return {}