# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from .._models import BaseModel

__all__ = ["BrandPrefetchResponse"]


class BrandPrefetchResponse(BaseModel):
    domain: Optional[str] = None
    """The domain that was queued for prefetching"""

    message: Optional[str] = None
    """Success message"""

    status: Optional[str] = None
    """Status of the response, e.g., 'ok'"""
