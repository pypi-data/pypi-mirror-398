"""
Custom exceptions for Sunbay Nexus Python SDK.

These mirror the semantics of the Java SDK exceptions while following
Python naming and usage conventions.
"""

from typing import Optional


class SunbayError(Exception):
    """Base class for all Sunbay Nexus SDK exceptions."""


class SunbayBusinessError(SunbayError):
    """
Business exception used for API business errors and parameter validation errors.
    """

    def __init__(self, message: str, code: Optional[str] = None, trace_id: Optional[str] = None) -> None:
        super().__init__(message)
        self.code = code
        self.trace_id = trace_id

    def __str__(self) -> str:
        if self.code is not None:
            return f"SunbayBusinessError(code={self.code!r}, message={str(super())!r}, trace_id={self.trace_id!r})"
        return f"SunbayBusinessError(message={str(super())!r})"


class SunbayNetworkError(SunbayError):
    """
Network exception used for HTTP/network level errors.
    """

    def __init__(self, message: str, retryable: bool, *, cause: Optional[BaseException] = None) -> None:
        super().__init__(message)
        self.retryable = retryable
        self.__cause__ = cause

    def __str__(self) -> str:
        return f"SunbayNetworkError(message={str(super())!r}, retryable={self.retryable!r})"


