# logging_config.py
import logging
from config import LOG_FILE, LOG_LEVEL, LOG_FORMAT

def setup_logging():
    logging.basicConfig(
        filename=LOG_FILE,
        level=LOG_LEVEL,
        format=LOG_FORMAT,
        filemode='w'
    )

    """
    # Optionally add console logging
    console_handler = logging.StreamHandler()
    console_handler.setLevel(LOG_LEVEL)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT))

    logger = logging.getLogger()
    logger.addHandler(console_handler)

    return logger
    """
