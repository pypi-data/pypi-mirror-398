import re
import traceback
from django.conf import settings
from django.db import connection
from django.utils.timezone import now
import json
from datetime import timedelta
from libsv1.utils.model import ModelUtils
from libsv1.utils.request import RequestUtils
from .models import GlobalSystemLog


class GlobalSystemLogAdd:
    def __init__(self, request=None, response=None, response_error=None, trace_error=None, message_error=None, onesignal_log=None, firebase_log=None, curl_log=None, additional_log=None, is_thread=False):
        if not getattr(settings, 'IS_GLOBAL_SYSTEM_LOG_ENABLE', False):
            return

        try:
            log = self.get_log(request)
            if request:
                self.set_log_request(log, request)
            if response:
                self.set_log_response(log, response)
            if response_error and not log.response_error:
                log.response_error = (
                    response_error if isinstance(response_error, (str, int)) else json.dumps(response_error, ensure_ascii=False)
                )
            if not log.response_status_code or log.response_status_code not in [404, 403, 401]:
                self.set_log_trace_and_message_error(log, trace_error, message_error)
            log.onesignal_log = onesignal_log
            log.firebase_log = firebase_log
            log.curl_log = curl_log
            log.additional_log = additional_log
            self.save_log(log)
        except Exception as exception:
            self.log_self_exception(exception)

        try:
            if is_thread:
                connection.close()
        except Exception as exception:
            print('Error closing connection')

    @classmethod
    def log_self_exception(cls, exception, user_agent='self'):
        log = cls.get_log()
        log.response_status_code = 500
        log.user_agent = user_agent
        log.is_saved = 1
        trace_error = traceback.format_exc()
        message_error = str(exception).strip()
        trace_error = trace_error.splitlines()
        cls.set_log_trace_and_message_error(log, trace_error, message_error)
        log.save()

    @staticmethod
    def get_log(request=None):
        log = None
        if request and hasattr(request, 'global_system_log_request_id') and request.global_system_log_request_id:
            log = GlobalSystemLog.objects.filter(request_id=request.global_system_log_request_id).first()
        if log is None:
            log = GlobalSystemLog()
            if request and hasattr(request, 'global_system_log_request_id') and request.global_system_log_request_id:
                log.request_id = request.global_system_log_request_id
            log.created_at = now()
            log.updated_at = now()
            log.execution_time = 0
            if request:
                log.ip = request.META.get('REMOTE_ADDR', None) if hasattr(request, 'META') else None
                log.user_agent = request.META.get('HTTP_USER_AGENT', None) if hasattr(request, 'META') else None
                log.authorization = request.META.get('HTTP_AUTHORIZATION', None) if hasattr(request, 'META') else None
                log.host = request.META.get('HTTP_HOST', None) if hasattr(request, 'META') else None
                log.method = request.META.get('REQUEST_METHOD', None) if hasattr(request, 'META') else None
                log.request_origin_get = json.dumps(request.GET.dict(), ensure_ascii=False) if request.GET else None
                log.request_origin_post = json.dumps(request.POST.dict(), ensure_ascii=False) if request.POST else None
                log.route = request.META.get('PATH_INFO', None) if hasattr(request, 'META') else None
                query_string = request.META.get('QUERY_STRING') if hasattr(request, 'META') else None
                if log.route:
                    log.url_query = f"{log.route}?{query_string}" if query_string else log.route
                else:
                    log.url_query = None
        return log

    @staticmethod
    def set_log_request(log, request):
        if request.headers:
            if 'save' in request.headers:
                log.is_saved = 1
            if 'autotest' in request.headers:
                log.use_for_auto_test = 1

            if log.headers is None:
                log.headers = json.dumps(dict(request.headers), ensure_ascii=False) if request.headers else None

        if log.request is None:
            parsed_request_data = RequestUtils.parse_request_data(request)
            if not parsed_request_data or (isinstance(parsed_request_data, str) and parsed_request_data == ""):
                log.request = None
            else:
                log.request = json.dumps(parsed_request_data, ensure_ascii=False)

        if log.request_files is None:
            log.request_files = '|'.join(
                [file.name for file in request.FILES.getlist('files')]
            ) if request.FILES else None

        if log.user_id is None:
            log.user_id = request.user.id if hasattr(request, 'user') else None

        if hasattr(request, 'user') and hasattr(request.user, 'guard_key') and not log.guard_key:
            log.guard_key = request.user.guard_key
        if hasattr(request, 'guard_key') and not log.guard_key:
            log.guard_key = request.guard_key
        if hasattr(request, 'user') and hasattr(request.user, 'email') and not log.guard_key:
            log.guard_key = request.user.email
        if hasattr(request, 'email') and not log.guard_key:
            log.guard_key = request.email

    @staticmethod
    def set_log_response(log, response):
        if log.response is None:
            try:
                if response and hasattr(response, 'streaming_content'):
                    if 'text' in response['Content-Type'] or 'json' in response['Content-Type']:
                        response_text = (
                            b''.join(response.streaming_content).decode('utf-8')
                        )
                    else:
                        response_text = '<BINARY DATA>'
                else:
                    response_text = response.content.decode('utf-8') if response and response.content else None

                if response_text and (response_text.strip().startswith('{') or response_text.strip().startswith('[')):
                    try:
                        log.response = json.loads(response_text)
                    except json.JSONDecodeError:
                        log.response = response_text[:10000]
                else:
                    log.response = response_text[:10000] if response_text else None

            except UnicodeDecodeError:
                log.response = '<UNDECODABLE DATA>'
            except Exception as e:
                log.response = f'<ERROR PROCESSING RESPONSE: {str(e)}>'

        if log.response_status_code is None:
            log.response_status_code = response.status_code if response.status_code else None

        if log.response_status_code is None:
            log.response_status_code = response.status_code if response.status_code else None

    @staticmethod
    def set_log_trace_and_message_error(log, trace_error=None, message_error=None):
        if trace_error and not log.trace_error:
            if isinstance(trace_error, str):
                log.trace_error = trace_error
            elif isinstance(trace_error, list):
                log.trace_error = "\n".join(map(str, trace_error))
            else:
                log.trace_error = json.dumps(trace_error, ensure_ascii=False)

            log.trace_error = (
                log.trace_error[:1000] + "..." if log.trace_error else None
            )

        if message_error and not log.message_error:
            log.message_error = (
                message_error if isinstance(message_error, (str, int)) else json.dumps(message_error, ensure_ascii=False)
            )

    @staticmethod
    def save_log(log):
        if (True
                and log.method
                and log.user_agent
                and log.user_agent != getattr(settings, 'AUTO_TEST_USER_AGENT', 'jufsdhius327yedks')
                and log.host
                and log.route
                and any(log.route.startswith(prefix) for prefix in getattr(settings, 'API_PREFIXES', []))
                and not any(log.route.startswith(prefix) for prefix in getattr(settings, 'GLOBAL_SYSTEM_LOG_IGNORE_PREFIXES', []))
        ):
            if log.message_error or log.trace_error:
                log.is_saved = 1

            if (True
                    and log.request
                    and not log.authorization
                    and log.route
                    and (log.route == "/user/edit" or log.route == "/api/user/edit")
                    and re.match(r'^{"onesignal_token":"[^"]{0,}"}$', log.request)
            ):
                log.ip = "need_remove"

            log.updated_at = now()
            execution_time = (log.updated_at - log.created_at).total_seconds()
            log.execution_time = max(int(execution_time), 0)
            log.save()

    @staticmethod
    def clear_hourly():
        if not getattr(settings, 'IS_GLOBAL_SYSTEM_LOG_ENABLE', False):
            return
        global_system_log_life_saved_hours = int(getattr(settings, 'GLOBAL_SYSTEM_LOG_LIFE_SAVED_HOURS', 0))
        global_system_log_life_saved_hours = global_system_log_life_saved_hours if global_system_log_life_saved_hours > 0 else 1

        cutoff_time = now() - timedelta(hours=global_system_log_life_saved_hours)
        global_system_logs = GlobalSystemLog.objects.filter(
            is_saved=False,
            use_for_auto_test=False,
            created_at__lt=cutoff_time
        )
        for log in global_system_logs:
            log.delete()

        ModelUtils.optimize_table(GlobalSystemLog)

    @staticmethod
    def clear_every_minute():
        if not getattr(settings, 'IS_GLOBAL_SYSTEM_LOG_ENABLE', False):
            return
        global_system_logs = GlobalSystemLog.objects.filter(ip='need_remove')
        for log in global_system_logs:
            log.delete()
        ModelUtils.optimize_table(GlobalSystemLog)

        global_system_log_life_ok_minutes = int(getattr(settings, 'GLOBAL_SYSTEM_LOG_LIFE_OK_MINUTES', 0))
        global_system_log_life_ok_minutes = global_system_log_life_ok_minutes if global_system_log_life_ok_minutes > 0 else 1

        cutoff_time = now() - timedelta(minutes=global_system_log_life_ok_minutes)
        global_system_logs = GlobalSystemLog.objects.filter(
            is_saved=False,
            use_for_auto_test=False,
            created_at__lt=cutoff_time
        )
        for log in global_system_logs:
            log.delete()

        ModelUtils.optimize_table(GlobalSystemLog)

        if ModelUtils.get_table_size_mb(GlobalSystemLog) > 200:
            cutoff_time = now() - timedelta(minutes=1)
            logs_to_delete = GlobalSystemLog.objects.filter(
                use_for_auto_test=False,
                created_at__lt=cutoff_time
            ).order_by('is_saved', 'id')

            i = 0
            for log in logs_to_delete:
                log.delete()
                if i > 100:
                    i = 0
                    ModelUtils.optimize_table(GlobalSystemLog)
                    if ModelUtils.get_table_size_mb(GlobalSystemLog) < 100:
                        break
                i += 1
