# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from datetime import date

from .._models import BaseModel

__all__ = ["VerificationVerifyNinResponse"]


class VerificationVerifyNinResponse(BaseModel):
    dob: Optional[date] = None

    full_name: Optional[str] = None

    gender: Optional[str] = None

    number_nin: Optional[str] = None

    status: Optional[str] = None
    """Verification status"""
