import sys
from loguru import logger


def logging_setup():
    format_info = "<green>{time:HH:mm:ss.SS}</green> | <level>{level}</level> | <level>{message}</level>"
    logger.remove()

    logger.add(
        sys.stdout,
        colorize=True,
        format=format_info,
        level="DEBUG"
    )

    logger.add("logs/all_logs.log", level="DEBUG", format=format_info)
    logger.add("logs/state.log", level="SUCCESS", format=format_info)


logging_setup()
