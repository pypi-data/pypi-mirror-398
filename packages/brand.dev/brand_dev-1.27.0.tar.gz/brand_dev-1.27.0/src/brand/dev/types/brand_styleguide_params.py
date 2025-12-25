# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal, Required, Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["BrandStyleguideParams"]


class BrandStyleguideParams(TypedDict, total=False):
    domain: Required[str]
    """Domain name to extract styleguide from (e.g., 'example.com', 'google.com').

    The domain will be automatically normalized and validated.
    """

    prioritize: Literal["speed", "quality"]
    """Optional parameter to prioritize screenshot capture for styleguide extraction.

    If 'speed', optimizes for faster capture with basic quality. If 'quality',
    optimizes for higher quality with longer wait times. Defaults to 'quality' if
    not provided.
    """

    timeout_ms: Annotated[int, PropertyInfo(alias="timeoutMS")]
    """Optional timeout in milliseconds for the request.

    If the request takes longer than this value, it will be aborted with a 408
    status code. Maximum allowed value is 300000ms (5 minutes).
    """
