# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from prembly import Prembly, AsyncPrembly
from tests.utils import assert_matches_type
from prembly.types import VerificationVerifyNinResponse

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestVerification:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_verify_nin(self, client: Prembly) -> None:
        verification = client.verification.verify_nin(
            number_nin="12345678901",
        )
        assert_matches_type(VerificationVerifyNinResponse, verification, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_verify_nin(self, client: Prembly) -> None:
        response = client.verification.with_raw_response.verify_nin(
            number_nin="12345678901",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        verification = response.parse()
        assert_matches_type(VerificationVerifyNinResponse, verification, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_verify_nin(self, client: Prembly) -> None:
        with client.verification.with_streaming_response.verify_nin(
            number_nin="12345678901",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            verification = response.parse()
            assert_matches_type(VerificationVerifyNinResponse, verification, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncVerification:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_verify_nin(self, async_client: AsyncPrembly) -> None:
        verification = await async_client.verification.verify_nin(
            number_nin="12345678901",
        )
        assert_matches_type(VerificationVerifyNinResponse, verification, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_verify_nin(self, async_client: AsyncPrembly) -> None:
        response = await async_client.verification.with_raw_response.verify_nin(
            number_nin="12345678901",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        verification = await response.parse()
        assert_matches_type(VerificationVerifyNinResponse, verification, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_verify_nin(self, async_client: AsyncPrembly) -> None:
        async with async_client.verification.with_streaming_response.verify_nin(
            number_nin="12345678901",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            verification = await response.parse()
            assert_matches_type(VerificationVerifyNinResponse, verification, path=["response"])

        assert cast(Any, response.is_closed) is True
