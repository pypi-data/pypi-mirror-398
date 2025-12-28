"""
Integration tests for NexusClient (sale & query).

这些测试会真实调用 Sunbay Nexus 的 HTTP 接口，语义上等价于 Java 版本的 NexusClientTest。
默认使用 pytest，并且带有跳过标记，避免在本地未配置好测试环境时误打线上。
"""

import logging
import time
from dataclasses import asdict, is_dataclass
from datetime import datetime, timedelta, timezone

import pytest

from sunbay_nexus_sdk import (
    NexusClient,
    SunbayBusinessError,
    SunbayNetworkError,
    TransactionStatus,
    TransactionType,
)
from sunbay_nexus_sdk.models.common import SaleAmount
from sunbay_nexus_sdk.models.request import QueryRequest, SaleRequest


# 注意：这里的参数与 Java 版本的 NexusClientTest 保持一致，
# 仅用于测试环境，不用于生产环境。

TEST_API_KEY = "mfgyn0hvs9teofvuad03jkwvmtrdm2sb"
TEST_BASE_URL = "https://open.sunbay.dev"

TEST_APP_ID = "test_sm6par3xf4d3tkum"
TEST_MERCHANT_ID = "M1254947005"
TEST_TERMINAL_SN = "TESTSN1764580772062"

# Java NexusClientTest testQuery 中使用的请求 ID
EXISTING_TRANSACTION_REQUEST_ID = "PAY_REQ_1765785418963"

# Dedicated logger for integration tests
test_logger = logging.getLogger("sunbay_nexus_sdk.tests.integration")


def _iso8601_after_minutes(minutes: int) -> str:
    # Align with Java test implementation:
    # ZonedDateTime.now().plusMinutes(10).format("yyyy-MM-dd'T'HH:mm:ssXXX")
    dt = datetime.now().astimezone() + timedelta(minutes=minutes)
    # ISO 8601 with timezone offset like +08:00
    return dt.isoformat(timespec="seconds")


def _build_client() -> NexusClient:
    return NexusClient(
        api_key=TEST_API_KEY,
        base_url=TEST_BASE_URL,
    )


def test_sale_integration():
    """
    真正调用 sale 接口的集成测试，用于验证 NexusClient.sale 整条链路。
    """
    client = _build_client()

    amount = SaleAmount(order_amount=222.0, pricing_currency="USD")
    request = SaleRequest(
        app_id=TEST_APP_ID,
        merchant_id=TEST_MERCHANT_ID,
        reference_order_id=f"ORDER{int(time.time() * 1000)}",
        transaction_request_id=f"PAY_REQ_{int(time.time() * 1000)}",
        amount=amount,
        description="Integration test sale",
        terminal_sn=TEST_TERMINAL_SN,
        attach='{"storeId":"STORE001","tableNo":"T05"}',
        notify_url="https://merchant.com/notify",
        time_expire=_iso8601_after_minutes(10),
    )

    try:
        response = client.sale(request)
        assert response is not None
        assert response.transaction_id
        # If we reach here, code == "0" (success), no need to check is_success()

        # 只打印关键字段，避免整包输出过长。
        test_logger.info(
            "Sale integration parsed by SDK - code=%s, msg=%s, trace_id=%s, "
            "transaction_id=%s, reference_order_id=%s, transaction_request_id=%s",
            getattr(response, "code", None),
            getattr(response, "msg", None),
            getattr(response, "trace_id", None),
            getattr(response, "transaction_id", None),
            getattr(response, "reference_order_id", None),
            getattr(response, "transaction_request_id", None),
        )
    except SunbayNetworkError as e:
        # 打印网络异常，测试视为失败，方便在 CI 或本地排查。
        pytest.fail(f"Network error during sale integration test: {e}")
    except SunbayBusinessError as e:
        # 打印业务异常，测试视为失败，不再跳过。
        pytest.fail(f"API business error during sale integration test: {e.code} {e}")


def test_query_integration():
    """
    真正调用 query 接口的集成测试，用于验证 NexusClient.query 整条链路。
    前提是你已经有一笔已存在的交易 ID 或请求 ID。
    """
    client = _build_client()

    request = QueryRequest(
        app_id=TEST_APP_ID,
        merchant_id=TEST_MERCHANT_ID,
        transaction_request_id=EXISTING_TRANSACTION_REQUEST_ID,
    )

    try:
        response = client.query(request)
        assert response is not None
        assert response.transaction_status is not None
        # If we reach here, code == "0" (success), no need to check is_success()

        # Verify enum values match API response
        if response.transaction_status:
            # API returns code (e.g., "S"), verify it matches enum
            status_enum = TransactionStatus(response.transaction_status)
            test_logger.info("Transaction status enum verification: %s -> %s", response.transaction_status, status_enum)

        if response.transaction_type:
            # API returns code (e.g., "SALE"), verify it matches enum
            type_enum = TransactionType(response.transaction_type)
            test_logger.info("Transaction type enum verification: %s -> %s", response.transaction_type, type_enum)

        test_logger.info(
            "Query integration parsed by SDK - code=%s, msg=%s, trace_id=%s, "
            "transaction_id=%s, transaction_request_id=%s, reference_order_id=%s, "
            "transaction_status=%s, transaction_type=%s",
            getattr(response, "code", None),
            getattr(response, "msg", None),
            getattr(response, "trace_id", None),
            getattr(response, "transaction_id", None),
            getattr(response, "transaction_request_id", None),
            getattr(response, "reference_order_id", None),
            getattr(response, "transaction_status", None),
            getattr(response, "transaction_type", None),
        )
    except SunbayNetworkError as e:
        pytest.fail(f"Network error during query integration test: {e}")
    except SunbayBusinessError as e:
        pytest.fail(f"API business error during query integration test: {e.code} {e}")


