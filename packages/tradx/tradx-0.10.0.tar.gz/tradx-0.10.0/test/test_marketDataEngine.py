import asyncio
import os


def test_Initialize() -> None:
    """
    Test the initialization of the marketDataEngine.
    This test performs the following steps:
    1. Sets up a user logger and specifies the log file path.
    2. Removes the log file if it already exists.
    3. Creates an instance of marketDataEngine with environment variables for API key, secret, source, and root.
    4. Initializes the marketDataEngine instance and waits for 5 seconds.
    5. Verifies that the log file is created.
    6. Verifies that the log file contains specific log messages indicating successful initialization, login, and connection.
    Raises:
        AssertionError: If the log file is not created or if the expected log messages are not found in the log file.
    """

    from tradx.logger.logger import setup_user_logger

    log_file_path = os.path.join(os.path.dirname(__file__), "test_marketDataEngine.log")
    if os.path.exists(log_file_path):
        os.remove(log_file_path)
    user_logger = setup_user_logger(log_file_path)

    async def objectCreation():
        from dotenv import load_dotenv

        load_dotenv()
        from tradx.marketDataEngine import marketDataEngine

        market_data_engine = marketDataEngine(
            os.getenv("MARKETDATA_API_KEY"),
            os.getenv("MARKETDATA_API_SECRET"),
            os.getenv("SOURCE"),
            os.getenv("ROOT"),
            user_logger,
        )
        await market_data_engine.initialize()
        await asyncio.sleep(5)
    asyncio.run(objectCreation())
    # Verify that the log file is created
    assert os.path.exists(log_file_path), "Log file was not created."

    # Verify that the log file contains the expected log messages
    with open(log_file_path, "r") as log_file:
        log_contents = log_file.read()
        assert (
            "|INFO|marketDataEngine.__init__|Market Data Engine Object initialized.|"
            in log_contents
        ), "Initialization message not found in log file."
        assert (
            "|INFO|marketDataEngine.login|Login successful.|" in log_contents
        ), "Login message not found in log file."
        assert (
            "|INFO|marketDataEngine.on_connect|Market Data Socket connected successfully!|"
            in log_contents
        ), "Connection message not found in log file."
