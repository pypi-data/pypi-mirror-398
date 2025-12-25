import logging
import inspect
import os


class CustomLogger(logging.Logger):
    """
    CustomLogger is a subclass of logging.Logger that adds the ability to log messages with an additional 'caller' attribute.
    Methods
    -------
    _log_with_caller(level, msg, *args, caller="Unknown", **kwargs)
        Logs a message with the specified level and caller information.
    info(msg, *args, caller="Unknown", **kwargs)
        Logs a message with level INFO and caller information.
    debug(msg, *args, caller="Unknown", **kwargs)
        Logs a message with level DEBUG and caller information.
    warning(msg, *args, caller="Unknown", **kwargs)
        Logs a message with level WARNING and caller information.
    error(msg, *args, caller="Unknown", **kwargs)
        Logs a message with level ERROR and caller information.
    critical(msg, *args, caller="Unknown", **kwargs)
        Logs a message with level CRITICAL and caller information.
    """
    

    def _log_with_caller(self, level, msg, *args, caller="Unknown", **kwargs):
        extra = kwargs.get("extra", {})
        extra["caller"] = caller
        kwargs["extra"] = extra
        super().log(level, msg, *args, **kwargs)

    def info(self, msg, *args, caller="Unknown", **kwargs):
        self._log_with_caller(logging.INFO, msg, *args, caller=caller, **kwargs)

    def debug(self, msg, *args, caller="Unknown", **kwargs):
        self._log_with_caller(logging.DEBUG, msg, *args, caller=caller, **kwargs)

    def warning(self, msg, *args, caller="Unknown", **kwargs):
        self._log_with_caller(logging.WARNING, msg, *args, caller=caller, **kwargs)

    def error(self, msg, *args, caller="Unknown", **kwargs):
        self._log_with_caller(logging.ERROR, msg, *args, caller=caller, **kwargs)

    def critical(self, msg, *args, caller="Unknown", **kwargs):
        self._log_with_caller(logging.CRITICAL, msg, *args, caller=caller, **kwargs)


# Replace the default logger class with the custom one
logging.setLoggerClass(CustomLogger)


# Set up the user logger
def setup_user_logger(filename: str):
    """
    Sets up a user-specific logger that logs messages to a file.
    Args:
        filename (str): The base name of the file where logs will be stored. 
                        The file will have a ".txt" extension.
    Returns:
        logging.Logger: A configured logger instance with a file handler and formatter.
    Raises:
        AssertionError: If the filename is not provided.
    """

    assert filename, "Filename must be provided"
    user_logger = logging.getLogger("user_logger")
    user_logger.setLevel(logging.DEBUG)  # Enable all log levels

    # Create a file handler to store logs in "LOG.txt"
    user_handler = logging.FileHandler(filename)
    user_handler.setLevel(logging.DEBUG)  # Capture all log levels in the handler

    # Create a formatter with caller information
    user_formatter = logging.Formatter(
        "|%(asctime)s|%(levelname)s|%(caller)s|%(message)s|"
    )
    user_handler.setFormatter(user_formatter)

    # Add the handler to the logger
    user_logger.addHandler(user_handler)
    return user_logger


