from tradx.baseClass.market.openInterestPartialData import OpenInterestPartialData


def test_fromString():
    message = "t:1_46082,o:0"
    open_interest_partial_data = OpenInterestPartialData(message)
    assert isinstance(open_interest_partial_data, OpenInterestPartialData)
