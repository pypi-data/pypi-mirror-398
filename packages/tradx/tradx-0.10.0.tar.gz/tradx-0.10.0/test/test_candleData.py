from tradx.baseClass.market.candleData import CandleData


def test_fromString():
    message = """
     {
        "MessageCode": 1505,
        "MessageVersion": 1,
        "ApplicationType": 0,
        "TokenID": 0,
        "ExchangeSegment": 1,
        "ExchangeInstrumentID": 467,
        "BarTime": 1736164979,
        "BarVolume": 1760422,
        "High": 607.65,
        "Low": 606.5,
        "Open": 606.55,
        "Close": 607.45,
        "OpenInterest": 0,
        "SumOfQtyInToPrice": 0
    }

    """
    candleData = CandleData(message)
    assert isinstance(candleData, CandleData)
