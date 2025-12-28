from rest_framework import serializers, status
from drf_spectacular.utils import OpenApiParameter


def pagination_parameters() -> list[OpenApiParameter]:
    return [
        OpenApiParameter(name='page', required=False, type=int),
        OpenApiParameter(name='page_size', required=False, type=int),
    ]

def search_query_parameters() -> list[OpenApiParameter]:
    return [
        OpenApiParameter(name='search_query', required=False, type=str),
    ]

class SearchQueryInputSerializer(serializers.Serializer):
    search_query = serializers.CharField(required=False, allow_null=True, max_length=500)

class PaginationInputSerializer(serializers.Serializer):
    page = serializers.IntegerField(required=False, allow_null=True, min_value=1, default=1)
    page_size = serializers.IntegerField(required=False, allow_null=True, min_value=1, default=10)

class PaginationOutputSerializer(serializers.Serializer):
    page_size = serializers.IntegerField()
    current_page = serializers.IntegerField()
    limit = serializers.IntegerField()
    offset = serializers.IntegerField()
    total = serializers.IntegerField()

# ------------------------------------------------------

class MinMaxIntegerSerializer(serializers.Serializer):
    min = serializers.IntegerField()
    max = serializers.IntegerField()

class LocationSerializer(serializers.Serializer):
    lat = serializers.FloatField()
    lng = serializers.FloatField()

class DatasetSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField(max_length=255)

class DatasetEnumSerializer(serializers.Serializer):
    id = serializers.CharField(max_length=150)
    name = serializers.CharField(max_length=255)

class ResponseNotFoundSerializer(serializers.Serializer):
    title = serializers.CharField(default="Oops!")
    message = serializers.CharField(default="Not found")
    status_code = serializers.IntegerField(default=status.HTTP_404_NOT_FOUND)

class ResponseNotExistSerializer(serializers.Serializer):
    title = serializers.CharField(default="Oops!")
    message = serializers.CharField(default="Not exist")
    status_code = serializers.IntegerField(default=status.HTTP_404_NOT_FOUND)

class ResponseAlreadyExistSerializer(serializers.Serializer):
    title = serializers.CharField(default="Oops!")
    message = serializers.CharField(default="Already exist")
    status_code = serializers.IntegerField(default=status.HTTP_404_NOT_FOUND)

class ResponseSuccessSerializer(serializers.Serializer):
    title = serializers.CharField(default="")
    message = serializers.CharField(default="Success")
    status_code = serializers.IntegerField(default=status.HTTP_200_OK)

class ResponseErrorSerializer(serializers.Serializer):
    title = serializers.CharField(default="Oops!")
    message = serializers.CharField(default="Undefined error")
    status_code = serializers.IntegerField(default=status.HTTP_400_BAD_REQUEST)

class ResponseForbiddenSerializer(serializers.Serializer):
    title = serializers.CharField(default="Oops!")
    message = serializers.CharField(default="Forbidden")
    status_code = serializers.IntegerField(default=status.HTTP_403_FORBIDDEN)

class ResponseUnauthorizedSerializer(serializers.Serializer):
    title = serializers.CharField(default="Oops!")
    message = serializers.CharField(default="Unauthorized")
    status_code = serializers.IntegerField(default=status.HTTP_401_UNAUTHORIZED)

class ResponseValidationSerializer(serializers.Serializer):
    title = serializers.CharField(default="Oops!")
    message = serializers.CharField(default="The given data was invalid")
    status_code = serializers.IntegerField(default=status.HTTP_400_BAD_REQUEST)

