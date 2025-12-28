from libsv1.utils.request import RequestUtils


class RequestNormalizerMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        RequestUtils.normalize_request_params(request)

        return self.get_response(request)

"""
# Django Request Normalizer

A configurable Django middleware that automatically cleans and normalizes incoming request data before it reaches your views.

## Features

-   **Trims Whitespace:** Strips leading/trailing whitespace from all string values.
-   **Normalizes Booleans:** Converts string values like `"true"` and `"false"` to actual booleans.
-   **Normalizes Nulls:** Converts string `"null"`, empty strings `""` for ID fields, and integer `0` for ID fields to `None`.
-   **Cleans Email:** Removes spaces and lowercases email fields.
-   **Handles All Data:** Works seamlessly with `GET` parameters, `application/json`, `multipart/form-data`, and `x-www-form-urlencoded` data.
-   **Configurable:** You can enable/disable the middleware or specify which URL prefixes it should act on.

## Usage

Add the middleware to your `MIDDLEWARE` list in `settings.py`. It should be placed before any middleware that accesses request data, such as DRF's authentication classes or your own views.

```python
# settings.py
MIDDLEWARE = [
    # ...
    'libsv1.middlewares.request_normalizer.RequestNormalizerMiddleware',
    # ...
]
```

## Configuration

To enable normalization, you must specify a list of URL prefixes for which it will be applied. This is done in your `settings.py`.

```python
# settings.py

# A list of URL prefixes for which normalization will be active.
API_PREFIXES = ['/api/v1/', '/api/v2/']
```

---

## Normalization Rules

| Input Value         | Key          | Output Value      | Explanation |
|----------------------|---------------|-------------------|--------------|
| `"null"`             | any           | `None`            | The string "null" becomes None |
| `"true"`             | any           | `True`            | The string "true" becomes True |
| `"false"`            | any           | `False`           | The string "false" becomes False |
| `0` (integer)        | `user_id`     | `None`            | 0 for _id or id fields becomes None |
| `"0"` (string)       | `id`          | `None`            | The string "0" for _id or id fields becomes None |
| `""` (empty string)  | `category_id` | `None`            | An empty string for _id or id fields becomes None |
| `" test%20string "`  | `name`        | `"test string"`   | Whitespace is trimmed and characters are decoded |
| `" User@Example.com "` | `email`     | `"user@example.com"` | Whitespace is removed and the string is lowercased |

---

## License

This project is licensed under the MIT License.
"""