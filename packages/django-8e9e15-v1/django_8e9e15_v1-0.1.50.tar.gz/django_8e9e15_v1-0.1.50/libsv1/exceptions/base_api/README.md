
```python
# settings.py
MIDDLEWARE = [
    # ...
    'libsv1.api_exception_handler.CustomExceptionMiddleware',
    # ...
]

REST_FRAMEWORK = {
    # ...
    'EXCEPTION_HANDLER': 'libsv1.exceptions.base_api.api_exception_handler',
    # ...
}
```
