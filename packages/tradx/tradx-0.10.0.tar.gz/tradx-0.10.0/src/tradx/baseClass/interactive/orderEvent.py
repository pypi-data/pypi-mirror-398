from pydantic import BaseModel, BeforeValidator
from typing_extensions import Annotated
from typing import Optional, Any
from datetime import datetime, timedelta
from decimal import Decimal
import json

def parse_decimal(value) -> Any:
    """
    Parses the given value and returns a decimal representation.
    If the value is a string, it returns 0.0. Otherwise, it returns the value as is.
    Args:
        value: The value to be parsed. It can be of any type.
    Returns:
        Any: The parsed decimal value or the original value.
    """

    if isinstance(value, str):
        return 0.0
    return value
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
class OrderEvent(BaseModel):
    

    LoginID: str
    ClientID: str = "*****"
    AppOrderID: int
    OrderReferenceID: Optional[str]
    GeneratedBy: str
    ExchangeOrderID: Optional[str]
    OrderCategoryType: str
    ExchangeSegment: str
    ExchangeInstrumentID: int
    OrderSide: str
    OrderType: str
    ProductType: str
    TimeInForce: str
    OrderPrice: Decimal
    OrderQuantity: int
    OrderStopPrice: Decimal
    OrderStatus: str
    OrderAverageTradedPrice: Annotated[Decimal, BeforeValidator(parse_decimal)]
    LeavesQuantity: int
    CumulativeQuantity: int
    OrderDisclosedQuantity: int
    OrderGeneratedDateTime: datetime
    ExchangeTransactTime: datetime
    LastUpdateDateTime: datetime
    OrderExpiryDate: datetime
    CancelRejectReason: Optional[str]
    OrderUniqueIdentifier: str
    OrderLegStatus: str
    IsSpread: bool
    BoLegDetails: int
    BoEntryOrderId: Optional[str]
    OrderAverageTradedPriceAPI: Annotated[Decimal, BeforeValidator(parse_decimal)]
    OrderSideAPI: str
    OrderGeneratedDateTimeAPI: str
    ExchangeTransactTimeAPI: str
    LastUpdateDateTimeAPI: str
    OrderExpiryDateAPI: str
    AlgoID: Optional[str]
    AlgoCategory: int
    MessageSynchronizeUniqueKey: str
    MessageCode: int
    MessageVersion: int
    TokenID: int
    ApplicationType: int
    SequenceNumber: int
    TradingSymbol: str

    def __init__(self, message: str):
        data = json.loads(message)
        super().__init__(**data)


