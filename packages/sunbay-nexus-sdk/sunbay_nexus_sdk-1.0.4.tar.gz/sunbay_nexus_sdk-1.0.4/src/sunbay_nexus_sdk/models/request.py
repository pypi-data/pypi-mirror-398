"""
Request models for Sunbay Nexus SDK.
"""

from dataclasses import dataclass
from typing import Optional

from .common import AuthAmount, PostAuthAmount, RefundAmount, SaleAmount, PaymentMethodInfo


@dataclass
class SaleRequest:
    """
    Sale transaction request.
    """

    app_id: str
    merchant_id: str
    reference_order_id: str
    transaction_request_id: str
    amount: SaleAmount
    description: str
    terminal_sn: str
    payment_method: Optional[PaymentMethodInfo] = None
    attach: Optional[str] = None
    notify_url: Optional[str] = None
    time_expire: Optional[str] = None


@dataclass
class AuthRequest:
    """
    Authorization request.
    """

    app_id: str
    merchant_id: str
    reference_order_id: str
    transaction_request_id: str
    amount: AuthAmount
    description: str
    terminal_sn: str
    payment_method: Optional[PaymentMethodInfo] = None
    attach: Optional[str] = None
    notify_url: Optional[str] = None
    time_expire: Optional[str] = None


@dataclass
class ForcedAuthRequest:
    """
    Forced authorization request.
    """

    app_id: str
    merchant_id: str
    reference_order_id: str
    transaction_request_id: str
    amount: AuthAmount
    description: str
    terminal_sn: str
    payment_method: Optional[PaymentMethodInfo] = None
    attach: Optional[str] = None
    notify_url: Optional[str] = None
    time_expire: Optional[str] = None


@dataclass
class IncrementalAuthRequest:
    """
    Incremental authorization request.
    """

    app_id: str
    merchant_id: str
    original_transaction_id: Optional[str] = None
    original_transaction_request_id: Optional[str] = None
    transaction_request_id: str = ""
    amount: Optional[AuthAmount] = None
    description: Optional[str] = None
    terminal_sn: Optional[str] = None
    attach: Optional[str] = None
    notify_url: Optional[str] = None


@dataclass
class QueryRequest:
    """
    Query transaction request.
    """

    app_id: str
    merchant_id: str
    transaction_id: Optional[str] = None
    reference_order_id: Optional[str] = None
    transaction_request_id: Optional[str] = None


@dataclass
class PostAuthRequest:
    """
    Post authorization request.
    """

    app_id: str
    merchant_id: str
    original_transaction_id: Optional[str] = None
    original_transaction_request_id: Optional[str] = None
    reference_order_id: Optional[str] = None
    transaction_request_id: str = ""
    amount: Optional[PostAuthAmount] = None
    description: Optional[str] = None
    terminal_sn: Optional[str] = None
    attach: Optional[str] = None
    notify_url: Optional[str] = None


@dataclass
class RefundRequest:
    """
    Refund request.
    """

    app_id: str
    merchant_id: str
    transaction_request_id: str
    amount: RefundAmount
    original_transaction_id: Optional[str] = None
    original_transaction_request_id: Optional[str] = None
    reference_order_id: Optional[str] = None
    payment_method: Optional[PaymentMethodInfo] = None
    description: Optional[str] = None
    terminal_sn: Optional[str] = None
    attach: Optional[str] = None
    notify_url: Optional[str] = None
    time_expire: Optional[str] = None


@dataclass
class BatchCloseRequest:
    """
    Batch close request.
    """

    app_id: str
    merchant_id: str
    transaction_request_id: str
    terminal_sn: str
    description: Optional[str] = None


@dataclass
class VoidRequest:
    """
    Void request.
    """

    app_id: str
    merchant_id: str
    transaction_request_id: str
    original_transaction_id: Optional[str] = None
    original_transaction_request_id: Optional[str] = None
    description: Optional[str] = None
    terminal_sn: Optional[str] = None
    attach: Optional[str] = None
    notify_url: Optional[str] = None


@dataclass
class AbortRequest:
    """
    Abort request.
    """

    app_id: str
    merchant_id: str
    original_transaction_id: Optional[str] = None
    original_transaction_request_id: Optional[str] = None
    terminal_sn: Optional[str] = None
    description: Optional[str] = None
    attach: Optional[str] = None


@dataclass
class TipAdjustRequest:
    """
    Tip adjust request.
    """

    app_id: str
    merchant_id: str
    terminal_sn: str
    original_transaction_id: Optional[str] = None
    original_transaction_request_id: Optional[str] = None
    tip_amount: float = 0.0
    attach: Optional[str] = None


