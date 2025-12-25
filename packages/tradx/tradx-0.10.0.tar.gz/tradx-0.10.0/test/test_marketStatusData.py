from tradx.baseClass.market.marketStatusData import MarketStatusData


def test_fromString():
    message = """
    {
    "ApplicationType":0,
    "ExchangeInstrumentID":0,
    "ExchangeSegment":1,
    "ExchangeTimeStamp":1295773200,
    "maketType":1,
    "message":"THE NORMAL MARKET HAS PREOPENED FOR 22 JAN 2021",
    "MessageCode":1507,
    "MessageVersion":4,
    "SequenceNumber":424567064044868,
    "TokenID":0,
    "tradingSession":1
   } 
   """
    market_depth_data = MarketStatusData(message)
    assert isinstance(market_depth_data, MarketStatusData)


def test_fromDict():
    message = {
        "ApplicationType": 0,
        "ExchangeInstrumentID": 0,
        "ExchangeSegment": 1,
        "ExchangeTimeStamp": 1295773200,
        "maketType": 1,
        "message": "THE NORMAL MARKET HAS PREOPENED FOR 22 JAN 2021",
        "MessageCode": 1507,
        "MessageVersion": 4,
        "SequenceNumber": 424567064044868,
        "TokenID": 0,
        "tradingSession": 1,
    }
    market_depth_data = MarketStatusData(message)
    assert isinstance(market_depth_data, MarketStatusData)
