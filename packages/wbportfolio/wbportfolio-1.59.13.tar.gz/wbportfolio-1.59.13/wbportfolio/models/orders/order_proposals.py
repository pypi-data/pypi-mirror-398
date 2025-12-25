import logging
import math
from contextlib import suppress
from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Self, TypeVar

import pandas as pd
from celery import shared_task
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import DatabaseError, models
from django.db.models import (
    F,
    OuterRef,
    Q,
    QuerySet,
    Subquery,
    Sum,
    Value,
)
from django.db.models.functions import Coalesce, Round
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy
from django_fsm import FSMField, transition
from pandas._libs.tslibs.offsets import BDay
from requests import HTTPError
from wbcompliance.models.risk_management.mixins import RiskCheckMixin
from wbcore.contrib.authentication.models import User
from wbcore.contrib.icons import WBIcon
from wbcore.contrib.notifications.dispatch import send_notification
from wbcore.contrib.notifications.utils import create_notification_type
from wbcore.enums import RequestType
from wbcore.metadata.configs.buttons import ActionButton
from wbcore.models import WBModel
from wbcore.utils.models import CloneMixin
from wbcore.workers import Queue
from wbfdm.enums import MarketData
from wbfdm.models import InstrumentPrice
from wbfdm.models.instruments.instruments import Cash, Instrument
from wbfdm.signals import investable_universe_updated

from wbportfolio.models.asset import AssetPosition
from wbportfolio.models.roles import PortfolioRole
from wbportfolio.pms.typing import Order as OrderDTO
from wbportfolio.pms.typing import Portfolio as PortfolioDTO

from ...order_routing import ExecutionStatus, RoutingException
from ...order_routing.router import Router
from .. import Portfolio
from .orders import Order

logger = logging.getLogger("pms")

SelfOrderProposal = TypeVar("SelfOrderProposal", bound="OrderProposal")


class OrderProposal(CloneMixin, RiskCheckMixin, WBModel):
    trade_date = models.DateField(verbose_name="Trading Date")

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        DENIED = "DENIED", "Denied"
        EXECUTION = "EXECUTION", "Execution"
        CONFIRMED = "CONFIRMED", "Confirmed"
        FAILED = "FAILED", "Failed"

    comment = models.TextField(default="", verbose_name="Order Comment", blank=True)
    status = FSMField(default=Status.DRAFT, choices=Status.choices, verbose_name="Status")
    rebalancing_model = models.ForeignKey(
        "wbportfolio.RebalancingModel",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="order_proposals",
        verbose_name="Rebalancing Model",
        help_text="Rebalancing Model that generates the target portfolio",
    )
    portfolio = models.ForeignKey(
        "wbportfolio.Portfolio", related_name="order_proposals", on_delete=models.PROTECT, verbose_name="Portfolio"
    )
    creator = models.ForeignKey(
        "directory.Person",
        blank=True,
        null=True,
        related_name="order_proposals",
        on_delete=models.PROTECT,
        verbose_name="Owner",
    )
    approver = models.ForeignKey(
        "directory.Person",
        blank=True,
        null=True,
        related_name="approver_order_proposals",
        on_delete=models.PROTECT,
        verbose_name="Approver",
    )
    min_order_value = models.IntegerField(
        default=0, verbose_name="Minimum Order Value", help_text="Minimum Order Value in the Portfolio currency"
    )
    min_weighting = models.DecimalField(
        max_digits=9,
        decimal_places=Order.ORDER_WEIGHTING_PRECISION,
        default=Decimal(0),
        help_text="The minimum weight allowed for this order proposal ",
        verbose_name="Minimum Weight",
        validators=[MinValueValidator(Decimal("0")), MaxValueValidator(Decimal("1"))],
    )

    total_cash_weight = models.DecimalField(
        default=Decimal("0"),
        decimal_places=4,
        max_digits=5,
        verbose_name="Total Cash Weight",
        help_text="The desired percentage for the cash component. The remaining percentage (100% minus this value) will be allocated to total target weighting. Default is 0%.",
        validators=[MinValueValidator(Decimal("0")), MaxValueValidator(Decimal("1"))],
    )
    total_effective_portfolio_contribution = models.DecimalField(
        default=Decimal("1"),
        max_digits=Order.ORDER_WEIGHTING_PRECISION * 2 + 3,
        decimal_places=Order.ORDER_WEIGHTING_PRECISION * 2,
    )
    execution_status = models.CharField(
        blank=True, default="", choices=ExecutionStatus.choices, verbose_name="Execution Status"
    )
    execution_status_detail = models.CharField(blank=True, default="", verbose_name="Execution Status Detail")
    execution_comment = models.CharField(blank=True, default="", verbose_name="Execution Comment")

    class Meta:
        verbose_name = "Order Proposal"
        verbose_name_plural = "Order Proposals"
        constraints = [
            models.UniqueConstraint(
                fields=["portfolio", "trade_date"],
                name="unique_order_proposal",
            ),
        ]

        notification_types = [
            create_notification_type(
                "wbportfolio.order_proposal.push_model_changes",
                "Push Model Changes",
                "Sends a notification when a the change/orders are pushed to modeled after portfolios",
                True,
                True,
                True,
            )
        ]

    def __str__(self) -> str:
        return f"{self.portfolio.name}: {self.trade_date} ({self.status})"

    def save(self, *args, **kwargs):
        # if the order proposal is created, we default these fields with the portfolio default value for automatic value assignement
        if not self.id and not self.min_order_value:
            self.min_order_value = self.portfolio.default_order_proposal_min_order_value
        if not self.id and not self.min_weighting:
            self.min_weighting = self.portfolio.default_order_proposal_min_weighting
        if not self.id and not self.total_cash_weight:
            self.total_cash_weight = self.portfolio.default_order_proposal_total_cash_weight
        # if a order proposal is created before the existing earliest order proposal, we automatically shift the linked instruments inception date to allow automatic NAV computation since the new inception date
        if not self.portfolio.order_proposals.filter(trade_date__lt=self.trade_date).exists():
            # we need to set the inception date as the first order proposal trade date (and thus, the first position date). We expect a NAV at 100 then
            self.portfolio.instruments.filter(inception_date__gt=self.trade_date).update(
                inception_date=self.trade_date
            )
        super().save(*args, **kwargs)

    @property
    def check_evaluation_date(self):
        return self.trade_date

    @property
    def checked_object(self) -> Any:
        return self.portfolio

    @cached_property
    def portfolio_total_asset_value(self) -> Decimal:
        return self.get_portfolio_total_asset_value()

    @cached_property
    def last_effective_date(self) -> date:
        try:
            return self.portfolio.assets.filter(date__lt=self.trade_date).latest("date").date
        except AssetPosition.DoesNotExist:
            return self.value_date

    @property
    def custodian_router(self) -> Router | None:
        try:
            return Router(self.portfolio.get_authenticated_custodian_adapter(raise_exception=True))
        except ValueError as e:
            logger.warning("Error while instantiating custodian adapter: %s", e)

    @cached_property
    def value_date(self) -> date:
        return (self.trade_date - BDay(1)).date()

    @property
    def previous_order_proposal(self) -> SelfOrderProposal | None:
        future_proposals = OrderProposal.objects.filter(portfolio=self.portfolio).filter(
            trade_date__lt=self.trade_date, status=OrderProposal.Status.CONFIRMED
        )
        if future_proposals.exists():
            return future_proposals.latest("trade_date")
        return None

    @property
    def next_order_proposal(self) -> SelfOrderProposal | None:
        future_proposals = OrderProposal.objects.filter(portfolio=self.portfolio).filter(
            trade_date__gt=self.trade_date, status=OrderProposal.Status.CONFIRMED
        )
        if future_proposals.exists():
            return future_proposals.earliest("trade_date")
        return None

    @property
    def cash_component(self) -> Cash:
        return self.portfolio.cash_component

    @property
    def total_effective_portfolio_weight(self) -> Decimal:
        return Decimal("1.0")

    @property
    def total_expected_target_weight(self) -> Decimal:
        return self.total_effective_portfolio_weight - self.total_cash_weight

    @property
    def can_be_confirmed(self) -> bool:
        return self.portfolio.can_be_rebalanced and self.status == self.Status.APPROVED

    @property
    def can_be_applied(self):
        return not self.has_non_successful_checks and self.portfolio.is_manageable

    @cached_property
    def total_effective_portfolio_cash_weight(self) -> Decimal:
        return self.portfolio.assets.filter(
            models.Q(date=self.last_effective_date)
            & (models.Q(underlying_quote__is_cash=True) | models.Q(underlying_quote__is_cash_equivalent=True))
        ).aggregate(Sum("weighting"))["weighting__sum"] or Decimal("0")

    def get_portfolio_total_asset_value(self):
        return self.portfolio.get_total_asset_value(self.last_effective_date)
        # return self.orders.annotate(
        #     effective_shares=Coalesce(
        #         Subquery(
        #             AssetPosition.objects.filter(
        #                 underlying_quote=OuterRef("underlying_instrument"),
        #                 date=self.last_effective_date,
        #                 portfolio=self.portfolio,
        #             )
        #             .values("portfolio")
        #             .annotate(s=Sum("shares"))
        #             .values("s")[:1]
        #         ),
        #         Decimal(0),
        #     ),
        #     effective_total_value_fx_portfolio=F("effective_shares") * F("currency_fx_rate") * F("price"),
        # ).aggregate(s=Sum("effective_total_value_fx_portfolio"))["s"] or Decimal(0.0)

    def get_orders(self):
        # TODO Issue here: the cash is subqueried on the portfolio, on portfolio such as the fund, there is multiple cash component, that we exclude in the orders (and use a unique cash position instead)
        # so the subquery returns the previous position (probably USD), but is missing the other cash aggregation. We need to find a way to handle that properly

        orders = self.orders.all().annotate(
            total_effective_portfolio_contribution=Value(self.total_effective_portfolio_contribution),
            last_effective_date=Subquery(
                AssetPosition.unannotated_objects.filter(
                    date__lt=OuterRef("value_date"),
                    portfolio=OuterRef("portfolio"),
                )
                .order_by("-date")
                .values("date")[:1]
            ),
            previous_weight=models.Case(
                models.When(
                    underlying_instrument__is_cash=False,
                    then=Coalesce(
                        Subquery(
                            AssetPosition.unannotated_objects.filter(
                                underlying_quote=OuterRef("underlying_instrument"),
                                date=OuterRef("last_effective_date"),
                                portfolio=OuterRef("portfolio"),
                            )
                            .values("portfolio")
                            .annotate(s=Sum("weighting"))
                            .values("s")[:1]
                        ),
                        Decimal(0),
                    ),
                ),
                default=Value(self.total_effective_portfolio_cash_weight),
            ),
            contribution=F("previous_weight") * (F("daily_return") + Value(Decimal("1"))),
            effective_weight=Round(
                models.Case(
                    models.When(total_effective_portfolio_contribution=Value(Decimal("0")), then=Value(Decimal("0"))),
                    default=F("contribution") / F("total_effective_portfolio_contribution") - F("quantization_error"),
                ),
                precision=Order.ORDER_WEIGHTING_PRECISION,
            ),
            target_weight=Round(F("effective_weight") + F("weighting"), precision=Order.ORDER_WEIGHTING_PRECISION),
            effective_shares=Coalesce(
                Subquery(
                    AssetPosition.objects.filter(
                        underlying_quote=OuterRef("underlying_instrument"),
                        date=OuterRef("last_effective_date"),
                        portfolio=OuterRef("portfolio"),
                    )
                    .values("portfolio")
                    .annotate(s=Sum("shares"))
                    .values("s")[:1]
                ),
                Decimal(0),
            ),
            target_shares=F("effective_shares") + F("shares"),
        )

        return orders.annotate(
            has_warnings=models.Case(
                models.When(
                    (models.Q(price=0) & ~models.Q(target_weight=0)) | models.Q(target_weight__lt=0), then=Value(True)
                ),
                default=Value(False),
            ),
        )

    def get_trades_batch(self):
        return self._get_default_effective_portfolio().get_orders(self.get_target_portfolio())

    @property
    def can_be_executed(self) -> bool:
        return (
            self.custodian_router is not None
            and not self.has_non_successful_checks
            and self.status == self.Status.APPROVED
            and (not self.execution_status or self.execution_status == ExecutionStatus.CANCELLED)
        )

    def can_execute(self, user: User) -> bool:
        return (not self.approver or user.is_superuser or user != self.approver.user_account) and self.can_be_executed

    def prepare_orders_for_execution(self, prioritize_target_weight: bool = False) -> list[OrderDTO]:
        """Prepares executable orders by filtering and converting them for submission.

        Filters out cash instruments and orders with zero weighting and shares, then
        creates OrderDTOs for those having valid instrument identifiers. Orders with
        unsupported asset classes or missing identifiers are marked as ignored with comments.
        Updates ignored orders in bulk.

        Args:
            prioritize_target_weight: If True, prioritize target weight over share quantities
              when preparing order quantities.

        Returns:
            A list of OrderDTO objects ready for execution submission.
        """
        executable_orders = []
        updated_orders = []
        self.orders.update(execution_status=Order.ExecutionStatus.IGNORED)
        for order in (
            self.get_orders()
            .exclude(models.Q(underlying_instrument__is_cash=True) | (models.Q(weighting=0) & models.Q(shares=0)))
            .select_related("underlying_instrument")
        ):
            instrument = order.underlying_instrument
            asset_class = instrument.get_security_ancestor().instrument_type.key.upper()

            try:
                if instrument.refinitiv_identifier_code or instrument.ticker or instrument.sedol:
                    quantity = {"target_weight": float(order.target_weight)}
                    if not prioritize_target_weight and order.shares:
                        quantity["shares"] = float(order.shares)
                        quantity["target_shares"] = (
                            float(order.target_shares) if order.target_shares is not None else None
                        )

                    executable_orders.append(
                        OrderDTO(
                            id=order.id,
                            asset_class=OrderDTO.AssetType[asset_class],
                            weighting=float(order.weighting),
                            trade_date=order.value_date,
                            refinitiv_identifier_code=instrument.refinitiv_identifier_code,
                            bloomberg_ticker=instrument.bloomberg_ticker,
                            sedol=instrument.sedol,
                            execution_instruction=order.execution_instruction,
                            execution_instruction_parameters=order.execution_instruction_parameters,
                            **quantity,
                        )
                    )
                else:
                    order.execution_status = Order.ExecutionStatus.FAILED
                    order.execution_comment = "Underlying instrument does not have a valid identifier."
                    updated_orders.append(order)
            except (AttributeError, KeyError):
                order.execution_status = Order.ExecutionStatus.FAILED
                order.execution_comment = f"Unsupported asset class {asset_class.title()}."
                updated_orders.append(order)

        Order.objects.bulk_update(updated_orders, ["execution_status", "execution_comment"])
        return executable_orders

    def handle_orders(self, orders: list[OrderDTO]):
        """Updates order statuses based on confirmed execution results.

        For each confirmed order, updates the corresponding database record with its
        execution status, comment, and price when available. Orders not present in the
        confirmation list are marked as failed.

        Args:
            orders: List of confirmed order DTOs returned from the custodian router.
        """
        leftover_orders = self.orders.filter(underlying_instrument__is_cash=False).all()
        # portfolio_value = self.portfolio_total_asset_value

        for confirmed_order in orders:
            with suppress(Order.DoesNotExist):
                order = leftover_orders.get(id=confirmed_order.id)
                order.execution_status = Order.ExecutionStatus.CONFIRMED
                order.execution_comment = confirmed_order.comment
                # if execution_price := confirmed_order.execution_price:
                #     order.price = round(Decimal(execution_price), 2)
                #     order.execution_status = Order.ExecutionStatus.EXECUTED
                # if shares := confirmed_order.shares:
                #     order.set_shares(Decimal(shares), portfolio_value)
                # elif weighting := confirmed_order.weighting:
                #     order.set_weighting(Decimal(weighting), portfolio_value)
                order.save()
                leftover_orders = leftover_orders.exclude(id=order.id)

        leftover_orders.delete()
        self.refresh_cash_position()

    def execute_orders(self, prioritize_target_weight: bool = False):
        """Submits prepared orders for execution via the custodian router and updates status.

        Prepares orders based on the target weight priority, submits them for execution,
        handles confirmed orders on success, and records execution status and comments.
        Logs and marks the execution as failed if submission raises an error.

        Args:
            prioritize_target_weight: Whether to prioritize target weights when preparing orders.
        """
        self.status = self.Status.EXECUTION
        orders = self.prepare_orders_for_execution(prioritize_target_weight=prioritize_target_weight)
        try:
            confirmed_orders, (status, rebalancing_comment) = self.custodian_router.submit_rebalancing(orders)
            self.handle_orders(confirmed_orders)
        except (ValueError, RoutingException, HTTPError) as e:
            logger.error(
                "Order Execution: routing or network exception ecountered.",
                extra={"order_proposal": self, "detail": e},
            )
            status = ExecutionStatus.FAILED
            rebalancing_comment = str(e)
        self.execution_status = status
        self.execution_comment = rebalancing_comment
        self.save()

    def refresh_execution_status(self):
        """Updates execution status from the custodian router and saves the model.

        Retrieves the latest rebalance status and details, assigns them to the instance,
        and persists changes to the database.
        """
        self.execution_status, self.execution_status_detail = self.custodian_router.get_rebalance_status()
        if self.execution_status == ExecutionStatus.COMPLETED:
            self.execution_status = self.Status.CONFIRMED
        self.save()

    def cancel_rebalancing(self):
        """Cancels the ongoing rebalance via the custodian router and updates the model.

        If cancellation succeeds, clears execution details, marks the status as cancelled,
        saves the instance, and returns the cancellation status.
        """
        cancel_rebalancing_status = self.custodian_router.cancel_rebalancing()
        if cancel_rebalancing_status:
            (
                self.execution_comment,
                self.execution_status_detail,
                self.execution_status,
            ) = (
                "",
                "",
                ExecutionStatus.CANCELLED,
            )
            self.save()
        return cancel_rebalancing_status

    def get_target_portfolio(self):
        positions = []
        instrument_ids = []
        for order in self.get_orders():
            pos = order.to_dto()
            instrument_ids.append(pos.underlying_instrument)
            positions.append(pos)

        # insert latest market data
        df = pd.DataFrame(
            Instrument.objects.filter(id__in=instrument_ids).dl.market_data(
                [MarketData.MARKET_CAPITALIZATION_CONSOLIDATED, MarketData.VOLUME, MarketData.CLOSE],
                from_date=self.trade_date - timedelta(days=50),
                to_date=self.trade_date,
                target_currency="USD",
            )
        )
        df["volume_50d"] = df["volume"]
        df = (
            df[
                [
                    "valuation_date",
                    "instrument_id",
                    "volume",
                    "volume_50d",
                    "close",
                    "market_capitalization_consolidated",
                ]
            ]
            .sort_values(by="valuation_date")
            .groupby("instrument_id")
            .agg(
                {
                    "volume": "last",
                    "volume_50d": "mean",
                    "close": "last",
                    "market_capitalization_consolidated": "last",
                }
            )
        )
        df["volume_usd"] = df.volume * df.close

        for pos in positions:
            if pos.underlying_instrument in df.index:
                pos.market_capitalization_usd = df.loc[pos.underlying_instrument, "market_capitalization_consolidated"]
                pos.volume_usd = (
                    df.loc[pos.underlying_instrument, "volume"] * df.loc[pos.underlying_instrument, "close"]
                )
                if pos.shares:
                    if volume_50d := df.loc[pos.underlying_instrument, "volume_50d"]:
                        pos.daily_liquidity = float(pos.shares) / volume_50d / 0.33
                    if pos.market_capitalization_usd:
                        pos.market_share = (
                            float(pos.shares)
                            * df.loc[pos.underlying_instrument, "close"]
                            / pos.market_capitalization_usd
                        )

        return PortfolioDTO(positions)

    # Start tools methods
    def _clone(self, **kwargs) -> SelfOrderProposal:
        """
        Method to clone self as a new order proposal. It will automatically shift the order date if a proposal already exists
        Args:
            **kwargs: The keyword arguments
        Returns:
            The cloned order proposal
        """
        trade_date = kwargs.get("clone_date", self.trade_date)

        # Find the next valid order date
        while OrderProposal.objects.filter(portfolio=self.portfolio, trade_date=trade_date).exists():
            trade_date += timedelta(days=1)

        order_proposal_clone = OrderProposal.objects.create(
            trade_date=trade_date,
            comment=kwargs.get("clone_comment", self.comment),
            status=OrderProposal.Status.DRAFT,
            rebalancing_model=self.rebalancing_model,
            portfolio=self.portfolio,
            creator=self.creator,
        )
        for order in self.orders.all():
            order.id = None
            order.order_proposal = order_proposal_clone
            order.save()

        return order_proposal_clone

    def normalize_orders(self, total_cash_weight: Decimal):
        """
        Normalize the orders to accomodate the given cash weight
        """
        self.total_cash_weight = total_cash_weight
        self.reset_orders()

    def fix_quantization(self):
        if self.orders.exists():
            orders = self.get_orders()
            t_weight = orders.aggregate(models.Sum("effective_weight"))["effective_weight__sum"] or Decimal("0.0")
            quantization_error = orders.aggregate(models.Sum("quantization_error"))[
                "quantization_error__sum"
            ] or Decimal("0.0")
            # we handle quantization error due to the decimal max digits. In that case, we take the biggest order (highest weight) and we remove the quantization error
            if t_weight and (
                quantize_error := ((t_weight + quantization_error) - self.total_effective_portfolio_weight)
            ):
                biggest_order = orders.exclude(underlying_instrument__is_cash=True).latest("effective_weight")
                biggest_order.quantization_error = quantize_error
                biggest_order.save()

    def get_default_target_portfolio(self, use_desired_target_weight: bool = False, **kwargs) -> PortfolioDTO:
        if self.rebalancing_model:
            params = {}
            if rebalancer := getattr(self.portfolio, "automatic_rebalancer", None):
                params.update(rebalancer.parameters)
            params.update(kwargs)
            return self.rebalancing_model.get_target_portfolio(
                self.portfolio, self.trade_date, self.value_date, **params
            )
        return self._get_default_effective_portfolio(
            include_delta_weight=True, use_desired_target_weight=use_desired_target_weight
        )

    def _get_default_effective_portfolio(
        self, include_delta_weight: bool = False, use_desired_target_weight: bool = False
    ):
        """
        Converts the internal portfolio state and pending orders into a PortfolioDTO.

        Returns:
            PortfolioDTO: Object that encapsulates all portfolio positions.
        """
        portfolio = {}

        try:
            analytic_portfolio = self.portfolio.get_analytic_portfolio(self.last_effective_date, use_dl=True)
            last_returns, contribution = analytic_portfolio.get_contributions()
            last_returns = last_returns.to_dict()
            effective_weights = analytic_portfolio.get_next_weights()
        except ValueError:
            effective_weights, last_returns, contribution = {}, {}, 1
        self.total_effective_portfolio_contribution = Decimal(contribution)
        # 1. Gather all non-cash, positively weighted assets from the existing portfolio.
        for asset in self.portfolio.assets.filter(
            date=self.last_effective_date,
            weighting__gt=0,
        ):
            portfolio[asset.underlying_quote] = {
                "shares": asset._shares,
                "weighting": Decimal(effective_weights.get(asset.underlying_quote.id, asset.weighting))
                if not use_desired_target_weight
                else Decimal("0"),
                "price": asset._price,
                "currency_fx_rate": asset._currency_fx_rate,
            }

        # 2. Add or update non-cash orders, possibly overriding weights.
        for order in self.get_orders().filter(
            underlying_instrument__is_cash=False, underlying_instrument__is_cash_equivalent=False
        ):
            order.daily_return = last_returns.get(order.underlying_instrument.id, 0)
            if use_desired_target_weight and order.desired_target_weight:
                weighting = order.desired_target_weight
            else:
                weighting = order._effective_weight
                if include_delta_weight:
                    weighting += order.weighting
            portfolio[order.underlying_instrument] = {
                "weighting": weighting,
                "shares": order._effective_shares,
                "price": order.price,
                "currency_fx_rate": order.currency_fx_rate,
            }
        positions = []

        # 5. Build PositionDTO objects for all instruments.
        for instrument, row in portfolio.items():
            daily_return = Decimal(last_returns.get(instrument.id, 0))
            # Assemble the position object
            pos = Order.create_dto(
                instrument,
                row["weighting"],
                row["price"],
                self.last_effective_date,
                shares=row["shares"],
                daily_return=daily_return,
                currency_fx_rate=row["currency_fx_rate"],
            )
            positions.append(pos)
        total_weighting = sum(map(lambda pos: pos.weighting, positions))
        # 6. Optionally include a cash position to balance the total weighting.
        if (
            portfolio
            and total_weighting
            and self.total_effective_portfolio_weight
            and (cash_weight := self.total_effective_portfolio_weight - total_weighting)
        ):
            cash_position = self.get_estimated_target_cash(target_cash_weight=cash_weight)
            positions.append(cash_position._build_dto())
        return PortfolioDTO(positions)

    def reset_orders(
        self,
        effective_portfolio: PortfolioDTO
        | None = None,  # we need to have this parameter as sometime we want to get the effective portfolio from drifted weight (unsaved)
        target_portfolio: PortfolioDTO | None = None,
        use_desired_target_weight: bool = False,
    ):
        """
        Will delete all existing orders and recreate them from the method `create_or_update_trades`
        """
        if self.rebalancing_model:
            self.orders.all().delete()
        else:
            self.orders.filter(underlying_instrument__is_cash=True).delete()
        self.orders.update(quantization_error=0)
        # delete all existing orders
        # Get effective and target portfolio
        if not effective_portfolio:
            effective_portfolio = self._get_default_effective_portfolio()
        if not target_portfolio:
            target_portfolio = self.get_default_target_portfolio(use_desired_target_weight=use_desired_target_weight)

        if self.total_cash_weight:
            target_portfolio = target_portfolio.normalize_cash(self.total_cash_weight)
        if target_portfolio:
            objs = []
            portfolio_value = self.portfolio_total_asset_value
            for order_dto in effective_portfolio.get_orders(target_portfolio):
                instrument = Instrument.objects.get(id=order_dto.underlying_instrument)
                # we cannot do a bulk-create because Order is a multi table inheritance
                weighting = round(order_dto.delta_weight, Order.ORDER_WEIGHTING_PRECISION)
                daily_return = order_dto.daily_return
                try:
                    order = self.orders.get(underlying_instrument=instrument)
                    order.daily_return = daily_return
                except Order.DoesNotExist:
                    order = Order(
                        underlying_instrument=instrument,
                        order_proposal=self,
                        value_date=self.trade_date,
                        weighting=weighting,
                        daily_return=daily_return,
                    )
                order.order_type = Order.get_type(
                    weighting, round(order_dto.effective_weight, 8), round(order_dto.target_weight, 8)
                )
                order.quantization_error = order_dto.effective_quantization_error
                if order_dto.price:
                    order.price = order_dto.price
                order.pre_save()
                order.set_weighting(weighting, portfolio_value)
                order.desired_target_weight = order_dto.target_weight

                # if we cannot automatically find a price, we consider the stock is invalid and we sell it
                if not order.price and order.weighting > 0:
                    order.price = Decimal("0.0")
                    order.weighting = -order_dto.effective_weight
                objs.append(order)
            Order.objects.bulk_create(
                objs,
                update_fields=[
                    "value_date",
                    "weighting",
                    "daily_return",
                    "currency_fx_rate",
                    "order_type",
                    "portfolio",
                    "price",
                    "price_gross",
                    "desired_target_weight",
                    "quantization_error",
                    "shares",
                ],
                unique_fields=["order_proposal", "underlying_instrument"],
                update_conflicts=True,
                batch_size=1000,
            )
        # final sanity check to make sure invalid order with effective and target weight of 0 are automatically removed:
        self.get_orders().exclude(underlying_instrument__is_cash=True).filter(
            target_weight=0, effective_weight=0
        ).delete()
        self.get_orders().filter(target_weight=0).exclude(effective_shares=0).update(shares=-F("effective_shares"))
        self.fix_quantization()
        self.save()

    def refresh_cash_position(self):
        self.total_cash_weight = self.total_effective_portfolio_weight - self.get_orders().filter(
            underlying_instrument__is_cash=False
        ).aggregate(s=Sum("target_weight"))["s"] or Decimal("0")
        cash_order = None
        try:
            cash_order = Order.objects.get(order_proposal=self, underlying_instrument=self.cash_component)
        except Order.DoesNotExist:
            if self.total_cash_weight:
                cash_order = Order.objects.create(
                    order_proposal=self, underlying_instrument=self.cash_component, weighting=Decimal("0")
                )
        if cash_order:
            cash_order.weighting = self.total_cash_weight - cash_order._previous_weight
            cash_order.save()

    def refresh_returns(self):
        weights = {
            row[0]: float(row[1]) for row in self.get_orders().values_list("underlying_instrument", "previous_weight")
        }
        last_returns, contribution = self.portfolio.get_analytic_portfolio(
            self.value_date, weights=weights, use_dl=True
        ).get_contributions()
        last_returns = last_returns.to_dict()
        orders_to_update = []
        for order in self.orders.all():
            with suppress(KeyError):
                order.price = self.portfolio.builder.prices[self.trade_date][order.underlying_instrument.id]
            try:
                order.daily_return = last_returns[order.underlying_instrument.id]
            except KeyError:
                order.daily_return = Decimal("1.0")
            order.quantization_error = Decimal("0")
            orders_to_update.append(order)
        Order.objects.bulk_update(orders_to_update, ["daily_return", "price", "quantization_error"])
        self.total_effective_portfolio_contribution = Decimal(contribution)
        self.save()
        # ensure that sell orders keep having target weight at zero (might happens when returns are refreshed expost)
        for order in self.get_orders().filter(Q(order_type=Order.Type.SELL) & ~Q(weighting=-F("target_weight"))):
            order.weighting = -order.effective_weight
            order.save()

        # At this point, user needs to manually modify the orders in order to account for ex-post change. I am not sure we should we quantization at that point. To be monitored
        # self.fix_quantization()

    def replay(
        self,
        broadcast_changes_at_date: bool = True,
        reapply_order_proposal: bool = False,
        synchronous: bool = False,
        **reset_order_kwargs,
    ):
        last_order_proposal = self
        last_order_proposal_created = False
        self.portfolio.load_builder_returns((self.trade_date - BDay(3)).date(), date.today())
        while last_order_proposal and last_order_proposal.status == OrderProposal.Status.CONFIRMED:
            last_order_proposal.portfolio = self.portfolio  # we set the same ptf reference
            if not last_order_proposal_created:
                if reapply_order_proposal or last_order_proposal.rebalancing_model:
                    logger.info(f"Replaying order proposal {last_order_proposal}")
                    last_order_proposal.apply_workflow(
                        silent_exception=True, force_reset_order=True, **reset_order_kwargs
                    )
                    last_order_proposal.save()
                else:
                    logger.info(f"Resetting order proposal {last_order_proposal}")
                    last_order_proposal.reset_orders(**reset_order_kwargs)
                if last_order_proposal.status != OrderProposal.Status.CONFIRMED:
                    break
            next_order_proposal = last_order_proposal.next_order_proposal
            if next_order_proposal:
                next_trade_date = next_order_proposal.trade_date - timedelta(days=1)
            elif next_expected_rebalancing_date := self.portfolio.get_next_rebalancing_date(
                last_order_proposal.trade_date
            ):
                next_trade_date = (
                    next_expected_rebalancing_date + timedelta(days=7)
                )  # we don't know yet if rebalancing is valid and can be executed on `next_expected_rebalancing_date`, so we add safety window of 7 days
            else:
                next_trade_date = date.today()
            next_trade_date = min(next_trade_date, date.today())
            gen = self.portfolio.drift_weights(
                last_order_proposal.trade_date, next_trade_date, stop_at_rebalancing=True
            )
            try:
                while True:
                    self.portfolio.builder.add(next(gen))
            except StopIteration as e:
                overriding_order_proposal = e.value

            self.portfolio.builder.bulk_create_positions(
                delete_leftovers=True,
            )
            for draft_tp in OrderProposal.objects.filter(
                portfolio=self.portfolio,
                trade_date__gt=last_order_proposal.trade_date,
                trade_date__lte=next_trade_date,
                status=OrderProposal.Status.DRAFT,
            ):
                draft_tp.reset_orders()
            if overriding_order_proposal:
                last_order_proposal_created = True
                last_order_proposal = overriding_order_proposal
            else:
                last_order_proposal_created = False
                last_order_proposal = next_order_proposal
        self.portfolio.builder.schedule_change_at_dates(
            synchronous=synchronous, broadcast_changes_at_date=broadcast_changes_at_date
        )

    def invalidate_future_order_proposal(self):
        # Delete all future automatic order proposals and set the manual one into a draft state
        self.portfolio.order_proposals.filter(
            trade_date__gt=self.trade_date, rebalancing_model__isnull=False, comment="Automatic rebalancing"
        ).delete()
        for future_order_proposal in self.portfolio.order_proposals.filter(
            trade_date__gt=self.trade_date, status=OrderProposal.Status.CONFIRMED
        ):
            future_order_proposal.revert()
            future_order_proposal.save()

    def get_estimated_shares(
        self, weight: Decimal, underlying_quote: Instrument, quote_price: Decimal
    ) -> Decimal | None:
        """
        Estimates the number of shares for a order based on the given weight and underlying quote.

        This method calculates the estimated shares by dividing the order's total value in the portfolio's currency by the price of the underlying quote in the same currency. It handles currency conversion and suppresses any ValueError that might occur during the price retrieval.

        Args:
            weight (Decimal): The weight of the order.
            underlying_quote (Instrument): The underlying instrument for the order.

        Returns:
            Decimal | None: The estimated number of shares or None if the calculation fails.
        """
        # Retrieve the price of the underlying quote on the order date TODO: this is very slow and probably due to the to_date argument to the dl which slowdown drastically the query

        # if an order exists for this estimation and the target weight is 0, then we return the inverse of the effective shares
        with suppress(Order.DoesNotExist):
            order = self.get_orders().get(underlying_instrument=underlying_quote)
            if order.target_weight == 0:
                return -order.effective_shares
        # Calculate the order's total value in the portfolio's currency
        trade_total_value_fx_portfolio = self.portfolio_total_asset_value * weight

        # Convert the quote price to the portfolio's currency
        price_fx_portfolio = quote_price * underlying_quote.currency.convert(
            self.trade_date, self.portfolio.currency, exact_lookup=False
        )
        # If the price is valid, calculate and return the estimated shares
        if price_fx_portfolio:
            return trade_total_value_fx_portfolio / price_fx_portfolio

    def get_round_lot_size(self, shares: Decimal, underlying_quote: Instrument) -> Decimal:
        if (round_lot_size := underlying_quote.round_lot_size) != 1 and (
            not underlying_quote.exchange or underlying_quote.exchange.apply_round_lot_size
        ):
            if shares > 0:
                shares = math.ceil(shares / round_lot_size) * round_lot_size
            elif abs(shares) > round_lot_size:
                shares = math.floor(shares / round_lot_size) * round_lot_size
        return shares

    def get_estimated_target_cash(self, target_cash_weight: Decimal | None = None) -> AssetPosition:
        """
        Estimates the target cash weight and shares for a order proposal.

        This method calculates the target cash weight by summing the weights of cash orders and adding any leftover weight from non-cash orders. It then estimates the target shares for this cash component if the portfolio is not only weighting-based.

        Args:
            target_cash_weight (Decimal): the expected target cash weight (Optional). If not provided, we estimate from the existing orders

        Returns:
            tuple[Decimal, Decimal]: A tuple containing the target cash weight and the estimated target shares.
        """
        # Retrieve orders with base information
        orders = self.get_orders()
        # Calculate the total target weight of all orders
        total_target_weight = orders.filter(
            underlying_instrument__is_cash=False, underlying_instrument__is_cash_equivalent=False
        ).aggregate(s=models.Sum("target_weight"))["s"] or Decimal(0)
        if target_cash_weight is None:
            target_cash_weight = Decimal("1") - total_target_weight

        # Initialize target shares to zero
        total_target_shares = Decimal(0)

        # Get or create a cash component for the portfolio's currency
        cash_component = self.cash_component
        # If the portfolio is not only weighting-based, estimate the target shares for the cash component
        if not self.portfolio.only_weighting:
            # Estimate the target shares for the cash component
            with suppress(ValueError):
                total_target_shares = self.get_estimated_shares(target_cash_weight, cash_component, Decimal("1.0"))

        # otherwise, we create a new position
        underlying_quote_price = InstrumentPrice.objects.get_or_create(
            instrument=cash_component,
            date=self.trade_date,
            calculated=False,
            defaults={"net_value": Decimal(1)},
        )[0]
        return AssetPosition(
            underlying_quote=cash_component,
            portfolio_created=None,
            portfolio=self.portfolio,
            date=self.trade_date,
            weighting=target_cash_weight,
            initial_price=underlying_quote_price.net_value,
            initial_shares=total_target_shares,
            asset_valuation_date=self.trade_date,
            underlying_quote_price=underlying_quote_price,
            currency=cash_component.currency,
            is_estimated=False,
        )

    # WORKFLOW METHODS
    @transition(
        field=status,
        source=Status.DRAFT,
        target=Status.PENDING,
        permission=lambda instance, user: PortfolioRole.is_portfolio_manager(
            user.profile, portfolio=instance.portfolio
        ),
        custom={
            "_transition_button": ActionButton(
                method=RequestType.PATCH,
                identifiers=("wbportfolio:order",),
                icon=WBIcon.SEND.icon,
                key="submit",
                label="Submit",
                action_label="Submit",
                # description_fields="<p>Start: {{start}}</p><p>End: {{end}}</p><p>Title: {{title}}</p>",
            )
        },
    )
    def submit(self, by=None, description=None, pretrade_check: bool = True, **kwargs):
        orders = []
        orders_validation_warnings = []
        qs = self.get_orders()
        for order in qs:
            order_warnings = order.submit(
                by=by, description=description, portfolio_total_asset_value=self.portfolio_total_asset_value, **kwargs
            )

            if order_warnings:
                orders_validation_warnings.extend(order_warnings)
            orders.append(order)

        Order.objects.bulk_update(orders, ["shares", "weighting", "desired_target_weight"])
        if pretrade_check:
            self.evaluate_pretrade_checks()
        else:
            self.refresh_cash_position()
        return orders_validation_warnings

    def can_submit(self):
        errors = dict()
        return errors

    @transition(
        field=status,
        source=Status.PENDING,
        target=Status.APPROVED,
        permission=lambda instance, user: PortfolioRole.is_portfolio_manager(
            user.profile, portfolio=instance.portfolio
        )
        and not instance.has_non_successful_checks,
        custom={
            "_transition_button": ActionButton(
                method=RequestType.PATCH,
                identifiers=("wbportfolio:order",),
                icon=WBIcon.APPROVE.icon,
                key="approve",
                label="Approve",
                action_label="Approve",
                # description_fields="<p>Start: {{start}}</p><p>End: {{end}}</p><p>Title: {{title}}</p>",
            )
        },
    )
    def approve(self, by=None, replay: bool = True, **kwargs):
        if by:
            self.approver = getattr(by, "profile", None)
        elif not self.approver:
            self.approver = self.creator
        if self.portfolio.can_be_rebalanced:
            self.apply()
            if replay:
                replay_as_task.apply_async(
                    (self.id,),
                    {
                        "user_id": by.id if by else None,
                        "broadcast_changes_at_date": False,
                        "reapply_order_proposal": True,
                    },
                    countdown=10,
                )
        if by and self.custodian_router:
            for user in User.objects.exclude(id=by.id).filter(
                profile__in=PortfolioRole.portfolio_managers(), is_active=True
            ):
                send_notification(
                    code="wbportfolio.portfolio.action_done",
                    title="An Order Proposal was approved and is waiting execution",
                    body=f"The order proposal {self} has been approved by {by.profile.full_name} and is now pending execution. Please review the orders carefully and proceed with execution if appropriate.",
                    user=user,
                    reverse_name="wbportfolio:orderproposal-detail",
                    reverse_args=[self.id],
                )

    @transition(
        field=status,
        source=Status.APPROVED,
        target=Status.CONFIRMED,
        permission=lambda instance, user: PortfolioRole.is_portfolio_manager(
            user.profile, portfolio=instance.portfolio
        )
        and instance.portfolio.can_be_rebalanced,
        custom={
            "_transition_button": ActionButton(
                method=RequestType.PATCH,
                identifiers=("wbportfolio:order",),
                icon=WBIcon.LOCK.icon,
                key="confirm",
                label="Confirm",
                action_label="Lock order proposal",
                # description_fields="<p>Start: {{start}}</p><p>End: {{end}}</p><p>Title: {{title}}</p>",
            )
        },
    )
    def confirm(self, by=None, replay: bool = True, **kwargs):
        self.refresh_cash_position()
        if self.portfolio.can_be_rebalanced:
            self.apply()
            if replay:
                replay_as_task.apply_async(
                    (self.id,),
                    {
                        "user_id": by.id if by else None,
                        "broadcast_changes_at_date": False,
                        "reapply_order_proposal": True,
                    },
                    countdown=10,
                )

    @transition(
        field=status,
        source=Status.PENDING,
        target=Status.DENIED,
        permission=lambda instance, user: PortfolioRole.is_portfolio_manager(
            user.profile, portfolio=instance.portfolio
        )
        and not instance.has_non_successful_checks,
        custom={
            "_transition_button": ActionButton(
                method=RequestType.PATCH,
                identifiers=("wbportfolio:order",),
                icon=WBIcon.DENY.icon,
                key="deny",
                label="Deny",
                action_label="Deny",
                # description_fields="<p>Start: {{start}}</p><p>End: {{end}}</p><p>Title: {{title}}</p>",
            )
        },
    )
    def deny(self, by=None, description=None, **kwargs):
        pass

    def can_deny(self):
        pass

    def apply(self):
        # We validate order which will create or update the initial asset positions
        if not self.portfolio.can_be_rebalanced:
            raise ValueError("Non-Rebalanceable portfolio cannot be traded manually.")
        self.portfolio.load_builder_returns(self.trade_date, self.trade_date)
        # We do not want to create the estimated cash position if there is not orders in the order proposal (shouldn't be possible anyway)
        target_portfolio = self.get_target_portfolio()
        assets = {i: float(pos.weighting) for i, pos in target_portfolio.positions_map.items()}
        self.portfolio.builder.add((self.trade_date, assets)).bulk_create_positions(
            force_save=True, is_estimated=False, delete_leftovers=True
        )

    @transition(
        field=status,
        source=Status.PENDING,
        target=Status.DRAFT,
        permission=lambda instance, user: PortfolioRole.is_portfolio_manager(
            user.profile, portfolio=instance.portfolio
        )
        and instance.has_all_check_completed
        or not instance.checks.exists(),  # we wait for all checks to succeed before proposing the back to draft transition
        custom={
            "_transition_button": ActionButton(
                method=RequestType.PATCH,
                identifiers=("wbportfolio:order",),
                icon=WBIcon.UNDO.icon,
                key="backtodraft",
                label="Back to Draft",
                action_label="backtodraft",
                # description_fields="<p>Start: {{start}}</p><p>End: {{end}}</p><p>Title: {{title}}</p>",
            )
        },
    )
    def backtodraft(self, **kwargs):
        self.checks.delete()

    def can_backtodraft(self):
        pass

    @transition(
        field=status,
        source=Status.CONFIRMED,
        target=Status.DRAFT,
        permission=lambda instance, user: PortfolioRole.is_portfolio_manager(
            user.profile, portfolio=instance.portfolio
        ),
        custom={
            "_transition_button": ActionButton(
                method=RequestType.PATCH,
                identifiers=("wbportfolio:order",),
                icon=WBIcon.REGENERATE.icon,
                key="revert",
                label="Revert",
                action_label="revert",
                description_fields="<p>Unapply orders and move everything back to draft (i.e. The underlying asset positions will change like the orders were never applied)</p>",
            )
        },
    )
    def revert(self, **kwargs):
        self.approver = None
        self.portfolio.assets.filter(date=self.trade_date, is_estimated=False).update(
            is_estimated=True
        )  # we delete the existing portfolio as it has been reverted

    def can_revert(self):
        errors = dict()
        if not self.portfolio.can_be_rebalanced:
            errors["portfolio"] = [
                gettext_lazy(
                    "The portfolio needs to be a model portfolio in order to revert this order proposal manually"
                )
            ]
        return errors

    def apply_workflow(
        self,
        apply_automatically: bool = True,
        silent_exception: bool = False,
        force_reset_order: bool = False,
        **reset_order_kwargs,
    ):
        # before, we need to save all positions in the builder first because effective weight depends on it
        self.portfolio.load_builder_returns(self.trade_date, self.trade_date)
        self.portfolio.builder.bulk_create_positions(delete_leftovers=True)
        if self.status == OrderProposal.Status.CONFIRMED:
            logger.info("Reverting order proposal ...")
            self.revert()
        if self.status == OrderProposal.Status.DRAFT:
            if (
                self.rebalancing_model or force_reset_order
            ):  # if there is no position (for any reason) or we the order proposal has a rebalancer model attached (orders are computed based on an aglo), we reapply this order proposal
                logger.info("Resetting orders ...")
                try:  # we silent any validation error while setting proposal, because if this happens, we assume the current order proposal state if valid and we continue to batch compute
                    self.reset_orders(**reset_order_kwargs)
                except (ValidationError, DatabaseError) as e:
                    self.status = OrderProposal.Status.FAILED
                    if not silent_exception:
                        raise ValidationError(e) from e
                    return
            logger.info("Submitting order proposal ...")
            self.submit(pretrade_check=False)
        if apply_automatically:
            logger.info("Applying order proposal ...")
            if self.status == OrderProposal.Status.PENDING:
                self.approve(replay=False)
            else:
                self.apply()
            self.status = self.Status.CONFIRMED

    # End FSM logics

    @classmethod
    def get_endpoint_basename(cls) -> str:
        return "wbportfolio:orderproposal"

    @classmethod
    def get_representation_endpoint(cls) -> str:
        return "wbportfolio:orderproposalrepresentation-list"

    @classmethod
    def get_representation_value_key(cls) -> str:
        return "id"

    @classmethod
    def get_representation_label_key(cls) -> str:
        return "{{_portfolio.name}} ({{trade_date}})"

    @classmethod
    def build(
        cls,
        trade_date: date,
        portfolio,
        target_portfolio: PortfolioDTO,
        creator: User | None = None,
        approve_automatically: bool = True,
    ) -> Self:
        order_proposal, _ = OrderProposal.objects.update_or_create(
            portfolio=portfolio,
            trade_date=trade_date,
            defaults={"status": OrderProposal.Status.DRAFT, "creator": creator.profile if creator else None},
        )
        order_proposal.reset_orders(target_portfolio=target_portfolio)
        if approve_automatically:
            order_proposal.submit()
            order_proposal.approve(by=creator)
            if portfolio.can_be_rebalanced:
                order_proposal.apply()
            order_proposal.save()
        return order_proposal

    def push_to_dependant_portfolios(
        self, only_portfolios: QuerySet[Portfolio] | None = None, **build_kwargs
    ) -> list[Self]:
        order_proposals = []
        for rel in self.portfolio.get_model_portfolio_relationships(self.trade_date):
            existing_order_proposal = OrderProposal.objects.filter(
                portfolio=rel.portfolio, trade_date=self.trade_date
            ).first()
            # we allow push only on existing draft order proposal
            dependency_portfolio = rel.dependency_portfolio
            if (
                (only_portfolios is None or rel.portfolio in only_portfolios)
                and (not existing_order_proposal or existing_order_proposal.status == OrderProposal.Status.DRAFT)
                and dependency_portfolio.assets.filter(date=self.trade_date).exists()
            ):
                target_portfolio = dependency_portfolio._build_dto(self.trade_date)
                order_proposals.append(
                    OrderProposal.build(self.trade_date, rel.portfolio, target_portfolio, **build_kwargs)
                )
        return order_proposals

    def evaluate_pretrade_checks(self, asynchronously: bool = True):
        self.checks.all().delete()
        self.refresh_cash_position()
        self.evaluate_active_rules(
            self.trade_date,
            self.get_target_portfolio(),
            asynchronously=asynchronously,
            ignore_breached_objects=list(
                Instrument.objects.filter(id__in=self.orders.filter(weighting=0).values("underlying_instrument"))
            ),
        )


@receiver(post_save, sender="wbportfolio.OrderProposal")
def post_fail_order_proposal(sender, instance: OrderProposal, created, raw, **kwargs):
    # if we have a order proposal in a fail state, we ensure that all future existing order proposal are either deleted (automatic one) or set back to draft
    if not raw and instance.status == OrderProposal.Status.FAILED:
        # we delete all order proposal that have a rebalancing model and are marked as "automatic" (quite hardcoded yet)
        instance.invalidate_future_order_proposal()


@shared_task(queue=Queue.DEFAULT.value)
def replay_as_task(order_proposal_id, user_id: int | None = None, **kwargs):
    order_proposal = OrderProposal.objects.get(id=order_proposal_id)
    order_proposal.replay(**kwargs)
    if user_id:
        body = f'We’ve successfully replayed your order proposal for "{order_proposal.portfolio}" from {order_proposal.trade_date:%Y-%m-%d}. You can now review its updated composition.'
        user = User.objects.get(id=user_id)
        if order_proposal.portfolio.builder.excluded_positions:
            excluded_quotes = []
            for batch in order_proposal.portfolio.builder.excluded_positions.values():
                for pos in batch:
                    excluded_quotes.append(pos.underlying_instrument)
            body += "<p><strong>Note</strong></p><p>While replaying and drifting the portfolio, we excluded the positions from the following quotes because of missing price</p> <ul>"
            for excluded_quote in set(excluded_quotes):
                body += f"<li>{excluded_quote}</li>"
            body += "</ul>"
            order_proposal.portfolio.builder.clear()
        send_notification(
            code="wbportfolio.portfolio.action_done",
            title="Order Proposal Replay Completed",
            body=body,
            user=user,
            reverse_name="wbportfolio:portfolio-detail",
            reverse_args=[order_proposal.portfolio.id],
        )


@shared_task(queue=Queue.HIGH_PRIORITY.value)
def execute_orders_as_task(order_proposal_id: int, prioritize_target_weight: bool = False, **kwargs):
    order_proposal = OrderProposal.objects.get(id=order_proposal_id)
    order_proposal.execute_orders()


@shared_task(queue=Queue.BACKGROUND.value)
def push_model_change_as_task(
    model_order_proposal_id: int,
    user_id: int | None = None,
    only_for_portfolio_ids: list[int] | None = None,
    approve_automatically: bool = False,
):
    # not happy with that but we will keep it for the MVP lifecycle
    model_order_proposal = OrderProposal.objects.get(id=model_order_proposal_id)
    user = User.objects.get(id=user_id) if user_id else None
    params = dict(approve_automatically=approve_automatically, creator=user)
    only_portfolios = None
    if only_for_portfolio_ids:
        only_portfolios = Portfolio.objects.filter(id__in=only_for_portfolio_ids)

    order_proposals = model_order_proposal.push_to_dependant_portfolios(only_portfolios=only_portfolios, **params)
    product_html_list = "<ul>\n"
    for order_proposal in order_proposals:
        product_html_list += f"<li>{order_proposal.portfolio}</li>\n"

    product_html_list += "</ul>"
    if user:
        send_notification(
            code="wbportfolio.order_proposal.push_model_changes",
            title="Portfolio Model changes are pushed to dependant portfolios",
            body=f"""
    <p>The latest updates to the portfolio model <strong>{model_order_proposal.portfolio}</strong> have been successfully applied to the associated portfolios, and corresponding orders have been created.</p>
    <p>To proceed with executing these orders, please review the following related portfolios: </p>
            {product_html_list}
            """,
            user=user,
        )


@receiver(investable_universe_updated, sender="wbfdm.Instrument")
def update_exante_order_proposal_returns(*args, end_date: date | None = None, **kwargs):
    for op in OrderProposal.objects.filter(trade_date__gte=end_date):
        op.refresh_returns()


@receiver(pre_delete, sender=OrderProposal)
def post_delete_adjustment(sender, instance: OrderProposal, **kwargs):
    for check in instance.checks.all():
        check.delete()
