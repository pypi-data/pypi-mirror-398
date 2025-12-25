from pydantic import BaseModel, BeforeValidator
from typing_extensions import Annotated
from datetime import datetime, timedelta
import json
from typing import Any
from enum import Enum


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


class ExchangeTradingSession(Enum):
    """
    Enum class representing different stages of an exchange trading session.
    Attributes:
        PreOpenStart (int): Represents the start of the pre-open session.
        PreOpenEnd (int): Represents the end of the pre-open session.
        NormalStart (int): Represents the start of the normal trading session.
        NormalEnd (int): Represents the end of the normal trading session.
        PreClosingStart (int): Represents the start of the pre-closing session.
        PreClosingEnd (int): Represents the end of the pre-closing session.
    """

    PreOpenStart = 0
    PreOpenEnd = 1
    NormalStart = 2
    NormalEnd = 4
    PreClosingStart = 8
    PreClosingEnd = 16


class ExchangeMarketType(Enum):
    """
    Enum class representing different types of exchange market statuses.
    Attributes:
        Normal (int): Represents a normal market type.
        OddLot (int): Represents an odd lot market type.
        Spot (int): Represents a spot market type.
        Auction (int): Represents an auction market type.
        CallAuction1 (int): Represents the first call auction market type.
        CallAuction2 (int): Represents the second call auction market type.
    """

    Normal = 1
    OddLot = 2
    Spot = 3
    Auction = 4
    CallAuction1 = 5
    CallAuction2 = 6


class MarketStatusData(BaseModel):
    """
    MarketStatusData is a data model representing the status of a market.
    Attributes:
        ApplicationType (int): The type of application.
        ExchangeInstrumentID (int): The ID of the exchange instrument.
        ExchangeSegment (int): The segment of the exchange.
        ExchangeTimeStamp (datetime): The timestamp of the exchange, validated and parsed.
        maketType (ExchangeMarketType): The type of market.
        message (str): The message content.
        MessageCode (int): The code of the message.
        MessageVersion (int): The version of the message.
        SequenceNumber (int): The sequence number.
        TokenID (int): The token ID.
        tradingSession (ExchangeTradingSession): The trading session.
    Methods:
        from_string(cls, message: str): Class method to create an instance of MarketStatusData from a JSON string.
    """

    ApplicationType: int
    ExchangeInstrumentID: int
    ExchangeSegment: int
    ExchangeTimeStamp: Annotated[datetime, BeforeValidator(parse_datetime)]
    maketType: ExchangeMarketType
    message: str
    MessageCode: int
    MessageVersion: int
    SequenceNumber: int
    TokenID: int
    tradingSession: ExchangeTradingSession

    class Config:
        use_enum_values = True

    def __init__(self, input_data: Any):
        if isinstance(input_data, dict):

            super().__init__(**input_data)
        elif isinstance(input_data, str):

            data = json.loads(input_data)
            super().__init__(**data)
        else:
            raise ValueError("Unsupported input type for MarketStatusData")
