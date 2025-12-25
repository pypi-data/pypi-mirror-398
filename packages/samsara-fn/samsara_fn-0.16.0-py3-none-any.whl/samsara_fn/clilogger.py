import logging
import sys
import os


class CustomFormatter(logging.Formatter):
    """Custom formatter that adds a prefix with log level to log messages.

    This formatter enhances log messages by:
    1. Adding a prefix with the log level (debug, info, warn, err, crit)
    2. Applying color coding:
       - Red for ERROR and CRITICAL messages
       - Orange/Yellow for WARNING messages
       - Default color for INFO and DEBUG messages

    The format of the prefix is: [prefix-level]
    Example: [cli-info] This is an info message
    """

    # ANSI color codes
    RED = "\033[91m"
    ORANGE = "\033[93m"  # Yellow/Orange color
    RESET = "\033[0m"

    def __init__(self, prefix: str = "cli") -> None:
        super().__init__()
        self.prefix = prefix

    def format(self, record: logging.LogRecord) -> str:
        # Map log levels to their short names
        level_map = {
            logging.DEBUG: "debug",
            logging.INFO: "info",
            logging.WARNING: "warn",
            logging.ERROR: "err",
            logging.CRITICAL: "crit",
        }
        level_name = level_map.get(record.levelno, "info")

        # Add prefix with level to the message
        prefix = f"[{self.prefix}-{level_name}]"

        # Add colors for different log levels
        if record.levelno >= logging.ERROR:
            prefix = f"{self.RED}{prefix}{self.RESET}"
        elif record.levelno == logging.WARNING:
            prefix = f"{self.ORANGE}{prefix}{self.RESET}"

        record.msg = f"{prefix} {record.msg}"
        return super().format(record)


def setup_logger(prefix: str = "cli") -> logging.Logger:
    """
    Set up and configure the logger.

    Args:
        prefix: Optional prefix for log messages. Defaults to "cli".

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(f"samsara_functions_{prefix}")
    verbose = os.environ.get("SAMSARA_SIMULATOR_VERBOSE", "0") == "1"

    # Remove any existing handlers to prevent duplicates
    logger.handlers.clear()

    # Set level based on verbose environment variable
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)

    # Create console handler for stdout (INFO and DEBUG messages)
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.DEBUG if verbose else logging.INFO)
    stdout_handler.addFilter(lambda record: record.levelno <= logging.INFO)

    # Create console handler for stderr (WARNING, ERROR and CRITICAL messages)
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(logging.WARNING)
    stderr_handler.addFilter(lambda record: record.levelno >= logging.WARNING)

    # Create formatter and add it to the handlers
    formatter = CustomFormatter(prefix=prefix)
    stdout_handler.setFormatter(formatter)
    stderr_handler.setFormatter(formatter)

    # Add the handlers to the logger
    logger.addHandler(stdout_handler)
    logger.addHandler(stderr_handler)

    return logger


# Create a default logger instance
logger = setup_logger()


def update_verbosity():
    global logger
    logger = setup_logger()
