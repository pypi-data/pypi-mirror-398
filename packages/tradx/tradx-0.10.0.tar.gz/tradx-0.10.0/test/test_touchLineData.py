from tradx.baseClass.market.touchLineData import TouchLineData


def test_fromString_1():
    message = """
    {
    "MessageCode": 1501,
    "ExchangeSegment": 1,
    "ExchangeInstrumentID": 467,
    "LastTradedPrice": 610.3,
    "LastTradedQunatity": 1,
    "TotalBuyQuantity": 363004,
    "TotalSellQuantity": 327007,
    "TotalTradedQuantity": 1983015,
    "AverageTradedPrice": 612.81,
    "LastTradedTime": 1420632949,
    "LastUpdateTime": 1420632949,
    "PercentChange": -2.038523274478332,
    "Open": 627,
    "High": 627,
    "Low": 605.15,
    "Close": 623,
    "TotalValueTraded": null,
    "AskInfo": {
        "Size": 15,
        "Price": 610.3,
        "TotalOrders": 1,
        "BuyBackMarketMaker": 0
    },
    "BidInfo": {
        "Size": 119,
        "Price": 610.15,
        "TotalOrders": 3,
        "BuyBackMarketMaker": 0
    },
    "XMarketType": 1,
    "BookType": 1
    }
    """
    touchLineData = TouchLineData(message)
    assert isinstance(touchLineData, TouchLineData)


def test_fromString_2():
    message = """
    {
    "MessageCode": 1501,
    "MessageVersion": 4,
    "ApplicationType": 0,
    "TokenID": 0,
    "ExchangeSegment": 1,
    "ExchangeInstrumentID": 26000,
    "ExchangeTimeStamp": 1421315385,
    "Touchline": {
        "BidInfo": {
        "Size": 0,
        "Price": 0,
        "TotalOrders": 0,
        "BuyBackMarketMaker": 0
        },
        "AskInfo": {
        "Size": 0,
        "Price": 0,
        "TotalOrders": 0,
        "BuyBackMarketMaker": 0
        },
        "LastTradedPrice": 23202.15,
        "LastTradedQunatity": 0,
        "TotalBuyQuantity": 0,
        "TotalSellQuantity": 0,
        "TotalTradedQuantity": 0,
        "AverageTradedPrice": 23202.15,
        "LastTradedTime": 1421315385,
        "LastUpdateTime": 1421315385,
        "PercentChange": 0.5,
        "Open": 23165.9,
        "High": 23227.2,
        "Low": 23150.05,
        "Close": 23085.95,
        "TotalValueTraded": null,
        "BuyBackTotalBuy": 0,
        "BuyBackTotalSell": 0
    },
    "BookType": 1,
    "XMarketType": 1,
    "SequenceNumber": 1590018768596832
    }
    """
    touchLineData = TouchLineData(message)
    assert isinstance(touchLineData, TouchLineData)
