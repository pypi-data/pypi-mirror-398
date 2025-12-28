"""
Common value objects shared across multiple requests and responses.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Amount:
    """
    Generic amount information.

    This mirrors the Java Amount class and is mainly used in responses.
    """

    price_currency: Optional[str] = None
    trans_amount: Optional[float] = None
    order_amount: Optional[float] = None
    tax_amount: Optional[float] = None
    surcharge_amount: Optional[float] = None
    tip_amount: Optional[float] = None
    cashback_amount: Optional[float] = None
    pricing_currency: Optional[str] = None


@dataclass
class SaleAmount:
    """
    Amount information for sale transactions.
    """

    order_amount: float
    pricing_currency: str


@dataclass
class AuthAmount:
    """
    Amount information for auth/forced auth/incremental auth.
    """

    order_amount: float
    pricing_currency: str


@dataclass
class PostAuthAmount:
    """
    Amount information for post authorization.
    """

    order_amount: float
    pricing_currency: str
    tip_amount: Optional[float] = None
    tax_amount: Optional[float] = None
    surcharge_amount: Optional[float] = None


@dataclass
class RefundAmount:
    """
    Amount information for refund.
    """

    order_amount: float
    pricing_currency: str
    tip_amount: Optional[float] = None
    tax_amount: Optional[float] = None
    surcharge_amount: Optional[float] = None
    cashback_amount: Optional[float] = None


@dataclass
class BatchTotalAmount:
    """
    Total amount information for batch close.
    """

    transaction_count: Optional[int] = None
    order_amount: Optional[float] = None
    tax_amount: Optional[float] = None
    surcharge_amount: Optional[float] = None
    tip_amount: Optional[float] = None
    cashback_amount: Optional[float] = None
    pricing_currency: Optional[str] = None


@dataclass
class PaymentMethodInfo:
    """
    Basic payment method information.

    The exact fields may evolve over time. This class focuses on properties
    that are generally useful to expose to callers. Additional fields can be
    added in a backward compatible way.
    """

    network_type: Optional[str] = None
    card_last4: Optional[str] = None
    entry_mode: Optional[str] = None


