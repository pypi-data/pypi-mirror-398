# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Iterable
from typing_extensions import Literal, Required, Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["BrandAIQueryParams", "DataToExtract", "SpecificPages"]


class BrandAIQueryParams(TypedDict, total=False):
    data_to_extract: Required[Iterable[DataToExtract]]
    """Array of data points to extract from the website"""

    domain: Required[str]
    """The domain name to analyze"""

    specific_pages: SpecificPages
    """Optional object specifying which pages to analyze"""

    timeout_ms: Annotated[int, PropertyInfo(alias="timeoutMS")]
    """Optional timeout in milliseconds for the request.

    If the request takes longer than this value, it will be aborted with a 408
    status code. Maximum allowed value is 300000ms (5 minutes).
    """


class DataToExtract(TypedDict, total=False):
    datapoint_description: Required[str]
    """Description of what to extract"""

    datapoint_example: Required[str]
    """Example of the expected value"""

    datapoint_name: Required[str]
    """Name of the data point to extract"""

    datapoint_type: Required[Literal["text", "number", "date", "boolean", "list", "url"]]
    """Type of the data point"""

    datapoint_list_type: Literal["string", "text", "number", "date", "boolean", "list", "url", "object"]
    """Type of items in the list when datapoint_type is 'list'.

    Defaults to 'string'. Use 'object' to extract an array of objects matching a
    schema.
    """

    datapoint_object_schema: Dict[str, Literal["string", "number", "date", "boolean"]]
    """Schema definition for objects when datapoint_list_type is 'object'.

    Provide a map of field names to their scalar types.
    """


class SpecificPages(TypedDict, total=False):
    """Optional object specifying which pages to analyze"""

    about_us: bool
    """Whether to analyze the about us page"""

    blog: bool
    """Whether to analyze the blog"""

    careers: bool
    """Whether to analyze the careers page"""

    contact_us: bool
    """Whether to analyze the contact us page"""

    faq: bool
    """Whether to analyze the FAQ page"""

    home_page: bool
    """Whether to analyze the home page"""

    pricing: bool
    """Whether to analyze the pricing page"""

    privacy_policy: bool
    """Whether to analyze the privacy policy page"""

    terms_and_conditions: bool
    """Whether to analyze the terms and conditions page"""
