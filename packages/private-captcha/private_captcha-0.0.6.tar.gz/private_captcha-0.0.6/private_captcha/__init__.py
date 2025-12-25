"""Python client for the Private Captcha service."""

from .client import Client, GLOBAL_DOMAIN, EU_DOMAIN
from .exceptions import (
    APIKeyError,
    PrivateCaptchaError,
    SolutionError,
    HTTPError,
    VerificationFailedError,
)
from .models import VerifyOutput

__all__ = [
    "Client",
    "GLOBAL_DOMAIN",
    "EU_DOMAIN",
    "PrivateCaptchaError",
    "APIKeyError",
    "SolutionError",
    "HTTPError",
    "VerifyOutput",
    "VerificationFailedError",
]
