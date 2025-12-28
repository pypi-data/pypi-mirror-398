import hashlib
from django.utils.translation import gettext
from rest_framework.permissions import IsAuthenticated as BaseIsAuthenticated
from rest_framework.exceptions import PermissionDenied, AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication
from libsv1.mixins.test_case import TestCaseMixin
from django.conf import settings
from app.datasets import RoleDataset, UserStatusDataset
from app.models import UserAccessToken
from rest_framework.permissions import BasePermission
from django.http import HttpResponseForbidden
from functools import wraps
from django.contrib.auth.decorators import login_required
import hashlib
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password


class IsAuthenticated(BaseIsAuthenticated):
    def has_permission(self, request, view):
        if request.user and request.user.is_authenticated and TestCaseMixin.user_has_test_email(request.user.email):
            user = request.user
        else:
            if not TokenService.check_token(TokenService.get_access_token_from_http(request)):
                raise AuthenticationFailed()
            user, _ = JWTAuthentication().authenticate(request)

        check_user_app_role = False
        if any(request.path.startswith(prefix) for prefix in settings.API_PREFIXES):
            check_user_app_role = True
        CheckUserStatus(user=user, check_user_app_role=check_user_app_role)

        return True

class IsRootAdminRole(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.has_role(RoleDataset.ROOT_ADMIN)

def admin_required(view_func):
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        if not (request.user and request.user.is_authenticated and request.user.has_role(RoleDataset.ROOT_ADMIN)):
            return HttpResponseForbidden("Forbidden")
        return view_func(request, *args, **kwargs)
    return _wrapped_view

class CheckUserStatus:
    def __init__(self, user=None, check_user_app_role=False, is_root_admin_role=False):
        if not user:
            raise PermissionDenied()
        if user.user_status_id == UserStatusDataset.SUSPENDED:
            raise PermissionDenied('___' + gettext("User is suspended."))
        if user.user_status_id == UserStatusDataset.BLOCKED:
            raise PermissionDenied('___' + gettext("User is blocked."))
        if user.user_status_id != UserStatusDataset.ACTIVE:
            raise PermissionDenied('___' + gettext("User is not active."))
        if check_user_app_role and not (user.has_role(RoleDataset.USER_APP) or user.has_role(RoleDataset.ROOT_ADMIN)):
            raise PermissionDenied('___' + gettext("User does not have user app role."))
        if is_root_admin_role and not user.has_role(RoleDataset.ROOT_ADMIN):
            raise PermissionDenied('___' + gettext("User does not have root admin role."))

class TokenService:
    @staticmethod
    def get_access_token_from_http(request):
        access_token = request.META.get('HTTP_AUTHORIZATION')
        if access_token and ' ' in access_token:
            return access_token.split(' ')[1]
        return ''

    @staticmethod
    def generate_access_token(user):
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        UserAccessToken.objects.create(token=TokenService.get_token(access_token), user_id=user.id)
        return access_token

    @staticmethod
    def check_token(access_token):
        if not access_token:
            return False
        return UserAccessToken.objects.filter(token=TokenService.get_token(access_token)).exists()

    @staticmethod
    def delete_token(access_token):
        if access_token:
            UserAccessToken.objects.filter(token=TokenService.get_token(access_token)).delete()

    @staticmethod
    def get_token(access_token):
        return hashlib.sha256(access_token.encode()).hexdigest()

    @staticmethod
    def logout(request):
        TokenService.delete_token(TokenService.get_access_token_from_http(request))

    @staticmethod
    def get_user(request):
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            return request.user
        return None

class SHA256Backend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        try:
            user = UserModel.objects.get(email=username)
        except UserModel.DoesNotExist:
            return None

        sha256_password = hashlib.sha256(password.encode()).hexdigest()

        if user and check_password(sha256_password, user.password):
            return user
        return None