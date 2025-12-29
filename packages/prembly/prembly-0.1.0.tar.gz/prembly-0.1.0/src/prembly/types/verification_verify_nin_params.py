# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, TypedDict

__all__ = ["VerificationVerifyNinParams"]


class VerificationVerifyNinParams(TypedDict, total=False):
    number_nin: Required[str]
    """The 11-digit Nigerian National Identification Number"""
