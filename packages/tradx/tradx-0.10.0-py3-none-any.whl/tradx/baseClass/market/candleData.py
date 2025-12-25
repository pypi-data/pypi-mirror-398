from pydantic import BaseModel
from decimal import Decimal
from datetime import datetime, timezone
import json
from typing import Any


class CandleData(BaseModel):
    """
    CandleData model representing candlestick data for trading.

    Attributes:
        MessageCode (int): The message code.
        MessageVersion (int): The version of the message.
        ApplicationType (int): The type of application.
        TokenID (int): The token ID.
        ExchangeSegment (int): The exchange segment.
        BarTime (datetime): The time of the bar.
        BarVolume (Decimal): The volume of the bar.
        OpenInterest (Decimal): The open interest.
        SumOfQtyInToPrice (Decimal): The sum of quantity into price.
        ExchangeInstrumentID (int): The exchange instrument ID.
        Open (Decimal): The opening price.
        High (Decimal): The highest price.
        Low (Decimal): The lowest price.
        Close (Decimal): The closing price.
    Methods:
        from_string(cls, message: str):
            Creates an instance of CandleData from a JSON string.
        __getitem__(self, item):
            Allows access to specific attributes using dictionary-like indexing.
        __str__(self):
            Returns a JSON string representation of the instance with selected attributes.
    """

    MessageCode: int
    MessageVersion: int
    ApplicationType: int
    TokenID: int
    ExchangeSegment: int
    BarTime: int
    BarVolume: Decimal
    OpenInterest: Decimal
    SumOfQtyInToPrice: Decimal
    ExchangeInstrumentID: int
    BarTime: datetime
    Open: Decimal
    High: Decimal
    Low: Decimal
    Close: Decimal

    def __init__(self, input_data: Any):
        if isinstance(input_data, dict):
            input_data["BarTime"] = datetime.fromtimestamp(
                input_data["BarTime"], timezone.utc
            )
            super().__init__(**input_data)
        elif isinstance(input_data, str):
            data = json.loads(input_data)
            data["BarTime"] = datetime.fromtimestamp(data["BarTime"], timezone.utc)
            super().__init__(**data)
        else:
            raise ValueError("Unsupported input type for CandleData")

    def __getitem__(self, item):
        allowed_keys = {
            "High",
            "Low",
            "Open",
            "Close",
            "ExchangeInstrumentID",
            "BarTime",
            "Volume",
        }
        if item in allowed_keys:
            return getattr(self, item)

    def __str__(self):
        allowed_keys = {
            "High",
            "Low",
            "Open",
            "Close",
            "ExchangeInstrumentID",
            "BarTime",
            "BarVolume",
        }
        filtered_data = {key: getattr(self, key) for key in allowed_keys}
        return json.dumps(filtered_data, default=str, indent=4)
