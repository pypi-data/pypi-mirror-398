"""
Enum definitions corresponding to Java SDK enums.

These are optional helpers to make code more self-documenting on the caller side.
The underlying API still uses string values on the wire.
The code values match the Java SDK enum codes.
"""

from enum import Enum


class TransactionStatus(str, Enum):
    """
    Transaction status enum.
    Code values match Java SDK TransactionStatus enum.
    """

    # Initial state
    INITIAL = "I"
    # Transaction processing. Channel called but no result obtained, or unexpected exception returned.
    PROCESSING = "P"
    # Transaction successful
    SUCCESS = "S"
    # Transaction failed
    FAIL = "F"
    # Transaction closed
    CLOSED = "C"


class TransactionType(str, Enum):
    """
    Transaction type enum.
    Code values match Java SDK TransactionType enum.
    """

    # Sale transaction
    SALE = "SALE"
    # Authorization (pre-auth)
    AUTH = "AUTH"
    # Forced authorization
    FORCED_AUTH = "FORCED_AUTH"
    # Incremental authorization
    INCREMENTAL = "INCREMENTAL"
    # Post authorization (pre-auth completion)
    POST_AUTH = "POST_AUTH"
    # Refund
    REFUND = "REFUND"
    # Void
    VOID = "VOID"


class CardNetworkType(str, Enum):
    """
    Card network type enum.
    Code values match Java SDK CardNetworkType enum.
    """

    # Credit card
    CREDIT = "CREDIT"
    # Debit card
    DEBIT = "DEBIT"
    # EBT (Electronic Benefit Transfer)
    EBT = "EBT"
    # EGC (Electronic Gift Card)
    EGC = "EGC"
    # Unknown card type
    UNKNOWN = "UNKNOWN"


class EntryMode(str, Enum):
    """
    Entry mode enum.
    Code values match Java SDK EntryMode enum.
    """

    # Manual entry
    MANUAL = "MANUAL"
    # Swipe card
    SWIPE = "SWIPE"
    # Fallback swipe
    FALLBACK_SWIPE = "FALLBACK_SWIPE"
    # Contact chip
    CONTACT = "CONTACT"
    # Contactless
    CONTACTLESS = "CONTACTLESS"


class PaymentCategory(str, Enum):
    """
    Payment category enum.
    Code values match Java SDK PaymentCategory enum.
    """

    # Card payment
    CARD = "CARD"
    # Credit card network
    CARD_CREDIT = "CARD-CREDIT"
    # Debit card network
    CARD_DEBIT = "CARD-DEBIT"
    # QR code merchant presented mode
    QR_MPM = "QR-MPM"
    # QR code customer presented mode
    QR_CPM = "QR-CPM"


class AuthenticationMethod(str, Enum):
    """
    Authentication method enum.
    Code values match Java SDK AuthenticationMethod enum.
    """

    # Not authenticated
    NOT_AUTHENTICATED = "NOT_AUTHENTICATED"
    # PIN authentication
    PIN = "PIN"
    # Offline PIN
    OFFLINE_PIN = "OFFLINE_PIN"
    # Bypass authentication
    BY_PASS = "BY_PASS"
    # Signature authentication
    SIGNATURE = "SIGNATURE"


