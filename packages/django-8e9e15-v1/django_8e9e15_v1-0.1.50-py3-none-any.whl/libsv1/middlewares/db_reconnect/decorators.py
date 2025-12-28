import functools
from django.db import OperationalError
from .core import close_old_connections, should_reconnect


def ensure_db_connection(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except OperationalError as e:
            if should_reconnect(e):
                close_old_connections()
                return func(*args, **kwargs)
            else:
                raise
    return wrapper