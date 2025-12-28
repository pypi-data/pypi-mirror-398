
```python
# settings.py

API_PREFIXES = [
    '/api/',
    #'/dashboard/api/',
]

IS_GLOBAL_SYSTEM_LOG_ENABLE = True
GLOBAL_SYSTEM_LOG_LIFE_SAVED_HOURS = 60 * 24 * 3
GLOBAL_SYSTEM_LOG_LIFE_OK_MINUTES = 60 * 12
GLOBAL_SYSTEM_LOG_IGNORE_PREFIXES = [
    '/doc/',
    '/test',
    '/api/test',
]

INSTALLED_APPS = [
    # ...
    'libsv1.apps.global_system_log.apps.ModuleAppConfig',
    # ...
]

MIDDLEWARE = [
    # ...
    'libsv1.apps.global_system_log.middleware.GlobalSystemLogMiddleware',
    # ...
]
```
