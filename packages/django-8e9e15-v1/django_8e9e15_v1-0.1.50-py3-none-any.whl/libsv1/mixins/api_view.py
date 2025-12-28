import json
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from app.serializers import ResponseSuccessSerializer, ResponseNotFoundSerializer, ResponseErrorSerializer, ResponseForbiddenSerializer, ResponseUnauthorizedSerializer, ResponseValidationSerializer, ResponseNotExistSerializer, ResponseAlreadyExistSerializer


class APIViewMixin(APIView):
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def response_json(self, data=None, status_code=status.HTTP_200_OK, headers=None):
        return Response(json.loads(json.dumps(data, default=str)), status=status_code, headers=headers)

    def response(self, data=None, status_code=status.HTTP_200_OK, headers=None):
        headers = headers or {}
        return Response(data, status=status_code, headers=headers)

    def response_not_found(self, error="Not found", title="Oops!"):
        return self.response(ResponseNotFoundSerializer({
            "title": title,
            "message": error,
            "status_code": status.HTTP_404_NOT_FOUND,
        }).data, status_code=status.HTTP_404_NOT_FOUND)

    def response_not_exist(self, error="Not exist", title="Oops!"):
        return self.response(ResponseNotExistSerializer({
            "title": title,
            "message": error,
            "status_code": status.HTTP_404_NOT_FOUND,
        }).data, status_code=status.HTTP_404_NOT_FOUND)

    def response_already_exist(self, error="Already exist", title="Oops!"):
        return self.response(ResponseAlreadyExistSerializer({
            "title": title,
            "message": error,
            "status_code": status.HTTP_400_BAD_REQUEST,
        }).data, status_code=status.HTTP_400_BAD_REQUEST)

    def response_success(self, message="Success", title=""):
        return self.response(ResponseSuccessSerializer({
            "title": title,
            "message": message,
            "status_code": status.HTTP_200_OK,
        }).data, status_code=status.HTTP_200_OK)

    def response_error(self, error="Undefined error", title="Oops!", status_code=status.HTTP_400_BAD_REQUEST):
        return self.response(ResponseErrorSerializer({
            "title": title,
            "message": error,
            "status_code": status_code,
        }).data, status_code=status_code)

    def response_forbidden(self, title="Oops!"):
        return self.response(ResponseForbiddenSerializer({
            "title": title,
            "message": "Forbidden",
            "status_code": status.HTTP_403_FORBIDDEN,
        }).data, status.HTTP_403_FORBIDDEN)

    def response_unauthorized(self, error="Unauthorized", title="Oops!"):
        return self.response(ResponseUnauthorizedSerializer({
            "title": title,
            "message": error,
            "status_code": status.HTTP_401_UNAUTHORIZED,
        }).data, status_code=status.HTTP_401_UNAUTHORIZED)

    def response_validation_error(self, error=None):
        return self.response(ResponseValidationSerializer({
            "title": "Oops!",
            "message": "The given data was invalid",
            "error": error,
            "status_code": status.HTTP_400_BAD_REQUEST,
        }).data, status_code=status.HTTP_400_BAD_REQUEST)

    # ---------------------------------------------

    @staticmethod
    def get_pagination_from_serializer(serializer):
        page = serializer.validated_data.get("page")
        page_size = serializer.validated_data.get("page_size")
        offset = (page - 1) * page_size
        limit = offset + page_size
        return page, page_size, offset, limit

    @staticmethod
    def response_pagination(page, page_size, offset, limit, total):
        return {
            'page_size': page_size,
            'current_page': page,
            'limit': limit,
            'offset': offset,
            'total': total,
        }
