from pydantic import BaseModel, BeforeValidator
from typing_extensions import Annotated
from decimal import Decimal
from datetime import datetime, timedelta
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


class LtpPartialData(BaseModel):
    """
    LtpPartialData is a model representing partial data for the last traded price (LTP) of an instrument.
    Attributes:
        ExchangeSegment (int): The exchange segment identifier.
        ExchangeInstrumentID (int): The exchange instrument identifier.
        BookType (int): The book type identifier.
        MarketType (ExchangeMarketType): The market type.
        LastTradedPrice (Decimal): The last traded price of the instrument.
        LastTradedQunatity (int): The last traded quantity of the instrument.
        LastUpdateTime (datetime): The last update time of the data.
    Methods:
        from_string(cls, message: str): Parses a string message to create an instance of LtpPartialData.
            Args:
                message (str): The input string containing key-value pairs separated by commas.
            Returns:
                LtpPartialData: An instance of LtpPartialData populated with the parsed data.
    """

    ExchangeSegment: int
    ExchangeInstrumentID: int
    BookType: int
    MarketType: ExchangeMarketType
    LastTradedPrice: Decimal
    LastTradedQunatity: int
    LastUpdateTime: Annotated[datetime, BeforeValidator(parse_datetime)]

    class Config:
        use_enum_values = True

    def __init__(self, input_data: Any):
        if isinstance(input_data, dict):
  
            super().__init__(**input_data)
        elif isinstance(input_data, str):
        
            # Split the message by commas to get individual key-value pairs
            key_value_pairs = input_data.split(",")

            # Initialize an empty dictionary to store the parsed data
            data = {}

            # Iterate over each key-value pair
            for pair in key_value_pairs:
                key, value = pair.split(":")
                if key == "t":
                    exchange_segment, instrument_id = map(int, value.split("_"))
                    data["ExchangeSegment"] = exchange_segment
                    data["ExchangeInstrumentID"] = instrument_id
                elif key == "ltp":
                    data["LastTradedPrice"] = Decimal(value)
                elif key == "ltq":
                    data["LastTradedQunatity"] = int(value)
                elif key == "lut":
                    data["LastUpdateTime"] = int(value)
                elif key == "bt":
                    data["BookType"] = int(value)
                elif key == "mt":
                    data["MarketType"] = int(value)
            super().__init__(**data)
        else:
            raise ValueError("Unsupported input type for LtpPartialData")
