import json
import logging
from typing import Any
import pusher
from django.conf import settings
from pusher.errors import PusherError

logger = logging.getLogger(__name__)

try:
    pusher_client = pusher.Pusher(
        app_id=settings.PUSHER_APP_ID,
        key=settings.PUSHER_KEY,
        secret=settings.PUSHER_SECRET,
        cluster=getattr(settings, "PUSHER_CLUSTER", ""),
        ssl=getattr(settings, "PUSHER_SSL", False),
    )
except AttributeError as e:
    logger.error(f"Pusher settings (PUSHER_APP_ID, PUSHER_KEY, PUSHER_SECRET) are not configured: {e}")
    pusher_client = None


def pusher_dump(data: Any, user_id: str | int = "", filter: str = "", comment: str = "") -> None:
    if not pusher_client:
        logger.error("Pusher client is not initialized due to missing settings.")
        return

    if not user_id or not filter:
        logger.warning("Pusher dump aborted: user_id and filter cannot be empty.")
        return

    channel_name = ''
    try:
        data_json = json.dumps(data, default=str)
        channel_name = f"{user_id}-channel"
        event_name = f"{filter}-event"

        pusher_client.trigger(
            channel_name, event_name, {"comment": comment, "data": data_json}
        )
    except PusherError as e:
        logger.error(f"Failed to send Pusher event to channel {channel_name}: {e}")
    except TypeError as e:
        logger.error(f"Failed to serialize data for Pusher: {e}")