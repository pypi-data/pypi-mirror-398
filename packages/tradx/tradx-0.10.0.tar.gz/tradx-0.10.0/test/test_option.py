import pandas as pd
from tradx.baseClass.market.optionsInstrument import OptionManager
from datetime import datetime


def generate() -> pd.DataFrame:
    data = {
        "ExchangeSegment": ["NSEFO", "NSEFO", "NSEFO", "NSEFO"],
        "ExchangeInstrumentID": [130764, 112931, 38133, 38134],
        "InstrumentType": [2, 2, 2, 2],
        "Name": ["MCX", "MCX", "ABB", "ABB"],
        "Description": [
            "MCX25MAR4800CE",
            "MCX25JAN7400CE",
            "ABB25FEB9300CE",
            "ABB25FEB9300PE",
        ],
        "Series": ["OPTSTK", "OPTSTK", "OPTSTK", "OPTSTK"],
        "NameWithSeries": ["MCX-OPTSTK", "MCX-OPTSTK", "ABB-OPTSTK", "ABB-OPTSTK"],
        "InstrumentID": [2508600000000, 2503000000000, 2505800000000, 2505800000000],
        "PriceBand_High": [1775.3, 27.75, 30.55, 2943.9],
        "PriceBand_Low": [982.1, 0.05, 0.05, 2076.5],
        "FreezeQty": [4001, 4001, 3751, 3751],
        "TickSize": [0.05, 0.05, 0.05, 0.05],
        "LotSize": [100, 100, 125, 125],
        "Multiplier": [1, 1, 1, 1],
        "UnderlyingInstrumentId": [
            1100100000000,
            1100100000000,
            1100100000000,
            1100100000000,
        ],
        "UnderlyingIndexName": ["MCX", "MCX", "ABB", "ABB"],
        "ContractExpiration": [
            "2025-03-27T14:30:00",
            "2025-01-30T14:30:00",
            "2025-02-27T14:30:00",
            "2025-02-27T14:30:00",
        ],
        "StrikePrice": [4800, 7400, 9300, 9300],
        "OptionType": [3, 3, 3, 4],
        "DisplayName": [
            "MCX 27MAR2025 CE 4800",
            "MCX 30JAN2025 CE 7400",
            "ABB 27FEB2025 CE 9300",
            "ABB 27FEB2025 PE 9300",
        ],
        "PriceNumerator": [1, 1, 1, 1],
        "PriceDenominator": [1, 1, 1, 1],
        "DetailedDescription": [
            "MCX25MAR4800CE",
            "MCX25JAN7400CE",
            "ABB25FEB9300CE",
            "ABB25FEB9300PE",
        ],
    }
    df = pd.DataFrame(data)
    return df


def test_search_expiry_by_underline() -> None:
    df = generate()
    option_manager = OptionManager(df)
    assert option_manager.search_expiry_by_underline("MCX") == [
        datetime(2025, 1, 30, 14, 30, 0),
        datetime(2025, 3, 27, 14, 30, 0),
    ]
    assert option_manager.search_expiry_by_underline("ABB") == [
        datetime(2025, 2, 27, 14, 30, 0),
    ]


def test_search_all_underline() -> None:
    df = generate()
    option_manager = OptionManager(df)
    assert option_manager.search_all_underline() == [
        "MCX",
        "ABB",
    ] or option_manager.search_all_underline() == ["ABB", "MCX"]


def test_search_option_by_underline() -> None:
    df = generate()
    option_manager = OptionManager(df)
    assert len(option_manager.search_option_by_underline("MCX")) == 2
    assert len(option_manager.search_option_by_underline("ABB")) == 2


def test_search_option_by_expiry_underline() -> None:
    df = generate()
    option_manager = OptionManager(df)
    assert (
        len(
            option_manager.search_option_by_expiry_underline(
                "MCX", datetime(2025, 1, 30, 14, 30, 0)
            )
        )
        == 1
    )
    assert (
        len(
            option_manager.search_option_by_expiry_underline(
                "MCX", datetime(2025, 3, 27, 14, 30, 0)
            )
        )
        == 1
    )
    assert (
        len(
            option_manager.search_option_by_expiry_underline(
                "ABB", datetime(2025, 2, 27, 14, 30, 0)
            )
        )
        == 2
    )


def test_search_option_1() -> None:
    df = generate()
    option_manager = OptionManager(df)
    result = option_manager.search_option(ExchangeSegment="NSEFO")
    assert len(result) == 4


def test_search_option_2() -> None:
    df = generate()
    option_manager = OptionManager(df)
    result = option_manager.search_option(Name="MC")
    assert len(result) == 2


def test_search_option_3() -> None:
    df = generate()
    option_manager = OptionManager(df)
    result = option_manager.search_option(
        Name="MC", ContractExpiration=datetime(2025, 2, 18, 14, 30, 0)
    )
    assert len(result) == 1


def test_search_option_4() -> None:
    df = generate()
    option_manager = OptionManager(df)
    result = option_manager.search_option(Name="MC", minimumExpiry=True)
    assert len(result) == 1
