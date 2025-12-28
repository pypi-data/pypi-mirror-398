import builtins
import logging
from datetime import datetime
from typing import Any

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

_original_print = builtins.print

def dprint(*args: Any, **kwargs: Any) -> None:
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    _original_print(f"[{timestamp}]", *args, **kwargs)

def _new_print_with_timestamp(*args: Any, **kwargs: Any) -> None:
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    _original_print(f"[{timestamp}]", *args, **kwargs)

def install_global_dprint() -> None:
    setattr(builtins, 'dprint', dprint)
    logger.info("Global function 'dprint' has been installed.")

def override_global_print() -> None:
    builtins.print = _new_print_with_timestamp
    logger.info("Global function 'print' has been overridden.")