from pydantic import BaseModel
from decimal import Decimal
import json


class Order(BaseModel):
    """
    Order class representing an order in the system.
    Attributes:
        OrderUniqueIdentifier (str): A unique identifier for the order.
        AppOrderID (int): The application-specific order ID.
        OrderStatus (str): The status of the order. Defaults to an empty string.
    Methods:
        __init__(OrderUniqueIdentifier: str, AppOrderID: int, OrderStatus: str = ""):
            Initializes a new instance of the Order class.
    """

    OrderUniqueIdentifier: str
    AppOrderID: int
    OrderStatus: str
    ProductType: str
    OrderType: str
    OrderQuantity: int
    OrderDisclosedQuantity: int
    OrderPrice: Decimal
    OrderStopPrice: Decimal
    TimeInForce: str
    OrderSide: str

    def __init__(
        self,
        OrderUniqueIdentifier: str,
        AppOrderID: int,
        ProductType: str,
        OrderType: str,
        OrderQuantity: int,
        OrderDisclosedQuantity: int,
        OrderPrice: Decimal,
        OrderStopPrice: Decimal,
        OrderSide: str,
        TimeInForce: str,
        OrderStatus: str = "",
    ):
        super().__init__(
            OrderUniqueIdentifier=OrderUniqueIdentifier,
            AppOrderID=AppOrderID,
            ProductType=ProductType,
            OrderType=OrderType,
            OrderQuantity=OrderQuantity,
            OrderDisclosedQuantity=OrderDisclosedQuantity,
            OrderPrice=OrderPrice,
            OrderStopPrice=OrderStopPrice,
            OrderStatus=OrderStatus,
            OrderSide=OrderSide,
            TimeInForce=TimeInForce,
        )

    @classmethod
    def from_str(cls, message: str):
        data = json.loads(message)
        return cls(**data)
