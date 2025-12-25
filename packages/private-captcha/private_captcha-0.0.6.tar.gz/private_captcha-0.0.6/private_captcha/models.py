"""Data models for Private Captcha API responses."""

from dataclasses import dataclass
from enum import IntEnum
from typing import Optional


class VerifyCode(IntEnum):
    """Represents verification error codes from the API."""
    NO_ERROR = 0
    ERROR_OTHER = 1
    DUPLICATE_SOLUTIONS_ERROR = 2
    INVALID_SOLUTION_ERROR = 3
    PARSE_RESPONSE_ERROR = 4
    PUZZLE_EXPIRED_ERROR = 5
    INVALID_PROPERTY_ERROR = 6
    WRONG_OWNER_ERROR = 7
    VERIFIED_BEFORE_ERROR = 8
    MAINTENANCE_MODE_ERROR = 9
    TEST_PROPERTY_ERROR = 10
    INTEGRITY_ERROR = 11
    ORG_SCOPE_ERROR = 12

    def __str__(self) -> str:
        return _VERIFY_CODE_MAP.get(self, "error")


_VERIFY_CODE_MAP = {
    VerifyCode.NO_ERROR: "",
    VerifyCode.ERROR_OTHER: "error-other",
    VerifyCode.DUPLICATE_SOLUTIONS_ERROR: "solution-duplicates",
    VerifyCode.INVALID_SOLUTION_ERROR: "solution-invalid",
    VerifyCode.PARSE_RESPONSE_ERROR: "solution-bad-format",
    VerifyCode.PUZZLE_EXPIRED_ERROR: "puzzle-expired",
    VerifyCode.INVALID_PROPERTY_ERROR: "property-invalid",
    VerifyCode.WRONG_OWNER_ERROR: "property-owner-mismatch",
    VerifyCode.VERIFIED_BEFORE_ERROR: "solution-verified-before",
    VerifyCode.MAINTENANCE_MODE_ERROR: "maintenance-mode",
    VerifyCode.TEST_PROPERTY_ERROR: "property-test",
    VerifyCode.INTEGRITY_ERROR: "integrity-error",
    VerifyCode.ORG_SCOPE_ERROR: "org-scope-error",
}


@dataclass
class VerifyOutput:
    """Represents the result of a verification call."""
    success: bool
    code: VerifyCode
    origin: Optional[str] = None
    timestamp: Optional[str] = None

    # Internal fields, for debugging and tracing
    _trace_id: Optional[str] = None
    _attempt: Optional[int] = None

    def ok(self) -> bool:
        """Checks if captcha solution verification succeeded."""
        return self.success and (self.code == VerifyCode.NO_ERROR)

    @property
    def trace_id(self) -> Optional[str]:
        """The request ID for tracing purposes."""
        return self._trace_id

    def __str__(self) -> str:
        """The string representation of the verification error code."""
        return str(self.code)

    @classmethod
    def from_dict(cls, data: dict, **kwargs) -> "VerifyOutput":
        """Creates a VerifyOutput object from a dictionary."""
        return cls(
            success=data.get("success", False),
            code=VerifyCode(data.get("code", VerifyCode.ERROR_OTHER)),
            origin=data.get("origin"),
            timestamp=data.get("timestamp"),
            **kwargs,
        )
