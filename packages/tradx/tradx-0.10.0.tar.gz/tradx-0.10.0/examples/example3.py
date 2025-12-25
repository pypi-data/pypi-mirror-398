# Importing modules from tradx
from tradx.marketDataEngine import marketDataEngine
from tradx.interactiveEngine import interactiveEngine
from tradx.baseClass.baseAlgo import BaseAlgo
from tradx.baseClass.market.candleData import CandleData
from tradx.baseClass.market.index import Index
from tradx.baseClass.market.optionsInstrument import OptionsInstrument, OptionType
from tradx.baseClass.interactive.orderEvent import OrderEvent
from tradx.baseClass.interactive.tradeEvent import TradeEvent
from tradx.baseClass.interactive.order import Order
from tradx.baseClass.interactive.position import Position
from tradx.logger.logger import setup_user_logger
from tradx.constants.holidays import holidays

# Importing other necessary modules
import asyncio
import os
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
from typing import List, Any
from decimal import Decimal

"""
This script demonstrates the implementation of two example algorithmic trading strategies using the `tradx` library. 
It includes the following components:
Classes:
    - Example1: An example trading algorithm that places a market order on current week expiry nifty call at-the-money.
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


async def exit_input(
    exit_event: asyncio.Event,
):
    """Waits for user input to exit the program."""
    x = ""
    event_wait_task = asyncio.ensure_future(exit_event.wait())
    while x != "exit" and (not exit_event.is_set()):
        try:
            io_task = asyncio.ensure_future(ainput("Type 'exit' to exit\n"))
            done, pending = await asyncio.wait(
                [io_task, event_wait_task], return_when=asyncio.FIRST_COMPLETED
            )
            if event_wait_task in done:
                io_task.cancel()
            else:
                x = done.pop().result()
                if x == "exit":
                    exit_event.set()
        except asyncio.CancelledError:
            pass
    print("Gracefully exiting the algorithm.")
    exit_event.set()


class SIndex:
    """Class to manage index options and calculate strike prices based on given values and strike gaps."""

    def __init__(
        self,
        symbol: Index,
        strikegap: Decimal,
        value: Decimal,
        lot_size: int,
        optionChain: List[OptionsInstrument] = [],
    ) -> None:
        self._symbol: Index = symbol
        self._strikegap: Decimal = strikegap
        self._value: Decimal = value
        self._lot_size: int = lot_size
        self._strike: int = 0
        self._prev_strike: int = None  # To store the previous strike value
        self._optionChain: List[OptionsInstrument] = optionChain

    @property
    def symbol(self) -> Index:
        return self._symbol

    @property
    def lot_size(self) -> int:
        return self._lot_size

    @symbol.setter
    def symbol(self, value) -> None:
        if not isinstance(value, Index):
            raise ValueError("Symbol must be a tradx.baseClass.Index.Index")
        self._symbol = value

    @property
    def strikegap(self) -> Decimal:
        return self._strikegap

    @strikegap.setter
    def strikegap(self, value) -> None:
        self._strikegap = value

    @property
    def value(self) -> Decimal:
        return self._value

    @value.setter
    def value(self, value: Any) -> None:
        """
        Sets the value and calculates the strike price based on the given value.
        Args:
            value (Any): The value to be set. It will be converted to a Decimal.
        Sets:
            self._value (Decimal): The value converted to a Decimal.
            self._strike (int): The calculated strike price based on the value and strike gap.
        """

        self._value = Decimal(value)
        strike = int(self._strikegap * round(self._value / self._strikegap))
        self._strike = strike

    @property
    def strike(self) -> int:
        return self._strike

    @property
    def previous_strike(self) -> int:
        """Returns the previous calculated strike value."""
        return self._previous_strike

    @property
    def has_changed(self) -> bool:
        """Checks if the strike value has changed."""
        return self.previous_strike != self.strike

    @property
    def optionChain(self) -> List[OptionsInstrument]:
        return self._optionChain

    @optionChain.setter
    def optionChain(self, value: List[OptionsInstrument]) -> None:
        if not isinstance(value, List):
            raise ValueError("OptionChain must be a list")
        self._optionChain = value

    def search_option(
        self,
        StrikePrice: int = None,
        OptionType: int = None,
        ExchangeInstrumentID: int = None,
    ) -> List[OptionsInstrument]:
        """
        Search for options based on specified criteria.
        Args:
            StrikePrice (int, optional): The strike price of the option. Must be an integer.
            OptionType (int, optional): The type of the option. Must be an integer.
        Returns:
            List[OptionsInstrument]: A list of options that match the specified criteria.
            If no criteria are specified, returns the entire option chain.
        Raises:
            AssertionError: If StrikePrice or OptionType are not integers.
        """
        assert StrikePrice is None or isinstance(
            StrikePrice, int
        ), "StrikePrice must be an integer"
        assert OptionType is None or isinstance(
            OptionType, int
        ), "OptionType must be an integer"

        criteria = {
            "StrikePrice": StrikePrice,
            "OptionType": OptionType,
            "ExchangeInstrumentID": ExchangeInstrumentID,
        }
        criteria = {k: v for k, v in criteria.items() if v is not None}

        if not criteria:
            return self._optionChain

        results = self._optionChain
        for key, value in criteria.items():
            results = [option for option in results if getattr(option, key) == value]

        return results

    def update_previous(self) -> None:
        self._previous_strike = self._strike

    def end(self) -> None:
        self._optionChain.clear()


class Example1(BaseAlgo):
    def __init__(
        self, marketDataEngine: marketDataEngine, interactiveEngine: interactiveEngine
    ):
        super().__init__(marketDataEngine, interactiveEngine)
        self.nifty = SIndex(None, 50, 0, 75)
        self.marketDataEngine = marketDataEngine
        self.interactiveEngine = interactiveEngine

    async def initialize(self):
        options = await self.marketDataEngine.option_search(
            UnderlyingIndexName=self.nifty.symbol.Name, minimumExpiry=True
        )
        self.nifty.optionChain = options
        instruments = []
        instruments.append(
            {
                "exchangeSegment": self.nifty.symbol.ExchangeSegment,
                "exchangeInstrumentID": self.nifty.symbol.ExchangeInstrumentID,
            }
        )
        _list = await self.marketDataEngine.fetch_ltp(instruments)
        nifty_index_data = next(
            item
            for item in _list
            if item.ExchangeInstrumentID == self.nifty.symbol.ExchangeInstrumentID
        )
        self.nifty.value = nifty_index_data.LastTradedPrice
        print(f"Nifty index value: {self.nifty.value}")
        instruments.clear()
        nifty_call_atm = self.nifty.search_option(
            StrikePrice=self.nifty.strike,
            OptionType=OptionType.CE.value,
        )[0]
        asyncio.ensure_future(
            self.interactiveEngine.market_order(
                self.interactiveEngine.xt.EXCHANGE_NSEFO,
                nifty_call_atm.ExchangeInstrumentID,
                "NRML",
                -1 * self.nifty.lot_size,
                self.order_no(),
            )
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
    exit_event = asyncio.Event()
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
    scheduler.add_job(
        algo1.initialize, "date", run_date=datetime.now() + timedelta(seconds=20)
    )
    scheduler.add_job(
        algo1.liquidateIntraday(), "date", run_date=datetime.now() + timedelta(seconds=40)
    )

    _input_task = asyncio.ensure_future(exit_input(exit_event))
    await exit_event.wait()
    await tradeObject.shutdown()
    await interactiveObj.shutdown()


if __name__ == "__main__":
    try:
        """Entering only if today is not a holiday"""
        _today = datetime.today().date()
        if _today in holidays:
            os._exit(0)
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n❌ Exiting...")
