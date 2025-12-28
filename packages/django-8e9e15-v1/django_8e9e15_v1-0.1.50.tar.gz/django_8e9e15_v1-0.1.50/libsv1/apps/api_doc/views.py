from django.contrib.auth.decorators import login_required
from django.http import FileResponse
import os
from django.shortcuts import HttpResponse
from django.conf import settings
import platform
from drf_spectacular.generators import SchemaGenerator
import sys
from drf_spectacular.extensions import OpenApiSerializerExtension
from libsv1.utils.model import ModelUtils
from rest_framework import serializers


class CustomSerializerExtension(OpenApiSerializerExtension):
    target_class = serializers.Serializer
    match_subclasses = True

    def map_serializer(self, auto_schema, direction):
        return auto_schema._map_serializer(self.target, direction, bypass_extensions=True)

    def get_name(self, auto_schema, direction):
        view = auto_schema.view
        serializer = self.target
        app_name = view.__module__.split('.')[0]
        generated_name = f"{app_name}_{view.__class__.__name__}_{serializer.__class__.__name__}"
        return generated_name

def custom_postprocessing_hook(result, generator, request, public):
    if 'components' in result and 'schemas' in result['components']:
        for key, component in result['components']['schemas'].items():
            for prop_name, prop_schema in component.get('properties', {}).items():
                if prop_schema.get('format') == 'double':
                    prop_schema['example'] = 0.1
                elif prop_schema.get('format') == 'date-time':
                    prop_schema['example'] = '2025-03-21 00:00:00'
    if 'components' in result and 'securitySchemes' in result['components']:
        unwanted_schemes = ['jwtAuth', 'tokenAuth', 'basicAuth']
        for scheme in unwanted_schemes:
            if scheme in result['components']['securitySchemes']:
                del result['components']['securitySchemes'][scheme]
    return result

class BaseDynamicSchemaGenerator(SchemaGenerator):
    schema_path_prefix = None

    def _get_clean_segments(self, path):
        if self.schema_path_prefix and path.startswith(self.schema_path_prefix):
            path = path[len(self.schema_path_prefix):].lstrip('/')

        segments = path.split('/')
        clean_segments = [s for s in segments if not (s.startswith('{') and s.endswith('}'))]

        return clean_segments

    def _get_sort_key(self, item):
        path, methods = item

        method_priority = {
            'GET': 0,
            'POST': 1,
            'PUT': 2,
            'PATCH': 2,
            'DELETE': 4,
            'HEAD': 5,
            'OPTIONS': 6
        }

        priorities = [method_priority.get(m.upper(), 3) for m in methods.keys()]
        min_priority = min(priorities) if priorities else 99

        return (min_priority, len(path), path)

    def parse(self, request=None, public=False):
        result = super().parse(request, public)

        if not self.schema_path_prefix:
            return {}

        groups_buffer = {}

        for path, methods in result.items():
            if not path.startswith(self.schema_path_prefix):
                continue

            is_resource_detail = path.strip().endswith('}')
            segments = self._get_clean_segments(path)
            group_name = "---"

            if segments:
                if is_resource_detail:
                    group_name = "/".join(segments)
                else:
                    if len(segments) > 1:
                        group_name = "/".join(segments[:-1])
                    else:
                        group_name = "---"

            if group_name not in groups_buffer:
                groups_buffer[group_name] = {}

            groups_buffer[group_name][path] = methods

        sorted_group_names = sorted(groups_buffer.keys(), key=lambda x: x.count('/'), reverse=True)

        for group_name in sorted_group_names:
            if group_name == "---":
                continue

            if len(groups_buffer[group_name]) == 1:
                if '/' in group_name:
                    parent_group = group_name.rsplit('/', 1)[0]
                    if parent_group not in groups_buffer:
                        groups_buffer[parent_group] = {}
                    groups_buffer[parent_group].update(groups_buffer[group_name])
                    del groups_buffer[group_name]
                else:
                    if "---" not in groups_buffer:
                        groups_buffer["---"] = {}
                    groups_buffer["---"].update(groups_buffer[group_name])
                    del groups_buffer[group_name]

        final_paths = {}

        def add_group_to_final(g_name, g_paths):
            sorted_items = sorted(g_paths.items(), key=self._get_sort_key)

            for path, methods in sorted_items:
                for method, operation in methods.items():
                    operation['tags'] = [g_name]
                final_paths[path] = methods

        if "---" in groups_buffer:
            add_group_to_final("---", groups_buffer["---"])
            del groups_buffer["---"]

        sorted_keys = sorted(groups_buffer.keys(), key=lambda x: (len(x), x))

        for group_name in sorted_keys:
            add_group_to_final(group_name, groups_buffer[group_name])

        return final_paths

class ApiSchemaGenerator(BaseDynamicSchemaGenerator):
    schema_path_prefix = '/api/'

class DashboardApiSchemaGenerator(BaseDynamicSchemaGenerator):
    schema_path_prefix = '/dashboard/api/'

@login_required
def erd_view(request, ext):
    from eralchemy import render_er

    if ext not in ['png', 'svg']:
        return HttpResponse("Unsupported format. Use 'png' or 'svg'.", status=400)
    content_type = 'image/svg+xml' if ext == 'svg' else 'image/png'

    setup_graphviz_path()
    db_uri = ModelUtils.get_db_uri()
    output_dir = os.path.join(settings.MEDIA_ROOT, 'doc')
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, 'erd_diagram.'+ext)

    render_er(db_uri, output_file)
    return FileResponse(open(output_file, 'rb'), content_type=content_type)

@login_required
def graph_models_view(request, ext):
    from subprocess import run

    if ext not in ['png', 'svg']:
        return HttpResponse("Unsupported format. Use 'png' or 'svg'.", status=400)
    content_type = 'image/svg+xml' if ext == 'svg' else 'image/png'

    setup_graphviz_path()
    output_dir = os.path.join(settings.MEDIA_ROOT, 'doc')
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, 'models_diagram.'+ext)

    additional_apps = request.GET.get('apps', '').strip()
    additional_apps = [app.strip() for app in additional_apps.split(',') if app.strip()]
    apps = ["app"]
    for app in additional_apps:
        if any(app == installed_app.split('.')[-1] for installed_app in settings.INSTALLED_APPS):
            apps.append(app)

    if platform.system() == "Windows":
        result = run(
            [sys.executable, 'manage.py', "graph_models", *apps, "-o", output_file],
            check=True,
            capture_output=True,
            text=True
        )
    elif platform.system() == "Linux":
        manage_py_path = os.path.join(settings.BASE_DIR, "manage.py")

        if settings.PYTHON_PATH:
            python_interpreter = os.path.join(settings.BASE_DIR, settings.PYTHON_PATH)
            if not os.path.exists(python_interpreter):
                python_interpreter = settings.PYTHON_PATH
        elif settings.VENV_PATH:
            python_interpreter = os.path.join(settings.BASE_DIR, settings.VENV_PATH, "bin", "python")
            if not os.path.exists(python_interpreter):
                python_interpreter = os.path.join(settings.VENV_PATH, "bin", "python")
        else:
            python_interpreter = os.path.join(settings.BASE_DIR, "venv", "bin", "python")

        result = run(
            [python_interpreter, manage_py_path, "graph_models", *apps, "-o", output_file],
            check=True,
            capture_output=True,
            text=True
        )
    else:
        raise EnvironmentError(f"OS {platform.system()} not supported")

    if not os.path.exists(output_file):
        return HttpResponse("The chart file was not created. Check the error logs..", status=500)
    return FileResponse(open(output_file, 'rb'), content_type=content_type)

def setup_graphviz_path():
    import shutil

    if not shutil.which("dot"):
        print("Graphviz not found. Adding the path to PATH...")

        if platform.system() == "Windows":
            graphviz_path = r"C:\Program Files\Graphviz\bin"
        elif platform.system() == "Linux":
            graphviz_path = "/usr/bin"
        else:
            raise EnvironmentError(f"OS {platform.system()} not supported")

        os.environ['PATH'] += os.pathsep + graphviz_path
        if not shutil.which("dot"):
            raise RuntimeError("Graphviz still not found. Install it manually.")