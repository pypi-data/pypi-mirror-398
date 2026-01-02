import logging

DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


def configure_logging(level: int = logging.INFO, fmt: str | None = None) -> None:
    """
    Configure logging for the prop_profiler package.

    Args:
        level: Logging level to apply to the root and package logger.
        fmt: Optional logging format string.
    """
    logging.basicConfig(level=level, format=fmt or DEFAULT_LOG_FORMAT, force=True)
    logging.getLogger("prop_profiler").setLevel(level)
