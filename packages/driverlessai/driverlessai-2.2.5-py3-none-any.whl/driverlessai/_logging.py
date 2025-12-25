import logging
import sys

logger = logging.getLogger("driverlessai")
"""Package logger."""


class ConsoleLoggingHandler(logging.StreamHandler):
    """A logging handler that prints log messages to standard output."""

    def __init__(self) -> None:
        super().__init__(sys.stdout)
        self.setFormatter(logging.Formatter("%(levelname)s - %(message)s"))


def configure_console_logger() -> None:
    """Adds a console handler."""
    for handler in logger.handlers:
        if isinstance(handler, ConsoleLoggingHandler):
            return  # we have already added the ConsoleLoggingHandler
    logger.addHandler(ConsoleLoggingHandler())
    if logger.level == logging.NOTSET:
        logger.setLevel(logging.INFO)
