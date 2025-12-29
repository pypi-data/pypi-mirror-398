import logging
import colorlog
import os

logger = colorlog.getLogger("my_logger")
logger.setLevel(logging.DEBUG)


if os.environ.get("UVICORN_MAIN_PROCESS") == "1":
    if logger.hasHandlers():
        logger.handlers.clear()

    handler = colorlog.StreamHandler()
    handler.setFormatter(
        colorlog.ColoredFormatter(
            "%(log_color)s%(levelname)s:%(name)s:%(message)s",
            log_colors={
                "DEBUG": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "bold_red",
            },
        )
    )
    logger.addHandler(handler)
