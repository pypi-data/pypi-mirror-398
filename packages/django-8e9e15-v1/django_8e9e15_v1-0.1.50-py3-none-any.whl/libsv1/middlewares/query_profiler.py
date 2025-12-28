import logging
from django.conf import settings
from django.db import connection

logger = logging.getLogger(__name__)

class QueryProfilerMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not settings.DEBUG:
            return self.get_response(request)

        response = self.get_response(request)

        self._log_queries()

        return response

    def _log_queries(self):
        ignore_patterns = getattr(settings, 'QUERY_PROFILER_IGNORE_PATTERNS', [])

        queries = connection.queries
        if not queries:
            return

        query_count = len(queries)
        total_time = sum(float(q['time']) for q in queries)

        logger.debug(
            "SQL Query Profiler: %d queries executed in %.2fms",
            query_count, total_time * 1000
        )

        for query in queries:
            sql = query['sql'].lower()

            if any(pattern in sql for pattern in ignore_patterns):
                continue

            logger.debug("-> (%.2fms) %s", float(query['time']) * 1000, query['sql'])

"""
# Django Query Profiler

A simple Django middleware to log SQL queries executed during a request. This middleware is active only when `DEBUG = True`.

## Usage

1.  Add the middleware to your `MIDDLEWARE` list in `settings.py`. It should be placed after any other middleware that might generate queries.

    ```python
    # settings.py
    MIDDLEWARE = [
        # ... other middleware
        'libsv1.middlewares.query_profiler.QueryProfilerMiddleware',
    ]
    ```

2.  (Optional) You can specify a list of string patterns to ignore in the logs. Any query containing one of these patterns will not be logged.

    ```python
    # settings.py
    QUERY_PROFILER_IGNORE_PATTERNS = ['global_system_logs']
    ```

3.  Ensure your logging is configured to display `DEBUG` level messages.
"""