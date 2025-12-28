from gettext import gettext
from django.core.validators import RegexValidator
from rest_framework import serializers
from libsv1.utils.string import StringUtils
from django.db.models.query import QuerySet

def validate_phone_number(msg='must contain only digits'):
    return RegexValidator(regex=r'^\d{7,11}$', message=gettext(msg))

def validate_phone_code(msg='must contain 1 to 4 digits and should start with "+"'):
    return RegexValidator(regex=r'^\+\d{1,4}$', message=gettext(msg))

def validate_display_phone_number(msg='must contain 8 to 15 digits and should start with "+"'):
    return RegexValidator(regex=r'^\+\d{8,15}$', message=gettext(msg))

def validate_exists(value, model_or_queryset, field=None, key='id'):
    if value is None or value == "":
        return

    if isinstance(model_or_queryset, QuerySet):
        queryset = model_or_queryset
    else:
        model_class = model_or_queryset
        queryset = model_class.objects.all()

    final_queryset = queryset.filter(**{key: value})

    if not final_queryset.exists():
        if field is None:
            field = StringUtils.convert_case(queryset.model.__name__, 'Sentence case')

        raise serializers.ValidationError(
            '___' + gettext("{field} does not exist").format(field=field)
        )

