"""
Response models for Sunbay Nexus SDK.
"""

from dataclasses import dataclass
from typing import Optional

from .base import BaseResponse
from .common import Amount, BatchTotalAmount


@dataclass
class SaleResponse(BaseResponse):
    """
    Sale transaction response.
    """

    transaction_id: Optional[str] = None
    reference_order_id: Optional[str] = None
    transaction_request_id: Optional[str] = None


@dataclass
class AuthResponse(BaseResponse):
    """
    Authorization response.
    """

    transaction_id: Optional[str] = None
    reference_order_id: Optional[str] = None
    transaction_request_id: Optional[str] = None


@dataclass
class ForcedAuthResponse(BaseResponse):
    """
    Forced authorization response.
    """

    transaction_id: Optional[str] = None
    reference_order_id: Optional[str] = None
    transaction_request_id: Optional[str] = None


@dataclass
class IncrementalAuthResponse(BaseResponse):
    """
    Incremental authorization response.
    """

    transaction_id: Optional[str] = None
    reference_order_id: Optional[str] = None
    transaction_request_id: Optional[str] = None


@dataclass
class PostAuthResponse(BaseResponse):
    """
    Post authorization response.
    """

    transaction_id: Optional[str] = None
    reference_order_id: Optional[str] = None
    transaction_request_id: Optional[str] = None


@dataclass
class RefundResponse(BaseResponse):
    """
    Refund response.
    """

    transaction_id: Optional[str] = None
    reference_order_id: Optional[str] = None
    transaction_request_id: Optional[str] = None
    original_transaction_id: Optional[str] = None
    original_transaction_request_id: Optional[str] = None


@dataclass
class VoidResponse(BaseResponse):
    """
    Void response.
    """

    transaction_id: Optional[str] = None
    transaction_request_id: Optional[str] = None
    original_transaction_id: Optional[str] = None
    original_transaction_request_id: Optional[str] = None


@dataclass
class AbortResponse(BaseResponse):
    """
    Abort response.
    """

    original_transaction_id: Optional[str] = None
    original_transaction_request_id: Optional[str] = None


@dataclass
class TipAdjustResponse(BaseResponse):
    """
    Tip adjust response.
    """

    original_transaction_id: Optional[str] = None
    original_transaction_request_id: Optional[str] = None
    tip_amount: Optional[float] = None


@dataclass
class QueryResponse(BaseResponse):
    """
    Query transaction response.
    """

    transaction_id: Optional[str] = None
    transaction_request_id: Optional[str] = None
    reference_order_id: Optional[str] = None
    transaction_status: Optional[str] = None
    transaction_type: Optional[str] = None
    amount: Optional[Amount] = None
    create_time: Optional[str] = None
    complete_time: Optional[str] = None
    masked_pan: Optional[str] = None
    card_network_type: Optional[str] = None
    payment_method_id: Optional[str] = None
    sub_payment_method_id: Optional[str] = None
    batch_no: Optional[str] = None
    voucher_no: Optional[str] = None
    stan: Optional[str] = None
    rrn: Optional[str] = None
    auth_code: Optional[str] = None
    entry_mode: Optional[str] = None
    authentication_method: Optional[str] = None
    transaction_result_code: Optional[str] = None
    transaction_result_msg: Optional[str] = None
    terminal_sn: Optional[str] = None
    description: Optional[str] = None
    attach: Optional[str] = None


@dataclass
class BatchCloseResponse(BaseResponse):
    """
    Batch close response.
    """

    batch_no: Optional[str] = None
    terminal_sn: Optional[str] = None
    close_time: Optional[str] = None
    transaction_count: Optional[int] = None
    total_amount: Optional[BatchTotalAmount] = None


