from tradx.baseClass.market.openInterestData import OpenInterestData


def test_fromString():
    message = """
    {
    "MessageCode":1510,
    "MessageVersion":0,
    "ApplicationType":0,
    "TokenID":0,
    "ExchangeSegment":1,
    "ExchangeInstrumentID":46082,
    "ExchangeTimeStamp":0,
    "XTSMarketType":1,
    "OpenInterest":0
    }
   """
    open_interest_data = OpenInterestData(message)
    assert isinstance(open_interest_data, OpenInterestData)
