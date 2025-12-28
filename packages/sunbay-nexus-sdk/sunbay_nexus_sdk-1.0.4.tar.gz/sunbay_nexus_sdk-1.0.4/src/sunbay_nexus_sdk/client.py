"""
Public NexusClient for Sunbay Nexus Python SDK.

This client mirrors the Java SDK entry point and is intended to be the main
interface used by integrators.
"""

import logging
import os
from typing import Optional

from .constants import (
    DEFAULT_BASE_URL,
    DEFAULT_CONNECT_TIMEOUT,
    DEFAULT_MAX_CONNECTIONS,
    DEFAULT_MAX_RETRIES,
    DEFAULT_READ_TIMEOUT,
    PATH_BATCH_CLOSE,
    PATH_QUERY,
    PATH_SALE,
)
from .exceptions import SunbayBusinessError
from .http import HttpClient
from .models.request import (
    AbortRequest,
    AuthRequest,
    BatchCloseRequest,
    ForcedAuthRequest,
    IncrementalAuthRequest,
    PostAuthRequest,
    QueryRequest,
    RefundRequest,
    SaleRequest,
    TipAdjustRequest,
    VoidRequest,
)
from .models.response import (
    AbortResponse,
    AuthResponse,
    BatchCloseResponse,
    ForcedAuthResponse,
    IncrementalAuthResponse,
    PostAuthResponse,
    QueryResponse,
    RefundResponse,
    SaleResponse,
    TipAdjustResponse,
    VoidResponse,
)


class NexusClient:
    """
    Main client for interacting with Sunbay Nexus APIs.

    This client is designed to be thread-safe and reused across threads.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = DEFAULT_BASE_URL,
        connect_timeout: float = DEFAULT_CONNECT_TIMEOUT,
        read_timeout: float = DEFAULT_READ_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        max_connections: int = DEFAULT_MAX_CONNECTIONS,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        if api_key is None:
            api_key = os.getenv("SUNBAY_API_KEY")
        if not api_key:
            raise SunbayBusinessError("API key cannot be null or empty")

        # Allow overriding base_url via environment for different environments
        # (e.g. dev / uat / prod) while keeping a sensible default.
        env_base_url = os.getenv("SUNBAY_BASE_URL")
        if env_base_url:
            base_url = env_base_url

        self._http_client = HttpClient(
            api_key=api_key,
            base_url=base_url,
            connect_timeout=connect_timeout,
            read_timeout=read_timeout,
            max_retries=max_retries,
            max_connections=max_connections,
            logger=logger,
        )

    # --- Transaction APIs ---

    def sale(self, request: SaleRequest) -> SaleResponse:
        if request is None:
            raise SunbayBusinessError("SaleRequest cannot be null")
        return self._http_client.post(PATH_SALE, request, SaleResponse)

    def auth(self, request: AuthRequest) -> AuthResponse:
        if request is None:
            raise SunbayBusinessError("AuthRequest cannot be null")
        return self._http_client.post(PATH_AUTH, request, AuthResponse)

    def forced_auth(self, request: ForcedAuthRequest) -> ForcedAuthResponse:
        if request is None:
            raise SunbayBusinessError("ForcedAuthRequest cannot be null")
        return self._http_client.post(PATH_FORCED_AUTH, request, ForcedAuthResponse)

    def incremental_auth(self, request: IncrementalAuthRequest) -> IncrementalAuthResponse:
        if request is None:
            raise SunbayBusinessError("IncrementalAuthRequest cannot be null")
        return self._http_client.post(PATH_INCREMENTAL_AUTH, request, IncrementalAuthResponse)

    def post_auth(self, request: PostAuthRequest) -> PostAuthResponse:
        if request is None:
            raise SunbayBusinessError("PostAuthRequest cannot be null")
        return self._http_client.post(PATH_POST_AUTH, request, PostAuthResponse)

    def refund(self, request: RefundRequest) -> RefundResponse:
        if request is None:
            raise SunbayBusinessError("RefundRequest cannot be null")
        return self._http_client.post(PATH_REFUND, request, RefundResponse)

    def void_transaction(self, request: VoidRequest) -> VoidResponse:
        if request is None:
            raise SunbayBusinessError("VoidRequest cannot be null")
        return self._http_client.post(PATH_VOID, request, VoidResponse)

    def abort(self, request: AbortRequest) -> AbortResponse:
        if request is None:
            raise SunbayBusinessError("AbortRequest cannot be null")
        return self._http_client.post(PATH_ABORT, request, AbortResponse)

    def tip_adjust(self, request: TipAdjustRequest) -> TipAdjustResponse:
        if request is None:
            raise SunbayBusinessError("TipAdjustRequest cannot be null")
        return self._http_client.post(PATH_TIP_ADJUST, request, TipAdjustResponse)

    # --- Query APIs ---

    def query(self, request: QueryRequest) -> QueryResponse:
        if request is None:
            raise SunbayBusinessError("QueryRequest cannot be null")
        return self._http_client.get(PATH_QUERY, request, QueryResponse)

    # --- Settlement APIs ---

    def batch_close(self, request: BatchCloseRequest) -> BatchCloseResponse:
        if request is None:
            raise SunbayBusinessError("BatchCloseRequest cannot be null")
        return self._http_client.post(PATH_BATCH_CLOSE, request, BatchCloseResponse)

    # --- Lifecycle ---

    def __enter__(self) -> "NexusClient":
        """
        Context manager entry. Allows using NexusClient with 'with' statement.

        Note: Python requests Session will automatically close on program exit
        via garbage collection, so explicit cleanup is not necessary.
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Context manager exit. No explicit cleanup needed as Python's garbage
        collector will handle resource cleanup automatically.
        """
        pass


