# Django DB Reconnect

A simple Django app that provides a middleware and a decorator to automatically handle database connection losses (e.g., "MySQL server has gone away").

This utility catches specific `OperationalError` exceptions, closes the stale database connections, and retries the operation once. This can help improve the stability of long-running Django applications or applications with intermittent network access to the database.

## Usage

1.  Add the middleware to your `MIDDLEWARE` list in `settings.py`.

```python
# settings.py
MIDDLEWARE = [
    'libsv1.middlewares.db_reconnect.DBConnectionMiddleware',
]
```

2.  (Optional) You can override this list by defining DB_RECONNECT_ERROR_CODES in your settings.py.

```python
# settings.py
DB_RECONNECT_ERROR_CODES = [2006, 2013]
```