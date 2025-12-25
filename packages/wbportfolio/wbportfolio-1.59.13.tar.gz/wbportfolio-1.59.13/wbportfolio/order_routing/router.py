from django.conf import settings

from wbportfolio.order_routing import ExecutionStatus
from wbportfolio.order_routing.adapters import BaseCustodianAdapter
from wbportfolio.pms.typing import Order


class Router:
    def __init__(self, adapter: BaseCustodianAdapter):
        self.adapter = adapter

    @property
    def submit_as_draft(self):
        return getattr(settings, "DEBUG", True) or getattr(settings, "ORDER_ROUTING_AS_DRAFT", True)

    def submit_rebalancing(self, orders: list[Order]) -> tuple[list[Order], tuple[str, str]]:
        """
        Submit a rebalance order for the certificate.
        """
        items = self.adapter.serialize_orders(orders)
        confirmed_items, msg = self.adapter.submit_rebalancing(items, as_draft=self.submit_as_draft)
        status = ExecutionStatus.IN_DRAFT if self.submit_as_draft else ExecutionStatus.PENDING
        return self.adapter.deserialize_items(confirmed_items), (status, msg)

    def get_rebalance_status(self) -> tuple[ExecutionStatus, str]:
        return self.adapter.get_rebalance_status()

    def cancel_rebalancing(self) -> bool:
        return self.adapter.cancel_current_rebalancing()

    def get_current_rebalancing_request(self) -> list[Order]:
        items = self.adapter.get_current_rebalancing()
        return self.adapter.deserialize_items(items)
