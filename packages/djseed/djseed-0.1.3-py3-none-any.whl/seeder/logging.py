# seeder/logging.py

import logging
from typing import Optional


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Return a shared logger for djseed. If no handlers are configured yet,
    attach a simple stdout handler with an INFO default level.
    """
    logger_name = name if name else "djseed"
    logger = logging.getLogger(logger_name)
    if not logging.getLogger("djseed").handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
        root_logger = logging.getLogger("djseed")
        root_logger.addHandler(handler)
        root_logger.setLevel(logging.DEBUG)
        root_logger.propagate = False
    return logger


__all__ = ["get_logger"]
