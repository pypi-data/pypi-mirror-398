import os
import sys

from loguru import logger

from nature.utils import is_debug

logger.add("multiprocess.log", enqueue=True)


def set_log_level(level: str):
    logger.remove()  # Remove existing handlers
    logger.add(sys.stderr, level=level.upper())


if is_debug():
    set_log_level(os.environ.get("NATURE_LOG_LEVEL", "DEBUG"))
else:
    set_log_level(os.environ.get("NATURE_LOG_LEVEL", "INFO"))
