from django.db import models
from django.utils.timezone import now
from libsv1.utils.model import ModelUtils


class GlobalSystemLog(models.Model):
    id = models.AutoField(primary_key=True)
    request_id = models.CharField(max_length=150, unique=True)
    use_for_auto_test = models.IntegerField(default=0, db_index=True)
    is_saved = models.IntegerField(default=0, db_index=True)
    user_id = models.BigIntegerField(null=True, blank=True)
    guard_key = models.CharField(null=True, blank=True, max_length=150)
    ip = models.CharField(null=True, blank=True, max_length=50, db_index=True)
    user_agent = models.TextField(null=True, blank=True)
    authorization = models.TextField(null=True, blank=True)
    host = models.CharField(null=True, blank=True, max_length=150)
    route = models.TextField(null=True, blank=True)
    url_query = models.TextField(null=True, blank=True)
    method = models.CharField(null=True, blank=True, max_length=10)
    headers = models.TextField(null=True, blank=True)
    request = models.TextField(null=True, blank=True)
    request_files = models.TextField(null=True, blank=True)
    request_origin_get = models.TextField(null=True, blank=True)
    request_origin_post = models.TextField(null=True, blank=True)
    response = models.TextField(null=True, blank=True)
    response_status_code = models.CharField(null=True, blank=True, max_length=150)
    response_error = models.TextField(null=True, blank=True)
    trace_error = models.TextField(null=True, blank=True)
    message_error = models.TextField(null=True, blank=True)
    onesignal_logs = models.JSONField(null=True, blank=True, default=list)
    firebase_logs = models.JSONField(null=True, blank=True, default=list)
    curl_logs = models.JSONField(null=True, blank=True, default=list)
    additional_logs = models.JSONField(null=True, blank=True, default=list)
    additional_val = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(default=now, db_index=True)
    updated_at = models.DateTimeField(default=now)
    execution_time = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        db_table = 'global_system_logs'

    @property
    def onesignal_log(self):
        return ModelUtils.get_last_log(self.onesignal_logs)

    @onesignal_log.setter
    def onesignal_log(self, value):
        self.onesignal_logs = ModelUtils.add_to_logs(self.onesignal_logs, value)

    @property
    def firebase_log(self):
        return ModelUtils.get_last_log(self.firebase_logs)

    @firebase_log.setter
    def firebase_log(self, value):
        self.firebase_logs = ModelUtils.add_to_logs(self.firebase_logs, value)

    @property
    def curl_log(self):
        return ModelUtils.get_last_log(self.curl_logs)

    @curl_log.setter
    def curl_log(self, value):
        self.curl_logs = ModelUtils.add_to_logs(self.curl_logs, value)

    @property
    def additional_log(self):
        return ModelUtils.get_last_log(self.additional_logs)

    @additional_log.setter
    def additional_log(self, value):
        self.additional_logs = ModelUtils.add_to_logs(self.additional_logs, value)
