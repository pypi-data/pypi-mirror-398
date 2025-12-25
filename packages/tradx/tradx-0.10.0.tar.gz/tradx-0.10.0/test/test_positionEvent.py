from tradx.baseClass.interactive.positionEvent import PositionEvent


def test_fromString():
    message = """
    {
    "LoginID": "ANSYM1",
    "AccountID": "PR03",
    "TradingSymbol": "JUBLFOOD",
    "ExchangeSegment": "NSECM",
    "ExchangeInstrumentID": "18096",
    "ProductType": "MIS",
    "Multiplier": "1",
    "Marketlot": "1",
    "BuyAveragePrice": "710.2",
    "SellAveragePrice": "715.175",
    "LongPosition": "26",
    "ShortPosition": "26",
    "NetPosition": "0",
    "BuyValue": "18465.2",
    "SellValue": "18594.55",
    "NetValue": "129.34999999999854",
    "UnrealizedMTM": "0.00",
    "RealizedMTM": "0.00",
    "MTM": "0.00",
    "BEP": "0.00",
    "SumOfTradedQuantityAndPriceBuy": "18465.2",
    "SumOfTradedQuantityAndPriceSell": "18594.55",
    "IsDayWiseNetWise": "DayWise",
    "StatisticsLevel": "ParentLevel",
    "IsInterOpPosition": false,
    "childPositions": {},
    "MessageCode": 9002,
    "MessageVersion": 1,
    "TokenID": 0,
    "ApplicationType": 0,
    "SequenceNumber": 0
    }
    """
    position_event = PositionEvent(message)
    assert isinstance(position_event, PositionEvent)
