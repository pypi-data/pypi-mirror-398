import logging
import inspect
from datetime import datetime
import os


class CustomLogger(logging.Logger):
    """Custom logger that dynamically captures caller details."""

    def _log_with_caller(self, level, msg, *args, **kwargs):
        # Dynamically fetch the calling function's details
        frame = inspect.stack()[2]  # Get the caller's stack frame (2 levels up)
        caller_file = os.path.basename(frame.filename)  # Extract the filename
        caller_func = frame.function  # Extract the function name

        # Add caller information to `extra`
        extra = kwargs.get("extra", {})
        extra["caller_file"] = caller_file
        extra["caller_func"] = caller_func
        kwargs["extra"] = extra

        # Proceed with the standard logging
        super().log(level, msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        self._log_with_caller(logging.INFO, msg, *args, **kwargs)

    def debug(self, msg, *args, **kwargs):
        self._log_with_caller(logging.DEBUG, msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        self._log_with_caller(logging.WARNING, msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        self._log_with_caller(logging.ERROR, msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        self._log_with_caller(logging.CRITICAL, msg, *args, **kwargs)


# Replace the default logger class with the custom one
logging.setLoggerClass(CustomLogger)


# Function to set up the user logger
def setup_user_logger():
    """Sets up and returns the user logger."""
    user_logger = logging.getLogger("user_logger")

    # Ensure the "log" directory exists
    os.makedirs("./log", exist_ok=True)

    # Dynamically fetch the caller's filename for the log file
    caller_file = os.path.splitext(os.path.basename(inspect.stack()[1].filename))[0]

    # Create a file handler with a timestamped filename
    log_filename = f"./log/{caller_file}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt"
    user_handler = logging.FileHandler(log_filename)
    user_handler.setLevel(logging.DEBUG)  # Capture all log levels

    # Create a formatter with detailed caller information
    user_formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(caller_file)s - Function: %(caller_func)s - Line: %(caller_lineno)d - %(message)s"
    )
    user_handler.setFormatter(user_formatter)

    # Add the handler to the logger
    user_logger.addHandler(user_handler)
    user_logger.setLevel(logging.DEBUG)  # Enable all log levels
    return user_logger



