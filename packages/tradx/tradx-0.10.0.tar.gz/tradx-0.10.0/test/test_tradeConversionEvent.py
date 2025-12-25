from tradx.baseClass.interactive.tradeConversionEvent import TradeConversionEvent


def test_fromString():
    message = """
    {
    "LoginID": "SYMP1",
    "ClientID": "SYMP1",
    "UniqueKey": "SYMP1:Client:SYMP1:NRML:NONE:NSECM:2885:ParentLevel",
    "Success": true,
    "ErrorMessage": "",
    "OriginalProduct": "MIS",
    "TargetProduct": "NRML",
    "OriginalQty": 10,
    "TargetQty": 10,
    "EntityType": "Client",
    "ExchangeSegment": "NSECM",
    "ExchangeInstrumentId": 0,
    "TargetEntityId": "SYMP1",
    "NetValue": -2587.5,
    "Status": "PositionConverted",
    "RejectionReason": "",
    "RejectedBy": "",
    "Price": -2587.5,
    "NOWTimeStamp": "2021-10-29T17:22:25.945707",
    "OrderSide": "Buy",
    "IsProOrder": false,
    "MessageCode": 9007,
    "MessageVersion": 4,
    "TokenID": 0,
    "ApplicationType": 0,
    "SequenceNumber": 0
    }
    """
    trade_event = TradeConversionEvent(message)
    assert isinstance(trade_event, TradeConversionEvent)
