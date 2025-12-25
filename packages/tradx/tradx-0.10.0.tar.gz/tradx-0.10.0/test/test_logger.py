from tradx.logger.logger import setup_user_logger
import os


def test_setupUserLogger():
    """
    Test the setup_user_logger function to ensure it creates a logger that writes
    log messages to a specified file.
    This test performs the following steps:
    1. Sets up a user logger with a log file path.
    2. Defines an example function that logs info, error, and debug messages.
    3. Calls the example function to generate log messages.
    4. Verifies that the log file is created.
    5. Verifies that the log file contains the expected log messages.
    Assertions:
    - The log file is created at the specified path.
    - The log file contains the expected info, error, and debug messages.
    """

    log_file_path = os.path.join(os.path.dirname(__file__), "test_logger.log")
    if os.path.exists(log_file_path):
            os.remove(log_file_path)
    user_logger = setup_user_logger(log_file_path)
    
    def example_function():
        user_logger.info(
            "This is an info message from example_function.", caller="example_function"
        )
        user_logger.error(
            "This is an error message from example_function.", caller="example_function"
        )
        user_logger.debug(
            "This is a debug message from example_function.", caller="example_function"
        )

    example_function()

    # Verify that the log file is created
    assert os.path.exists(log_file_path), "Log file was not created."

    # Verify that the log file contains the expected log messages
    with open(log_file_path, "r") as log_file:
        log_contents = log_file.read()
        assert (
            "This is an info message from example_function." in log_contents
        ), "Info message not found in log file."
        assert (
            "This is an error message from example_function." in log_contents
        ), "Error message not found in log file."
        assert (
            "This is a debug message from example_function." in log_contents
        ), "Debug message not found in log file."
