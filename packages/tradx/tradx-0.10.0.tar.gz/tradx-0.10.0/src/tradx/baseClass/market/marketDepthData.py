from pydantic import BaseModel, BeforeValidator
from typing_extensions import Annotated
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Any
import json


def parse_datetime(value) -> Any:
    """
    Parses the given value into a datetime object if it is an integer.
    If the value is an integer, it is interpreted as the number of seconds since January 1, 1980.
    The function returns a datetime object representing that date and time.
    If the value is not an integer, it is returned as-is.
    Args:
        value (Any): The value to be parsed. Expected to be an integer representing seconds since January 1, 1980, or any other type.
    Returns:
        Any: A datetime object if the input is an integer, otherwise the input value unchanged.
    """

    if isinstance(value, int):
        return datetime(1980, 1, 1) + timedelta(seconds=value)
    return value


class BidAskInfo(BaseModel):
    """
    BidAskInfo is a data model representing the bid and ask information in a market depth context.
    Attributes:
        Size (int): The size of the bid or ask.
        Price (Decimal): The price of the bid or ask.
        TotalOrders (int): The total number of orders at this bid or ask price.
        BuyBackMarketMaker (int): Indicator if the market maker is buying back.
    """

    Size: int
    Price: Decimal
    TotalOrders: int
    BuyBackMarketMaker: int


class TouchlineInfo(BaseModel):
    """
    TouchlineInfo represents the market depth data for a trading instrument.
    Attributes:
        BidInfo (BidAskInfo): Information about the bid.
        AskInfo (BidAskInfo): Information about the ask.
        LastTradedPrice (Decimal): The last traded price of the instrument.
        LastTradedQunatity (int): The quantity of the last trade.
        TotalBuyQuantity (int): The total quantity of buy orders.
        TotalSellQuantity (int): The total quantity of sell orders.
        TotalTradedQuantity (int): The total quantity of traded orders.
        AverageTradedPrice (Decimal): The average price of traded orders.
        LastTradedTime (datetime): The time of the last trade.
        LastUpdateTime (datetime): The time of the last update.
        PercentChange (Decimal): The percentage change in price.
        Open (Decimal): The opening price.
        High (Decimal): The highest price.
        Low (Decimal): The lowest price.
        Close (Decimal): The closing price.
        TotalValueTraded (int): The total value of traded orders.
        BuyBackTotalBuy (int): The total quantity of buy-back orders.
        BuyBackTotalSell (int): The total quantity of sell-back orders.
    """

    BidInfo: BidAskInfo
    AskInfo: BidAskInfo
    LastTradedPrice: Decimal
    LastTradedQunatity: int
    TotalBuyQuantity: int
    TotalSellQuantity: int
    TotalTradedQuantity: int
    AverageTradedPrice: Decimal
    LastTradedTime: Annotated[datetime, BeforeValidator(parse_datetime)]
    LastUpdateTime: Annotated[datetime, BeforeValidator(parse_datetime)]
    PercentChange: Decimal
    Open: Decimal
    High: Decimal
    Low: Decimal
    Close: Decimal
    TotalValueTraded: int
    BuyBackTotalBuy: int
    BuyBackTotalSell: int


class MarketDepthData(BaseModel):
    """
    MarketDepthData represents the market depth information for a specific instrument.
    Attributes:
        MessageCode (int): The code representing the type of message.
        MessageVersion (int): The version of the message format.
        ApplicationType (int): The type of application sending the message.
        TokenID (int): The unique identifier for the token.
        ExchangeSegment (int): The segment of the exchange.
        ExchangeInstrumentID (int): The unique identifier for the instrument on the exchange.
        ExchangeTimeStamp (datetime): The timestamp of the data from the exchange.
        Bids (list[BidAskInfo]): A list of bid information.
        Asks (list[BidAskInfo]): A list of ask information.
        Touchline (TouchlineInfo): The touchline information.
        BookType (int): The type of order book.
        XMarketType (int): The type of market.
        SequenceNumber (int): The sequence number of the message.
    """

    MessageCode: int
    MessageVersion: int
    ApplicationType: int
    TokenID: int
    ExchangeSegment: int
    ExchangeInstrumentID: int
    ExchangeTimeStamp: Annotated[datetime, BeforeValidator(parse_datetime)]
    Bids: list[BidAskInfo]
    Asks: list[BidAskInfo]
    Touchline: TouchlineInfo
    BookType: int
    XMarketType: int
    SequenceNumber: int

    def __init__(self, input_data: Any):
        if isinstance(input_data, dict):
            super().__init__(**input_data)
        elif isinstance(input_data, str):
            data = json.loads(input_data)
            super().__init__(**data)
        else:
            raise ValueError("Unsupported input type for MarketDepthData")
