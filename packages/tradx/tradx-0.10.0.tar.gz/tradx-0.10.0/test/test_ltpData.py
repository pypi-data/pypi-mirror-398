from tradx.baseClass.market.ltpData import LtpData


def test_fromString():
    message = """
    {
    "MessageCode":1512,
    "MessageVersion":4,
    "ApplicationType":0,
    "TokenID":0,
    "ExchangeSegment":1,
    "ExchangeInstrumentID":2885,
    "BookType":1,
    "XMarketType":1,
    "LastTradedPrice":2571.75,
    "LastTradedQunatity":3,
    "LastUpdateTime":1317813249
    }
   """
    ltp_data = LtpData(message)
    assert isinstance(ltp_data, LtpData)
