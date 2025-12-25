from pydantic import BaseModel, BeforeValidator, Field
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
    BidAskInfo is a data model that represents bid and ask information in a trading system.
    Attributes:
        Size (int): The size of the bid or ask.
        Price (Decimal): The price of the bid or ask.
        TotalOrders (int): The total number of orders at this bid or ask price.
        BuyBackMarketMaker (int): Indicator of whether the market maker is buying back.
    """

    Size: int
    Price: Decimal
    TotalOrders: int
    BuyBackMarketMaker: int


class TouchLineData(BaseModel):
    """
    TouchLineData class represents the structure of touch line data for trading instruments.
    Attributes:
        MessageCode (int): The message code.
        MessageVersion (int): The version of the message. Default is -1 (value is not provided).
        ApplicationType (int): The type of application. Default is -1 (value is not provided).
        TokenID (int): The token ID. Default is -1 (value is not provided).
        ExchangeSegment (int): The exchange segment.
        ExchangeInstrumentID (int): The exchange instrument ID.
        ExchangeTimeStamp (datetime): The exchange timestamp.
        LastTradedPrice (Decimal): The last traded price.
        LastTradedQunatity (int): The last traded quantity.
        TotalBuyQuantity (int): The total buy quantity.
        TotalSellQuantity (int): The total sell quantity.
        TotalTradedQuantity (int): The total traded quantity.
        AverageTradedPrice (Decimal): The average traded price.
        LastTradedTime (datetime): The last traded time.
        LastUpdateTime (datetime): The last update time.
        PercentChange (Decimal): The percent change.
        Open (Decimal): The open price.
        High (Decimal): The high price.
        Low (Decimal): The low price.
        Close (Decimal): The close price.
        TotalValueTraded (int): The total value traded. Default is 0.
        BidInfo (BidAskInfo): The bid information.
        AskInfo (BidAskInfo): The ask information.
        BuyBackTotalBuy (int): The total buy back. Default is -1 (value is not provided).
        BuyBackTotalSell (int): The total sell back. Default is -1 (value is not provided).
        BookType (int): The book type.
        XMarketType (int): The market type.
        SequenceNumber (int): The sequence number. Default is -1 (value is not provided).
    Methods:
        from_string(cls, message: str): Creates an instance of TouchLineData from a JSON string.
    Example usage:
        TouchLineData can be instantiated with two types of arguments:
        1. {
            "MessageCode": 1501,
            "ExchangeSegment": 1,
            "ExchangeInstrumentID": 467,
            "LastTradedPrice": 610.3,
            "LastTradedQunatity": 1,
            "TotalBuyQuantity": 363004,
            "TotalSellQuantity": 327007,
            "TotalTradedQuantity": 1983015,
            "AverageTradedPrice": 612.81,
            "LastTradedTime": 1420632949,
            "LastUpdateTime": 1420632949,
            "PercentChange": -2.038523274478332,
            "Open": 627,
            "High": 627,
            "Low": 605.15,
            "Close": 623,
            "TotalValueTraded": null,
            "AskInfo": {
                "Size": 15,
                "Price": 610.3,
                "TotalOrders": 1,
                "BuyBackMarketMaker": 0
            },
            "BidInfo": {
                "Size": 119,
                "Price": 610.15,
                "TotalOrders": 3,
                "BuyBackMarketMaker": 0
            },
            "XMarketType": 1,
            "BookType": 1
        }
        2. {
            "MessageCode": 1501,
            "MessageVersion": 4,
            "ApplicationType": 0,
            "TokenID": 0,
            "ExchangeSegment": 1,
            "ExchangeInstrumentID": 26000,
            "ExchangeTimeStamp": 1421315385,
            "Touchline": {
                "BidInfo": {
                    "Size": 0,
                    "Price": 0,
                    "TotalOrders": 0,
                    "BuyBackMarketMaker": 0
                },
                "AskInfo": {
                    "Size": 0,
                    "Price": 0,
                    "TotalOrders": 0,
                    "BuyBackMarketMaker": 0
                },
                "LastTradedPrice": 23202.15,
                "LastTradedQunatity": 0,
                "TotalBuyQuantity": 0,
                "TotalSellQuantity": 0,
                "TotalTradedQuantity": 0,
                "AverageTradedPrice": 23202.15,
                "LastTradedTime": 1421315385,
                "LastUpdateTime": 1421315385,
                "PercentChange": 0.5,
                "Open": 23165.9,
                "High": 23227.2,
                "Low": 23150.05,
                "Close": 23085.95,
                "TotalValueTraded": null,
                "BuyBackTotalBuy": 0,
                "BuyBackTotalSell": 0
            },
            "BookType": 1,
            "XMarketType": 1,
            "SequenceNumber": 1590018768596832
        }
    """

    MessageCode: int
    MessageVersion: int = Field(default=-1)
    ApplicationType: int = Field(default=-1)
    TokenID: int = Field(default=-1)
    ExchangeSegment: int
    ExchangeInstrumentID: int
    ExchangeTimeStamp: Annotated[
        datetime, Field(default=datetime(1980, 1, 1)), BeforeValidator(parse_datetime)
    ]
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
    TotalValueTraded: Annotated[
        int, BeforeValidator(lambda x: x if x is not None else 0)
    ]
    BidInfo: BidAskInfo
    AskInfo: BidAskInfo
    BuyBackTotalBuy: int = Field(default=-1)
    BuyBackTotalSell: int = Field(default=-1)
    BookType: int
    XMarketType: int
    SequenceNumber: int = Field(default=-1)

    def __init__(self, input_data: Any):
        if isinstance(input_data, dict):
       
            super().__init__(**input_data)
        elif isinstance(input_data, str):
      
            data = json.loads(input_data)
            if "Touchline" in data:
                touchline_data = data.pop("Touchline")
                super().__init__(**data, **touchline_data)
            else:
                super().__init__(**data)
        else:
            raise ValueError("Unsupported input type for TouchLineData")
