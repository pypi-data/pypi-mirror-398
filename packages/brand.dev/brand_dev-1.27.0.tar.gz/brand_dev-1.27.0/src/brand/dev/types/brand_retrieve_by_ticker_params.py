# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal, Required, Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["BrandRetrieveByTickerParams"]


class BrandRetrieveByTickerParams(TypedDict, total=False):
    ticker: Required[str]
    """Stock ticker symbol to retrieve brand data for (e.g., 'AAPL', 'GOOGL', 'BRK.A').

    Must be 1-15 characters, letters/numbers/dots only.
    """

    force_language: Literal[
        "albanian",
        "arabic",
        "azeri",
        "bengali",
        "bulgarian",
        "cebuano",
        "croatian",
        "czech",
        "danish",
        "dutch",
        "english",
        "estonian",
        "farsi",
        "finnish",
        "french",
        "german",
        "hausa",
        "hawaiian",
        "hindi",
        "hungarian",
        "icelandic",
        "indonesian",
        "italian",
        "kazakh",
        "kyrgyz",
        "latin",
        "latvian",
        "lithuanian",
        "macedonian",
        "mongolian",
        "nepali",
        "norwegian",
        "pashto",
        "pidgin",
        "polish",
        "portuguese",
        "romanian",
        "russian",
        "serbian",
        "slovak",
        "slovene",
        "somali",
        "spanish",
        "swahili",
        "swedish",
        "tagalog",
        "turkish",
        "ukrainian",
        "urdu",
        "uzbek",
        "vietnamese",
        "welsh",
    ]
    """Optional parameter to force the language of the retrieved brand data."""

    max_speed: Annotated[bool, PropertyInfo(alias="maxSpeed")]
    """Optional parameter to optimize the API call for maximum speed.

    When set to true, the API will skip time-consuming operations for faster
    response at the cost of less comprehensive data.
    """

    ticker_exchange: Literal[
        "AMEX",
        "AMS",
        "AQS",
        "ASX",
        "ATH",
        "BER",
        "BME",
        "BRU",
        "BSE",
        "BUD",
        "BUE",
        "BVC",
        "CBOE",
        "CNQ",
        "CPH",
        "DFM",
        "DOH",
        "DUB",
        "DUS",
        "DXE",
        "EGX",
        "FSX",
        "HAM",
        "HEL",
        "HKSE",
        "HOSE",
        "ICE",
        "IOB",
        "IST",
        "JKT",
        "JNB",
        "JPX",
        "KLS",
        "KOE",
        "KSC",
        "KUW",
        "LIS",
        "LSE",
        "MCX",
        "MEX",
        "MIL",
        "MUN",
        "NASDAQ",
        "NEO",
        "NSE",
        "NYSE",
        "NZE",
        "OSL",
        "OTC",
        "PAR",
        "PNK",
        "PRA",
        "RIS",
        "SAO",
        "SAU",
        "SES",
        "SET",
        "SGO",
        "SHH",
        "SHZ",
        "SIX",
        "STO",
        "STU",
        "TAI",
        "TAL",
        "TLV",
        "TSX",
        "TSXV",
        "TWO",
        "VIE",
        "WSE",
        "XETRA",
    ]
    """Optional stock exchange for the ticker. Defaults to NASDAQ if not specified."""

    timeout_ms: Annotated[int, PropertyInfo(alias="timeoutMS")]
    """Optional timeout in milliseconds for the request.

    If the request takes longer than this value, it will be aborted with a 408
    status code. Maximum allowed value is 300000ms (5 minutes).
    """
