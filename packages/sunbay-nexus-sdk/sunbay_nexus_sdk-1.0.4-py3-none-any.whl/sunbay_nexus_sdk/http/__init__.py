"""
HTTP client for Sunbay Nexus SDK.

This module encapsulates HTTP details (headers, timeouts, retries,
response parsing) so that the public client only deals with business logic.
"""

from __future__ import annotations

import json
import logging
import platform
import sys
import time
from dataclasses import asdict, is_dataclass
from typing import Any, Dict, Optional, Type, TypeVar

import requests
from requests import Response, Session
from requests.exceptions import RequestException, Timeout

from .. import __version__, constants
from ..exceptions import SunbayBusinessError, SunbayNetworkError
from ..models.base import BaseResponse
from ..utils.id_generator import generate_request_id

T = TypeVar("T", bound=BaseResponse)


class HttpClient:
    """
    Low-level HTTP client used by NexusClient.
    """

    def __init__(
        self,
        api_key: str,
        base_url: str,
        connect_timeout: float,
        read_timeout: float,
        max_retries: int,
        max_connections: int,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._connect_timeout = connect_timeout
        self._read_timeout = read_timeout
        self._max_retries = max_retries
        # Logger follows mainstream SDK practice:
        # - use standard logging
        # - do not configure handlers or levels here
        # - let application decide how to handle output
        self._logger = logger or logging.getLogger("sunbay_nexus_sdk.http")

        self._session = Session()
        adapter = requests.adapters.HTTPAdapter(pool_maxsize=max_connections)
        self._session.mount("http://", adapter)
        self._session.mount("https://", adapter)

    def post(self, path: str, request_body: Any, response_type: Type[T]) -> T:
        url = f"{self._base_url}{path}"
        json_body = self._serialize_request_body(request_body)
        headers = self._build_headers(is_post=True)

        if self._logger.isEnabledFor(logging.INFO):
            self._logger.info(
                "Request %s %s - Headers: %s, Body: %s",
                "POST",
                url,
                headers,
                json_body,
            )

        try:
            response = self._session.post(
                url,
                headers=headers,
                data=json_body,
                timeout=(self._connect_timeout, self._read_timeout),
            )
            return self._handle_response("POST", url, response, response_type)
        except Timeout as exc:
            self._logger.warning("Request timeout %s %s: %s", "POST", url, exc)
            raise SunbayNetworkError("Request timeout", retryable=True, cause=exc) from exc
        except RequestException as exc:
            self._logger.warning("Network error %s %s: %s", "POST", url, exc)
            raise SunbayNetworkError(f"Network error: {exc}", retryable=True, cause=exc) from exc

    def get(self, path: str, request_obj: Any, response_type: Type[T]) -> T:
        url = f"{self._base_url}{path}"
        params = self._build_query_params(request_obj)
        headers = self._build_headers(is_post=False)

        if self._logger.isEnabledFor(logging.INFO):
            self._logger.info(
                "Request %s %s - Headers: %s, Params: %s",
                "GET",
                url,
                headers,
                params,
            )

        attempts = 0
        max_attempts = max(self._max_retries, 1)

        while True:
            attempts += 1
            try:
                response = self._session.get(
                    url,
                    headers=headers,
                    params=params,
                    timeout=(self._connect_timeout, self._read_timeout),
                )
                return self._handle_response("GET", url, response, response_type)
            except Timeout as exc:
                if attempts >= max_attempts:
                    self._logger.warning("Request timeout %s %s after %s attempts", "GET", url, attempts)
                    raise SunbayNetworkError("Request timeout", retryable=True, cause=exc) from exc
                if self._logger.isEnabledFor(logging.DEBUG):
                    self._logger.debug(
                        "Request timeout %s %s (attempt %s/%s), will retry",
                        "GET",
                        url,
                        attempts,
                        max_attempts,
                    )
                self._sleep_before_retry(attempts)
            except RequestException as exc:
                if attempts >= max_attempts:
                    self._logger.warning("Network error %s %s after %s attempts: %s", "GET", url, attempts, exc)
                    raise SunbayNetworkError(f"Network error: {exc}", retryable=True, cause=exc) from exc
                if self._logger.isEnabledFor(logging.DEBUG):
                    self._logger.debug(
                        "Network error %s %s (attempt %s/%s): %s, will retry",
                        "GET",
                        url,
                        attempts,
                        max_attempts,
                        exc,
                    )
                self._sleep_before_retry(attempts)

    @staticmethod
    def _sleep_before_retry(attempts: int) -> None:
        delay_seconds = 1.0 * attempts
        time.sleep(delay_seconds)

    @staticmethod
    def _serialize_request_body(request_body: Any) -> str:
        if is_dataclass(request_body):
            raw_payload = asdict(request_body)
        elif isinstance(request_body, dict):
            raw_payload = request_body
        else:
            raise SunbayBusinessError("Request body must be a dataclass instance or dict")

        # Convert Python-style field names (snake_case) to API-style (camelCase),
        # aligning with Java SDK behaviour and backend expectations.
        payload = HttpClient._to_camel_dict(raw_payload)
        return json.dumps(payload, ensure_ascii=False)

    @staticmethod
    def _build_query_params(request_obj: Any) -> Dict[str, Any]:
        if request_obj is None:
            return {}
        if is_dataclass(request_obj):
            data = asdict(request_obj)
        elif isinstance(request_obj, dict):
            data = request_obj
        else:
            raise SunbayBusinessError("Request object for GET must be a dataclass instance or dict")

        filtered = {k: v for k, v in data.items() if v is not None}
        return HttpClient._to_camel_dict(filtered)

    @staticmethod
    def _to_camel_dict(source: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert a dict with snake_case keys to camelCase keys recursively.

        This keeps the Python dataclass field style while matching the
        JSON/query parameter naming convention expected by the HTTP API.
        """

        def _snake_to_camel(name: str) -> str:
            parts = name.split("_")
            if not parts:
                return name
            head = parts[0]
            tail = [p.capitalize() for p in parts[1:] if p]
            return head + "".join(tail)

        result: Dict[str, Any] = {}
        for key, value in source.items():
            camel_key = _snake_to_camel(key)
            if isinstance(value, dict):
                result[camel_key] = HttpClient._to_camel_dict(value)
            elif isinstance(value, list):
                result[camel_key] = [
                    HttpClient._to_camel_dict(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                result[camel_key] = value
        return result

    def _build_headers(self, *, is_post: bool) -> Dict[str, str]:
        # Build User-Agent following mainstream SDK practice (e.g., AWS Boto3, Stripe)
        # Format: SDKName/Version Python/PythonVersion OS/OSVersion
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        os_name = platform.system()
        os_version = platform.release()
        user_agent = f"SunbayNexusSDK-Python/{__version__} Python/{python_version} {os_name}/{os_version}"

        headers: Dict[str, str] = {
            constants.HEADER_AUTHORIZATION: f"{constants.AUTHORIZATION_BEARER_PREFIX}{self._api_key}",
            constants.HEADER_REQUEST_ID: generate_request_id(),
            constants.HEADER_TIMESTAMP: str(int(time.time() * 1000)),
            constants.HEADER_USER_AGENT: user_agent,
        }
        if is_post:
            headers[constants.HEADER_CONTENT_TYPE] = constants.CONTENT_TYPE_JSON
        return headers

    @staticmethod
    def _parse_response_body(body: Optional[str], response_type: Type[T]) -> T:
        if body is None or not body.strip():
            raise SunbayNetworkError("Empty response body", retryable=False)

        try:
            root = json.loads(body)
        except json.JSONDecodeError as exc:
            raise SunbayNetworkError("Failed to parse response body as JSON", retryable=False, cause=exc) from exc

        code = root.get("code")
        msg = root.get("msg")
        trace_id = root.get("traceId")
        data = root.get("data")

        if data is None:
            payload: Dict[str, Any] = {}
        elif isinstance(data, dict):
            # Convert API camelCase fields in data payload to Python snake_case
            # so that dataclass constructors receive matching keyword arguments.
            payload = HttpClient._to_snake_dict(data)
        else:
            payload = {"data": data}

        # Normalize nested amount structures and inject base fields, allowing
        # data fields to override only when explicitly set.
        HttpClient._normalize_amount_fields(payload)
        payload.setdefault("code", code)
        payload.setdefault("msg", msg)
        payload.setdefault("trace_id", trace_id)

        obj = response_type(**payload)  # type: ignore[arg-type]
        if not isinstance(obj, BaseResponse):
            raise SunbayNetworkError("Response type is not a subclass of BaseResponse", retryable=False)
        return obj

    def _handle_response(
        self,
        method: str,
        url: str,
        response: Response,
        response_type: Type[T],
    ) -> T:
        status = response.status_code
        text = response.text

        if self._logger.isEnabledFor(logging.INFO):
            self._logger.info("Response %s %s - Status: %s, Body: %s", method, url, status, text)

        if constants.HTTP_STATUS_OK_START <= status < constants.HTTP_STATUS_OK_END:
            obj = self._parse_response_body(text, response_type)
            if not obj.is_success():
                self._logger.error(
                    "API error %s %s - code: %s, msg: %s, trace_id: %s",
                    method,
                    url,
                    obj.code,
                    obj.msg,
                    obj.trace_id,
                )
                raise SunbayBusinessError(obj.msg or "API error", code=obj.code, trace_id=obj.trace_id)
            return obj

        message_parts = [f"HTTP {status}"]
        if constants.HTTP_STATUS_CLIENT_ERROR_START <= status < constants.HTTP_STATUS_CLIENT_ERROR_END:
            message_parts.append("(Client Error)")
        elif status >= constants.HTTP_STATUS_SERVER_ERROR_START:
            message_parts.append("(Server Error)")
        if text:
            message_parts.append(f"- {text}")
        message = " ".join(message_parts)

        self._logger.error("HTTP error %s %s - Status: %s, Message: %s", method, url, status, message)
        raise SunbayNetworkError(message, retryable=False)

    @staticmethod
    def _to_snake_dict(source: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert a dict with camelCase keys to snake_case keys recursively.

        This mirrors the behaviour of the Java SDK's JSON mapping where
        JSON uses camelCase but Java/Python fields use standard naming.
        """

        def _camel_to_snake(name: str) -> str:
            chars = []
            for ch in name:
                if ch.isupper():
                    if chars:
                        chars.append("_")
                    chars.append(ch.lower())
                else:
                    chars.append(ch)
            return "".join(chars)

        result: Dict[str, Any] = {}
        for key, value in source.items():
            snake_key = _camel_to_snake(key)
            if isinstance(value, dict):
                result[snake_key] = HttpClient._to_snake_dict(value)
            elif isinstance(value, list):
                result[snake_key] = [
                    HttpClient._to_snake_dict(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                result[snake_key] = value
        return result

    @staticmethod
    def _normalize_amount_fields(payload: Dict[str, Any]) -> None:
        """
        Normalize numeric fields inside amount-like structures.

        The HTTP API may encode monetary fields as strings. This helper converts
        known numeric amount fields to float so that they match the Python
        dataclass type hints (e.g. Amount, BatchTotalAmount).
        """

        numeric_keys = (
            "trans_amount",
            "order_amount",
            "tax_amount",
            "surcharge_amount",
            "tip_amount",
            "cashback_amount",
        )

        def _convert_fields(amount_dict: Dict[str, Any]) -> None:
            for key in numeric_keys:
                value = amount_dict.get(key)
                if isinstance(value, str):
                    try:
                        amount_dict[key] = float(value)
                    except ValueError:
                        # Keep original value if it cannot be parsed as float.
                        continue

        for field_name in ("amount", "total_amount"):
            obj = payload.get(field_name)
            if isinstance(obj, dict):
                _convert_fields(obj)

