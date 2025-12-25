# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["BrandPrefetchByEmailParams"]


class BrandPrefetchByEmailParams(TypedDict, total=False):
    email: Required[str]
    """Email address to prefetch brand data for.

    The domain will be extracted from the email. Free email providers (gmail.com,
    yahoo.com, etc.) and disposable email addresses are not allowed.
    """

    timeout_ms: Annotated[int, PropertyInfo(alias="timeoutMS")]
    """Optional timeout in milliseconds for the request.

    If the request takes longer than this value, it will be aborted with a 408
    status code. Maximum allowed value is 300000ms (5 minutes).
    """
