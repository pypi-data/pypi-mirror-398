from django.conf import settings
from django.shortcuts import redirect


class RemoveTrailingSlashMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method in ('GET', 'HEAD'):
            if request.path != '/' and request.path.endswith('/'):
                ignore_prefixes = getattr(settings, 'REMOVE_SLASH_IGNORE_PREFIXES', ['/admin/'])

                if not any(request.path.startswith(prefix) for prefix in ignore_prefixes):
                    new_url = request.path.rstrip('/')
                    if request.GET:
                        new_url += f'?{request.META["QUERY_STRING"]}'

                    return redirect(new_url, permanent=True)

        return self.get_response(request)

"""
# Django Remove Trailing Slash

A simple Django middleware that enforces a "no trailing slash" policy by permanently redirecting (301) any URL ending in a slash to its non-slashed version.

This is useful for SEO purposes to prevent duplicate content indexing.

## Features

-   Performs a 301 Permanent Redirect.
-   Preserves query strings.
-   Ignores the root path (`/`).
-   Allows configurable exclusion of URL prefixes (e.g., `/admin/`, `/api/`).


## Usage

1.  Add the middleware to your `MIDDLEWARE` list in `settings.py`. It is recommended to place it before Django's `CommonMiddleware`.

```python
# settings.py
MIDDLEWARE = [
   'libsv1.middlewares.remove_slash.RemoveTrailingSlashMiddleware',
    # ... other middleware
]
```

2.  (Optional) By default, the middleware ignores URLs starting with `/admin/`. You can customize this by adding `REMOVE_SLASH_IGNORE_PREFIXES` to your `settings.py`.

```python
# settings.py
REMOVE_SLASH_IGNORE_PREFIXES = ['/admin/', '/api/v1/']
```

That's it! The middleware will now automatically handle redirects.
"""