# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal, Required, Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["BrandRetrieveByNameParams"]


class BrandRetrieveByNameParams(TypedDict, total=False):
    name: Required[str]
    """
    Company name to retrieve brand data for (e.g., 'Apple Inc', 'Microsoft
    Corporation'). Must be 3-30 characters.
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

    timeout_ms: Annotated[int, PropertyInfo(alias="timeoutMS")]
    """Optional timeout in milliseconds for the request.

    If the request takes longer than this value, it will be aborted with a 408
    status code. Maximum allowed value is 300000ms (5 minutes).
    """
