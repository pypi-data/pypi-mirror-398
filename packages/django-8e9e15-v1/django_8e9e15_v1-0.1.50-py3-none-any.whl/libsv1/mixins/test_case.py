from django.test import TestCase
from django.utils.translation import deactivate_all
from rest_framework.response import Response
from app.datasets import UserStatusDataset, RoleDataset
from app.models import User
from rest_framework import status
from rest_framework.test import APIClient
import json
from django.http import QueryDict

class TestCaseMixin(TestCase):
    exceptions = []

    client = None
    url = ""
    user = None
    user_email = 'user@example.com'
    user_password = 'testpassword'
    user_full_name = 'Test User'
    user_social_token = 'test_social_token'
    test_user_emails = [
        "user@example.com",
    ]

    @staticmethod
    def user_has_test_email(email):
        return email in TestCaseMixin.test_user_emails

    def setUp(self):
        super().setUp()
        self.exceptions = []
        self.client = APIClient()
        deactivate_all()

    def tearDown(self):
        super().tearDown()
        assert not self.exceptions, f"Errors occurred: {self.exceptions}"
        self.exceptions = []

    def check_user_status(self, request_data=None, request_method="POST"):
        if self.user:
            user = self.user
        else:
            user = User.objects.filter(email=self.user_email).first()

        user.user_status_id = UserStatusDataset.SUSPENDED
        user.save()
        if request_method == "POST":
            response: Response = self.client.post(path=self.url, data=request_data, format="json")
        else:
            response: Response = self.client.get(path=self.url, date=request_data, format="json")
        print(self.url, response.data)
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)
        self.assertEqual('User is suspended.', response.data['message'])

        user.user_status_id = UserStatusDataset.BLOCKED
        user.save()
        response: Response = self.client.post(path=self.url, data=request_data, format="json")
        print(self.url, response.data)
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)
        self.assertEqual('User is blocked.', response.data['message'])

        user.user_status_id = UserStatusDataset.NEW
        user.save()
        response: Response = self.client.post(path=self.url, data=request_data, format="json")
        print(self.url, response.data)
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)
        self.assertEqual('User is not active.', response.data['message'])

        user.user_status_id = UserStatusDataset.ACTIVE
        user.save()
        user.remove_roles(RoleDataset.USER_APP)
        response: Response = self.client.post(path=self.url, data=request_data, format="json")
        print(self.url, response.data)
        self.assertEqual(status.HTTP_403_FORBIDDEN, response.status_code)
        self.assertEqual('User does not have user app role.', response.data['message'])

    def convert_request_data_to_content_type(self, request_data, content_type):
        if content_type == 'application/json':
            return json.dumps(request_data).encode('utf-8')
        elif content_type == 'application/x-www-form-urlencoded':
            convert_request_data = QueryDict('', mutable=True)
            for key, value in request_data.items():
                if isinstance(value, list):
                    for item in value:
                        convert_request_data.appendlist(key, item)
                else:
                    convert_request_data[key] = value
            return convert_request_data.urlencode().encode('utf-8')

        else:
            return request_data
