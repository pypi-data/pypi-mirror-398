from decimal import Decimal
from pydantic import BaseModel
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pandas.core.series import Series


class CMInstrument(BaseModel):
    ExchangeSegment: str
    ExchangeInstrumentID: int
    InstrumentType: int
    Name: str
    Description: str
    Series: str
    NameWithSeries: str
    InstrumentID: int
    PriceBand_High: Decimal
    PriceBand_Low: Decimal
    FreezeQty: int
    TickSize: Decimal
    LotSize: int
    Multiplier: Decimal
    DisplayName: str
    ISIN: str
    PriceNumerator: int
    PriceDenominator: int
    DetailedDescription: str
    ExtendedSurvlndicator: int
    Cautionlndicator: int
    GSMIndicator: int

    def __init__(
        self,
        ExchangeSegment: str,
        ExchangeInstrumentID: int,
        InstrumentType: int,
        Name: str,
        Description: str,
        Series: str,
        NameWithSeries: str,
        InstrumentID: int,
        PriceBand_High: Decimal,
        PriceBand_Low: Decimal,
        FreezeQty: int,
        TickSize: Decimal,
        LotSize: int,
        Multiplier: Decimal,
        DisplayName: str,
        ISIN: str,
        PriceNumerator: int,
        PriceDenominator: int,
        DetailedDescription: str,
        ExtendedSurvlndicator: int,
        Cautionlndicator: int,
        GSMIndicator: int,
    ):
        super().__init__(
            ExchangeSegment=ExchangeSegment,
            ExchangeInstrumentID=ExchangeInstrumentID,
            InstrumentType=InstrumentType,
            Name=Name,
            Description=Description,
            Series=Series,
            NameWithSeries=NameWithSeries,
            InstrumentID=InstrumentID,
            PriceBand_High=PriceBand_High,
            PriceBand_Low=PriceBand_Low,
            FreezeQty=FreezeQty,
            TickSize=TickSize,
            LotSize=LotSize,
            Multiplier=Multiplier,
            DisplayName=DisplayName,
            ISIN=ISIN,
            PriceNumerator=PriceNumerator,
            PriceDenominator=PriceDenominator,
            DetailedDescription=DetailedDescription,
            ExtendedSurvlndicator=ExtendedSurvlndicator,
            Cautionlndicator=Cautionlndicator,
            GSMIndicator=GSMIndicator,
        )

    def __init__(self, df: "Series"):
        super().__init__(**df)
