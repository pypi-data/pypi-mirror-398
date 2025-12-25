# Importing modules from tradx
from tradx.marketDataEngine import marketDataEngine
from tradx.interactiveEngine import interactiveEngine
from tradx.baseClass.baseAlgo import BaseAlgo
from tradx.baseClass.market.candleData import CandleData
from tradx.baseClass.interactive.orderEvent import OrderEvent
from tradx.baseClass.interactive.tradeEvent import TradeEvent
from tradx.baseClass.interactive.order import Order
from tradx.baseClass.interactive.position import Position
from tradx.logger.logger import setup_user_logger

# Importing other necessary modules
import asyncio
import os
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta


"""
This script demonstrates the implementation of two example algorithmic trading strategies using the `tradx` library. 
It includes the following components:
Classes:
    - Example1: An example trading algorithm that places a market order.
    - Example2: An example trading algorithm that places a limit order.
Functions:
    - main: The main asynchronous function that initializes the trading environment, sets up logging, and schedules the execution of the example algorithms.
Usage:
    - The script loads environment variables from a .env file.
    - It sets up a user logger to log trading activities.
    - It initializes the market data engine and interactive engine using API keys and other configurations from the environment variables.
    - It creates instances of Example1 and Example2 algorithms.
    - It schedules the initialization and liquidation of the algorithms using the AsyncIOScheduler.
    - It waits for user input to exit the script.
Dependencies:
    - tradx.marketDataEngine
    - tradx.interactiveEngine
    - tradx.baseClass.baseAlgo
    - tradx.baseClass.candleData
    - tradx.baseClass.orderEvent
    - tradx.baseClass.tradeEvent
    - tradx.baseClass.order
    - tradx.baseClass.position
    - tradx.logger.logger
    - asyncio
    - os
    - dotenv
    - apscheduler.schedulers.asyncio
    - datetime
To run the script, execute it as a standalone Python file.
"""


class Example1(BaseAlgo):
    def __init__(
        self, marketDataEngine: marketDataEngine, interactiveEngine: interactiveEngine
    ):
        super().__init__(marketDataEngine, interactiveEngine)
        self.marketDataEngine = marketDataEngine
        self.interactiveEngine = interactiveEngine

    async def initialize(self):
        order = self.order_no()
        asyncio.ensure_future(
            self.interactiveEngine.market_order("NSEFO", 48117, "NRML", 75, order)
        )

    async def deinitialize(self):
        asyncio.ensure_future(self.unsubscribe())

    async def on_barData(self, data: CandleData):
        """Expected Bar data here."""
        self.marketDataEngine.user_logger.info(
            f"Received the bar: {data}", caller=f"{self.__class__.__name__}.on_data"
        )

    async def on_orderEvent(self, order: OrderEvent):
        self.interactiveEngine.user_logger.info(
            f"Received order event: {order}",
            caller=f"{self.__class__.__name__}.on_orderEvent",
        )

    async def on_tradeEvent(self, trade: TradeEvent):
        self.interactiveEngine.user_logger.info(
            f"Received trade event: {trade}",
            caller=f"{self.__class__.__name__}.on_tradeEvent",
        )

    async def subscribe(self): ...
    async def unsubscribe(self): ...


class Example2(BaseAlgo):
    def __init__(
        self, marketDataEngine: marketDataEngine, interactiveEngine: interactiveEngine
    ):
        super().__init__(marketDataEngine, interactiveEngine)
        self.marketDataEngine = marketDataEngine
        self.interactiveEngine = interactiveEngine

    async def initialize(self):
        order = self.order_no()
        asyncio.ensure_future(
            self.interactiveEngine.limit_order("NSEFO", 48117, "NRML", 75, 0.5, order)
        )

    async def deinitialize(self):
        asyncio.ensure_future(self.unsubscribe())

    async def on_barData(self, data: CandleData):
        """Expected Bar data here."""
        self.marketDataEngine.user_logger.info(
            f"Received the bar: {data}", caller=f"{self.__class__.__name__}.on_data"
        )

    async def on_orderEvent(self, order: OrderEvent):
        self.interactiveEngine.user_logger.info(
            f"Received order event: {order}",
            caller=f"{self.__class__.__name__}.on_orderEvent",
        )

    async def on_tradeEvent(self, trade: TradeEvent):
        self.interactiveEngine.user_logger.info(
            f"Received trade event: {trade}",
            caller=f"{self.__class__.__name__}.on_tradeEvent",
        )

    async def subscribe(self): ...

    async def unsubscribe(self): ...


async def main():
    log_file_path = os.path.join(os.path.dirname(__file__), "TEST.log")
    if os.path.exists(log_file_path):
        os.remove(log_file_path)
    user_logger = setup_user_logger(log_file_path)
    scheduler = AsyncIOScheduler()
    scheduler.start()
    tradeObject = marketDataEngine(
        "MARKETDATA_API_KEY",
        "MARKETDATA_API_SECRET",
        "SOURCE",
        "ROOT",
        user_logger,
    )

    interactiveObj = interactiveEngine(
        "INTERACTIVE_API_KEY",
        "INTERACTIVE_API_SECRET",
        "SOURCE",
        "ROOT",
        user_logger,
    )

    await interactiveObj.initialize()
    await tradeObject.loadMaster()
    algo1 = Example1(tradeObject, interactiveObj)
    algo2 = Example2(tradeObject, interactiveObj)
    scheduler.add_job(
        algo1.initialize, "date", run_date=datetime.now() + timedelta(seconds=20)
    )
    scheduler.add_job(
        algo2.initialize, "date", run_date=datetime.now() + timedelta(seconds=30)
    )
    scheduler.add_job(
        algo1.liquidateIntraday, "date", run_date=datetime.now() + timedelta(seconds=40)
    )
    scheduler.add_job(
        algo2.liquidateIntraday, "date", run_date=datetime.now() + timedelta(seconds=50)
    )

    await asyncio.to_thread(input, "Type 'exit' to exit\n")
    await interactiveObj.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
