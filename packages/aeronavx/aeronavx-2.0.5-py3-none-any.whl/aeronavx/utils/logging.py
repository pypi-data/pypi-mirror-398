import logging
import sys
from typing import Optional


_logger: Optional[logging.Logger] = None


def get_logger(name: str = "aeronavx") -> logging.Logger:
    global _logger

    if _logger is None:
        _logger = logging.getLogger(name)
        _logger.setLevel(logging.INFO)

        if not _logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setLevel(logging.INFO)

            formatter = logging.Formatter(
                fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)
            _logger.addHandler(handler)

    return _logger


def set_log_level(level: int) -> None:
    logger = get_logger()
    logger.setLevel(level)
    for handler in logger.handlers:
        handler.setLevel(level)
