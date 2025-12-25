# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List

from .._models import BaseModel

__all__ = ["BrandFontsResponse", "Font"]


class Font(BaseModel):
    fallbacks: List[str]
    """Array of fallback font families"""

    font: str
    """Font family name"""

    num_elements: float
    """Number of elements using this font"""

    num_words: float
    """Number of words using this font"""

    percent_elements: float
    """Percentage of elements using this font"""

    percent_words: float
    """Percentage of words using this font"""

    uses: List[str]
    """Array of CSS selectors or element types where this font is used"""


class BrandFontsResponse(BaseModel):
    code: int
    """HTTP status code, e.g., 200"""

    domain: str
    """The normalized domain that was processed"""

    fonts: List[Font]
    """Array of font usage information"""

    status: str
    """Status of the response, e.g., 'ok'"""
