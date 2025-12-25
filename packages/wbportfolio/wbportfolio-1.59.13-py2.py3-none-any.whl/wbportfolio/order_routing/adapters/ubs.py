import logging
from datetime import datetime

from django.conf import settings
from requests import HTTPError

from wbportfolio.api_clients.ubs import UBSNeoAPIClient
from wbportfolio.pms.typing import Order

from .. import ExecutionInstruction, ExecutionStatus, RoutingException
from . import BaseCustodianAdapter

logger = logging.getLogger("oms")


ASSET_CLASS_MAP = {
    Order.AssetType.EQUITY: "EQUITY",
    Order.AssetType.AMERICAN_DEPOSITORY_RECEIPT: "EQUITY",
}  # API can support BOND, FUTURE, OPTION, and DYNAMIC_STRATEGY
ASSET_CLASS_MAP_INV = {
    v: k for k, v in ASSET_CLASS_MAP.items()
}  # API can support BOND, FUTURE, OPTION, and DYNAMIC_STRATEGY

STATUS_MAP = {
    "Amend Pending": ExecutionStatus.PENDING,
    "Cancel Pending": ExecutionStatus.PENDING,
    "Cancelled": ExecutionStatus.CANCELLED,
    "Complete": ExecutionStatus.COMPLETED,
    "Complete (Order Cancelled)": ExecutionStatus.COMPLETED,
    "Complete (Partial Fill)": ExecutionStatus.COMPLETED,
    "In Draft": ExecutionStatus.IN_DRAFT,
    "Pending Approval": ExecutionStatus.PENDING,
    "Pending Execution": ExecutionStatus.PENDING,
    "Rebalance Cancelled": ExecutionStatus.CANCELLED,
    "Rebalance Cancelled (Executing partially)": ExecutionStatus.CANCELLED,
    "Rejected": ExecutionStatus.REJECTED,
    "Rejection Acknowledged": ExecutionStatus.PENDING,
    "Waiting for Response": ExecutionStatus.PENDING,
}
EXECUTION_INSTRUCTION_MAP = {
    ExecutionInstruction.MARKET_ON_CLOSE: "MARKET_ON_CLOSE",
    ExecutionInstruction.GUARANTEED_MARKET_ON_CLOSE: "GUARANTEED_MARKET_ON_CLOSE",
    ExecutionInstruction.GUARANTEED_MARKET_ON_OPEN: "GUARANTEED_MARKET_ON_OPEN",
    ExecutionInstruction.GPW_MARKET_ON_CLOSE: "GPW_MARKET_ON_CLOSE",
    ExecutionInstruction.MARKET_ON_OPEN: "MARKET_ON_OPEN",
    ExecutionInstruction.IN_LINE_WITH_VOLUME: "IN_LINE_WITH_VOLUME",
    ExecutionInstruction.LIMIT_ORDER: "LIMIT_ORDER",
    ExecutionInstruction.VWAP: "VWAP",
    ExecutionInstruction.TWAP: "TWAP",
}
EXECUTION_INSTRUCTION_MAP_INV = {v: k for k, v in EXECUTION_INSTRUCTION_MAP.items()}


class CustodianAdapter(BaseCustodianAdapter):
    client: UBSNeoAPIClient

    def __init__(self, *args, raise_exception: bool = False, **kwargs):
        super().__init__(*args, **kwargs)
        self.raise_exception = raise_exception

    def _handle_response(self, res):
        logger.info(res["message"])
        if errors := res.get("errors"):
            logger.warning(errors)
            if self.raise_exception:
                raise RoutingException(errors)

    def _serialize_execution_instruction(
        self, execution_instruction: ExecutionInstruction, execution_parameters: dict
    ):
        repr = EXECUTION_INSTRUCTION_MAP[execution_instruction]
        if execution_parameters:
            if execution_instruction == ExecutionInstruction.IN_LINE_WITH_VOLUME:
                repr += f':{execution_parameters["percent"]:.0f%}'
            elif execution_instruction == ExecutionInstruction.LIMIT_ORDER:
                repr += f':{execution_parameters["price"]:.1f}'
                if good_for_date := execution_parameters.get("good_for_date"):
                    repr += f",{good_for_date}"
            elif (
                execution_instruction == ExecutionInstruction.VWAP
                or execution_instruction == ExecutionInstruction.TWAP
            ):
                repr += f':{execution_parameters["period"]},{execution_parameters["time"]}'
        return repr

    def serialize_orders(self, orders: list[Order]) -> list[dict[str, str]]:
        items = []
        for order in orders:
            if order.refinitiv_identifier_code:
                identifier_type, identifier = "RIC", order.refinitiv_identifier_code
            elif order.bloomberg_ticker:
                identifier_type, identifier = "BBTICKER", order.bloomberg_ticker
            else:
                identifier_type, identifier = "SEDOL", order.sedol
            item = {
                "assetClass": ASSET_CLASS_MAP[order.asset_class],
                "identifierType": identifier_type,
                "identifier": identifier,
                "executionInstruction": self._serialize_execution_instruction(
                    order.execution_instruction, order.execution_instruction_parameters
                ),
                "userElementId": str(order.id),
                "tradeDate": order.trade_date.strftime("%Y-%m-%d"),
            }
            if order.shares:
                item["sharesToTrade"] = str(order.shares)
            else:
                item["targetWeight"] = str(order.target_weight * 100)
            items.append(item)
        return items

    def deserialize_items(self, items: list[dict[str, str]]):
        orders = []
        for item in items:
            orders.append(
                Order(
                    id=item.get("userElementId"),
                    asset_class=ASSET_CLASS_MAP_INV[item.get("assetClass")],
                    refinitiv_identifier_code=item.get(
                        "ric", item["identifier"] if item.get("identifierType") == "RIC" else None
                    ),
                    bloomberg_ticker=item["identifier"] if item.get("identifierType") == "BBTICKER" else None,
                    sedol=item["identifier"] if item.get("identifierType") == "SEDOL" else None,
                    trade_date=datetime.strptime(item.get("tradeDate"), "%Y-%m-%d"),
                    target_weight=float(item["targetWeight"]) / 100 if "targetWeight" in item else None,
                    shares=float(item["sharesToTrade"]) if "sharesToTrade" in item else None,
                    execution_instruction=EXECUTION_INSTRUCTION_MAP_INV[item["executionInstruction"]],
                )
            )
        return orders

    def authenticate(self) -> bool:
        """
        Authenticate or renew tokens with the custodian API.
        Raises an exception if authentication fails.
        """
        self.client = UBSNeoAPIClient(settings.UBS_NEO_API_TOKEN)
        return True

    def is_valid(self) -> bool:
        """
        Check whether the given isin is valid and can be rebalanced
        """

        try:
            status_res = self.client.get_rebalance_service_status()

            isin_res = self.client.get_rebalance_status_for_isin(self.isin)
            self._handle_response(status_res)
            self._handle_response(isin_res)
            return (
                status_res["status"] == UBSNeoAPIClient.SUCCESS_VALUE
                and isin_res["status"] == UBSNeoAPIClient.SUCCESS_VALUE
            )
        except (HTTPError, KeyError) as e:
            logger.warning(f"Couldn't validate adapter: {str(e)}")
            return False

    def submit_rebalancing(
        self, items: list[dict[str, str]], as_draft: bool = True
    ) -> tuple[list[dict[str, str]], str]:
        """
        Submit a rebalance order for the certificate.
        """
        if not as_draft:
            res = self.client.submit_rebalance(self.isin, items)
        else:
            res = self.client.save_draft(self.isin, items)
        self._handle_response(res)
        return res["rebalanceItems"], res["message"]

    def cancel_current_rebalancing(self) -> bool:
        """
        Cancel an existing rebalance order identified by ISIN.
        """
        try:
            res = self.client.cancel_rebalance(self.isin)
            self._handle_response(res)
            return res["status"] == UBSNeoAPIClient.SUCCESS_VALUE
        except (HTTPError, KeyError):
            return False

    def get_rebalance_status(self) -> tuple[ExecutionStatus, str]:
        res = self.client.get_rebalance_status_for_isin(self.isin)
        self._handle_response(res)
        status = res.get("rebalanceStatus", "")
        return STATUS_MAP.get(status, ExecutionStatus.UNKNOWN), status

    def get_current_rebalancing(self) -> list[dict[str, str]]:
        """
        Fetch the current rebalance request details for a certificate.
        """
        res = self.client.get_current_rebalance_request(self.isin)
        self._handle_response(res)
        return res["rebalanceItems"]
