from tradx.baseClass.market.ltpPartialData import LtpPartialData


def test_fromString():
    message = "t:1_2885,ltp:2570.8,ltq:25,lut:1317813273,bt:1,mt:1"
    ltp_partial_data = LtpPartialData(message)
    assert isinstance(ltp_partial_data, LtpPartialData)
