# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Iterable
from typing_extensions import Literal

import httpx

from ..types import (
    brand_fonts_params,
    brand_ai_query_params,
    brand_prefetch_params,
    brand_retrieve_params,
    brand_screenshot_params,
    brand_styleguide_params,
    brand_retrieve_naics_params,
    brand_retrieve_by_isin_params,
    brand_retrieve_by_name_params,
    brand_prefetch_by_email_params,
    brand_retrieve_by_email_params,
    brand_retrieve_by_ticker_params,
    brand_retrieve_simplified_params,
    brand_identify_from_transaction_params,
)
from .._types import Body, Omit, Query, Headers, NotGiven, omit, not_given
from .._utils import maybe_transform, async_maybe_transform
from .._compat import cached_property
from .._resource import SyncAPIResource, AsyncAPIResource
from .._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from .._base_client import make_request_options
from ..types.brand_fonts_response import BrandFontsResponse
from ..types.brand_ai_query_response import BrandAIQueryResponse
from ..types.brand_prefetch_response import BrandPrefetchResponse
from ..types.brand_retrieve_response import BrandRetrieveResponse
from ..types.brand_screenshot_response import BrandScreenshotResponse
from ..types.brand_styleguide_response import BrandStyleguideResponse
from ..types.brand_retrieve_naics_response import BrandRetrieveNaicsResponse
from ..types.brand_retrieve_by_isin_response import BrandRetrieveByIsinResponse
from ..types.brand_retrieve_by_name_response import BrandRetrieveByNameResponse
from ..types.brand_prefetch_by_email_response import BrandPrefetchByEmailResponse
from ..types.brand_retrieve_by_email_response import BrandRetrieveByEmailResponse
from ..types.brand_retrieve_by_ticker_response import BrandRetrieveByTickerResponse
from ..types.brand_retrieve_simplified_response import BrandRetrieveSimplifiedResponse
from ..types.brand_identify_from_transaction_response import BrandIdentifyFromTransactionResponse

__all__ = ["BrandResource", "AsyncBrandResource"]


class BrandResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> BrandResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/brand-dot-dev/python-sdk#accessing-raw-response-data-eg-headers
        """
        return BrandResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> BrandResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/brand-dot-dev/python-sdk#with_streaming_response
        """
        return BrandResourceWithStreamingResponse(self)

    def retrieve(
        self,
        *,
        domain: str | Omit = omit,
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
        | Omit = omit,
        max_speed: bool | Omit = omit,
        timeout_ms: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> BrandRetrieveResponse:
        """
        Retrieve logos, backdrops, colors, industry, description, and more from any
        domain

        Args:
          domain: Domain name to retrieve brand data for (e.g., 'example.com', 'google.com').
              Cannot be used with name or ticker parameters.

          force_language: Optional parameter to force the language of the retrieved brand data. Works with
              all three lookup methods.

          max_speed: Optional parameter to optimize the API call for maximum speed. When set to true,
              the API will skip time-consuming operations for faster response at the cost of
              less comprehensive data. Works with all three lookup methods.

          timeout_ms: Optional timeout in milliseconds for the request. If the request takes longer
              than this value, it will be aborted with a 408 status code. Maximum allowed
              value is 300000ms (5 minutes).

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get(
            "/brand/retrieve",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "domain": domain,
                        "force_language": force_language,
                        "max_speed": max_speed,
                        "timeout_ms": timeout_ms,
                    },
                    brand_retrieve_params.BrandRetrieveParams,
                ),
            ),
            cast_to=BrandRetrieveResponse,
        )

    def ai_query(
        self,
        *,
        data_to_extract: Iterable[brand_ai_query_params.DataToExtract],
        domain: str,
        specific_pages: brand_ai_query_params.SpecificPages | Omit = omit,
        timeout_ms: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> BrandAIQueryResponse:
        """Beta feature: Use AI to extract specific data points from a brand's website.

        The
        AI will crawl the website and extract the requested information based on the
        provided data points.

        Args:
          data_to_extract: Array of data points to extract from the website

          domain: The domain name to analyze

          specific_pages: Optional object specifying which pages to analyze

          timeout_ms: Optional timeout in milliseconds for the request. If the request takes longer
              than this value, it will be aborted with a 408 status code. Maximum allowed
              value is 300000ms (5 minutes).

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/brand/ai/query",
            body=maybe_transform(
                {
                    "data_to_extract": data_to_extract,
                    "domain": domain,
                    "specific_pages": specific_pages,
                    "timeout_ms": timeout_ms,
                },
                brand_ai_query_params.BrandAIQueryParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=BrandAIQueryResponse,
        )

    def fonts(
        self,
        *,
        domain: str,
        timeout_ms: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> BrandFontsResponse:
        """
        Beta feature: Extract font information from a brand's website including font
        families, usage statistics, fallbacks, and element/word counts.

        Args:
          domain: Domain name to extract fonts from (e.g., 'example.com', 'google.com'). The
              domain will be automatically normalized and validated.

          timeout_ms: Optional timeout in milliseconds for the request. If the request takes longer
              than this value, it will be aborted with a 408 status code. Maximum allowed
              value is 300000ms (5 minutes).

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get(
            "/brand/fonts",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "domain": domain,
                        "timeout_ms": timeout_ms,
                    },
                    brand_fonts_params.BrandFontsParams,
                ),
            ),
            cast_to=BrandFontsResponse,
        )

    def identify_from_transaction(
        self,
        *,
        transaction_info: str,
        city: str | Omit = omit,
        country_gl: Literal[
            "ad",
            "ae",
            "af",
            "ag",
            "ai",
            "al",
            "am",
            "an",
            "ao",
            "aq",
            "ar",
            "as",
            "at",
            "au",
            "aw",
            "az",
            "ba",
            "bb",
            "bd",
            "be",
            "bf",
            "bg",
            "bh",
            "bi",
            "bj",
            "bm",
            "bn",
            "bo",
            "br",
            "bs",
            "bt",
            "bv",
            "bw",
            "by",
            "bz",
            "ca",
            "cc",
            "cd",
            "cf",
            "cg",
            "ch",
            "ci",
            "ck",
            "cl",
            "cm",
            "cn",
            "co",
            "cr",
            "cu",
            "cv",
            "cx",
            "cy",
            "cz",
            "de",
            "dj",
            "dk",
            "dm",
            "do",
            "dz",
            "ec",
            "ee",
            "eg",
            "eh",
            "er",
            "es",
            "et",
            "fi",
            "fj",
            "fk",
            "fm",
            "fo",
            "fr",
            "ga",
            "gb",
            "gd",
            "ge",
            "gf",
            "gh",
            "gi",
            "gl",
            "gm",
            "gn",
            "gp",
            "gq",
            "gr",
            "gs",
            "gt",
            "gu",
            "gw",
            "gy",
            "hk",
            "hm",
            "hn",
            "hr",
            "ht",
            "hu",
            "id",
            "ie",
            "il",
            "in",
            "io",
            "iq",
            "ir",
            "is",
            "it",
            "jm",
            "jo",
            "jp",
            "ke",
            "kg",
            "kh",
            "ki",
            "km",
            "kn",
            "kp",
            "kr",
            "kw",
            "ky",
            "kz",
            "la",
            "lb",
            "lc",
            "li",
            "lk",
            "lr",
            "ls",
            "lt",
            "lu",
            "lv",
            "ly",
            "ma",
            "mc",
            "md",
            "mg",
            "mh",
            "mk",
            "ml",
            "mm",
            "mn",
            "mo",
            "mp",
            "mq",
            "mr",
            "ms",
            "mt",
            "mu",
            "mv",
            "mw",
            "mx",
            "my",
            "mz",
            "na",
            "nc",
            "ne",
            "nf",
            "ng",
            "ni",
            "nl",
            "no",
            "np",
            "nr",
            "nu",
            "nz",
            "om",
            "pa",
            "pe",
            "pf",
            "pg",
            "ph",
            "pk",
            "pl",
            "pm",
            "pn",
            "pr",
            "ps",
            "pt",
            "pw",
            "py",
            "qa",
            "re",
            "ro",
            "rs",
            "ru",
            "rw",
            "sa",
            "sb",
            "sc",
            "sd",
            "se",
            "sg",
            "sh",
            "si",
            "sj",
            "sk",
            "sl",
            "sm",
            "sn",
            "so",
            "sr",
            "st",
            "sv",
            "sy",
            "sz",
            "tc",
            "td",
            "tf",
            "tg",
            "th",
            "tj",
            "tk",
            "tl",
            "tm",
            "tn",
            "to",
            "tr",
            "tt",
            "tv",
            "tw",
            "tz",
            "ua",
            "ug",
            "um",
            "us",
            "uy",
            "uz",
            "va",
            "vc",
            "ve",
            "vg",
            "vi",
            "vn",
            "vu",
            "wf",
            "ws",
            "ye",
            "yt",
            "za",
            "zm",
            "zw",
        ]
        | Omit = omit,
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
        | Omit = omit,
        max_speed: bool | Omit = omit,
        mcc: str | Omit = omit,
        phone: float | Omit = omit,
        timeout_ms: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> BrandIdentifyFromTransactionResponse:
        """
        Endpoint specially designed for platforms that want to identify transaction data
        by the transaction title.

        Args:
          transaction_info: Transaction information to identify the brand

          city: Optional city name to prioritize when searching for the brand.

          country_gl: Optional country code (GL parameter) to specify the country. This affects the
              geographic location used for search queries.

          force_language: Optional parameter to force the language of the retrieved brand data.

          max_speed: Optional parameter to optimize the API call for maximum speed. When set to true,
              the API will skip time-consuming operations for faster response at the cost of
              less comprehensive data.

          mcc: Optional Merchant Category Code (MCC) to help identify the business
              category/industry.

          phone: Optional phone number from the transaction to help verify brand match.

          timeout_ms: Optional timeout in milliseconds for the request. If the request takes longer
              than this value, it will be aborted with a 408 status code. Maximum allowed
              value is 300000ms (5 minutes).

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get(
            "/brand/transaction_identifier",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "transaction_info": transaction_info,
                        "city": city,
                        "country_gl": country_gl,
                        "force_language": force_language,
                        "max_speed": max_speed,
                        "mcc": mcc,
                        "phone": phone,
                        "timeout_ms": timeout_ms,
                    },
                    brand_identify_from_transaction_params.BrandIdentifyFromTransactionParams,
                ),
            ),
            cast_to=BrandIdentifyFromTransactionResponse,
        )

    def prefetch(
        self,
        *,
        domain: str,
        timeout_ms: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> BrandPrefetchResponse:
        """
        Signal that you may fetch brand data for a particular domain soon to improve
        latency. This endpoint does not charge credits and is available for paid
        customers to optimize future requests. [You must be on a paid plan to use this
        endpoint]

        Args:
          domain: Domain name to prefetch brand data for

          timeout_ms: Optional timeout in milliseconds for the request. If the request takes longer
              than this value, it will be aborted with a 408 status code. Maximum allowed
              value is 300000ms (5 minutes).

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/brand/prefetch",
            body=maybe_transform(
                {
                    "domain": domain,
                    "timeout_ms": timeout_ms,
                },
                brand_prefetch_params.BrandPrefetchParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=BrandPrefetchResponse,
        )

    def prefetch_by_email(
        self,
        *,
        email: str,
        timeout_ms: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> BrandPrefetchByEmailResponse:
        """
        Signal that you may fetch brand data for a particular domain soon to improve
        latency. This endpoint accepts an email address, extracts the domain from it,
        validates that it's not a disposable or free email provider, and queues the
        domain for prefetching. This endpoint does not charge credits and is available
        for paid customers to optimize future requests. [You must be on a paid plan to
        use this endpoint]

        Args:
          email: Email address to prefetch brand data for. The domain will be extracted from the
              email. Free email providers (gmail.com, yahoo.com, etc.) and disposable email
              addresses are not allowed.

          timeout_ms: Optional timeout in milliseconds for the request. If the request takes longer
              than this value, it will be aborted with a 408 status code. Maximum allowed
              value is 300000ms (5 minutes).

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/brand/prefetch-by-email",
            body=maybe_transform(
                {
                    "email": email,
                    "timeout_ms": timeout_ms,
                },
                brand_prefetch_by_email_params.BrandPrefetchByEmailParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=BrandPrefetchByEmailResponse,
        )

    def retrieve_by_email(
        self,
        *,
        email: str,
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
        | Omit = omit,
        max_speed: bool | Omit = omit,
        timeout_ms: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> BrandRetrieveByEmailResponse:
        """
        Retrieve brand information using an email address while detecting disposable and
        free email addresses. This endpoint extracts the domain from the email address
        and returns brand data for that domain. Disposable and free email addresses
        (like gmail.com, yahoo.com) will throw a 422 error.

        Args:
          email: Email address to retrieve brand data for (e.g., 'contact@example.com'). The
              domain will be extracted from the email. Free email providers (gmail.com,
              yahoo.com, etc.) and disposable email addresses are not allowed.

          force_language: Optional parameter to force the language of the retrieved brand data.

          max_speed: Optional parameter to optimize the API call for maximum speed. When set to true,
              the API will skip time-consuming operations for faster response at the cost of
              less comprehensive data.

          timeout_ms: Optional timeout in milliseconds for the request. If the request takes longer
              than this value, it will be aborted with a 408 status code. Maximum allowed
              value is 300000ms (5 minutes).

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get(
            "/brand/retrieve-by-email",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "email": email,
                        "force_language": force_language,
                        "max_speed": max_speed,
                        "timeout_ms": timeout_ms,
                    },
                    brand_retrieve_by_email_params.BrandRetrieveByEmailParams,
                ),
            ),
            cast_to=BrandRetrieveByEmailResponse,
        )

    def retrieve_by_isin(
        self,
        *,
        isin: str,
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
        | Omit = omit,
        max_speed: bool | Omit = omit,
        timeout_ms: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> BrandRetrieveByIsinResponse:
        """
        Retrieve brand information using an ISIN (International Securities
        Identification Number). This endpoint looks up the company associated with the
        ISIN and returns its brand data.

        Args:
          isin: ISIN (International Securities Identification Number) to retrieve brand data for
              (e.g., 'AU000000IMD5', 'US0378331005'). Must be exactly 12 characters: 2 letters
              followed by 9 alphanumeric characters and ending with a digit.

          force_language: Optional parameter to force the language of the retrieved brand data.

          max_speed: Optional parameter to optimize the API call for maximum speed. When set to true,
              the API will skip time-consuming operations for faster response at the cost of
              less comprehensive data.

          timeout_ms: Optional timeout in milliseconds for the request. If the request takes longer
              than this value, it will be aborted with a 408 status code. Maximum allowed
              value is 300000ms (5 minutes).

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get(
            "/brand/retrieve-by-isin",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "isin": isin,
                        "force_language": force_language,
                        "max_speed": max_speed,
                        "timeout_ms": timeout_ms,
                    },
                    brand_retrieve_by_isin_params.BrandRetrieveByIsinParams,
                ),
            ),
            cast_to=BrandRetrieveByIsinResponse,
        )

    def retrieve_by_name(
        self,
        *,
        name: str,
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
        | Omit = omit,
        max_speed: bool | Omit = omit,
        timeout_ms: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> BrandRetrieveByNameResponse:
        """Retrieve brand information using a company name.

        This endpoint searches for the
        company by name and returns its brand data.

        Args:
          name: Company name to retrieve brand data for (e.g., 'Apple Inc', 'Microsoft
              Corporation'). Must be 3-30 characters.

          force_language: Optional parameter to force the language of the retrieved brand data.

          max_speed: Optional parameter to optimize the API call for maximum speed. When set to true,
              the API will skip time-consuming operations for faster response at the cost of
              less comprehensive data.

          timeout_ms: Optional timeout in milliseconds for the request. If the request takes longer
              than this value, it will be aborted with a 408 status code. Maximum allowed
              value is 300000ms (5 minutes).

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get(
            "/brand/retrieve-by-name",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "name": name,
                        "force_language": force_language,
                        "max_speed": max_speed,
                        "timeout_ms": timeout_ms,
                    },
                    brand_retrieve_by_name_params.BrandRetrieveByNameParams,
                ),
            ),
            cast_to=BrandRetrieveByNameResponse,
        )

    def retrieve_by_ticker(
        self,
        *,
        ticker: str,
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
        | Omit = omit,
        max_speed: bool | Omit = omit,
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
        | Omit = omit,
        timeout_ms: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> BrandRetrieveByTickerResponse:
        """Retrieve brand information using a stock ticker symbol.

        This endpoint looks up
        the company associated with the ticker and returns its brand data.

        Args:
          ticker: Stock ticker symbol to retrieve brand data for (e.g., 'AAPL', 'GOOGL', 'BRK.A').
              Must be 1-15 characters, letters/numbers/dots only.

          force_language: Optional parameter to force the language of the retrieved brand data.

          max_speed: Optional parameter to optimize the API call for maximum speed. When set to true,
              the API will skip time-consuming operations for faster response at the cost of
              less comprehensive data.

          ticker_exchange: Optional stock exchange for the ticker. Defaults to NASDAQ if not specified.

          timeout_ms: Optional timeout in milliseconds for the request. If the request takes longer
              than this value, it will be aborted with a 408 status code. Maximum allowed
              value is 300000ms (5 minutes).

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get(
            "/brand/retrieve-by-ticker",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "ticker": ticker,
                        "force_language": force_language,
                        "max_speed": max_speed,
                        "ticker_exchange": ticker_exchange,
                        "timeout_ms": timeout_ms,
                    },
                    brand_retrieve_by_ticker_params.BrandRetrieveByTickerParams,
                ),
            ),
            cast_to=BrandRetrieveByTickerResponse,
        )

    def retrieve_naics(
        self,
        *,
        input: str,
        max_results: int | Omit = omit,
        min_results: int | Omit = omit,
        timeout_ms: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> BrandRetrieveNaicsResponse:
        """
        Endpoint to classify any brand into a 2022 NAICS code.

        Args:
          input: Brand domain or title to retrieve NAICS code for. If a valid domain is provided
              in `input`, it will be used for classification, otherwise, we will search for
              the brand using the provided title.

          max_results: Maximum number of NAICS codes to return. Must be between 1 and 10. Defaults
              to 5.

          min_results: Minimum number of NAICS codes to return. Must be at least 1. Defaults to 1.

          timeout_ms: Optional timeout in milliseconds for the request. If the request takes longer
              than this value, it will be aborted with a 408 status code. Maximum allowed
              value is 300000ms (5 minutes).

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get(
            "/brand/naics",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "input": input,
                        "max_results": max_results,
                        "min_results": min_results,
                        "timeout_ms": timeout_ms,
                    },
                    brand_retrieve_naics_params.BrandRetrieveNaicsParams,
                ),
            ),
            cast_to=BrandRetrieveNaicsResponse,
        )

    def retrieve_simplified(
        self,
        *,
        domain: str,
        timeout_ms: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> BrandRetrieveSimplifiedResponse:
        """
        Returns a simplified version of brand data containing only essential
        information: domain, title, colors, logos, and backdrops. This endpoint is
        optimized for faster responses and reduced data transfer.

        Args:
          domain: Domain name to retrieve simplified brand data for

          timeout_ms: Optional timeout in milliseconds for the request. If the request takes longer
              than this value, it will be aborted with a 408 status code. Maximum allowed
              value is 300000ms (5 minutes).

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get(
            "/brand/retrieve-simplified",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "domain": domain,
                        "timeout_ms": timeout_ms,
                    },
                    brand_retrieve_simplified_params.BrandRetrieveSimplifiedParams,
                ),
            ),
            cast_to=BrandRetrieveSimplifiedResponse,
        )

    def screenshot(
        self,
        *,
        domain: str,
        full_screenshot: Literal["true", "false"] | Omit = omit,
        page: Literal["login", "signup", "blog", "careers", "pricing", "terms", "privacy", "contact"] | Omit = omit,
        prioritize: Literal["speed", "quality"] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> BrandScreenshotResponse:
        """Beta feature: Capture a screenshot of a website.

        Supports both viewport
        (standard browser view) and full-page screenshots. Can also screenshot specific
        page types (login, pricing, etc.) by using heuristics to find the appropriate
        URL. Returns a URL to the uploaded screenshot image hosted on our CDN.

        Args:
          domain: Domain name to take screenshot of (e.g., 'example.com', 'google.com'). The
              domain will be automatically normalized and validated.

          full_screenshot: Optional parameter to determine screenshot type. If 'true', takes a full page
              screenshot capturing all content. If 'false' or not provided, takes a viewport
              screenshot (standard browser view).

          page: Optional parameter to specify which page type to screenshot. If provided, the
              system will scrape the domain's links and use heuristics to find the most
              appropriate URL for the specified page type (30 supported languages). If not
              provided, screenshots the main domain landing page.

          prioritize: Optional parameter to prioritize screenshot capture. If 'speed', optimizes for
              faster capture with basic quality. If 'quality', optimizes for higher quality
              with longer wait times. Defaults to 'quality' if not provided.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get(
            "/brand/screenshot",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "domain": domain,
                        "full_screenshot": full_screenshot,
                        "page": page,
                        "prioritize": prioritize,
                    },
                    brand_screenshot_params.BrandScreenshotParams,
                ),
            ),
            cast_to=BrandScreenshotResponse,
        )

    def styleguide(
        self,
        *,
        domain: str,
        prioritize: Literal["speed", "quality"] | Omit = omit,
        timeout_ms: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> BrandStyleguideResponse:
        """
        Beta feature: Automatically extract comprehensive design system information from
        a brand's website including colors, typography, spacing, shadows, and UI
        components.

        Args:
          domain: Domain name to extract styleguide from (e.g., 'example.com', 'google.com'). The
              domain will be automatically normalized and validated.

          prioritize: Optional parameter to prioritize screenshot capture for styleguide extraction.
              If 'speed', optimizes for faster capture with basic quality. If 'quality',
              optimizes for higher quality with longer wait times. Defaults to 'quality' if
              not provided.

          timeout_ms: Optional timeout in milliseconds for the request. If the request takes longer
              than this value, it will be aborted with a 408 status code. Maximum allowed
              value is 300000ms (5 minutes).

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get(
            "/brand/styleguide",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "domain": domain,
                        "prioritize": prioritize,
                        "timeout_ms": timeout_ms,
                    },
                    brand_styleguide_params.BrandStyleguideParams,
                ),
            ),
            cast_to=BrandStyleguideResponse,
        )


class AsyncBrandResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncBrandResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/brand-dot-dev/python-sdk#accessing-raw-response-data-eg-headers
        """
        return AsyncBrandResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncBrandResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/brand-dot-dev/python-sdk#with_streaming_response
        """
        return AsyncBrandResourceWithStreamingResponse(self)

    async def retrieve(
        self,
        *,
        domain: str | Omit = omit,
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
        | Omit = omit,
        max_speed: bool | Omit = omit,
        timeout_ms: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> BrandRetrieveResponse:
        """
        Retrieve logos, backdrops, colors, industry, description, and more from any
        domain

        Args:
          domain: Domain name to retrieve brand data for (e.g., 'example.com', 'google.com').
              Cannot be used with name or ticker parameters.

          force_language: Optional parameter to force the language of the retrieved brand data. Works with
              all three lookup methods.

          max_speed: Optional parameter to optimize the API call for maximum speed. When set to true,
              the API will skip time-consuming operations for faster response at the cost of
              less comprehensive data. Works with all three lookup methods.

          timeout_ms: Optional timeout in milliseconds for the request. If the request takes longer
              than this value, it will be aborted with a 408 status code. Maximum allowed
              value is 300000ms (5 minutes).

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._get(
            "/brand/retrieve",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "domain": domain,
                        "force_language": force_language,
                        "max_speed": max_speed,
                        "timeout_ms": timeout_ms,
                    },
                    brand_retrieve_params.BrandRetrieveParams,
                ),
            ),
            cast_to=BrandRetrieveResponse,
        )

    async def ai_query(
        self,
        *,
        data_to_extract: Iterable[brand_ai_query_params.DataToExtract],
        domain: str,
        specific_pages: brand_ai_query_params.SpecificPages | Omit = omit,
        timeout_ms: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> BrandAIQueryResponse:
        """Beta feature: Use AI to extract specific data points from a brand's website.

        The
        AI will crawl the website and extract the requested information based on the
        provided data points.

        Args:
          data_to_extract: Array of data points to extract from the website

          domain: The domain name to analyze

          specific_pages: Optional object specifying which pages to analyze

          timeout_ms: Optional timeout in milliseconds for the request. If the request takes longer
              than this value, it will be aborted with a 408 status code. Maximum allowed
              value is 300000ms (5 minutes).

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/brand/ai/query",
            body=await async_maybe_transform(
                {
                    "data_to_extract": data_to_extract,
                    "domain": domain,
                    "specific_pages": specific_pages,
                    "timeout_ms": timeout_ms,
                },
                brand_ai_query_params.BrandAIQueryParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=BrandAIQueryResponse,
        )

    async def fonts(
        self,
        *,
        domain: str,
        timeout_ms: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> BrandFontsResponse:
        """
        Beta feature: Extract font information from a brand's website including font
        families, usage statistics, fallbacks, and element/word counts.

        Args:
          domain: Domain name to extract fonts from (e.g., 'example.com', 'google.com'). The
              domain will be automatically normalized and validated.

          timeout_ms: Optional timeout in milliseconds for the request. If the request takes longer
              than this value, it will be aborted with a 408 status code. Maximum allowed
              value is 300000ms (5 minutes).

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._get(
            "/brand/fonts",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "domain": domain,
                        "timeout_ms": timeout_ms,
                    },
                    brand_fonts_params.BrandFontsParams,
                ),
            ),
            cast_to=BrandFontsResponse,
        )

    async def identify_from_transaction(
        self,
        *,
        transaction_info: str,
        city: str | Omit = omit,
        country_gl: Literal[
            "ad",
            "ae",
            "af",
            "ag",
            "ai",
            "al",
            "am",
            "an",
            "ao",
            "aq",
            "ar",
            "as",
            "at",
            "au",
            "aw",
            "az",
            "ba",
            "bb",
            "bd",
            "be",
            "bf",
            "bg",
            "bh",
            "bi",
            "bj",
            "bm",
            "bn",
            "bo",
            "br",
            "bs",
            "bt",
            "bv",
            "bw",
            "by",
            "bz",
            "ca",
            "cc",
            "cd",
            "cf",
            "cg",
            "ch",
            "ci",
            "ck",
            "cl",
            "cm",
            "cn",
            "co",
            "cr",
            "cu",
            "cv",
            "cx",
            "cy",
            "cz",
            "de",
            "dj",
            "dk",
            "dm",
            "do",
            "dz",
            "ec",
            "ee",
            "eg",
            "eh",
            "er",
            "es",
            "et",
            "fi",
            "fj",
            "fk",
            "fm",
            "fo",
            "fr",
            "ga",
            "gb",
            "gd",
            "ge",
            "gf",
            "gh",
            "gi",
            "gl",
            "gm",
            "gn",
            "gp",
            "gq",
            "gr",
            "gs",
            "gt",
            "gu",
            "gw",
            "gy",
            "hk",
            "hm",
            "hn",
            "hr",
            "ht",
            "hu",
            "id",
            "ie",
            "il",
            "in",
            "io",
            "iq",
            "ir",
            "is",
            "it",
            "jm",
            "jo",
            "jp",
            "ke",
            "kg",
            "kh",
            "ki",
            "km",
            "kn",
            "kp",
            "kr",
            "kw",
            "ky",
            "kz",
            "la",
            "lb",
            "lc",
            "li",
            "lk",
            "lr",
            "ls",
            "lt",
            "lu",
            "lv",
            "ly",
            "ma",
            "mc",
            "md",
            "mg",
            "mh",
            "mk",
            "ml",
            "mm",
            "mn",
            "mo",
            "mp",
            "mq",
            "mr",
            "ms",
            "mt",
            "mu",
            "mv",
            "mw",
            "mx",
            "my",
            "mz",
            "na",
            "nc",
            "ne",
            "nf",
            "ng",
            "ni",
            "nl",
            "no",
            "np",
            "nr",
            "nu",
            "nz",
            "om",
            "pa",
            "pe",
            "pf",
            "pg",
            "ph",
            "pk",
            "pl",
            "pm",
            "pn",
            "pr",
            "ps",
            "pt",
            "pw",
            "py",
            "qa",
            "re",
            "ro",
            "rs",
            "ru",
            "rw",
            "sa",
            "sb",
            "sc",
            "sd",
            "se",
            "sg",
            "sh",
            "si",
            "sj",
            "sk",
            "sl",
            "sm",
            "sn",
            "so",
            "sr",
            "st",
            "sv",
            "sy",
            "sz",
            "tc",
            "td",
            "tf",
            "tg",
            "th",
            "tj",
            "tk",
            "tl",
            "tm",
            "tn",
            "to",
            "tr",
            "tt",
            "tv",
            "tw",
            "tz",
            "ua",
            "ug",
            "um",
            "us",
            "uy",
            "uz",
            "va",
            "vc",
            "ve",
            "vg",
            "vi",
            "vn",
            "vu",
            "wf",
            "ws",
            "ye",
            "yt",
            "za",
            "zm",
            "zw",
        ]
        | Omit = omit,
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
        | Omit = omit,
        max_speed: bool | Omit = omit,
        mcc: str | Omit = omit,
        phone: float | Omit = omit,
        timeout_ms: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> BrandIdentifyFromTransactionResponse:
        """
        Endpoint specially designed for platforms that want to identify transaction data
        by the transaction title.

        Args:
          transaction_info: Transaction information to identify the brand

          city: Optional city name to prioritize when searching for the brand.

          country_gl: Optional country code (GL parameter) to specify the country. This affects the
              geographic location used for search queries.

          force_language: Optional parameter to force the language of the retrieved brand data.

          max_speed: Optional parameter to optimize the API call for maximum speed. When set to true,
              the API will skip time-consuming operations for faster response at the cost of
              less comprehensive data.

          mcc: Optional Merchant Category Code (MCC) to help identify the business
              category/industry.

          phone: Optional phone number from the transaction to help verify brand match.

          timeout_ms: Optional timeout in milliseconds for the request. If the request takes longer
              than this value, it will be aborted with a 408 status code. Maximum allowed
              value is 300000ms (5 minutes).

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._get(
            "/brand/transaction_identifier",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "transaction_info": transaction_info,
                        "city": city,
                        "country_gl": country_gl,
                        "force_language": force_language,
                        "max_speed": max_speed,
                        "mcc": mcc,
                        "phone": phone,
                        "timeout_ms": timeout_ms,
                    },
                    brand_identify_from_transaction_params.BrandIdentifyFromTransactionParams,
                ),
            ),
            cast_to=BrandIdentifyFromTransactionResponse,
        )

    async def prefetch(
        self,
        *,
        domain: str,
        timeout_ms: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> BrandPrefetchResponse:
        """
        Signal that you may fetch brand data for a particular domain soon to improve
        latency. This endpoint does not charge credits and is available for paid
        customers to optimize future requests. [You must be on a paid plan to use this
        endpoint]

        Args:
          domain: Domain name to prefetch brand data for

          timeout_ms: Optional timeout in milliseconds for the request. If the request takes longer
              than this value, it will be aborted with a 408 status code. Maximum allowed
              value is 300000ms (5 minutes).

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/brand/prefetch",
            body=await async_maybe_transform(
                {
                    "domain": domain,
                    "timeout_ms": timeout_ms,
                },
                brand_prefetch_params.BrandPrefetchParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=BrandPrefetchResponse,
        )

    async def prefetch_by_email(
        self,
        *,
        email: str,
        timeout_ms: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> BrandPrefetchByEmailResponse:
        """
        Signal that you may fetch brand data for a particular domain soon to improve
        latency. This endpoint accepts an email address, extracts the domain from it,
        validates that it's not a disposable or free email provider, and queues the
        domain for prefetching. This endpoint does not charge credits and is available
        for paid customers to optimize future requests. [You must be on a paid plan to
        use this endpoint]

        Args:
          email: Email address to prefetch brand data for. The domain will be extracted from the
              email. Free email providers (gmail.com, yahoo.com, etc.) and disposable email
              addresses are not allowed.

          timeout_ms: Optional timeout in milliseconds for the request. If the request takes longer
              than this value, it will be aborted with a 408 status code. Maximum allowed
              value is 300000ms (5 minutes).

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/brand/prefetch-by-email",
            body=await async_maybe_transform(
                {
                    "email": email,
                    "timeout_ms": timeout_ms,
                },
                brand_prefetch_by_email_params.BrandPrefetchByEmailParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=BrandPrefetchByEmailResponse,
        )

    async def retrieve_by_email(
        self,
        *,
        email: str,
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
        | Omit = omit,
        max_speed: bool | Omit = omit,
        timeout_ms: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> BrandRetrieveByEmailResponse:
        """
        Retrieve brand information using an email address while detecting disposable and
        free email addresses. This endpoint extracts the domain from the email address
        and returns brand data for that domain. Disposable and free email addresses
        (like gmail.com, yahoo.com) will throw a 422 error.

        Args:
          email: Email address to retrieve brand data for (e.g., 'contact@example.com'). The
              domain will be extracted from the email. Free email providers (gmail.com,
              yahoo.com, etc.) and disposable email addresses are not allowed.

          force_language: Optional parameter to force the language of the retrieved brand data.

          max_speed: Optional parameter to optimize the API call for maximum speed. When set to true,
              the API will skip time-consuming operations for faster response at the cost of
              less comprehensive data.

          timeout_ms: Optional timeout in milliseconds for the request. If the request takes longer
              than this value, it will be aborted with a 408 status code. Maximum allowed
              value is 300000ms (5 minutes).

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._get(
            "/brand/retrieve-by-email",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "email": email,
                        "force_language": force_language,
                        "max_speed": max_speed,
                        "timeout_ms": timeout_ms,
                    },
                    brand_retrieve_by_email_params.BrandRetrieveByEmailParams,
                ),
            ),
            cast_to=BrandRetrieveByEmailResponse,
        )

    async def retrieve_by_isin(
        self,
        *,
        isin: str,
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
        | Omit = omit,
        max_speed: bool | Omit = omit,
        timeout_ms: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> BrandRetrieveByIsinResponse:
        """
        Retrieve brand information using an ISIN (International Securities
        Identification Number). This endpoint looks up the company associated with the
        ISIN and returns its brand data.

        Args:
          isin: ISIN (International Securities Identification Number) to retrieve brand data for
              (e.g., 'AU000000IMD5', 'US0378331005'). Must be exactly 12 characters: 2 letters
              followed by 9 alphanumeric characters and ending with a digit.

          force_language: Optional parameter to force the language of the retrieved brand data.

          max_speed: Optional parameter to optimize the API call for maximum speed. When set to true,
              the API will skip time-consuming operations for faster response at the cost of
              less comprehensive data.

          timeout_ms: Optional timeout in milliseconds for the request. If the request takes longer
              than this value, it will be aborted with a 408 status code. Maximum allowed
              value is 300000ms (5 minutes).

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._get(
            "/brand/retrieve-by-isin",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "isin": isin,
                        "force_language": force_language,
                        "max_speed": max_speed,
                        "timeout_ms": timeout_ms,
                    },
                    brand_retrieve_by_isin_params.BrandRetrieveByIsinParams,
                ),
            ),
            cast_to=BrandRetrieveByIsinResponse,
        )

    async def retrieve_by_name(
        self,
        *,
        name: str,
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
        | Omit = omit,
        max_speed: bool | Omit = omit,
        timeout_ms: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> BrandRetrieveByNameResponse:
        """Retrieve brand information using a company name.

        This endpoint searches for the
        company by name and returns its brand data.

        Args:
          name: Company name to retrieve brand data for (e.g., 'Apple Inc', 'Microsoft
              Corporation'). Must be 3-30 characters.

          force_language: Optional parameter to force the language of the retrieved brand data.

          max_speed: Optional parameter to optimize the API call for maximum speed. When set to true,
              the API will skip time-consuming operations for faster response at the cost of
              less comprehensive data.

          timeout_ms: Optional timeout in milliseconds for the request. If the request takes longer
              than this value, it will be aborted with a 408 status code. Maximum allowed
              value is 300000ms (5 minutes).

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._get(
            "/brand/retrieve-by-name",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "name": name,
                        "force_language": force_language,
                        "max_speed": max_speed,
                        "timeout_ms": timeout_ms,
                    },
                    brand_retrieve_by_name_params.BrandRetrieveByNameParams,
                ),
            ),
            cast_to=BrandRetrieveByNameResponse,
        )

    async def retrieve_by_ticker(
        self,
        *,
        ticker: str,
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
        | Omit = omit,
        max_speed: bool | Omit = omit,
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
        | Omit = omit,
        timeout_ms: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> BrandRetrieveByTickerResponse:
        """Retrieve brand information using a stock ticker symbol.

        This endpoint looks up
        the company associated with the ticker and returns its brand data.

        Args:
          ticker: Stock ticker symbol to retrieve brand data for (e.g., 'AAPL', 'GOOGL', 'BRK.A').
              Must be 1-15 characters, letters/numbers/dots only.

          force_language: Optional parameter to force the language of the retrieved brand data.

          max_speed: Optional parameter to optimize the API call for maximum speed. When set to true,
              the API will skip time-consuming operations for faster response at the cost of
              less comprehensive data.

          ticker_exchange: Optional stock exchange for the ticker. Defaults to NASDAQ if not specified.

          timeout_ms: Optional timeout in milliseconds for the request. If the request takes longer
              than this value, it will be aborted with a 408 status code. Maximum allowed
              value is 300000ms (5 minutes).

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._get(
            "/brand/retrieve-by-ticker",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "ticker": ticker,
                        "force_language": force_language,
                        "max_speed": max_speed,
                        "ticker_exchange": ticker_exchange,
                        "timeout_ms": timeout_ms,
                    },
                    brand_retrieve_by_ticker_params.BrandRetrieveByTickerParams,
                ),
            ),
            cast_to=BrandRetrieveByTickerResponse,
        )

    async def retrieve_naics(
        self,
        *,
        input: str,
        max_results: int | Omit = omit,
        min_results: int | Omit = omit,
        timeout_ms: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> BrandRetrieveNaicsResponse:
        """
        Endpoint to classify any brand into a 2022 NAICS code.

        Args:
          input: Brand domain or title to retrieve NAICS code for. If a valid domain is provided
              in `input`, it will be used for classification, otherwise, we will search for
              the brand using the provided title.

          max_results: Maximum number of NAICS codes to return. Must be between 1 and 10. Defaults
              to 5.

          min_results: Minimum number of NAICS codes to return. Must be at least 1. Defaults to 1.

          timeout_ms: Optional timeout in milliseconds for the request. If the request takes longer
              than this value, it will be aborted with a 408 status code. Maximum allowed
              value is 300000ms (5 minutes).

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._get(
            "/brand/naics",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "input": input,
                        "max_results": max_results,
                        "min_results": min_results,
                        "timeout_ms": timeout_ms,
                    },
                    brand_retrieve_naics_params.BrandRetrieveNaicsParams,
                ),
            ),
            cast_to=BrandRetrieveNaicsResponse,
        )

    async def retrieve_simplified(
        self,
        *,
        domain: str,
        timeout_ms: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> BrandRetrieveSimplifiedResponse:
        """
        Returns a simplified version of brand data containing only essential
        information: domain, title, colors, logos, and backdrops. This endpoint is
        optimized for faster responses and reduced data transfer.

        Args:
          domain: Domain name to retrieve simplified brand data for

          timeout_ms: Optional timeout in milliseconds for the request. If the request takes longer
              than this value, it will be aborted with a 408 status code. Maximum allowed
              value is 300000ms (5 minutes).

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._get(
            "/brand/retrieve-simplified",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "domain": domain,
                        "timeout_ms": timeout_ms,
                    },
                    brand_retrieve_simplified_params.BrandRetrieveSimplifiedParams,
                ),
            ),
            cast_to=BrandRetrieveSimplifiedResponse,
        )

    async def screenshot(
        self,
        *,
        domain: str,
        full_screenshot: Literal["true", "false"] | Omit = omit,
        page: Literal["login", "signup", "blog", "careers", "pricing", "terms", "privacy", "contact"] | Omit = omit,
        prioritize: Literal["speed", "quality"] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> BrandScreenshotResponse:
        """Beta feature: Capture a screenshot of a website.

        Supports both viewport
        (standard browser view) and full-page screenshots. Can also screenshot specific
        page types (login, pricing, etc.) by using heuristics to find the appropriate
        URL. Returns a URL to the uploaded screenshot image hosted on our CDN.

        Args:
          domain: Domain name to take screenshot of (e.g., 'example.com', 'google.com'). The
              domain will be automatically normalized and validated.

          full_screenshot: Optional parameter to determine screenshot type. If 'true', takes a full page
              screenshot capturing all content. If 'false' or not provided, takes a viewport
              screenshot (standard browser view).

          page: Optional parameter to specify which page type to screenshot. If provided, the
              system will scrape the domain's links and use heuristics to find the most
              appropriate URL for the specified page type (30 supported languages). If not
              provided, screenshots the main domain landing page.

          prioritize: Optional parameter to prioritize screenshot capture. If 'speed', optimizes for
              faster capture with basic quality. If 'quality', optimizes for higher quality
              with longer wait times. Defaults to 'quality' if not provided.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._get(
            "/brand/screenshot",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "domain": domain,
                        "full_screenshot": full_screenshot,
                        "page": page,
                        "prioritize": prioritize,
                    },
                    brand_screenshot_params.BrandScreenshotParams,
                ),
            ),
            cast_to=BrandScreenshotResponse,
        )

    async def styleguide(
        self,
        *,
        domain: str,
        prioritize: Literal["speed", "quality"] | Omit = omit,
        timeout_ms: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> BrandStyleguideResponse:
        """
        Beta feature: Automatically extract comprehensive design system information from
        a brand's website including colors, typography, spacing, shadows, and UI
        components.

        Args:
          domain: Domain name to extract styleguide from (e.g., 'example.com', 'google.com'). The
              domain will be automatically normalized and validated.

          prioritize: Optional parameter to prioritize screenshot capture for styleguide extraction.
              If 'speed', optimizes for faster capture with basic quality. If 'quality',
              optimizes for higher quality with longer wait times. Defaults to 'quality' if
              not provided.

          timeout_ms: Optional timeout in milliseconds for the request. If the request takes longer
              than this value, it will be aborted with a 408 status code. Maximum allowed
              value is 300000ms (5 minutes).

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._get(
            "/brand/styleguide",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "domain": domain,
                        "prioritize": prioritize,
                        "timeout_ms": timeout_ms,
                    },
                    brand_styleguide_params.BrandStyleguideParams,
                ),
            ),
            cast_to=BrandStyleguideResponse,
        )


class BrandResourceWithRawResponse:
    def __init__(self, brand: BrandResource) -> None:
        self._brand = brand

        self.retrieve = to_raw_response_wrapper(
            brand.retrieve,
        )
        self.ai_query = to_raw_response_wrapper(
            brand.ai_query,
        )
        self.fonts = to_raw_response_wrapper(
            brand.fonts,
        )
        self.identify_from_transaction = to_raw_response_wrapper(
            brand.identify_from_transaction,
        )
        self.prefetch = to_raw_response_wrapper(
            brand.prefetch,
        )
        self.prefetch_by_email = to_raw_response_wrapper(
            brand.prefetch_by_email,
        )
        self.retrieve_by_email = to_raw_response_wrapper(
            brand.retrieve_by_email,
        )
        self.retrieve_by_isin = to_raw_response_wrapper(
            brand.retrieve_by_isin,
        )
        self.retrieve_by_name = to_raw_response_wrapper(
            brand.retrieve_by_name,
        )
        self.retrieve_by_ticker = to_raw_response_wrapper(
            brand.retrieve_by_ticker,
        )
        self.retrieve_naics = to_raw_response_wrapper(
            brand.retrieve_naics,
        )
        self.retrieve_simplified = to_raw_response_wrapper(
            brand.retrieve_simplified,
        )
        self.screenshot = to_raw_response_wrapper(
            brand.screenshot,
        )
        self.styleguide = to_raw_response_wrapper(
            brand.styleguide,
        )


class AsyncBrandResourceWithRawResponse:
    def __init__(self, brand: AsyncBrandResource) -> None:
        self._brand = brand

        self.retrieve = async_to_raw_response_wrapper(
            brand.retrieve,
        )
        self.ai_query = async_to_raw_response_wrapper(
            brand.ai_query,
        )
        self.fonts = async_to_raw_response_wrapper(
            brand.fonts,
        )
        self.identify_from_transaction = async_to_raw_response_wrapper(
            brand.identify_from_transaction,
        )
        self.prefetch = async_to_raw_response_wrapper(
            brand.prefetch,
        )
        self.prefetch_by_email = async_to_raw_response_wrapper(
            brand.prefetch_by_email,
        )
        self.retrieve_by_email = async_to_raw_response_wrapper(
            brand.retrieve_by_email,
        )
        self.retrieve_by_isin = async_to_raw_response_wrapper(
            brand.retrieve_by_isin,
        )
        self.retrieve_by_name = async_to_raw_response_wrapper(
            brand.retrieve_by_name,
        )
        self.retrieve_by_ticker = async_to_raw_response_wrapper(
            brand.retrieve_by_ticker,
        )
        self.retrieve_naics = async_to_raw_response_wrapper(
            brand.retrieve_naics,
        )
        self.retrieve_simplified = async_to_raw_response_wrapper(
            brand.retrieve_simplified,
        )
        self.screenshot = async_to_raw_response_wrapper(
            brand.screenshot,
        )
        self.styleguide = async_to_raw_response_wrapper(
            brand.styleguide,
        )


class BrandResourceWithStreamingResponse:
    def __init__(self, brand: BrandResource) -> None:
        self._brand = brand

        self.retrieve = to_streamed_response_wrapper(
            brand.retrieve,
        )
        self.ai_query = to_streamed_response_wrapper(
            brand.ai_query,
        )
        self.fonts = to_streamed_response_wrapper(
            brand.fonts,
        )
        self.identify_from_transaction = to_streamed_response_wrapper(
            brand.identify_from_transaction,
        )
        self.prefetch = to_streamed_response_wrapper(
            brand.prefetch,
        )
        self.prefetch_by_email = to_streamed_response_wrapper(
            brand.prefetch_by_email,
        )
        self.retrieve_by_email = to_streamed_response_wrapper(
            brand.retrieve_by_email,
        )
        self.retrieve_by_isin = to_streamed_response_wrapper(
            brand.retrieve_by_isin,
        )
        self.retrieve_by_name = to_streamed_response_wrapper(
            brand.retrieve_by_name,
        )
        self.retrieve_by_ticker = to_streamed_response_wrapper(
            brand.retrieve_by_ticker,
        )
        self.retrieve_naics = to_streamed_response_wrapper(
            brand.retrieve_naics,
        )
        self.retrieve_simplified = to_streamed_response_wrapper(
            brand.retrieve_simplified,
        )
        self.screenshot = to_streamed_response_wrapper(
            brand.screenshot,
        )
        self.styleguide = to_streamed_response_wrapper(
            brand.styleguide,
        )


class AsyncBrandResourceWithStreamingResponse:
    def __init__(self, brand: AsyncBrandResource) -> None:
        self._brand = brand

        self.retrieve = async_to_streamed_response_wrapper(
            brand.retrieve,
        )
        self.ai_query = async_to_streamed_response_wrapper(
            brand.ai_query,
        )
        self.fonts = async_to_streamed_response_wrapper(
            brand.fonts,
        )
        self.identify_from_transaction = async_to_streamed_response_wrapper(
            brand.identify_from_transaction,
        )
        self.prefetch = async_to_streamed_response_wrapper(
            brand.prefetch,
        )
        self.prefetch_by_email = async_to_streamed_response_wrapper(
            brand.prefetch_by_email,
        )
        self.retrieve_by_email = async_to_streamed_response_wrapper(
            brand.retrieve_by_email,
        )
        self.retrieve_by_isin = async_to_streamed_response_wrapper(
            brand.retrieve_by_isin,
        )
        self.retrieve_by_name = async_to_streamed_response_wrapper(
            brand.retrieve_by_name,
        )
        self.retrieve_by_ticker = async_to_streamed_response_wrapper(
            brand.retrieve_by_ticker,
        )
        self.retrieve_naics = async_to_streamed_response_wrapper(
            brand.retrieve_naics,
        )
        self.retrieve_simplified = async_to_streamed_response_wrapper(
            brand.retrieve_simplified,
        )
        self.screenshot = async_to_streamed_response_wrapper(
            brand.screenshot,
        )
        self.styleguide = async_to_streamed_response_wrapper(
            brand.styleguide,
        )
