from abc import ABC, abstractmethod
import shortuuid
from typing import TYPE_CHECKING, List
from tradx.baseClass.interactive.order import Order
from tradx.baseClass.interactive.position import Position

import asyncio


if TYPE_CHECKING:
    from tradx.marketDataEngine import marketDataEngine
    from tradx.interactiveEngine import interactiveEngine
    from tradx.baseClass.market.touchLineData import TouchLineData
    from tradx.baseClass.interactive.orderEvent import OrderEvent
    from tradx.baseClass.interactive.tradeEvent import TradeEvent
    from tradx.baseClass.market.candleData import CandleData


class BaseAlgo(ABC):
    """
    BaseAlgo is an abstract base class for algorithmic trading strategies. It provides a framework for handling market data, orders, and trades, and requires subclasses to implement specific methods for processing data and events.
    Attributes:
        cache (dict): A cache for storing temporary data.
        order_nos (ShortUUID): Instance of ShortUUID for generating unique order identifiers.
        position_diary (List[Position]): A list to store position data.
        order_diary (List[Order]): A list to store order data.
        name (str): A unique identifier for the algorithm.
    Methods:
        __init__(marketDataEngine, interactiveEngine):
            Initializes the BaseAlgo class with marketDataEngine and interactiveEngine instances.
        on_barData(data):
            Abstract method to process candle data. Must be implemented by subclasses.
        subscribe():
            Abstract method to handle subscription logic. Must be implemented by subclasses.
        order_no():
            Generates a unique order identifier.
        order_(order):
            Handles the order event by updating the status of an existing order or inserting a new order.
        on_orderEvent(message):
            Abstract method to handle order events. Must be implemented by subclasses.
        trade_(trade):
            Handles a trade event by updating the position diary and triggering the on_tradeEvent callback.
        on_tradeEvent(message):
            Abstract method to handle trade events. Must be implemented by subclasses.
        unsubscribe():
            Abstract method to handle unsubscription logic. Must be implemented by subclasses.
        initialize():
            Abstract method to initialize the strategy. Must be implemented by subclasses.
        deinitialize():
            Abstract method to deinitialize the strategy. Must be implemented by subclasses.
        liquidateIntraday():
            Class method to liquidate all intraday positions and cancel pending orders.
        isInvested():
            Class method to check if there are any investments by summing the quantities of all positions in the position diary.
    """

    def __init__(
        self,
        marketDataEngine: "marketDataEngine",
        interactiveEngine: "interactiveEngine",
    ):
        """
        Initialize the BaseAlgo class.

        Args:
            marketDataEngine (marketDataEngine): Instance of marketDataEngine.
            interactiveEngine (interactiveEngine): Instance of interactiveEngine.
        """
        # Initialize instance variables
        self.cache = {}
        self.marketDataEngine = marketDataEngine
        self.interactiveEngine = interactiveEngine
        self.order_nos = shortuuid
        self.position_diary: List[Position] = []
        self.order_diary: List[Order] = []
        self.uuids = set()
        # Registering inside interactive engine
        self.name = interactiveEngine.shortuuid.ShortUUID().random(length=4)
        self.interactiveEngine.strategy_to_id[self.name] = self

        # Logging the initialization
        if self.marketDataEngine.user_logger:
            self.marketDataEngine.user_logger.info(
                f"Algorithm initialized with ID: {self.name}",
                caller=f"{self.__class__.__name__}.__init__",
            )

    @abstractmethod
    async def on_barData(self, data: "CandleData") -> None:
        """
        Abstract method (virtual function) to process candle data.
        Must be implemented by subclasses.

        Args:
            data (any): The input data to process.
        """
        ...

    @abstractmethod
    async def on_touchLineData(self, data: "TouchLineData") -> None:
        """
        Asynchronous method to handle touch line data.
        Args:
            data (TouchLineData): The touch line data to be processed.
        Returns:
            None
        """

        ...

    @abstractmethod
    async def subscribe(self) -> None:
        """
        Abstract method (virtual function) to process subscribe.
        Must be implemented by subclasses.

        Args:
            data (any): The input data to process.
        """
        ...

    def order_no(self) -> str:
        """
        Generate a unique order identifier.
        The identifier is an 8-digit string composed of a 4-digit algorithm ID (derived from `self.name`)
        and a 4-digit random sequence generated using the `ShortUUID` library.
        Returns:
            str: An 8-digit unique order identifier.
        """
        # Generate a unique 4-character key not present in self.uuids
        while True:
            ids = self.order_nos.ShortUUID().random(length=4)
            if ids not in self.uuids:
                self.uuids.add(ids)
                break
        return f"{self.name}{ids}"

    async def order_(self, order: "OrderEvent") -> None:
        """
        Handles the order event by either updating the status of an existing order
        or inserting a new order into the order diary.
        Args:
            order (OrderEvent): The order event containing order details.
        Returns:
            None
        """

        existing_order = next(
            (
                O
                for O in self.order_diary
                if O.OrderUniqueIdentifier == order.OrderUniqueIdentifier
            ),
            None,
        )

        if existing_order:
            # Update the status of the existing order
            existing_order.OrderStatus = order.OrderStatus
            existing_order.OrderPrice = order.OrderAverageTradedPriceAPI
            if existing_order.AppOrderID != order.AppOrderID:

                if self.interactiveEngine.user_logger:
                    self.interactiveEngine.user_logger.info(
                        f"Updated order {order.OrderUniqueIdentifier} App order id from {existing_order.AppOrderID} to {order.AppOrderID}",
                        caller=f"{self.__class__.__name__}.order_",
                    )
                    existing_order.AppOrderID = order.AppOrderID
            if self.interactiveEngine.user_logger:
                self.interactiveEngine.user_logger.info(
                    f"Updated order {order.OrderUniqueIdentifier} status to {order.OrderStatus}",
                    caller=f"{self.__class__.__name__}.order_",
                )
        else:
            # Insert the new order by creating an object
            new_order = Order(
                order.OrderUniqueIdentifier,
                order.AppOrderID,
                order.ProductType,
                order.OrderType,
                order.OrderQuantity,
                order.OrderDisclosedQuantity,
                order.OrderAverageTradedPrice,
                order.OrderStopPrice,
                order.OrderSideAPI,
                order.TimeInForce,
                order.OrderStatus,
            )
            self.order_diary.append(new_order)
            if self.interactiveEngine.user_logger:
                self.interactiveEngine.user_logger.info(
                    f"Inserted new order {order.OrderUniqueIdentifier} with status {order.OrderStatus}",
                    caller=f"{self.__class__.__name__}.order_",
                )
        asyncio.ensure_future(self.on_orderEvent(order))

    @abstractmethod
    async def on_orderEvent(self, message: "OrderEvent") -> None:
        """
        On Order Event for strategy.
        """
        ...

    async def trade_(self, trade: "TradeEvent") -> None:
        """
        Handles a trade event by updating the position diary and triggering the on_tradeEvent callback.
        Args:
            trade (TradeEvent): The trade event to be processed.
        Returns:
            None
        The method performs the following steps:
        1. Checks if the trade exists in the position diary.
        2. Updates the position if it exists, otherwise inserts a new position.
        3. Logs the update or insertion of the position.
        4. Ensures the on_tradeEvent callback is called asynchronously.
        """
        if trade.OrderStatus != "Filled":
            return
        # Check if the trade exists in the position diary
        existing_position = next(
            (
                _
                for _ in self.position_diary
                if _.ExchangeSegment == trade.ExchangeSegment
                and _.ExchangeInstrumentID == trade.ExchangeInstrumentID
                and _.ProductType == trade.ProductType
            ),
            None,
        )
        # Update the position
        _quantity = (1 if trade.OrderSide == "Buy" else -1) * trade.OrderQuantity
        if existing_position:
            existing_position.Quantity += _quantity
            if self.interactiveEngine.user_logger:
                self.interactiveEngine.user_logger.info(
                    f"Updated position for trade {trade.ExchangeInstrumentID}: {existing_position.Quantity}",
                    caller=f"{self.__class__.__name__}.trade_",
                )
        else:
            new_position = Position(
                trade.ExchangeSegment,
                trade.ExchangeInstrumentID,
                trade.ProductType,
                _quantity,
            )
            self.position_diary.append(new_position)
            if self.interactiveEngine.user_logger:
                self.interactiveEngine.user_logger.info(
                    f"Inserted new position {trade.ExchangeInstrumentID} with quantity {new_position.Quantity}",
                    caller=f"{self.__class__.__name__}.trade_",
                )
        asyncio.ensure_future(self.on_tradeEvent(trade))

    @abstractmethod
    def on_tradeEvent(self, message: "TradeEvent") -> None:
        """
        On trade Event for strategy.
        """
        ...

    @abstractmethod
    async def unsubscribe(self) -> None:
        """
        Abstract method (virtual function) to handle unsubscription logic.
        Must be implemented by subclasses.
        """
        ...

    @abstractmethod
    async def initialize(self) -> None:
        """
        Initialize the strategy.
        This function is intended to be a one-time asynchronous setup function for the strategy.
        It can be used to perform any necessary initialization tasks, such as scheduling jobs with APScheduler.
        """
        # Perform initialization tasks here
        ...

    @abstractmethod
    async def deinitialize(self) -> None:
        """
        Deinitialize the strategy.
        This function is intended to be a one-time asynchronous teardown function for the strategy.
        It can be used to perform any necessary cleanup tasks, such as unscheduling jobs with APScheduler.
        """
        # Perform deinitialization tasks here
        ...

    async def liquidateIntraday(self) -> None:
        """
        Asynchronously liquidates all intraday positions and cancels pending orders.
        This method iterates through the order diary and cancels any orders that are
        in the "PendingNew" or "New" status. It also iterates through the position
        diary and places market orders to liquidate any positions with a non-zero
        quantity.
        Returns:
            None
        """
        if self.interactiveEngine.user_logger:
            self.interactiveEngine.user_logger.info(
                f"Cancel open order and square off position for strategy {self.name}",
                caller=f"{self.__class__.__name__}.liquidateIntraday",
            )

        for order in self.order_diary:
            if order.OrderStatus in ["PendingNew", "New", "Replaced", "PendingReplace"]:
                asyncio.ensure_future(
                    self.interactiveEngine.cancel_order(
                        order.AppOrderID, order.OrderUniqueIdentifier
                    )
                )
        for position in self.position_diary:
            if position.Quantity != 0:
                _order_no = self.order_no()
                asyncio.ensure_future(
                    self.interactiveEngine.market_order(
                        position.ExchangeSegment,
                        position.ExchangeInstrumentID,
                        position.ProductType,
                        -1 * position.Quantity,
                        _order_no,
                    )
                )

    def isInvested(self) -> bool:
        """
        Asynchronously checks if there are any investments by summing the quantities
        of all positions in the position diary.
        Returns:
            bool: True if the total quantity is not zero, indicating that there are
            investments. False otherwise.
        """

        qty = 0
        for position in self.position_diary:
            qty += abs(position.Quantity)
        return qty != 0

    async def liquidateIntradayDummy(self) -> None:

        if self.interactiveEngine.user_logger:
            self.interactiveEngine.user_logger.info(
                f"Cancel open order and square off position for strategy {self.name}",
                caller=f"{self.__class__.__name__}.liquidateIntraday",
            )

        # for order in self.order_diary:
        #     if order.OrderStatus in ["PendingNew", "New"]:
        #         asyncio.ensure_future(
        #             self.interactiveEngine.cancel_order(
        #                 order.AppOrderID, order.OrderUniqueIdentifier
        #             )
        #         )
        for position in self.position_diary:
            if position.Quantity != 0:
                _order_no = self.order_no()
                asyncio.ensure_future(
                    self.marketDataEngine.dummy_order(
                        position.ExchangeSegment,
                        position.ExchangeInstrumentID,
                        position.ProductType,
                        -1 * position.Quantity,
                        _order_no,
                        self,
                    )
                )



    

    """async def old_safe_market_order(
        self,
        ExchangeSegment,
        ExchangeInstrumentID,
        ProductType,
        Quantity,
        InitialBid,
        InitialAsk,
    ):
        
        # Places a safe market order by continuously modifying the order until it is filled.
        # Args:
        #     ExchangeSegment (str): The segment of the exchange.
        #     ExchangeInstrumentID (int): The instrument ID of the exchange.
        #     ProductType (str): The type of the product.
        #     Quantity (int): The quantity to be ordered. Positive for buy, negative for sell.
        # Returns:
        #     None
        # Raises:
        #     Exception: If there is an issue with fetching market data or placing/modifying the order.
        # This method performs the following steps:
        # 1. Generates a unique identifier for the order.
        # 2. Fetches the latest market data for the given instrument.
        # 3. Places a limit order with a slight price adjustment.
        # 4. Continuously checks the order status until it is filled.
        # 5. If the order is not filled, modifies the order with updated market data.
    
        OrderUniqueIdentifier = self.order_no()
        _adjust = Decimal("0.05")
        Data: TouchLineData = (
            await self.marketDataEngine.fetch_ltp(
                [
                    {
                        "exchangeSegment": ExchangeSegment,
                        "exchangeInstrumentID": ExchangeInstrumentID,
                    }
                ]
            )
        )[0]
        price = (
            (Data.AskInfo.Price + _adjust).to_eng_string()
            if Quantity > 0
            else (Data.BidInfo.Price - _adjust).to_eng_string()
        )
        await self.interactiveEngine.limit_order(
            ExchangeSegment,
            ExchangeInstrumentID,
            ProductType,
            Quantity,
            price,
            OrderUniqueIdentifier,
        )
        if self.interactiveEngine.user_logger:
            self.interactiveEngine.user_logger.info(
                f"Placing Limit Order for {ExchangeInstrumentID} with Quantity {Quantity} with Price {price} and Initial Bid {InitialBid} and Initial Ask {InitialAsk}",
                caller=f"{self.__class__.__name__}.safe_market_order",
            )
        await asyncio.sleep(0.1)
        order = next(
            (
                O
                for O in self.order_diary
                if O.OrderUniqueIdentifier == OrderUniqueIdentifier
            ),
            None,
        )
        while order is None or (order is not None and order.OrderStatus != "Filled"):
            await asyncio.sleep(0.1)
            order = next(
                (
                    O
                    for O in self.order_diary
                    if O.OrderUniqueIdentifier == OrderUniqueIdentifier
                ),
                None,
            )
            if order is not None and order.OrderStatus == "Rejected":
                if self.interactiveEngine.user_logger:
                    self.interactiveEngine.user_logger.info(
                        f"Order Rejected for {ExchangeInstrumentID} with Quantity {Quantity}",
                        caller=f"{self.__class__.__name__}.safe_market_order",
                    )
                break
            if order is not None and order.OrderStatus != "Filled":
                Data: TouchLineData = (
                    await self.marketDataEngine.fetch_ltp(
                        [
                            {
                                "exchangeSegment": ExchangeSegment,
                                "exchangeInstrumentID": ExchangeInstrumentID,
                            }
                        ]
                    )
                )[0]

                await self.interactiveEngine.xt.modify_order(
                    order.AppOrderID,
                    order.ProductType,
                    order.OrderType,
                    order.OrderQuantity,
                    order.OrderDisclosedQuantity,
                    (
                        (Data.AskInfo.Price + _adjust).to_eng_string()
                        if Quantity > 0
                        else (Data.BidInfo.Price - _adjust).to_eng_string()
                    ),
                    order.OrderStopPrice.to_eng_string(),
                    order.TimeInForce,
                    order.OrderUniqueIdentifier,
                    "*****",
                )
                if self.interactiveEngine.user_logger:
                    self.interactiveEngine.user_logger.info(
                        f"Modifying Order for {ExchangeInstrumentID} with Quantity {Quantity} and Price "
                        f"{(Data.AskInfo.Price + _adjust).to_eng_string() if Quantity > 0 else (Data.BidInfo.Price - _adjust).to_eng_string()}",
                        caller=f"{self.__class__.__name__}.safe_market_order",
                    )
                await asyncio.sleep(0.7)"""

    async def safeLiquidateIntraday(self) -> None:
        """
        Asynchronously liquidates all intraday positions and cancels all open orders.
        This method performs the following actions:
        1. Logs the action of canceling open orders and squaring off positions if a user logger is available.
        2. Iterates through the order diary and cancels any orders with a status of "PendingNew" or "New".
        3. Iterates through the position diary and places market orders to square off any positions with a non-zero quantity.
        Returns:
            None
        """

        if self.interactiveEngine.user_logger:
            self.interactiveEngine.user_logger.info(
                f"Cancel open order and square off position for strategy {self.name}",
                caller=f"{self.__class__.__name__}.safeLiquidateIntraday",
            )

        for order in self.order_diary:
            if order.OrderStatus in ["PendingNew", "New"]:
                asyncio.ensure_future(
                    self.interactiveEngine.cancel_order(
                        order.AppOrderID, order.OrderUniqueIdentifier
                    )
                )
        for position in self.position_diary:
            if position.Quantity != 0:
                asyncio.ensure_future(
                    self.safe_market_order(
                        position.ExchangeSegment,
                        position.ExchangeInstrumentID,
                        position.ProductType,
                        -1 * position.Quantity,
                        0,
                        0,
                    )
                )
