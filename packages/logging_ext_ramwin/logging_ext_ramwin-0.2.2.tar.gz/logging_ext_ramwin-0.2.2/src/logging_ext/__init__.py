"""
logging_ext - Extended logging handlers with date-based filename formatting
"""

import logging

from .handlers import DateBasedFileHandler

__version__ = "0.2.2"
__all__ = ["DateBasedFileHandler"]


try:
    import colorlog
    stream_handler = colorlog.StreamHandler()
    stream_handler.setFormatter(colorlog.ColoredFormatter(
        "%(log_color)s%(levelname)s:%(name)s:%(message)s"
        ))
except ModuleNotFoundError:
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(logging.Formatter(
     '%(asctime)s [%(module)s:%(lineno)d] %(levelname)s %(message)s'
    ))


def setup_handler():
    """
    init file log handler and stream handler
    """
    stream_handler.setLevel(logging.INFO)
    file_handler = logging.FileHandler("info.log", mode="w")
    file_handler.setFormatter(logging.Formatter(
         '%(asctime)s [%(module)s:%(lineno)d] %(levelname)s %(message)s'
        ))
    logging.basicConfig(level=logging.INFO, handlers=[stream_handler, file_handler])

    logger = logging.getLogger(__name__)
    logger.info("引入日志模块")
