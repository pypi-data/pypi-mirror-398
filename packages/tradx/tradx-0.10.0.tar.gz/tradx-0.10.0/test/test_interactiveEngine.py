import asyncio
import os
from tradx.logger.logger import setup_user_logger

log_file_path = os.path.join(os.path.dirname(__file__), "test_interactiveEngine.log")


def test_interactiveEngine() -> None:
    """
    Test the initialization of the interactiveEngine object.
    This test performs the following steps:
    1. Removes the existing log file if it exists.
    2. Sets up a user logger.
    3. Creates and initializes an interactiveEngine object asynchronously.
    4. Verifies that the log file is created.
    5. Verifies that the log file contains the expected log messages:
        - Initialization message
        - Login successful message
        - Connection successful message
    Raises:
        AssertionError: If the log file is not created or if the expected log messages are not found.
    """

    if os.path.exists(log_file_path):
        os.remove(log_file_path)
    user_logger = setup_user_logger(log_file_path)

    async def objectCreation():
        from dotenv import load_dotenv

        load_dotenv()
        from tradx.interactiveEngine import interactiveEngine

        interactive_engine = interactiveEngine(
            os.getenv("INTERACTIVE_API_KEY"),
            os.getenv("INTERACTIVE_API_SECRET"),
            os.getenv("SOURCE"),
            os.getenv("ROOT"),
            user_logger,
        )
        await interactive_engine.initialize()
        await asyncio.sleep(2)
        await interactive_engine.shutdown()

    asyncio.run(objectCreation())
    # Verify that the log file is created
    assert os.path.exists(log_file_path), "Log file was not created."

    # Verify that the log file contains the expected log messages
    with open(log_file_path, "r") as log_file:
        log_contents = log_file.read()
        # Check for tradx.interactiveEngine.initialize()
        assert (
            "|INFO|interactiveEngine.__init__|Interactive Engine Object initialized.|"
            in log_contents
        ), "Initialization message not found in log file."
        assert (
            "|INFO|interactiveEngine.login|Login successful.|" in log_contents
        ), "Login message not found in log file."
        # Check for tradx.interactiveEngine.on_connect()
        assert (
            "|INFO|interactiveEngine.on_connect|Interactive socket connected successfully!|"
            in log_contents
        ), "Connection message not found in log file."
        # Check for tradx.interactiveEngine.on_joined()
        assert (
            "|INFO|interactiveEngine.on_joined|Interactive socket joined successfully!"
            in log_contents
        ), "Connection message not found in log file."
        # Check for tradx.interactiveEngine.shutdown()

        assert (
            "|INFO|interactiveEngine.shutdown|Entering shut down mode.|" in log_contents
        ), "Shutdown mode entry message not found in log file."
        assert (
            "|INFO|interactiveEngine.shutdown|Logged Out.|" in log_contents
        ), "Logged out message not found in log file."
