
```python
# settings.py

INSTALLED_APPS = [
    # ...
    'libsv1.apps.api_doc.apps.ModuleAppConfig',
    'drf_spectacular',
    'drf_spectacular_sidecar',
    # ...
]

SECURITY_SCHEME_NAME = f'{PROJECT_ID.replace(" ", "_").replace("-", "_")}'

SPECTACULAR_SETTINGS = {
    'TITLE': PROJECT_NAME,
    'DESCRIPTION': '',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    # 'SCHEMA_PATH_PREFIX': '/api/',
    'SCHEMA_PATH_PREFIX_TRIM': '',
    'DEFAULT_EXTRA_MEDIA_TYPES': ['application/json'],
    'SWAGGER_UI_SETTINGS': {
        'persistAuthorization': True,
        'defaultModelsExpandDepth': -1,
        'validatorUrl': None,
    },
    'COMPONENT_SPLIT_REQUEST': True,
    'DEFAULT_SCHEMA_OPTIONS': {
        'component_encoding_rule': "application/json"
    },
    'DISABLE_ERRORS_AND_WARNINGS': True,
    'POSTPROCESSING_HOOKS': [
        'libsv1.apps.api_doc.views.custom_postprocessing_hook',
    ],
    'EXTENSIONS': [
        'libsv1.apps.api_doc.views.CustomSerializerExtension',
    ],
    'APPEND_COMPONENTS': {
        'securitySchemes': {
            SECURITY_SCHEME_NAME: {
                'type': 'http',
                'scheme': 'bearer',
                'bearerFormat': 'Token',
            }
        }
    },
    'SECURITY': [
        {SECURITY_SCHEME_NAME: []}
    ],
}

# core/urls.py

urlpatterns = [
    # ...
    path('', include('libsv1.apps.api_doc.urls')),
    # ...
]
```
