# logging_config.py
import os
import logging
import sys

def get_logger(log_name) -> logging.Logger:
    """
    Returns a shared logger instance for the entire application.
    Re-uses the logger if it's already been created, so we don't
    add duplicate handlers each time we import it.
    """
    # Get (or create) a logger with a fixed name
    logger = logging.getLogger(log_name)

    # If the logger has no handlers, set them up
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)  # or INFO, etc.

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_fmt = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        )
        console_handler.setFormatter(console_fmt)
        logger.addHandler(console_handler)

        # File handler
        desktop_path = os.path.expanduser("~/Desktop")
        # create if does not exist
        os.makedirs(desktop_path, exist_ok=True)

        file_handler = logging.FileHandler(os.path.join(desktop_path, "app.log"), mode="a")
        file_handler.setLevel(logging.DEBUG)
        file_fmt = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        )
        file_handler.setFormatter(file_fmt)
        logger.addHandler(file_handler)

        # Optional: Avoid log propagation to root if you prefer
        # logger.propagate = False

        logger.debug("Logger initialized with console and file handlers.")

    return logger