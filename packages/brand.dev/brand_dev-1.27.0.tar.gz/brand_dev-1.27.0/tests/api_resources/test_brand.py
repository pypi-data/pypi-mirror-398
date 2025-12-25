# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from brand.dev import BrandDev, AsyncBrandDev
from tests.utils import assert_matches_type
from brand.dev.types import (
    BrandFontsResponse,
    BrandAIQueryResponse,
    BrandPrefetchResponse,
    BrandRetrieveResponse,
    BrandScreenshotResponse,
    BrandStyleguideResponse,
    BrandRetrieveNaicsResponse,
    BrandRetrieveByIsinResponse,
    BrandRetrieveByNameResponse,
    BrandPrefetchByEmailResponse,
    BrandRetrieveByEmailResponse,
    BrandRetrieveByTickerResponse,
    BrandRetrieveSimplifiedResponse,
    BrandIdentifyFromTransactionResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestBrand:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve(self, client: BrandDev) -> None:
        brand = client.brand.retrieve()
        assert_matches_type(BrandRetrieveResponse, brand, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve_with_all_params(self, client: BrandDev) -> None:
        brand = client.brand.retrieve(
            domain="domain",
            force_language="albanian",
            max_speed=True,
            timeout_ms=1,
        )
        assert_matches_type(BrandRetrieveResponse, brand, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve(self, client: BrandDev) -> None:
        response = client.brand.with_raw_response.retrieve()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        brand = response.parse()
        assert_matches_type(BrandRetrieveResponse, brand, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve(self, client: BrandDev) -> None:
        with client.brand.with_streaming_response.retrieve() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            brand = response.parse()
            assert_matches_type(BrandRetrieveResponse, brand, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_ai_query(self, client: BrandDev) -> None:
        brand = client.brand.ai_query(
            data_to_extract=[
                {
                    "datapoint_description": "datapoint_description",
                    "datapoint_example": "datapoint_example",
                    "datapoint_name": "datapoint_name",
                    "datapoint_type": "text",
                }
            ],
            domain="domain",
        )
        assert_matches_type(BrandAIQueryResponse, brand, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_ai_query_with_all_params(self, client: BrandDev) -> None:
        brand = client.brand.ai_query(
            data_to_extract=[
                {
                    "datapoint_description": "datapoint_description",
                    "datapoint_example": "datapoint_example",
                    "datapoint_name": "datapoint_name",
                    "datapoint_type": "text",
                    "datapoint_list_type": "string",
                    "datapoint_object_schema": {
                        "testimonial_text": "string",
                        "testimonial_author": "string",
                    },
                }
            ],
            domain="domain",
            specific_pages={
                "about_us": True,
                "blog": True,
                "careers": True,
                "contact_us": True,
                "faq": True,
                "home_page": True,
                "pricing": True,
                "privacy_policy": True,
                "terms_and_conditions": True,
            },
            timeout_ms=1,
        )
        assert_matches_type(BrandAIQueryResponse, brand, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_ai_query(self, client: BrandDev) -> None:
        response = client.brand.with_raw_response.ai_query(
            data_to_extract=[
                {
                    "datapoint_description": "datapoint_description",
                    "datapoint_example": "datapoint_example",
                    "datapoint_name": "datapoint_name",
                    "datapoint_type": "text",
                }
            ],
            domain="domain",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        brand = response.parse()
        assert_matches_type(BrandAIQueryResponse, brand, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_ai_query(self, client: BrandDev) -> None:
        with client.brand.with_streaming_response.ai_query(
            data_to_extract=[
                {
                    "datapoint_description": "datapoint_description",
                    "datapoint_example": "datapoint_example",
                    "datapoint_name": "datapoint_name",
                    "datapoint_type": "text",
                }
            ],
            domain="domain",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            brand = response.parse()
            assert_matches_type(BrandAIQueryResponse, brand, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_fonts(self, client: BrandDev) -> None:
        brand = client.brand.fonts(
            domain="domain",
        )
        assert_matches_type(BrandFontsResponse, brand, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_fonts_with_all_params(self, client: BrandDev) -> None:
        brand = client.brand.fonts(
            domain="domain",
            timeout_ms=1,
        )
        assert_matches_type(BrandFontsResponse, brand, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_fonts(self, client: BrandDev) -> None:
        response = client.brand.with_raw_response.fonts(
            domain="domain",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        brand = response.parse()
        assert_matches_type(BrandFontsResponse, brand, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_fonts(self, client: BrandDev) -> None:
        with client.brand.with_streaming_response.fonts(
            domain="domain",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            brand = response.parse()
            assert_matches_type(BrandFontsResponse, brand, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_identify_from_transaction(self, client: BrandDev) -> None:
        brand = client.brand.identify_from_transaction(
            transaction_info="transaction_info",
        )
        assert_matches_type(BrandIdentifyFromTransactionResponse, brand, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_identify_from_transaction_with_all_params(self, client: BrandDev) -> None:
        brand = client.brand.identify_from_transaction(
            transaction_info="transaction_info",
            city="city",
            country_gl="ad",
            force_language="albanian",
            max_speed=True,
            mcc="mcc",
            phone=0,
            timeout_ms=1,
        )
        assert_matches_type(BrandIdentifyFromTransactionResponse, brand, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_identify_from_transaction(self, client: BrandDev) -> None:
        response = client.brand.with_raw_response.identify_from_transaction(
            transaction_info="transaction_info",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        brand = response.parse()
        assert_matches_type(BrandIdentifyFromTransactionResponse, brand, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_identify_from_transaction(self, client: BrandDev) -> None:
        with client.brand.with_streaming_response.identify_from_transaction(
            transaction_info="transaction_info",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            brand = response.parse()
            assert_matches_type(BrandIdentifyFromTransactionResponse, brand, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_prefetch(self, client: BrandDev) -> None:
        brand = client.brand.prefetch(
            domain="domain",
        )
        assert_matches_type(BrandPrefetchResponse, brand, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_prefetch_with_all_params(self, client: BrandDev) -> None:
        brand = client.brand.prefetch(
            domain="domain",
            timeout_ms=1,
        )
        assert_matches_type(BrandPrefetchResponse, brand, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_prefetch(self, client: BrandDev) -> None:
        response = client.brand.with_raw_response.prefetch(
            domain="domain",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        brand = response.parse()
        assert_matches_type(BrandPrefetchResponse, brand, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_prefetch(self, client: BrandDev) -> None:
        with client.brand.with_streaming_response.prefetch(
            domain="domain",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            brand = response.parse()
            assert_matches_type(BrandPrefetchResponse, brand, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_prefetch_by_email(self, client: BrandDev) -> None:
        brand = client.brand.prefetch_by_email(
            email="dev@stainless.com",
        )
        assert_matches_type(BrandPrefetchByEmailResponse, brand, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_prefetch_by_email_with_all_params(self, client: BrandDev) -> None:
        brand = client.brand.prefetch_by_email(
            email="dev@stainless.com",
            timeout_ms=1,
        )
        assert_matches_type(BrandPrefetchByEmailResponse, brand, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_prefetch_by_email(self, client: BrandDev) -> None:
        response = client.brand.with_raw_response.prefetch_by_email(
            email="dev@stainless.com",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        brand = response.parse()
        assert_matches_type(BrandPrefetchByEmailResponse, brand, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_prefetch_by_email(self, client: BrandDev) -> None:
        with client.brand.with_streaming_response.prefetch_by_email(
            email="dev@stainless.com",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            brand = response.parse()
            assert_matches_type(BrandPrefetchByEmailResponse, brand, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve_by_email(self, client: BrandDev) -> None:
        brand = client.brand.retrieve_by_email(
            email="dev@stainless.com",
        )
        assert_matches_type(BrandRetrieveByEmailResponse, brand, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve_by_email_with_all_params(self, client: BrandDev) -> None:
        brand = client.brand.retrieve_by_email(
            email="dev@stainless.com",
            force_language="albanian",
            max_speed=True,
            timeout_ms=1,
        )
        assert_matches_type(BrandRetrieveByEmailResponse, brand, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve_by_email(self, client: BrandDev) -> None:
        response = client.brand.with_raw_response.retrieve_by_email(
            email="dev@stainless.com",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        brand = response.parse()
        assert_matches_type(BrandRetrieveByEmailResponse, brand, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve_by_email(self, client: BrandDev) -> None:
        with client.brand.with_streaming_response.retrieve_by_email(
            email="dev@stainless.com",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            brand = response.parse()
            assert_matches_type(BrandRetrieveByEmailResponse, brand, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve_by_isin(self, client: BrandDev) -> None:
        brand = client.brand.retrieve_by_isin(
            isin="SE60513A9993",
        )
        assert_matches_type(BrandRetrieveByIsinResponse, brand, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve_by_isin_with_all_params(self, client: BrandDev) -> None:
        brand = client.brand.retrieve_by_isin(
            isin="SE60513A9993",
            force_language="albanian",
            max_speed=True,
            timeout_ms=1,
        )
        assert_matches_type(BrandRetrieveByIsinResponse, brand, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve_by_isin(self, client: BrandDev) -> None:
        response = client.brand.with_raw_response.retrieve_by_isin(
            isin="SE60513A9993",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        brand = response.parse()
        assert_matches_type(BrandRetrieveByIsinResponse, brand, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve_by_isin(self, client: BrandDev) -> None:
        with client.brand.with_streaming_response.retrieve_by_isin(
            isin="SE60513A9993",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            brand = response.parse()
            assert_matches_type(BrandRetrieveByIsinResponse, brand, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve_by_name(self, client: BrandDev) -> None:
        brand = client.brand.retrieve_by_name(
            name="xxx",
        )
        assert_matches_type(BrandRetrieveByNameResponse, brand, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve_by_name_with_all_params(self, client: BrandDev) -> None:
        brand = client.brand.retrieve_by_name(
            name="xxx",
            force_language="albanian",
            max_speed=True,
            timeout_ms=1,
        )
        assert_matches_type(BrandRetrieveByNameResponse, brand, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve_by_name(self, client: BrandDev) -> None:
        response = client.brand.with_raw_response.retrieve_by_name(
            name="xxx",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        brand = response.parse()
        assert_matches_type(BrandRetrieveByNameResponse, brand, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve_by_name(self, client: BrandDev) -> None:
        with client.brand.with_streaming_response.retrieve_by_name(
            name="xxx",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            brand = response.parse()
            assert_matches_type(BrandRetrieveByNameResponse, brand, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve_by_ticker(self, client: BrandDev) -> None:
        brand = client.brand.retrieve_by_ticker(
            ticker="ticker",
        )
        assert_matches_type(BrandRetrieveByTickerResponse, brand, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve_by_ticker_with_all_params(self, client: BrandDev) -> None:
        brand = client.brand.retrieve_by_ticker(
            ticker="ticker",
            force_language="albanian",
            max_speed=True,
            ticker_exchange="AMEX",
            timeout_ms=1,
        )
        assert_matches_type(BrandRetrieveByTickerResponse, brand, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve_by_ticker(self, client: BrandDev) -> None:
        response = client.brand.with_raw_response.retrieve_by_ticker(
            ticker="ticker",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        brand = response.parse()
        assert_matches_type(BrandRetrieveByTickerResponse, brand, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve_by_ticker(self, client: BrandDev) -> None:
        with client.brand.with_streaming_response.retrieve_by_ticker(
            ticker="ticker",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            brand = response.parse()
            assert_matches_type(BrandRetrieveByTickerResponse, brand, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve_naics(self, client: BrandDev) -> None:
        brand = client.brand.retrieve_naics(
            input="input",
        )
        assert_matches_type(BrandRetrieveNaicsResponse, brand, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve_naics_with_all_params(self, client: BrandDev) -> None:
        brand = client.brand.retrieve_naics(
            input="input",
            max_results=1,
            min_results=1,
            timeout_ms=1,
        )
        assert_matches_type(BrandRetrieveNaicsResponse, brand, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve_naics(self, client: BrandDev) -> None:
        response = client.brand.with_raw_response.retrieve_naics(
            input="input",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        brand = response.parse()
        assert_matches_type(BrandRetrieveNaicsResponse, brand, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve_naics(self, client: BrandDev) -> None:
        with client.brand.with_streaming_response.retrieve_naics(
            input="input",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            brand = response.parse()
            assert_matches_type(BrandRetrieveNaicsResponse, brand, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve_simplified(self, client: BrandDev) -> None:
        brand = client.brand.retrieve_simplified(
            domain="domain",
        )
        assert_matches_type(BrandRetrieveSimplifiedResponse, brand, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve_simplified_with_all_params(self, client: BrandDev) -> None:
        brand = client.brand.retrieve_simplified(
            domain="domain",
            timeout_ms=1,
        )
        assert_matches_type(BrandRetrieveSimplifiedResponse, brand, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve_simplified(self, client: BrandDev) -> None:
        response = client.brand.with_raw_response.retrieve_simplified(
            domain="domain",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        brand = response.parse()
        assert_matches_type(BrandRetrieveSimplifiedResponse, brand, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve_simplified(self, client: BrandDev) -> None:
        with client.brand.with_streaming_response.retrieve_simplified(
            domain="domain",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            brand = response.parse()
            assert_matches_type(BrandRetrieveSimplifiedResponse, brand, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_screenshot(self, client: BrandDev) -> None:
        brand = client.brand.screenshot(
            domain="domain",
        )
        assert_matches_type(BrandScreenshotResponse, brand, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_screenshot_with_all_params(self, client: BrandDev) -> None:
        brand = client.brand.screenshot(
            domain="domain",
            full_screenshot="true",
            page="login",
            prioritize="speed",
        )
        assert_matches_type(BrandScreenshotResponse, brand, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_screenshot(self, client: BrandDev) -> None:
        response = client.brand.with_raw_response.screenshot(
            domain="domain",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        brand = response.parse()
        assert_matches_type(BrandScreenshotResponse, brand, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_screenshot(self, client: BrandDev) -> None:
        with client.brand.with_streaming_response.screenshot(
            domain="domain",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            brand = response.parse()
            assert_matches_type(BrandScreenshotResponse, brand, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_styleguide(self, client: BrandDev) -> None:
        brand = client.brand.styleguide(
            domain="domain",
        )
        assert_matches_type(BrandStyleguideResponse, brand, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_styleguide_with_all_params(self, client: BrandDev) -> None:
        brand = client.brand.styleguide(
            domain="domain",
            prioritize="speed",
            timeout_ms=1,
        )
        assert_matches_type(BrandStyleguideResponse, brand, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_styleguide(self, client: BrandDev) -> None:
        response = client.brand.with_raw_response.styleguide(
            domain="domain",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        brand = response.parse()
        assert_matches_type(BrandStyleguideResponse, brand, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_styleguide(self, client: BrandDev) -> None:
        with client.brand.with_streaming_response.styleguide(
            domain="domain",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            brand = response.parse()
            assert_matches_type(BrandStyleguideResponse, brand, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncBrand:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve(self, async_client: AsyncBrandDev) -> None:
        brand = await async_client.brand.retrieve()
        assert_matches_type(BrandRetrieveResponse, brand, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve_with_all_params(self, async_client: AsyncBrandDev) -> None:
        brand = await async_client.brand.retrieve(
            domain="domain",
            force_language="albanian",
            max_speed=True,
            timeout_ms=1,
        )
        assert_matches_type(BrandRetrieveResponse, brand, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncBrandDev) -> None:
        response = await async_client.brand.with_raw_response.retrieve()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        brand = await response.parse()
        assert_matches_type(BrandRetrieveResponse, brand, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncBrandDev) -> None:
        async with async_client.brand.with_streaming_response.retrieve() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            brand = await response.parse()
            assert_matches_type(BrandRetrieveResponse, brand, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_ai_query(self, async_client: AsyncBrandDev) -> None:
        brand = await async_client.brand.ai_query(
            data_to_extract=[
                {
                    "datapoint_description": "datapoint_description",
                    "datapoint_example": "datapoint_example",
                    "datapoint_name": "datapoint_name",
                    "datapoint_type": "text",
                }
            ],
            domain="domain",
        )
        assert_matches_type(BrandAIQueryResponse, brand, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_ai_query_with_all_params(self, async_client: AsyncBrandDev) -> None:
        brand = await async_client.brand.ai_query(
            data_to_extract=[
                {
                    "datapoint_description": "datapoint_description",
                    "datapoint_example": "datapoint_example",
                    "datapoint_name": "datapoint_name",
                    "datapoint_type": "text",
                    "datapoint_list_type": "string",
                    "datapoint_object_schema": {
                        "testimonial_text": "string",
                        "testimonial_author": "string",
                    },
                }
            ],
            domain="domain",
            specific_pages={
                "about_us": True,
                "blog": True,
                "careers": True,
                "contact_us": True,
                "faq": True,
                "home_page": True,
                "pricing": True,
                "privacy_policy": True,
                "terms_and_conditions": True,
            },
            timeout_ms=1,
        )
        assert_matches_type(BrandAIQueryResponse, brand, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_ai_query(self, async_client: AsyncBrandDev) -> None:
        response = await async_client.brand.with_raw_response.ai_query(
            data_to_extract=[
                {
                    "datapoint_description": "datapoint_description",
                    "datapoint_example": "datapoint_example",
                    "datapoint_name": "datapoint_name",
                    "datapoint_type": "text",
                }
            ],
            domain="domain",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        brand = await response.parse()
        assert_matches_type(BrandAIQueryResponse, brand, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_ai_query(self, async_client: AsyncBrandDev) -> None:
        async with async_client.brand.with_streaming_response.ai_query(
            data_to_extract=[
                {
                    "datapoint_description": "datapoint_description",
                    "datapoint_example": "datapoint_example",
                    "datapoint_name": "datapoint_name",
                    "datapoint_type": "text",
                }
            ],
            domain="domain",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            brand = await response.parse()
            assert_matches_type(BrandAIQueryResponse, brand, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_fonts(self, async_client: AsyncBrandDev) -> None:
        brand = await async_client.brand.fonts(
            domain="domain",
        )
        assert_matches_type(BrandFontsResponse, brand, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_fonts_with_all_params(self, async_client: AsyncBrandDev) -> None:
        brand = await async_client.brand.fonts(
            domain="domain",
            timeout_ms=1,
        )
        assert_matches_type(BrandFontsResponse, brand, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_fonts(self, async_client: AsyncBrandDev) -> None:
        response = await async_client.brand.with_raw_response.fonts(
            domain="domain",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        brand = await response.parse()
        assert_matches_type(BrandFontsResponse, brand, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_fonts(self, async_client: AsyncBrandDev) -> None:
        async with async_client.brand.with_streaming_response.fonts(
            domain="domain",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            brand = await response.parse()
            assert_matches_type(BrandFontsResponse, brand, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_identify_from_transaction(self, async_client: AsyncBrandDev) -> None:
        brand = await async_client.brand.identify_from_transaction(
            transaction_info="transaction_info",
        )
        assert_matches_type(BrandIdentifyFromTransactionResponse, brand, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_identify_from_transaction_with_all_params(self, async_client: AsyncBrandDev) -> None:
        brand = await async_client.brand.identify_from_transaction(
            transaction_info="transaction_info",
            city="city",
            country_gl="ad",
            force_language="albanian",
            max_speed=True,
            mcc="mcc",
            phone=0,
            timeout_ms=1,
        )
        assert_matches_type(BrandIdentifyFromTransactionResponse, brand, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_identify_from_transaction(self, async_client: AsyncBrandDev) -> None:
        response = await async_client.brand.with_raw_response.identify_from_transaction(
            transaction_info="transaction_info",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        brand = await response.parse()
        assert_matches_type(BrandIdentifyFromTransactionResponse, brand, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_identify_from_transaction(self, async_client: AsyncBrandDev) -> None:
        async with async_client.brand.with_streaming_response.identify_from_transaction(
            transaction_info="transaction_info",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            brand = await response.parse()
            assert_matches_type(BrandIdentifyFromTransactionResponse, brand, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_prefetch(self, async_client: AsyncBrandDev) -> None:
        brand = await async_client.brand.prefetch(
            domain="domain",
        )
        assert_matches_type(BrandPrefetchResponse, brand, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_prefetch_with_all_params(self, async_client: AsyncBrandDev) -> None:
        brand = await async_client.brand.prefetch(
            domain="domain",
            timeout_ms=1,
        )
        assert_matches_type(BrandPrefetchResponse, brand, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_prefetch(self, async_client: AsyncBrandDev) -> None:
        response = await async_client.brand.with_raw_response.prefetch(
            domain="domain",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        brand = await response.parse()
        assert_matches_type(BrandPrefetchResponse, brand, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_prefetch(self, async_client: AsyncBrandDev) -> None:
        async with async_client.brand.with_streaming_response.prefetch(
            domain="domain",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            brand = await response.parse()
            assert_matches_type(BrandPrefetchResponse, brand, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_prefetch_by_email(self, async_client: AsyncBrandDev) -> None:
        brand = await async_client.brand.prefetch_by_email(
            email="dev@stainless.com",
        )
        assert_matches_type(BrandPrefetchByEmailResponse, brand, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_prefetch_by_email_with_all_params(self, async_client: AsyncBrandDev) -> None:
        brand = await async_client.brand.prefetch_by_email(
            email="dev@stainless.com",
            timeout_ms=1,
        )
        assert_matches_type(BrandPrefetchByEmailResponse, brand, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_prefetch_by_email(self, async_client: AsyncBrandDev) -> None:
        response = await async_client.brand.with_raw_response.prefetch_by_email(
            email="dev@stainless.com",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        brand = await response.parse()
        assert_matches_type(BrandPrefetchByEmailResponse, brand, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_prefetch_by_email(self, async_client: AsyncBrandDev) -> None:
        async with async_client.brand.with_streaming_response.prefetch_by_email(
            email="dev@stainless.com",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            brand = await response.parse()
            assert_matches_type(BrandPrefetchByEmailResponse, brand, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve_by_email(self, async_client: AsyncBrandDev) -> None:
        brand = await async_client.brand.retrieve_by_email(
            email="dev@stainless.com",
        )
        assert_matches_type(BrandRetrieveByEmailResponse, brand, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve_by_email_with_all_params(self, async_client: AsyncBrandDev) -> None:
        brand = await async_client.brand.retrieve_by_email(
            email="dev@stainless.com",
            force_language="albanian",
            max_speed=True,
            timeout_ms=1,
        )
        assert_matches_type(BrandRetrieveByEmailResponse, brand, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve_by_email(self, async_client: AsyncBrandDev) -> None:
        response = await async_client.brand.with_raw_response.retrieve_by_email(
            email="dev@stainless.com",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        brand = await response.parse()
        assert_matches_type(BrandRetrieveByEmailResponse, brand, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve_by_email(self, async_client: AsyncBrandDev) -> None:
        async with async_client.brand.with_streaming_response.retrieve_by_email(
            email="dev@stainless.com",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            brand = await response.parse()
            assert_matches_type(BrandRetrieveByEmailResponse, brand, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve_by_isin(self, async_client: AsyncBrandDev) -> None:
        brand = await async_client.brand.retrieve_by_isin(
            isin="SE60513A9993",
        )
        assert_matches_type(BrandRetrieveByIsinResponse, brand, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve_by_isin_with_all_params(self, async_client: AsyncBrandDev) -> None:
        brand = await async_client.brand.retrieve_by_isin(
            isin="SE60513A9993",
            force_language="albanian",
            max_speed=True,
            timeout_ms=1,
        )
        assert_matches_type(BrandRetrieveByIsinResponse, brand, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve_by_isin(self, async_client: AsyncBrandDev) -> None:
        response = await async_client.brand.with_raw_response.retrieve_by_isin(
            isin="SE60513A9993",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        brand = await response.parse()
        assert_matches_type(BrandRetrieveByIsinResponse, brand, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve_by_isin(self, async_client: AsyncBrandDev) -> None:
        async with async_client.brand.with_streaming_response.retrieve_by_isin(
            isin="SE60513A9993",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            brand = await response.parse()
            assert_matches_type(BrandRetrieveByIsinResponse, brand, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve_by_name(self, async_client: AsyncBrandDev) -> None:
        brand = await async_client.brand.retrieve_by_name(
            name="xxx",
        )
        assert_matches_type(BrandRetrieveByNameResponse, brand, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve_by_name_with_all_params(self, async_client: AsyncBrandDev) -> None:
        brand = await async_client.brand.retrieve_by_name(
            name="xxx",
            force_language="albanian",
            max_speed=True,
            timeout_ms=1,
        )
        assert_matches_type(BrandRetrieveByNameResponse, brand, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve_by_name(self, async_client: AsyncBrandDev) -> None:
        response = await async_client.brand.with_raw_response.retrieve_by_name(
            name="xxx",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        brand = await response.parse()
        assert_matches_type(BrandRetrieveByNameResponse, brand, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve_by_name(self, async_client: AsyncBrandDev) -> None:
        async with async_client.brand.with_streaming_response.retrieve_by_name(
            name="xxx",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            brand = await response.parse()
            assert_matches_type(BrandRetrieveByNameResponse, brand, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve_by_ticker(self, async_client: AsyncBrandDev) -> None:
        brand = await async_client.brand.retrieve_by_ticker(
            ticker="ticker",
        )
        assert_matches_type(BrandRetrieveByTickerResponse, brand, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve_by_ticker_with_all_params(self, async_client: AsyncBrandDev) -> None:
        brand = await async_client.brand.retrieve_by_ticker(
            ticker="ticker",
            force_language="albanian",
            max_speed=True,
            ticker_exchange="AMEX",
            timeout_ms=1,
        )
        assert_matches_type(BrandRetrieveByTickerResponse, brand, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve_by_ticker(self, async_client: AsyncBrandDev) -> None:
        response = await async_client.brand.with_raw_response.retrieve_by_ticker(
            ticker="ticker",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        brand = await response.parse()
        assert_matches_type(BrandRetrieveByTickerResponse, brand, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve_by_ticker(self, async_client: AsyncBrandDev) -> None:
        async with async_client.brand.with_streaming_response.retrieve_by_ticker(
            ticker="ticker",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            brand = await response.parse()
            assert_matches_type(BrandRetrieveByTickerResponse, brand, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve_naics(self, async_client: AsyncBrandDev) -> None:
        brand = await async_client.brand.retrieve_naics(
            input="input",
        )
        assert_matches_type(BrandRetrieveNaicsResponse, brand, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve_naics_with_all_params(self, async_client: AsyncBrandDev) -> None:
        brand = await async_client.brand.retrieve_naics(
            input="input",
            max_results=1,
            min_results=1,
            timeout_ms=1,
        )
        assert_matches_type(BrandRetrieveNaicsResponse, brand, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve_naics(self, async_client: AsyncBrandDev) -> None:
        response = await async_client.brand.with_raw_response.retrieve_naics(
            input="input",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        brand = await response.parse()
        assert_matches_type(BrandRetrieveNaicsResponse, brand, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve_naics(self, async_client: AsyncBrandDev) -> None:
        async with async_client.brand.with_streaming_response.retrieve_naics(
            input="input",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            brand = await response.parse()
            assert_matches_type(BrandRetrieveNaicsResponse, brand, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve_simplified(self, async_client: AsyncBrandDev) -> None:
        brand = await async_client.brand.retrieve_simplified(
            domain="domain",
        )
        assert_matches_type(BrandRetrieveSimplifiedResponse, brand, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve_simplified_with_all_params(self, async_client: AsyncBrandDev) -> None:
        brand = await async_client.brand.retrieve_simplified(
            domain="domain",
            timeout_ms=1,
        )
        assert_matches_type(BrandRetrieveSimplifiedResponse, brand, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve_simplified(self, async_client: AsyncBrandDev) -> None:
        response = await async_client.brand.with_raw_response.retrieve_simplified(
            domain="domain",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        brand = await response.parse()
        assert_matches_type(BrandRetrieveSimplifiedResponse, brand, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve_simplified(self, async_client: AsyncBrandDev) -> None:
        async with async_client.brand.with_streaming_response.retrieve_simplified(
            domain="domain",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            brand = await response.parse()
            assert_matches_type(BrandRetrieveSimplifiedResponse, brand, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_screenshot(self, async_client: AsyncBrandDev) -> None:
        brand = await async_client.brand.screenshot(
            domain="domain",
        )
        assert_matches_type(BrandScreenshotResponse, brand, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_screenshot_with_all_params(self, async_client: AsyncBrandDev) -> None:
        brand = await async_client.brand.screenshot(
            domain="domain",
            full_screenshot="true",
            page="login",
            prioritize="speed",
        )
        assert_matches_type(BrandScreenshotResponse, brand, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_screenshot(self, async_client: AsyncBrandDev) -> None:
        response = await async_client.brand.with_raw_response.screenshot(
            domain="domain",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        brand = await response.parse()
        assert_matches_type(BrandScreenshotResponse, brand, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_screenshot(self, async_client: AsyncBrandDev) -> None:
        async with async_client.brand.with_streaming_response.screenshot(
            domain="domain",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            brand = await response.parse()
            assert_matches_type(BrandScreenshotResponse, brand, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_styleguide(self, async_client: AsyncBrandDev) -> None:
        brand = await async_client.brand.styleguide(
            domain="domain",
        )
        assert_matches_type(BrandStyleguideResponse, brand, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_styleguide_with_all_params(self, async_client: AsyncBrandDev) -> None:
        brand = await async_client.brand.styleguide(
            domain="domain",
            prioritize="speed",
            timeout_ms=1,
        )
        assert_matches_type(BrandStyleguideResponse, brand, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_styleguide(self, async_client: AsyncBrandDev) -> None:
        response = await async_client.brand.with_raw_response.styleguide(
            domain="domain",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        brand = await response.parse()
        assert_matches_type(BrandStyleguideResponse, brand, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_styleguide(self, async_client: AsyncBrandDev) -> None:
        async with async_client.brand.with_streaming_response.styleguide(
            domain="domain",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            brand = await response.parse()
            assert_matches_type(BrandStyleguideResponse, brand, path=["response"])

        assert cast(Any, response.is_closed) is True
