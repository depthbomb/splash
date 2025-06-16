from sys import stdout
from flask import Flask
from loguru import logger
from logging import ERROR, getLogger

def configure_logging(app: Flask) -> None:
    debug = app.debug

    if not debug:
        # Set default logging level to error in production since we'll mostly rely on our own solution
        werkzeug_logger = getLogger('werkzeug')
        werkzeug_logger.setLevel(ERROR)

    logger.remove()
    logger.level("DEBUG", color="<light-black>")
    logger.level("INFO", color="<light-blue>")
    logger.level("ERROR", color="<light-red><b>")
    logger.add(
            stdout,
            level="TRACE" if debug else "INFO",
            format="{time:HH:mm:ss} │ <level>{level: <8}</level> │ <fg #fff>{message}</fg #fff>",
            colorize=debug,
            backtrace=True,
            diagnose=debug,
            enqueue=not debug
    )
