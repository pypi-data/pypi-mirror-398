# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal, Required, Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["BrandScreenshotParams"]


class BrandScreenshotParams(TypedDict, total=False):
    domain: Required[str]
    """Domain name to take screenshot of (e.g., 'example.com', 'google.com').

    The domain will be automatically normalized and validated.
    """

    full_screenshot: Annotated[Literal["true", "false"], PropertyInfo(alias="fullScreenshot")]
    """Optional parameter to determine screenshot type.

    If 'true', takes a full page screenshot capturing all content. If 'false' or not
    provided, takes a viewport screenshot (standard browser view).
    """

    page: Literal["login", "signup", "blog", "careers", "pricing", "terms", "privacy", "contact"]
    """Optional parameter to specify which page type to screenshot.

    If provided, the system will scrape the domain's links and use heuristics to
    find the most appropriate URL for the specified page type (30 supported
    languages). If not provided, screenshots the main domain landing page.
    """

    prioritize: Literal["speed", "quality"]
    """Optional parameter to prioritize screenshot capture.

    If 'speed', optimizes for faster capture with basic quality. If 'quality',
    optimizes for higher quality with longer wait times. Defaults to 'quality' if
    not provided.
    """
