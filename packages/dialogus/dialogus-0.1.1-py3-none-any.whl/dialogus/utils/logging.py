import logging
import sys

from loguru import logger


def configure_pretty_logging(debug_level: int = logging.DEBUG) -> None:
    """
    Configures the logging system to output pretty logs.

    This function enables the 'dialogus' logger, sets up an intercept handler to
    capture logs from the standard logging module, removes all existing handlers
    from the 'loguru' logger, and adds a new handler that outputs to stdout with
    pretty formatting (colored, not serialized, no backtrace or diagnosis information).

    Args:
        debug_level: The logging level to use. Should be one of the following:
            5 (TRACE), 10 (DEBUG), 20 (INFO), 30 (WARNING), 40 (ERROR), or 50 (CRITICAL).
    """
    logger.enable("dialogus")
    logging_format = (
        "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
        "<level>{level: <8}</level> | "
        "{name}:{function}:{line} | "
        "<level>{message}</level>"
    )

    logger.remove()
    should_colorize = sys.stderr.isatty()
    logger.add(
        sys.stderr, format=logging_format, level=debug_level, colorize=should_colorize
    )
