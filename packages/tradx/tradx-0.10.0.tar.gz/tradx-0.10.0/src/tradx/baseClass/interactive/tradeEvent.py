from pydantic import BaseModel, BeforeValidator
from typing_extensions import Annotated
from typing import Optional, Any, Dict
from datetime import datetime
from decimal import Decimal
import json


def parse_decimal(value) -> Any:
    """
    Converts a string representation of a decimal number to a Decimal object,
    removing any commas. If the input is not a string, it returns the input as is.
    Args:
        value (str or any): The value to be converted to a Decimal. If the value
                            is a string, it will remove any commas before conversion.
    Returns:
        Decimal or any: The Decimal representation of the input string, or the
                        original input if it is not a string.
    """

    if isinstance(value, str):
        value = value.replace(",", "")
        return Decimal(value)
    return value


def parse_datetime(value) -> Any:
    """
    Parses a datetime string into a datetime object.
    Args:
        value (Any): The value to be parsed. If the value is a string, it should be in the format "%d-%m-%Y %H:%M:%S".
    Returns:
        Any: A datetime object if the input is a string in the correct format, otherwise returns the input value unchanged.
    """

    if isinstance(value, str):
        return datetime.strptime(value, "%d-%m-%Y %H:%M:%S")
    return value


class TradeEvent(BaseModel):
    """
    TradeEvent model representing a trade event with various attributes.
    Attributes:
        LoginID (str): The login ID of the user.
        ClientID (str): The client ID, default is "*****".
        AppOrderID (int): The application order ID.
        OrderReferenceID (Optional[str]): The order reference ID.
        GeneratedBy (str): The entity that generated the order.
        ExchangeOrderID (str): The exchange order ID.
        OrderCategoryType (str): The category type of the order.
        ExchangeSegment (str): The exchange segment.
        ExchangeInstrumentID (int): The exchange instrument ID.
        OrderSide (str): The side of the order (buy/sell).
        OrderType (str): The type of the order.
        ProductType (str): The product type.
        TimeInForce (str): The time in force for the order.
        OrderPrice (Decimal): The price of the order.
        OrderQuantity (int): The quantity of the order.
        OrderStopPrice (Decimal): The stop price of the order.
        OrderStatus (str): The status of the order.
        OrderAverageTradedPrice (Decimal): The average traded price of the order.
        LeavesQuantity (int): The remaining quantity of the order.
        CumulativeQuantity (int): The cumulative quantity of the order.
        OrderDisclosedQuantity (int): The disclosed quantity of the order.
        OrderGeneratedDateTime (datetime): The date and time the order was generated.
        ExchangeTransactTime (datetime): The transaction time on the exchange.
        LastUpdateDateTime (datetime): The last update date and time.
        CancelRejectReason (Optional[str]): The reason for order cancellation or rejection.
        OrderUniqueIdentifier (str): The unique identifier for the order.
        OrderLegStatus (str): The status of the order leg.
        LastTradedPrice (Decimal): The last traded price.
        LastTradedQuantity (int): The last traded quantity.
        LastExecutionTransactTime (datetime): The last execution transaction time.
        ExecutionID (str): The execution ID.
        ExecutionReportIndex (int): The execution report index.
        IsSpread (bool): Indicates if the order is a spread.
        OrderAverageTradedPriceAPI (Decimal): The average traded price from the API.
        OrderSideAPI (str): The order side from the API.
        OrderGeneratedDateTimeAPI (datetime): The order generated date and time from the API.
        ExchangeTransactTimeAPI (datetime): The exchange transaction time from the API.
        LastUpdateDateTimeAPI (datetime): The last update date and time from the API.
        OrderExpiryDateAPI (datetime): The order expiry date from the API.
        LastExecutionTransactTimeAPI (datetime): The last execution transaction time from the API.
        MessageSynchronizeUniqueKey (str): The unique key for message synchronization.
        MessageCode (int): The message code.
        MessageVersion (int): The message version.
        TokenID (int): The token ID.
        ApplicationType (int): The application type.
        SequenceNumber (int): The sequence number.
        TradingSymbol (str): The trading symbol.
    Methods:
        from_string(cls, message: str): Creates an instance of TradeEvent from a JSON string.
    """

    LoginID: str
    ClientID: str = "*****"
    AppOrderID: int
    OrderReferenceID: Optional[str]
    GeneratedBy: str
    ExchangeOrderID: str
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
    CancelRejectReason: Optional[str]
    OrderUniqueIdentifier: str
    OrderLegStatus: str
    LastTradedPrice: Decimal
    LastTradedQuantity: int
    LastExecutionTransactTime: datetime
    ExecutionID: str
    ExecutionReportIndex: int
    IsSpread: bool
    OrderAverageTradedPriceAPI: Decimal
    OrderSideAPI: str
    OrderGeneratedDateTimeAPI: Annotated[datetime, BeforeValidator(parse_datetime)]
    ExchangeTransactTimeAPI: Annotated[datetime, BeforeValidator(parse_datetime)]
    LastUpdateDateTimeAPI: Annotated[datetime, BeforeValidator(parse_datetime)]
    OrderExpiryDateAPI: Annotated[datetime, BeforeValidator(parse_datetime)]
    LastExecutionTransactTimeAPI: Annotated[datetime, BeforeValidator(parse_datetime)]
    MessageSynchronizeUniqueKey: str
    MessageCode: int
    MessageVersion: int
    TokenID: int
    ApplicationType: int
    SequenceNumber: int
    TradingSymbol: str

    def __init__(self, input_data: Any):
        if isinstance(input_data, dict):

            super().__init__(**input_data)
        elif isinstance(input_data, str):

            data = json.loads(input_data)
            super().__init__(**data)
        else:
            raise ValueError("Unsupported input type for MarketStatusData")
