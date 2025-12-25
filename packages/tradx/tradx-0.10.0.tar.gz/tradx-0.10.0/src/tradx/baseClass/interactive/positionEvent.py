from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from decimal import Decimal
import json


class PositionEvent(BaseModel):
    """
    PositionEvent class represents a trading position event with various attributes related to trading positions.
    Attributes:
        LoginID (str): The login ID of the user.
        AccountID (str): The account ID associated with the position.
        TradingSymbol (str): The trading symbol of the instrument.
        ExchangeSegment (str): The exchange segment where the instrument is traded.
        ExchangeInstrumentID (int): The unique identifier for the instrument on the exchange.
        ProductType (str): The type of product being traded.
        Multiplier (Decimal): The multiplier for the instrument.
        Marketlot (int): The market lot size of the instrument.
        BuyAveragePrice (Decimal): The average price at which the instrument was bought.
        SellAveragePrice (Decimal): The average price at which the instrument was sold.
        LongPosition (int): The quantity of long positions.
        ShortPosition (int): The quantity of short positions.
        NetPosition (int): The net position (long - short).
        BuyValue (Decimal): The total value of bought positions.
        SellValue (Decimal): The total value of sold positions.
        NetValue (Decimal): The net value (buy - sell).
        UnrealizedMTM (Decimal): The unrealized mark-to-market value.
        RealizedMTM (Decimal): The realized mark-to-market value.
        MTM (Decimal): The total mark-to-market value.
        BEP (Decimal): The break-even price.
        SumOfTradedQuantityAndPriceBuy (Decimal): The sum of traded quantity and price for buy transactions.
        SumOfTradedQuantityAndPriceSell (Decimal): The sum of traded quantity and price for sell transactions.
        IsDayWiseNetWise (str): Indicator if the position is day-wise or net-wise.
        StatisticsLevel (str): The level of statistics.
        IsInterOpPosition (bool): Indicator if the position is interoperable.
        childPositions (dict): Dictionary of child positions.
        MessageCode (int): The message code.
        MessageVersion (int): The version of the message.
        TokenID (int): The token ID.
        ApplicationType (int): The type of application.
        SequenceNumber (int): The sequence number of the message.
    Methods:
        from_string(cls, message: str): Class method to create an instance of PositionEvent from a JSON string.
    """

    LoginID: str
    AccountID: str
    TradingSymbol: str
    ExchangeSegment: str
    ExchangeInstrumentID: int
    ProductType: str
    Multiplier: Decimal
    Marketlot: int
    BuyAveragePrice: Decimal
    SellAveragePrice: Decimal
    LongPosition: int
    ShortPosition: int
    NetPosition: int
    BuyValue: Decimal
    SellValue: Decimal
    NetValue: Decimal
    UnrealizedMTM: Decimal
    RealizedMTM: Decimal
    MTM: Decimal
    BEP: Decimal
    SumOfTradedQuantityAndPriceBuy: Decimal
    SumOfTradedQuantityAndPriceSell: Decimal
    IsDayWiseNetWise: str
    StatisticsLevel: str
    IsInterOpPosition: bool
    childPositions: dict
    MessageCode: int
    MessageVersion: int
    TokenID: int
    ApplicationType: int
    SequenceNumber: int

    def __init__(self, message: str):
        data = json.loads(message)
        if 'SellAveragePrice' in data and (data['SellAveragePrice'] == 'NaN' or data['SellAveragePrice'] != data['SellAveragePrice']):
            data['SellAveragePrice'] = Decimal("0")
        if 'BuyAveragePrice' in data and (data['BuyAveragePrice'] == 'NaN' or data['BuyAveragePrice'] != data['BuyAveragePrice']):
            data['BuyAveragePrice'] = Decimal("0")
        super().__init__(**data)



