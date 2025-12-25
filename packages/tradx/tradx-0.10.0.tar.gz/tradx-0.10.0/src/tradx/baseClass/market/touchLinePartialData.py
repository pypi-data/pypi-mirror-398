from pydantic import BaseModel, BeforeValidator
from typing_extensions import Annotated
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Any


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


class BidAskInfo(BaseModel):
    """
    BidAskInfo is a data model that represents bid and ask information in a trading system.
    Attributes:
        Size (int): The size of the bid or ask.
        Price (Decimal): The price of the bid or ask.
        TotalOrders (int): The total number of orders at this bid or ask price.
        BuyBackMarketMaker (int): Indicator of whether the market maker is buying back.
    """

    Size: int
    Price: Decimal
    TotalOrders: int
    BuyBackMarketMaker: int


class TouchLinePartialData(BaseModel):

    ExchangeSegment: int
    ExchangeInstrumentID: int
    LastTradedPrice: Decimal
    LastTradedQunatity: int
    TotalBuyQuantity: int
    TotalSellQuantity: int
    Volume: int
    AverageTradedPrice: Decimal
    LastTradedTime: Annotated[datetime, BeforeValidator(parse_datetime)]
    LastUpdateTime: Annotated[datetime, BeforeValidator(parse_datetime)]
    PercentChange: Decimal
    Open: Decimal
    High: Decimal
    Low: Decimal
    Close: Decimal
    TotalPriceVolume: int
    BidInfo: BidAskInfo
    AskInfo: BidAskInfo

    def __init__(self, data: str):
        data = "".join(data.split())
        fields = dict(item.split(":") for item in data.split(","))
        data_dict = {}
        data_dict["ExchangeSegment"], data_dict["ExchangeInstrumentID"] = fields[
            "t"
        ].split("_")
        data_dict["LastTradedPrice"] = Decimal(fields["ltp"])
        data_dict["LastTradedQunatity"] = fields["ltq"]
        data_dict["TotalBuyQuantity"] = fields["tb"]
        data_dict["TotalSellQuantity"] = fields["ts"]
        data_dict["Volume"] = fields["v"]
        data_dict["AverageTradedPrice"] = Decimal(fields["ap"])
        data_dict["LastTradedTime"] = fields["ltt"]
        data_dict["LastUpdateTime"] = fields["lut"]
        data_dict["PercentChange"] = Decimal(fields["pc"])
        data_dict["Open"] = Decimal(fields["o"])
        data_dict["High"] = Decimal(fields["h"])
        data_dict["Low"] = Decimal(fields["l"])
        data_dict["Close"] = Decimal(fields["c"])
        data_dict["TotalPriceVolume"] = fields["vp"]
        bid_info_fields = fields["bi"].split("|")
        ask_info_fields = fields["ai"].split("|")
        data_dict["BidInfo"] = BidAskInfo(
            Size=int(bid_info_fields[0]),
            Price=Decimal(bid_info_fields[1]),
            TotalOrders=int(bid_info_fields[2]),
            BuyBackMarketMaker=int(bid_info_fields[3]),
        )
        data_dict["AskInfo"] = BidAskInfo(
            Size=int(ask_info_fields[0]),
            Price=Decimal(ask_info_fields[1]),
            TotalOrders=int(ask_info_fields[2]),
            BuyBackMarketMaker=int(ask_info_fields[3]),
        )
        super().__init__(**data_dict)


a = """
 t:1_22,ltp:1567.95,ltq:20,tb:1428,ts:0,v:253453,ap:1576.2,ltt:1205682110,
 lut:1205682251,pc:0,o:1599.9,h:1607.25,l:1552.7,c:1567.95,vp:177838490,
 ai:0|1428|1567.95|10,bi:0|0|0|0|1 
"""
c = TouchLinePartialData.from_string(a)
print(c)

# Incomplete information, waiting for response from the user
