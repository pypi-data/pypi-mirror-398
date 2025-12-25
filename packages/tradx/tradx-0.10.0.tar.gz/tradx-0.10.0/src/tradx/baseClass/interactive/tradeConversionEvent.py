from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime
from decimal import Decimal
import json


class TradeConversionEvent(BaseModel):
    """
    TradeConversionEvent represents an event of trade conversion with various attributes.
    Attributes:
        LoginID (str): The login ID of the user.
        ClientID (str): The client ID associated with the trade.
        UniqueKey (str): A unique key identifying the trade conversion event.
        Success (bool): Indicates whether the trade conversion was successful.
        ErrorMessage (Optional[str]): Error message if the trade conversion failed.
        OriginalProduct (str): The original product involved in the trade.
        TargetProduct (str): The target product after conversion.
        OriginalQty (int): The original quantity of the product.
        TargetQty (int): The target quantity after conversion.
        EntityType (str): The type of entity involved in the trade.
        ExchangeSegment (str): The exchange segment where the trade occurred.
        ExchangeInstrumentId (int): The ID of the exchange instrument.
        TargetEntityId (str): The ID of the target entity.
        NetValue (Decimal): The net value of the trade.
        Status (str): The status of the trade conversion.
        RejectionReason (Optional[str]): The reason for rejection if the trade was rejected.
        RejectedBy (Optional[str]): The entity that rejected the trade.
        Price (Decimal): The price at which the trade was executed.
        NOWTimeStamp (datetime): The timestamp of the trade conversion event.
        OrderSide (str): The side of the order (e.g., buy or sell).
        IsProOrder (bool): Indicates if the order is a professional order.
        MessageCode (int): The message code associated with the trade.
        MessageVersion (int): The version of the message.
        TokenID (int): The token ID associated with the trade.
        ApplicationType (int): The type of application used for the trade.
        SequenceNumber (int): The sequence number of the trade.
    Methods:
        from_string(cls, message: str): Creates an instance of TradeConversionEvent from a JSON string.
    """

    LoginID: str
    ClientID: str
    UniqueKey: str
    Success: bool
    ErrorMessage: Optional[str]
    OriginalProduct: str
    TargetProduct: str
    OriginalQty: int
    TargetQty: int
    EntityType: str
    ExchangeSegment: str
    ExchangeInstrumentId: int
    TargetEntityId: str
    NetValue: Decimal
    Status: str
    RejectionReason: Optional[str]
    RejectedBy: Optional[str]
    Price: Decimal
    NOWTimeStamp: datetime
    OrderSide: str
    IsProOrder: bool
    MessageCode: int
    MessageVersion: int
    TokenID: int
    ApplicationType: int
    SequenceNumber: int

    def __init__(self, input_data: Any):
        if isinstance(input_data, dict):
        
            super().__init__(**input_data)
        elif isinstance(input_data, str):
            
            data = json.loads(input_data)
            super().__init__(**data)
        else:
            raise ValueError("Unsupported input type for MarketStatusData")


