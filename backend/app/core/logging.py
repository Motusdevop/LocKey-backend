import sys

from loguru import logger

from app.core.config import Settings


def configure_logging(settings: Settings) -> None:
    logger.remove()
    logger.add(
        sys.stderr,
        level=settings.log_level.upper(),
        enqueue=True,
        backtrace=False,
        diagnose=False,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "{name}:{function}:{line} | "
            "<level>{message}</level>"
        ),
    )
