"""
Base models for Sunbay Nexus SDK.
"""

from dataclasses import dataclass
from typing import Optional

from ..constants import RESPONSE_SUCCESS_CODE


@dataclass
class BaseResponse:
    """
    Common response fields returned by Sunbay Nexus APIs.
    """

    code: Optional[str] = None
    msg: Optional[str] = None
    trace_id: Optional[str] = None

    def is_success(self) -> bool:
        """
        Return True if the API call is considered successful.
        """
        return self.code == RESPONSE_SUCCESS_CODE


