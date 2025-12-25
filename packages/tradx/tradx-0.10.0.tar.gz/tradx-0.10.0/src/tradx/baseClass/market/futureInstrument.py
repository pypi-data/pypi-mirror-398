from decimal import Decimal
from pydantic import BaseModel
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pandas.core.series import Series

class FutureInstrument(BaseModel):
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
    ContractExpiration: datetime
    DisplayName: str
    PriceNumerator: int
    PriceDenominator: int
    DetailedDescription: str

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
        ContractExpiration: datetime,
        DisplayName: str,
        PriceNumerator: int,
        PriceDenominator: int,
        DetailedDescription: str,
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
            ContractExpiration=ContractExpiration,
            DisplayName=DisplayName,
            PriceNumerator=PriceNumerator,
            PriceDenominator=PriceDenominator,
            DetailedDescription=DetailedDescription,
        )
    def __init__(self, df: "Series"):
                super().__init__(**df)