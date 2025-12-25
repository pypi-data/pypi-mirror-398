from tradx.baseClass.market.marketDepthData import MarketDepthData


def test_fromString():
    message = """
    {
    "MessageCode": 1502,
    "MessageVersion": 1,
    "ApplicationType": 0,
    "TokenID": 0,
    "ExchangeSegment": 1,
    "ExchangeInstrumentID": 22,
    "ExchangeTimeStamp": 1205682251,
    "Bids": [
        {
        "Size": 1428,
        "Price": 1567.95,
        "TotalOrders": 10,
        "BuyBackMarketMaker": 0
        },
        {
        "Size": 0,
        "Price": 0,
        "TotalOrders": 0,
        "BuyBackMarketMaker": 0
        },
        {
        "Size": 0,
        "Price": 0,
        "TotalOrders": 0,
        "BuyBackMarketMaker": 0
        },
        {
        "Size": 0,
        "Price": 0,
        "TotalOrders": 0,
        "BuyBackMarketMaker": 0
        },
        {
        "Size": 0,
        "Price": 0,
        "TotalOrders": 0,
        "BuyBackMarketMaker": 0
        }
    ],
    "Asks": [
        {
        "Size": 0,
        "Price": 0,
        "TotalOrders": 0,
        "BuyBackMarketMaker": 0
        },
        {
        "Size": 0,
        "Price": 0,
        "TotalOrders": 0,
        "BuyBackMarketMaker": 0
        },
        {
        "Size": 0,
        "Price": 0,
        "TotalOrders": 0,
        "BuyBackMarketMaker": 0
        },
        {
        "Size": 0,
        "Price": 0,
        "TotalOrders": 0,
        "BuyBackMarketMaker": 0
        },
        {
        "Size": 0,
        "Price": 0,
        "TotalOrders": 0,
        "BuyBackMarketMaker": 0
        }
    ],
    "Touchline": {
        "BidInfo": {
        "Size": 1428,
        "Price": 1567.95,
        "TotalOrders": 10,
        "BuyBackMarketMaker": 0
        },
        "AskInfo": {
        "Size": 0,
        "Price": 0,
        "TotalOrders": 0,
        "BuyBackMarketMaker": 0
        },
        "LastTradedPrice": 1567.95,
        "LastTradedQunatity": 20,
        "TotalBuyQuantity": 1428,
        "TotalSellQuantity": 0,
        "TotalTradedQuantity": 253453,
        "AverageTradedPrice": 1576.2,
        "LastTradedTime": 1205682110,
        "LastUpdateTime": 1205682251,
        "PercentChange": 0,
        "Open": 1599.9,
        "High": 1607.25,
        "Low": 1552.7,
        "Close": 1567.95,
        "TotalValueTraded": 177838490,
        "BuyBackTotalBuy": 53190,
        "BuyBackTotalSell": 16823
    },
    "BookType": 0,
    "XMarketType": 0,
    "SequenceNumber": 186901854008294
    }
    """
    marketDepthData = MarketDepthData(message)
    assert isinstance(marketDepthData, MarketDepthData)
