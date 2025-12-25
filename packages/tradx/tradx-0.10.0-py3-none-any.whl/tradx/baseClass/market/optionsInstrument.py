from decimal import Decimal
from pydantic import BaseModel, BeforeValidator
from typing_extensions import Annotated
from enum import Enum
from datetime import datetime
from typing import TYPE_CHECKING, List, Any

if TYPE_CHECKING:
    from pandas.core.series import Series
    from pandas import DataFrame


class OptionType(Enum):
    CE = 3
    PE = 4


def parse_int(value: Any) -> int:
    if isinstance(value, str):
        return int(value)
    return value


def captilize_str(value: str) -> str:
    return value.upper()


class OptionsInstrument(BaseModel):
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
    UnderlyingInstrumentId: int
    UnderlyingIndexName: str
    ContractExpiration: datetime
    StrikePrice: Decimal
    OptionType: Annotated[OptionType, BeforeValidator(parse_int)]
    DisplayName: str
    PriceNumerator: int
    PriceDenominator: int
    DetailedDescription: str

    class Config:
        use_enum_values = True

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
        UnderlyingInstrumentId: int,
        UnderlyingIndexName: Annotated[
            str,
            BeforeValidator(str, captilize_str),
        ],
        ContractExpiration: datetime,
        StrikePrice: Decimal,
        OptionType: Any,
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
            UnderlyingInstrumentId=UnderlyingInstrumentId,
            UnderlyingIndexName=UnderlyingIndexName,
            ContractExpiration=ContractExpiration,
            StrikePrice=StrikePrice,
            OptionType=OptionType,
            DisplayName=DisplayName,
            PriceNumerator=PriceNumerator,
            PriceDenominator=PriceDenominator,
            DetailedDescription=DetailedDescription,
        )

    def __init__(self, df: "Series"):
        super().__init__(**df)


class OptionManager:
    """
    Manages a list of options instruments and provides methods to search and filter them.
    """

    def __init__(self, option_master: "DataFrame"):
        """
        Initializes the OptionManager with a DataFrame of options data.
        Args:
            option_master (pandas.DataFrame): DataFrame containing options data.
        """
        self.__list: List[OptionsInstrument] = []
        for index, row in option_master.iterrows():
            self.__list.append(OptionsInstrument(row))

        self.__all_underline = list(
            set([option.UnderlyingIndexName for option in self.__list])
        )

    def search_expiry_by_underline(self, underline: str) -> List[datetime]:
        """
        Searches for all contract expirations for a given underlying index name.
        Args:
            underline (str): The underlying index name to search for.
        Returns:
            List[OptionsInstrument.ContractExpiration]: A sorted list of contract expirations.
        """
        return sorted(
            list(
                set(
                    option.ContractExpiration
                    for option in self.__list
                    if option.UnderlyingIndexName == underline
                )
            )
        )

    def search_all_underline(self) -> List[str]:
        """
        Retrieves all unique underlying index names.
        Returns:
            List[OptionsInstrument.UnderlyingIndexName]: A list of all unique underlying index names.
        """
        return self.__all_underline

    def search_option_by_underline(self, underline: str) -> List[OptionsInstrument]:
        """
        Searches for all options instruments for a given underlying index name.
        Args:
            underline (str): The underlying index name to search for.
        Returns:
            List[OptionsInstrument]: A list of options instruments.
        """
        return [
            option for option in self.__list if option.UnderlyingIndexName == underline
        ]

    def search_option_by_expiry_underline(
        self, underline: str, expiry: datetime
    ) -> List[OptionsInstrument]:
        """
        Searches for all options instruments for a given underlying index name and contract expiration.
        Args:
            underline (str): The underlying index name to search for.
            expiry (OptionsInstrument.ContractExpiration): The contract expiration to search for.
        Returns:
            List[OptionsInstrument]: A list of options instruments.
        """
        return [
            option
            for option in self.__list
            if option.UnderlyingIndexName == underline
            and option.ContractExpiration == expiry
        ]

    def search_option(
        self,
        ExchangeSegment: str = None,
        ExchangeInstrumentID: int = None,
        InstrumentType: int = None,
        Name: str = None,
        Series: str = None,
        UnderlyingIndexName: str = None,
        ContractExpiration: datetime = None,
        StrikePrice: int = None,
        OptionType: int = None,
        minimumExpiry: bool = False,
    ) -> List[OptionsInstrument]:
        """
        Searches for options based on various criteria.
        Args:
            ExchangeSegment (str): Exchange segment to search for.
            ExchangeInstrumentID (int): Exchange instrument ID to search for.
            InstrumentType (int): Instrument type to search for.
            Name (str): Name to search for.
            Series (str): Series to search for.
            UnderlyingIndexName (str): Underlying index name to search for.
            ContractExpiration (datetime): Contract expiration to search for.
            StrikePrice (int): Strike price to search for.
            OptionType (int): Option type to search for.
            minimumExpiry (bool): If True, only return options with the minimum expiration date.
        Returns:
            pandas.DataFrame: DataFrame containing the search results.
        """
        assert ExchangeSegment is None or isinstance(
            ExchangeSegment, str
        ), "ExchangeSegment must be a string"
        assert ExchangeInstrumentID is None or isinstance(
            ExchangeInstrumentID, int
        ), "ExchangeInstrumentID must be an integer"
        assert InstrumentType is None or isinstance(
            InstrumentType, int
        ), "InstrumentType must be an integer"
        assert Name is None or isinstance(Name, str), "Name must be a string"
        assert Series is None or isinstance(Series, str), "Series must be a string"
        assert UnderlyingIndexName is None or isinstance(
            UnderlyingIndexName, str
        ), "UnderlyingIndexName must be a string"
        assert ContractExpiration is None or isinstance(
            ContractExpiration, datetime
        ), "ContractExpiration must be a datetime"
        assert StrikePrice is None or isinstance(
            StrikePrice, int
        ), "StrikePrice must be an integer"
        assert OptionType is None or isinstance(
            OptionType, int
        ), "OptionType must be an integer"
        assert isinstance(minimumExpiry, bool), "minimumExpiry must be a boolean"

        criteria = {
            "ExchangeSegment": ExchangeSegment,
            "ExchangeInstrumentID": ExchangeInstrumentID,
            "InstrumentType": InstrumentType,
            "Name": Name,
            "Series": Series,
            "UnderlyingIndexName": UnderlyingIndexName,
            "ContractExpiration": ContractExpiration,
            "StrikePrice": StrikePrice,
            "OptionType": OptionType,
        }
        criteria = {k: v for k, v in criteria.items() if v is not None}

        if not criteria:
            return self.__list

        results = self.__list
        for key, value in criteria.items():
            if key == "Name":
                results = [option for option in results if value in option.Name]
            elif key == "ContractExpiration":
                results = [
                    option for option in results if option.ContractExpiration <= value
                ]
            else:
                results = [
                    option for option in results if getattr(option, key) == value
                ]

        if minimumExpiry:
            _min_expiry = min([option.ContractExpiration for option in results])
            results = [
                option for option in results if option.ContractExpiration == _min_expiry
            ]

        return results
