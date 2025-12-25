from tradx.baseClass.interactive.tradeEvent import TradeEvent


def test_fromString():
    message = """
    {
    "LoginID": "ANSYM1",
    "ClientID": "PR03",
    "AppOrderID": 1110027235,
    "OrderReferenceID": "",
    "GeneratedBy": "TWSAPI",
    "ExchangeOrderID": "1000000019047473",
    "OrderCategoryType": "NORMAL",
    "ExchangeSegment": "NSECM",
    "ExchangeInstrumentID": 335,
    "OrderSide": "Sell",
    "OrderType": "Market",
    "ProductType": "MIS",
    "TimeInForce": "DAY",
    "OrderPrice": 0,
    "OrderQuantity": 3,
    "OrderStopPrice": 0,
    "OrderStatus": "Filled",
    "OrderAverageTradedPrice": "2,853.50",
    "LeavesQuantity": 0,
    "CumulativeQuantity": 3,
    "OrderDisclosedQuantity": 0,
    "OrderGeneratedDateTime": "2024-12-27T11:22:47.566038",
    "ExchangeTransactTime": "2024-12-27T11:22:47+05:30",
    "LastUpdateDateTime": "2024-12-27T11:22:47.5972834",
    "CancelRejectReason": "",
    "OrderUniqueIdentifier": "9NcLerkS",
    "OrderLegStatus": "SingleOrderLeg",
    "LastTradedPrice": 2853.5,
    "LastTradedQuantity": 3,
    "LastExecutionTransactTime": "2024-12-27T11:22:47",
    "ExecutionID": "2177829",
    "ExecutionReportIndex": 4,
    "IsSpread": false,
    "OrderAverageTradedPriceAPI": 2853.5,
    "OrderSideAPI": "SELL",
    "OrderGeneratedDateTimeAPI": "27-12-2024 11:22:47",
    "ExchangeTransactTimeAPI": "27-12-2024 11:22:47",
    "LastUpdateDateTimeAPI": "27-12-2024 11:22:47",
    "OrderExpiryDateAPI": "01-01-1980 00:00:00",
    "LastExecutionTransactTimeAPI": "27-12-2024 11:22:47",
    "MessageSynchronizeUniqueKey": "PR03",
    "MessageCode": 9005,
    "MessageVersion": 4,
    "TokenID": 0,
    "ApplicationType": 146,
    "SequenceNumber": 1574494704023895,
    "TradingSymbol": "BALKRISIND"
    }
    """
    trade_event = TradeEvent(message)
    assert isinstance(trade_event, TradeEvent)
