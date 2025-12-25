from tradx.baseClass.interactive.orderEvent import OrderEvent


def test_fromString():
    message = """
    {
        "LoginID": "ANSYM1",
        "ClientID": "PR03",
        "AppOrderID": 1110037830,
        "OrderReferenceID": "",
        "GeneratedBy": "TWSAPI",
        "ExchangeOrderID": "",
        "OrderCategoryType": "NORMAL",
        "ExchangeSegment": "NSECM",
        "ExchangeInstrumentID": 23650,
        "OrderSide": "Sell",
        "OrderType": "StopMarket",
        "ProductType": "MIS",
        "TimeInForce": "DAY",
        "OrderPrice": 0,
        "OrderQuantity": 46,
        "OrderStopPrice": 2148.35,
        "OrderStatus": "PendingNew",
        "OrderAverageTradedPrice": "",
        "LeavesQuantity": 46,
        "CumulativeQuantity": 0,
        "OrderDisclosedQuantity": 0,
        "OrderGeneratedDateTime": "2025-01-01T10:00:15.237162",
        "ExchangeTransactTime": "2025-01-01T10:00:15.237162+05:30",
        "LastUpdateDateTime": "2025-01-01T10:00:15.237162",
        "OrderExpiryDate": "1980-01-01T00:00:00",
        "CancelRejectReason": "",
        "OrderUniqueIdentifier": "zaooZdki",
        "OrderLegStatus": "SingleOrderLeg",
        "IsSpread": false,
        "BoLegDetails": 0,
        "BoEntryOrderId": "",
        "OrderAverageTradedPriceAPI": "NaN",
        "OrderSideAPI": "SELL",
        "OrderGeneratedDateTimeAPI": "01-01-2025 10:00:15",
        "ExchangeTransactTimeAPI": "01-01-2025 10:00:15",
        "LastUpdateDateTimeAPI": "01-01-2025 10:00:15",
        "OrderExpiryDateAPI": "01-01-1980 00:00:00",
        "AlgoID": "",
        "AlgoCategory": 0,
        "MessageSynchronizeUniqueKey": "ANSYM1",
        "MessageCode": 9004,
        "MessageVersion": 4,
        "TokenID": 0,
        "ApplicationType": 146,
        "SequenceNumber": 1578799396766893,
        "TradingSymbol": "MUTHOOTFIN"
    }
    """
    orderEvent = OrderEvent(message)
    assert isinstance(orderEvent, OrderEvent)
