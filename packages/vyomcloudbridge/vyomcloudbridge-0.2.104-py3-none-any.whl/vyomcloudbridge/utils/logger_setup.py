# vyomcloudbridge/utils/logger_setup.py
import logging
import os
from vyomcloudbridge.constants.constants import log_dir, log_file_name

default_log_dir = os.path.expanduser(log_dir)


def setup_logger(
    log_dir=default_log_dir, name=None, show_terminal=False, log_level=logging.INFO
) -> logging.Logger:

    if log_level is None:
        log_level = logging.INFO

    os.makedirs(log_dir, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    if logger.hasHandlers():  # Remove any existing handlers
        logger.handlers.clear()

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # file_handler = logging.FileHandler(os.path.join(log_dir, f"{name}.log"))
    file_handler = logging.FileHandler(os.path.join(log_dir, log_file_name))
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    if show_terminal:
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(log_level)
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

    logger.propagate = False
    return logger
