# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from typing_extensions import Literal

from .._models import BaseModel

__all__ = ["BrandRetrieveNaicsResponse", "Code"]


class Code(BaseModel):
    code: str
    """NAICS code"""

    confidence: Literal["high", "medium", "low"]
    """Confidence level for how well this NAICS code matches the company description"""

    name: str
    """NAICS title"""


class BrandRetrieveNaicsResponse(BaseModel):
    codes: Optional[List[Code]] = None
    """Array of NAICS codes and titles."""

    domain: Optional[str] = None
    """Domain found for the brand"""

    status: Optional[str] = None
    """Status of the response, e.g., 'ok'"""

    type: Optional[str] = None
    """Industry classification type, for naics api it will be `naics`"""
