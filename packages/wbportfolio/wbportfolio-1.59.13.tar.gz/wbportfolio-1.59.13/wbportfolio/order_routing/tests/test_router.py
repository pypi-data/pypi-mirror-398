from unittest.mock import MagicMock, PropertyMock, patch

import pytest
from django.conf import settings

from wbportfolio.order_routing import ExecutionStatus
from wbportfolio.order_routing.router import Router
from wbportfolio.pms.typing import Order


@pytest.fixture
def mock_adapter():
    adapter = MagicMock()
    return adapter


@pytest.fixture
def router(mock_adapter):
    return Router(adapter=mock_adapter)


def test_submit_as_draft_from_settings(monkeypatch, router):
    # Test default True if settings attribute missing
    monkeypatch.setattr(settings, "ORDER_ROUTING_AS_DRAFT", True)
    monkeypatch.setattr(settings, "DEBUG", False)
    assert router.submit_as_draft is True

    monkeypatch.setattr(settings, "ORDER_ROUTING_AS_DRAFT", False)
    monkeypatch.setattr(settings, "DEBUG", True)
    assert router.submit_as_draft is True

    monkeypatch.setattr(settings, "ORDER_ROUTING_AS_DRAFT", True)
    monkeypatch.setattr(settings, "DEBUG", True)
    assert router.submit_as_draft is True

    monkeypatch.setattr(settings, "ORDER_ROUTING_AS_DRAFT", False)
    monkeypatch.setattr(settings, "DEBUG", False)
    assert router.submit_as_draft is False


@patch.object(Router, "submit_as_draft", new_callable=PropertyMock)
def test_submit_rebalancing_calls_adapter_as_draft(mock_property, router, mock_adapter):
    mock_property.return_value = True
    orders = [MagicMock(spec=Order), MagicMock(spec=Order)]
    serialized_orders = ["serialized_order1", "serialized_order2"]  # simplified serialized orders as items
    confirmed_items = ["confirmed_order1", "confirmed_order2"]  # simplified deserialized orders from items
    msg = "Success message"

    mock_adapter.serialize_orders.return_value = serialized_orders
    mock_adapter.submit_rebalancing.return_value = (confirmed_items, msg)
    mock_adapter.deserialize_items.return_value = orders

    result_orders, (status, message) = router.submit_rebalancing(orders)
    assert result_orders == orders
    assert status == ExecutionStatus.IN_DRAFT
    assert message == msg
    mock_adapter.serialize_orders.assert_called_once_with(orders)
    mock_adapter.submit_rebalancing.assert_called_once_with(serialized_orders, as_draft=True)
    mock_adapter.deserialize_items.assert_called_once_with(confirmed_items)


@patch.object(Router, "submit_as_draft", new_callable=PropertyMock)
def test_submit_rebalancing_calls_adapter(mock_property, router, mock_adapter):
    mock_property.return_value = False
    orders = [MagicMock(spec=Order), MagicMock(spec=Order)]
    serialized_orders = ["serialized_order1", "serialized_order2"]  # simplified serialized orders as items
    confirmed_items = ["confirmed_order1", "confirmed_order2"]  # simplified deserialized orders from items
    msg = "Success message"

    mock_adapter.serialize_orders.return_value = serialized_orders
    mock_adapter.submit_rebalancing.return_value = (confirmed_items, msg)
    mock_adapter.deserialize_items.return_value = orders

    result_orders, (status, message) = router.submit_rebalancing(orders)
    assert result_orders == orders
    assert status == ExecutionStatus.PENDING
    assert message == msg
    mock_adapter.serialize_orders.assert_called_once_with(orders)
    mock_adapter.submit_rebalancing.assert_called_once_with(serialized_orders, as_draft=False)
    mock_adapter.deserialize_items.assert_called_once_with(confirmed_items)


def test_get_rebalance_status_returns_adapter_status(router, mock_adapter):
    expected_status = ExecutionStatus.PENDING
    expected_msg = "Status message"
    mock_adapter.get_rebalance_status.return_value = (expected_status, expected_msg)

    status, msg = router.get_rebalance_status()
    assert status == expected_status
    assert msg == expected_msg
    mock_adapter.get_rebalance_status.assert_called_once()


def test_cancel_rebalancing_returns_adapter_result(router, mock_adapter):
    mock_adapter.cancel_current_rebalancing.return_value = True
    result = router.cancel_rebalancing()
    assert result is True
    mock_adapter.cancel_current_rebalancing.assert_called_once()


def test_get_current_rebalancing_request_returns_deserialized(router, mock_adapter):
    serialized_orders = ["order1", "order2"]
    deserialized_orders = [MagicMock(spec=Order), MagicMock(spec=Order)]
    mock_adapter.get_current_rebalancing.return_value = serialized_orders
    mock_adapter.deserialize_items.return_value = deserialized_orders

    result = router.get_current_rebalancing_request()
    assert result == deserialized_orders
    mock_adapter.get_current_rebalancing.assert_called_once()
    mock_adapter.deserialize_items.assert_called_once_with(serialized_orders)
