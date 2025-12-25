from pydantic import BaseModel

class Index(BaseModel):
    """
    A class used to represent an Index.
    Attributes
    ----------
    Name : str
        The name of the index.
    ExchangeSegment : int
        The segment of the exchange.
    ExchangeInstrumentID : int
        The instrument ID of the exchange.
    Methods
    -------
    __init__(self, Name: str, ExchangeSegment: int, ExchangeInstrumentID: int)
        Constructs all the necessary attributes for the Index object.
    """

    Name: str
    ExchangeSegment: int
    ExchangeInstrumentID: int
    def __init__(self, Name: str, ExchangeSegment: int, ExchangeInstrumentID: int):
        super().__init__(Name=Name, ExchangeSegment=ExchangeSegment, ExchangeInstrumentID=ExchangeInstrumentID)