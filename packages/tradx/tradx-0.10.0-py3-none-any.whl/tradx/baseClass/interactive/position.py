from pydantic import BaseModel
import json


class Position(BaseModel):
    """
    A class to represent a financial position.
    Attributes:
    -----------
    ExchangeSegment : str
        The segment of the exchange where the instrument is traded.
    ExchangeInstrumentID : int
        The unique identifier of the instrument on the exchange.
    ProductType : str
        The type of the financial product.
    Quantity : int
        The quantity of the financial instrument. Default is 0.
    Methods:
    --------
    __init__(self, ExchangeSegment: str, ExchangeInstrumentID: int, ProductType: str, Quantity: int = 0):
        Constructs all the necessary attributes for the Position object.
    """

    ExchangeInstrumentID: int
    ExchangeSegment: str

    ProductType: str
    Quantity: int

    def __init__(
        self,
        ExchangeSegment: str,
        ExchangeInstrumentID: int,
        ProductType: str,
        Quantity: int = 0,
    ):
        assert isinstance(ExchangeSegment, str), "ExchangeSegment must be a string"
        assert isinstance(
            ExchangeInstrumentID, int
        ), "ExchangeInstrumentID must be an integer"
        assert isinstance(ProductType, str), "ProductType must be a string"
        assert isinstance(Quantity, int), "Quantity must be an integer"
        super().__init__(
            ExchangeSegment=ExchangeSegment,
            ExchangeInstrumentID=ExchangeInstrumentID,
            ProductType=ProductType,
            Quantity=Quantity,
        )

    @classmethod
    def from_str(cls, message: str):
        data = json.loads(message)
        return cls(**data)
