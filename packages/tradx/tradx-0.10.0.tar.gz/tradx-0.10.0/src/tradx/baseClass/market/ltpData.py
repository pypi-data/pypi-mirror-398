from pydantic import BaseModel, BeforeValidator
from typing_extensions import Annotated
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Any
import json
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


class LtpData(BaseModel):
    """
    LtpData model representing the Last Traded Price data.
    Attributes:
        MessageCode (int): The message code.
        MessageVersion (int): The version of the message.
        ApplicationType (int): The type of application.
        TokenID (int): The token ID.
        ExchangeSegment (int): The exchange segment.
        ExchangeInstrumentID (int): The exchange instrument ID.
        BookType (int): The type of book.
        XMarketType (ExchangeMarketType): The market type.
        LastTradedPrice (Decimal): The last traded price.
        LastTradedQunatity (int): The last traded quantity.
        LastUpdateTime (datetime): The last update time, parsed from a string.
    Methods:
        from_string(cls, message: str): Class method to create an instance of LtpData from a JSON string.
    """

    MessageCode: int
    MessageVersion: int
    ApplicationType: int
    TokenID: int
    ExchangeSegment: int
    ExchangeInstrumentID: int
    BookType: int
    XMarketType: ExchangeMarketType
    LastTradedPrice: Decimal
    LastTradedQunatity: int
    LastUpdateTime: Annotated[datetime, BeforeValidator(parse_datetime)]

    class Config:
        use_enum_values = True

    def __init__(self, input_data: Any):
        if isinstance(input_data, dict):
            super().__init__(**input_data)
        elif isinstance(input_data, str):
    
            data = json.loads(input_data)
            super().__init__(**data)
        else:
            raise ValueError("Unsupported input type for LtpData")