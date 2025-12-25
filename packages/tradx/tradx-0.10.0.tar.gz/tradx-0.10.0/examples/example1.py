from tradx.marketDataEngine import marketDataEngine
from tradx.interactiveEngine import interactiveEngine
from tradx.baseClass.baseAlgo import BaseAlgo
from tradx.baseClass.market.candleData import CandleData
from tradx.logger.logger import setup_user_logger
import asyncio
import os
from dotenv import load_dotenv

"""
This module defines an example trading strategy that subscribes to the 'NIFTY 50' index
and processes the received candle data using the tradx library.
Classes:
    Example1(BaseAlgo): A class that handles the subscription to the 'NIFTY 50' index
                        and processes the received candle data.
Functions:
    main(): The main function that initializes the market data engine, interactive engine,
            and the example strategy, subscribes to the 'NIFTY 50' index, and runs the
            strategy for 2 minutes before deinitializing and shutting down the engines.
Usage:
    Run this module as a script to execute the example strategy.
"""


class Example1(BaseAlgo):
    def __init__(
        self, marketDataEngine: marketDataEngine, interactiveEngine: interactiveEngine
    ):
        super().__init__(marketDataEngine, interactiveEngine)
        self.marketDataEngine = marketDataEngine

    async def initialize(self):

        asyncio.ensure_future(self.subscribe())

    async def deinitialize(self):
        asyncio.ensure_future(self.unsubscribe())

    async def on_barData(self, data: CandleData):
        """Expected Bar data here."""
        self.marketDataEngine.user_logger.info(
            f"Received the bar: {data}", caller=f"example1.on_data"
        )

    async def on_touchLineData(self, data):
        self.marketDataEngine.user_logger.info(
            f"Received the touchline: {data}", caller=f"example1.on_data"
        )

    async def on_orderEvent(self, order): ...

    async def on_tradeEvent(self, message): ...

    async def subscribe(self):
        nifty = next(
            obj for obj in self.marketDataEngine.index_list if obj.Name == "NIFTY 50"
        )
        await self.marketDataEngine.subscribe(
            [
                {
                    "exchangeSegment": nifty.ExchangeSegment,
                    "exchangeInstrumentID": nifty.ExchangeInstrumentID,
                }
            ],
            1501,
            self,
        )

    async def unsubscribe(self):
        nifty = next(
            obj for obj in self.marketDataEngine.index_list if obj.Name == "NIFTY 50"
        )
        await self.marketDataEngine.unsubscribe(
            [
                {
                    "exchangeSegment": nifty.ExchangeSegment,
                    "exchangeInstrumentID": nifty.ExchangeInstrumentID,
                }
            ],
            1501,
            self,
        )


async def main():
    load_dotenv()
    log_file_path = os.path.join(os.path.dirname(__file__), "example1.log")
    if os.path.exists(log_file_path):
        os.remove(log_file_path)
    user_logger = setup_user_logger(log_file_path)
    tradeObject = marketDataEngine(
        os.getenv("MARKETDATA_API_KEY"),
        os.getenv("MARKETDATA_API_SECRET"),
        os.getenv("SOURCE"),
        os.getenv("ROOT"),
        user_logger,
    )

    interactiveObj = interactiveEngine(
        os.getenv("INTERACTIVE_API_KEY"),
        os.getenv("INTERACTIVE_API_SECRET"),
        os.getenv("SOURCE"),
        os.getenv("ROOT"),
        user_logger,
    )

    await tradeObject.initialize()
    await tradeObject.loadMaster()
    algo1 = Example1(tradeObject, interactiveObj)
    await algo1.initialize()
    await asyncio.sleep(120)
    await algo1.deinitialize()
    await tradeObject.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
