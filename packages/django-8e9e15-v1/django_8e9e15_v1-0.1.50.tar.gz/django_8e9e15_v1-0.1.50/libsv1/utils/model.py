from gettext import gettext
from rest_framework import serializers
from django.db import connection
from libsv1.utils.string import StringUtils
from django.conf import settings
from libsv1.utils.file import FileUtils
from django.db.models import ExpressionWrapper, FloatField
from django.db.models.expressions import RawSQL
import json
import phonenumbers
from django.db import models
from django.core.serializers.json import DjangoJSONEncoder


class ModelUtils:
    @staticmethod
    def get_json_value(value):
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return None
        else:
            return None

    @staticmethod
    def set_json_value(value):
        if value:
            return json.dumps(value)
        return None

    @staticmethod
    def allowed_values(dataset, field, value, null=False):
        allowed_values = dataset.get(return_as_list='id')
        if value is not None or not null:
            if value not in allowed_values:
                raise serializers.ValidationError({
                    field: gettext("Invalid {field}. Allowed values are: {allowed_values}").format(allowed_values=allowed_values, field=field)
                })

    @staticmethod
    def get_last_log(logs):
        if isinstance(logs, list) and len(logs) > 0:
            return logs[-1]
        return None

    @staticmethod
    def add_to_logs(logs, value):
        if not isinstance(logs, list):
            logs = []
        if value:
            logs.append(value)
        return logs

    @staticmethod
    def get_distance_formula(lat, lng, km=False):
        return ExpressionWrapper(RawSQL("""%s * 2 * ASIN(SQRT(POWER(SIN(RADIANS(%s - ST_Y(location_point)) / 2), 2) + COS(RADIANS(%s)) * COS(RADIANS(ST_Y(location_point))) * POWER(SIN(RADIANS(%s - ST_X(location_point)) / 2), 2)))""",(6371 if km else 3959, lat, lat, lng)), output_field=FloatField())

    @staticmethod
    def get_location_from_point(value):
        if value:
            return {
                "lng": value.x,
                "lat": value.y,
            }
        else:
            return None

    @staticmethod
    def set_location_to_point(value):
        from django.contrib.gis.geos import Point
        if value and not isinstance(value, Point):
            lat = value.get("lat")
            lng = value.get("lng")
            if not lat is None and not lng is None:
                value = Point(x=lng, y=lat, srid=4326)
            else:
                value = None
        return value

    @staticmethod
    def file_upload(instance, field, path):
        field_value = getattr(instance, field)
        if instance.pk:
            old_field_value = getattr(instance, '_original_' + field)
            if str(old_field_value) == str(field_value) or FileUtils.exists_file(str(field_value)):
                return
        if not field_value:
            setattr(instance, field, '')
        try:
            if hasattr(field_value, 'read'):
                file_path = FileUtils.upload_files(path, [field_value], True)[0]
                setattr(instance, field, file_path)
        except Exception as e:
            pass

    @staticmethod
    def delete_old_file_after_update(instance, field, delete_not_use_file=False):
        if instance.pk:
            old_field_value = str(getattr(instance, '_original_' + field))
            field_value = str(getattr(instance, field))
            if old_field_value != field_value:
                if delete_not_use_file:
                    ModelUtils.delete_not_use_file(instance, field, old_field_value)
                else:
                    FileUtils.delete_file(old_field_value)

    @staticmethod
    def delete_not_use_file(instance, field, value):
        value = str(value)
        model_class = instance.__class__
        if not model_class.objects.exclude(id=instance.id).filter(**{field: value}).exists():
            FileUtils.delete_file(value)

    @staticmethod
    def optimize_table(model_class):
        table_name = model_class._meta.db_table
        db_engine = connection.settings_dict['ENGINE']
        with connection.cursor() as cursor:
            if db_engine == 'django.db.backends.postgresql':
                cursor.execute(f"VACUUM {table_name};")
            elif db_engine == 'django.db.backends.mysql':
                cursor.execute(f"OPTIMIZE TABLE `{table_name}`;")

    @staticmethod
    def get_table_size_mb(model_class):
        size = 0
        table_name = model_class._meta.db_table

        db_engine = connection.settings_dict['ENGINE']

        with connection.cursor() as cursor:
            if db_engine == 'django.db.backends.postgresql':
                cursor.execute(f"""
                    SELECT 
                        pg_total_relation_size('public.{table_name}') / (1024 * 1024) AS size
                """)
                result = cursor.fetchone()
                if result and result[0]:
                    size = int(result[0])

            elif db_engine == 'django.db.backends.mysql':
                cursor.execute(f"""
                    SELECT 
                        ROUND((DATA_LENGTH + INDEX_LENGTH) / (1024 * 1024), 0) AS size
                    FROM information_schema.TABLES
                    WHERE TABLE_SCHEMA = DATABASE()
                    AND TABLE_NAME = '{table_name}'
                """)
                result = cursor.fetchone()
                if result and result[0]:
                    size = int(result[0])

        return size

    @staticmethod
    def get_db_uri():
        db_settings = settings.DATABASES['default']
        if db_settings['ENGINE'] == 'django.db.backends.sqlite3':
            return f"sqlite:///{db_settings['NAME']}"
        elif db_settings['ENGINE'] == 'django.db.backends.postgresql':
            return f"postgresql://{db_settings['USER']}:{db_settings['PASSWORD']}@{db_settings['HOST']}:{db_settings['PORT']}/{db_settings['NAME']}"
        elif db_settings['ENGINE'] == 'django.db.backends.mysql' or db_settings['ENGINE'] == 'django.contrib.gis.db.backends.mysql':
            return f"mysql://{db_settings['USER']}:{db_settings['PASSWORD']}@{db_settings['HOST']}:{db_settings['PORT']}/{db_settings['NAME']}"
        else:
            raise ValueError(f"Database type `{db_settings['ENGINE']}` is not supported for ERD generation")

    @staticmethod
    def update_model_from_request(fields, request, serializer, model, set_none_if_has_not_field_in_request=False):
        for field in fields:
            if any(key.startswith(field) for key in request.data):
                setattr(model, field, serializer.validated_data.get(field, getattr(model, field)))
            elif set_none_if_has_not_field_in_request:
                setattr(model, field, None)

    @staticmethod
    def update_model_from_data(fields, data, model, set_none_if_has_not_field_in_data=False):
        for field in fields:
            if any(key.startswith(field) for key in data):
                setattr(model, field, data.get(field, getattr(model, field)))
            elif set_none_if_has_not_field_in_data:
                setattr(model, field, None)

    @staticmethod
    def sync_display_phone_number(instance):
        if (not instance.pk and instance.display_phone_number) or instance._display_phone_number != instance.display_phone_number:
            parsed_phonenumber = phonenumbers.parse(instance.display_phone_number, None)
            instance.phone_code = f"+{parsed_phonenumber.country_code}"
            instance.phone_number = parsed_phonenumber.national_number
        elif (not instance.pk and instance.phone_number) or instance._phone_code != instance.phone_code or instance._phone_number != instance.phone_number:
            instance.display_phone_number = StringUtils.clean_space(f'{instance.phone_code if instance.phone_code else ''}{instance.phone_number}')

    @staticmethod
    def sync_full_name(instance):
        instance.first_name = StringUtils.clean_space(instance.first_name)
        instance.last_name = StringUtils.clean_space(instance.last_name)
        instance.full_name = StringUtils.clean_space(instance.full_name)
        if (not instance.pk and instance.full_name) or instance._full_name != instance.full_name:
            parts = instance.full_name.split(' ', 1)
            instance.first_name = StringUtils.clean_space(parts[0])
            instance.last_name = StringUtils.clean_space(parts[1]) if len(parts) > 1 else ''
        elif (not instance.pk and (instance.first_name or instance.last_name)) or {'first_name': instance._first_name, 'last_name': instance._last_name} != {'first_name': instance.first_name, 'last_name': instance.last_name}:
            instance.full_name = StringUtils.clean_space(f'{instance.first_name.strip()} {instance.last_name.strip()}')

    @staticmethod
    def validate_email(model_class, value, instance=None, is_strict_required=None, msg='Email is already registered'):
        if is_strict_required is None and not value:
            return value

        if (is_strict_required and not value) or (not is_strict_required and (instance is None or instance.email) and not value):
            raise serializers.ValidationError(
                '___' + gettext("Email is required")
            )

        if not value:
            return value

        if not instance or (instance and instance.email != value):
            if model_class.objects.filter(email=value).exists():
                raise serializers.ValidationError(
                    '___' + gettext(msg)
                )
        return value

    @staticmethod
    def is_valid_phone_number(model_class, phone_code, phone_number, instance=None, is_strict_required=None, msg='Phone number is already registered'):
        if (not phone_code and phone_number) or (phone_code and not phone_number):
            raise serializers.ValidationError(
                '___' + gettext("Phone number is required")
            )

        if is_strict_required is None:
            if not phone_code and not phone_number:
                return True

        has_old_phone = instance and instance.phone_code and instance.phone_number
        is_empty_input = not phone_code or not phone_number

        if (is_strict_required and is_empty_input) or (not is_strict_required and (instance is None or has_old_phone) and is_empty_input):
            raise serializers.ValidationError(
                '___' + gettext("Phone number is required")
            )

        if not phone_code and not phone_number:
            return True

        current_value = None
        if instance:
            current_value = StringUtils.clean_space(f'{instance.phone_code}{instance.phone_number}')

        new_value = StringUtils.clean_space(f'{phone_code}{phone_number}')

        if new_value and current_value != new_value:
            if model_class.objects.filter(phone_code=phone_code, phone_number=phone_number).exists():
                raise serializers.ValidationError(
                    '___' + gettext(msg)
                )
        return True

class UTF8JSONField(models.TextField):
    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value

    def to_python(self, value):
        if isinstance(value, (dict, list)):
            return value
        if value is None:
            return value
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value

    def get_prep_value(self, value):
        if value is None:
            return value
        return json.dumps(value, cls=DjangoJSONEncoder, ensure_ascii=False)