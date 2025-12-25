# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Union, Optional

from .._models import BaseModel

__all__ = ["BrandAIQueryResponse", "DataExtracted"]


class DataExtracted(BaseModel):
    datapoint_name: Optional[str] = None
    """Name of the extracted data point"""

    datapoint_value: Union[str, float, bool, List[str], List[float], List[object], None] = None
    """Value of the extracted data point.

    Can be a primitive type, an array of primitives, or an array of objects when
    datapoint_list_type is 'object'.
    """


class BrandAIQueryResponse(BaseModel):
    data_extracted: Optional[List[DataExtracted]] = None
    """Array of extracted data points"""

    domain: Optional[str] = None
    """The domain that was analyzed"""

    status: Optional[str] = None
    """Status of the response, e.g., 'ok'"""

    urls_analyzed: Optional[List[str]] = None
    """List of URLs that were analyzed"""
