from pydantic import BaseModel
from typing import Any


class OpenInterestPartialData(BaseModel):
    """
    A class to represent partial data of open interest.
    Attributes:
    -----------
    ExchangeSegment : int
        The segment of the exchange.
    ExchangeInstrumentID : int
        The instrument ID of the exchange.
    OpenInterest : int
        The open interest value.
    Methods:
    --------
    from_string(cls, message: str):
        Parses a string message to create an instance of OpenInterestPartialData.
        The message should be in the format "t:exchange_segment_instrument_id,o:open_interest".
    """

    ExchangeSegment: int
    ExchangeInstrumentID: int
    OpenInterest: int

    def __init__(self, input_data: Any):
        if isinstance(input_data, dict):
            super().__init__(**input_data)
        elif isinstance(input_data, str):
            parts = input_data.split(",")
            data = {}
            for part in parts:
                key, value = part.split(":")
                if key == "t":
                    exchange_segment, instrument_id = value.split("_")
                    data["ExchangeSegment"] = int(exchange_segment)
                    data["ExchangeInstrumentID"] = int(instrument_id)
                elif key == "o":
                    data["OpenInterest"] = int(value)
            super().__init__(**data)
        else:
            raise ValueError("Unsupported input type for OpenInterestPartialData")
