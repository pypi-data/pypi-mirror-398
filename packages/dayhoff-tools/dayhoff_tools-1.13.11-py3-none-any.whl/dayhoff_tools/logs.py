import logging
import sys


def configure_logs(logging_level=logging.INFO):
    """Configure logging"""
    logging.getLogger().handlers.clear()
    logging.basicConfig(
        level=logging_level,  # Level of logging you want to capture
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",  # Format of the log message
        stream=sys.stdout,
    )


def test_logs():
    """Ensure that logging and printing work as expected."""
    # Create a logger object
    logger = logging.getLogger(__name__)

    # Log some messages
    logger.debug(
        "This is a debug message"
    )  # Will not be logged due to the INFO level setting
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")
