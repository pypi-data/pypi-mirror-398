import logging
from django.conf import settings
from django.db import connections

logger = logging.getLogger(__name__)

DEFAULT_ERROR_CODES = [2006, 2013]


def close_old_connections():
    for conn in connections.all():
        conn.close_if_unusable_or_obsolete()


def should_reconnect(error):
    error_codes = getattr(settings, 'DB_RECONNECT_ERROR_CODES', DEFAULT_ERROR_CODES)
    error_code = error.args[0]

    if error_code in error_codes:
        logger.warning(
            "Database connection lost (code: %s). Attempting to reconnect.",
            error_code
        )
        return True
    return False