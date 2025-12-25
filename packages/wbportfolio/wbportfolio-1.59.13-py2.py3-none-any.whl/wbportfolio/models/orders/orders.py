from contextlib import suppress
from datetime import date
from decimal import Decimal

from django.contrib import admin
from django.db import models
from django.db.models import (
    Sum,
)
from django.dispatch import receiver
from ordered_model.models import OrderedModel
from pandas import Timestamp
from wbcore.contrib.currency.models import CurrencyFXRates
from wbcore.contrib.io.mixins import ImportMixin
from wbfdm.models import Instrument

from wbportfolio.import_export.handlers.orders import OrderImportHandler
from wbportfolio.models.asset import AssetPosition
from wbportfolio.models.transactions.transactions import TransactionMixin
from wbportfolio.order_routing import ExecutionInstruction
from wbportfolio.pms.typing import Position as PositionDTO


class Order(TransactionMixin, ImportMixin, OrderedModel, models.Model):
    import_export_handler_class = OrderImportHandler

    ORDER_WEIGHTING_PRECISION = (
        8  # we need to match the asset position weighting. Skfolio advices using a even smaller number (5)
    )
    currency = None

    class Type(models.TextChoices):
        REBALANCE = "REBALANCE", "Rebalance"
        DECREASE = "DECREASE", "Decrease"
        INCREASE = "INCREASE", "Increase"
        BUY = "BUY", "Buy"
        SELL = "SELL", "Sell"
        NO_CHANGE = "NO_CHANGE", "No Change"  # default transaction subtype if weighing is 0

    class ExecutionStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        CONFIRMED = "CONFIRMED", "Confirmed"
        EXECUTED = "EXECUTED", "Executed"
        FAILED = "FAILED", "Failed"
        IGNORED = "IGNORED", "Ignored"

    order_type = models.CharField(max_length=32, default=Type.BUY, choices=Type.choices, verbose_name="Trade Type")
    shares = models.DecimalField(
        max_digits=15,
        decimal_places=4,
        default=Decimal("0.0"),
        help_text="The number of shares that were traded.",
        verbose_name="Shares",
    )
    desired_target_weight = models.DecimalField(
        max_digits=9,
        decimal_places=ORDER_WEIGHTING_PRECISION,
        default=Decimal(0),
        help_text="Desired Target Weight (for compliance and audit)",
        verbose_name="Desired Target Weight",
    )
    weighting = models.DecimalField(
        max_digits=9,
        decimal_places=ORDER_WEIGHTING_PRECISION,
        default=Decimal(0),
        help_text="The weight to be multiplied against the target",
        verbose_name="Weight",
    )
    order_proposal = models.ForeignKey(
        to="wbportfolio.OrderProposal",
        related_name="orders",
        on_delete=models.CASCADE,
        help_text="The Order Proposal this trade is coming from",
    )
    daily_return = models.DecimalField(
        max_digits=ORDER_WEIGHTING_PRECISION * 2
        + 3,  # we don't expect any drift factor to be in the order of magnitude greater than 1000
        decimal_places=ORDER_WEIGHTING_PRECISION
        * 2,  # we need a higher precision for this factor to avoid float inprecision
        default=Decimal(0.0),
        verbose_name="Daily Return",
        help_text="The Ex-Post daily return",
    )
    quantization_error = models.DecimalField(
        max_digits=9,
        decimal_places=ORDER_WEIGHTING_PRECISION,
        default=Decimal(0),
        verbose_name="Quantization Error",
    )
    execution_status = models.CharField(
        max_length=12,
        default=ExecutionStatus.PENDING.value,
        choices=ExecutionStatus.choices,
        verbose_name="Execution Status",
    )
    execution_instruction = models.CharField(
        max_length=26,
        choices=ExecutionInstruction.choices,
        default=ExecutionInstruction.MARKET_ON_CLOSE.value,
        verbose_name="Execution Instruction",
    )
    execution_instruction_parameters = models.JSONField(
        default=dict, blank=True, verbose_name="Execution Instruction Parameters"
    )
    execution_comment = models.TextField(default="", blank=True, verbose_name="Execution Comment")

    execution_trade = models.OneToOneField(
        to="wbportfolio.Trade",
        related_name="order",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        help_text="The executed Trade",
    )
    order_with_respect_to = "order_proposal"

    class Meta(OrderedModel.Meta):
        verbose_name = "Order"
        verbose_name_plural = "Orders"
        indexes = [
            models.Index(fields=["order_proposal"]),
            models.Index(fields=["underlying_instrument", "value_date"]),
            models.Index(fields=["portfolio", "underlying_instrument", "value_date"]),
            models.Index(fields=["order_proposal", "underlying_instrument"]),
            # models.Index(fields=["date", "underlying_instrument"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["order_proposal", "underlying_instrument"],
                name="unique_order",
            ),
        ]
        # notification_email_template = "portfolio/email/trade_notification.html"

    @property
    def product(self):
        from wbportfolio.models.products import Product

        try:
            return Product.objects.get(id=self.underlying_instrument.id)
        except Product.DoesNotExist:
            return None

    @property
    @admin.display(description="Last Effective Date")
    def _last_effective_date(self) -> date:
        if hasattr(self, "last_effective_date"):
            return self.last_effective_date
        elif (
            assets := AssetPosition.unannotated_objects.filter(
                date__lt=self.value_date,
                portfolio=self.portfolio,
            )
        ).exists():
            return assets.latest("date").date

    @property
    @admin.display(description="Effective Weight")
    def _previous_weight(self) -> Decimal:
        if hasattr(self, "previous_weight"):
            return self.previous_weight
        return AssetPosition.unannotated_objects.filter(
            underlying_quote=self.underlying_instrument,
            date=self._last_effective_date,
            portfolio=self.portfolio,
        ).aggregate(s=Sum("weighting"))["s"] or Decimal(0)

    @property
    @admin.display(description="Effective Weight")
    def _effective_weight(self) -> Decimal:
        if hasattr(self, "effective_weight"):
            return self.effective_weight
        return self.order_proposal.get_orders().get(id=self.id).effective_weight

    @property
    @admin.display(description="Effective Shares")
    def _effective_shares(self) -> Decimal:
        return getattr(
            self,
            "effective_shares",
            self.get_effective_shares(),
        )

    @property
    @admin.display(description="Target Weight")
    def _target_weight(self) -> Decimal:
        return getattr(
            self, "target_weight", round(self._effective_weight + self.weighting, self.ORDER_WEIGHTING_PRECISION)
        )

    @property
    @admin.display(description="Target Shares")
    def _target_shares(self) -> Decimal:
        return getattr(self, "target_shares", self._effective_shares + self.shares)

    def __str__(self):
        ticker = f"{self.underlying_instrument.ticker}:" if self.underlying_instrument.ticker else ""
        return f"{ticker}{self.weighting}"

    def pre_save(self):
        self.portfolio = self.order_proposal.portfolio
        self.value_date = self.order_proposal.trade_date
        self.set_currency_fx_rate()

        if not self.price:
            self.set_price()
        if not self.portfolio.only_weighting and not self.shares:
            estimated_shares = self.order_proposal.get_estimated_shares(
                self.weighting, self.underlying_instrument, self.price
            )
            if estimated_shares:
                self.shares = estimated_shares
        if effective_shares := self.get_effective_shares():
            if self.order_type == self.Type.SELL:
                self.shares = -effective_shares
            else:
                self.shares = max(self.shares, -effective_shares)
        super().pre_save()

    def save(self, *args, **kwargs):
        if self.id:
            self.set_type()
        self.pre_save()
        if not self.underlying_instrument.is_investable_universe:
            self.underlying_instrument.is_investable_universe = True
            self.underlying_instrument.save()

        super().save(*args, **kwargs)

    @classmethod
    def get_type(cls, weighting, effective_weight, target_weight) -> Type:
        if weighting == 0:
            return Order.Type.NO_CHANGE
        elif weighting is not None:
            if weighting > 0:
                if abs(effective_weight) > 1e-8:
                    return Order.Type.INCREASE
                else:
                    return Order.Type.BUY
            elif weighting < 0:
                if abs(target_weight) > 1e-8:
                    return Order.Type.DECREASE
                else:
                    return Order.Type.SELL

    def get_effective_shares(self) -> Decimal:
        return AssetPosition.objects.filter(
            underlying_quote=self.underlying_instrument,
            date=self.order_proposal.last_effective_date,
            portfolio=self.portfolio,
        ).aggregate(s=Sum("shares"))["s"] or Decimal("0")

    def set_type(self):
        effective_weight = self._effective_weight
        self.order_type = self.get_type(self.weighting, effective_weight, effective_weight + self.weighting)

    def _get_price(self) -> tuple[Decimal, Decimal]:
        daily_return = last_price = Decimal("0")

        effective_date = self.order_proposal.last_effective_date
        if self.underlying_instrument.is_cash or self.underlying_instrument.is_cash_equivalent:
            last_price = Decimal("1")
        else:
            try:
                last_price = Decimal(self.portfolio.builder.prices[self.value_date][self.underlying_instrument.id])
                daily_return = self.portfolio.builder.returns.loc[
                    Timestamp(self.value_date), self.underlying_instrument.id
                ]
            except KeyError:
                prices, returns = Instrument.objects.filter(id=self.underlying_instrument.id).get_returns_df(
                    from_date=effective_date,
                    to_date=self.value_date,
                    to_currency=self.order_proposal.portfolio.currency,
                    use_dl=True,
                )
                with suppress(IndexError):
                    daily_return = Decimal(returns.iloc[-1, 0])
                with suppress(KeyError, TypeError):
                    last_price = Decimal(
                        prices.get(self.value_date, prices[effective_date])[self.underlying_instrument.id]
                    )
        return last_price, daily_return

    def set_price(self):
        last_price, daily_return = self._get_price()
        self.daily_return = daily_return
        self.price = last_price

    def set_currency_fx_rate(self):
        self.currency_fx_rate = Decimal("1")
        if self.order_proposal.portfolio.currency != self.underlying_instrument.currency:
            with suppress(CurrencyFXRates.DoesNotExist):
                self.currency_fx_rate = self.underlying_instrument.currency.convert(
                    self.value_date, self.portfolio.currency, exact_lookup=True
                )

    def set_weighting(self, weighting: Decimal, portfolio_value: Decimal):
        self.weighting = weighting
        price_fx_portfolio = self.price * self.currency_fx_rate
        if price_fx_portfolio and portfolio_value:
            total_value = self.weighting * portfolio_value
            self.shares = total_value / price_fx_portfolio
        else:
            self.shares = Decimal("0")

    def set_shares(self, shares: Decimal, portfolio_value: Decimal):
        if portfolio_value:
            price_fx_portfolio = self.price * self.currency_fx_rate
            self.shares = shares
            total_value = shares * price_fx_portfolio
            self.weighting = total_value / portfolio_value
        else:
            self.weighting = self.shares = Decimal("0")

    def set_total_value_fx_portfolio(self, total_value_fx_portfolio: Decimal, portfolio_value: Decimal):
        price_fx_portfolio = self.price * self.currency_fx_rate
        if price_fx_portfolio and portfolio_value:
            self.shares = total_value_fx_portfolio / price_fx_portfolio
            self.weighting = total_value_fx_portfolio / portfolio_value
        else:
            self.weighting = self.shares = Decimal("0")

    def submit(self, by=None, description=None, portfolio_total_asset_value=None, **kwargs):
        warnings = []
        # if shares is defined and the underlying instrument defines a round lot size different than 1 and exchange allows its application, we round the share accordingly
        if self._target_weight:
            if self.order_proposal and not self.portfolio.only_weighting:
                shares = self.order_proposal.get_round_lot_size(self.shares, self.underlying_instrument)
                if shares != self.shares:
                    warnings.append(
                        f"{self.underlying_instrument.computed_str} has a round lot size of  {self.underlying_instrument.round_lot_size}: shares were rounded from {self.shares} to {shares}"
                    )
                shares = round(shares)  # ensure fractional shares are converted into integer
                # we need to recompute the delta weight has we changed the number of shares
                if shares != self.shares:
                    self.set_shares(shares, portfolio_total_asset_value)
            if abs(self.weighting) < self.order_proposal.min_weighting:
                warnings.append(
                    f"Weighting for order {self.underlying_instrument.computed_str} ({self.weighting}) is bellow the allowed Minimum Weighting ({self.order_proposal.min_weighting})"
                )
                self.set_weighting(Decimal("0"), portfolio_total_asset_value)
            if self.shares and abs(self.total_value_fx_portfolio) < self.order_proposal.min_order_value:
                warnings.append(
                    f"Total Value for order {self.underlying_instrument.computed_str} ({self.total_value_fx_portfolio}) is bellow the allowed Minimum Order Value ({self.order_proposal.min_order_value})"
                )
                self.set_weighting(Decimal("0"), portfolio_total_asset_value)
        if not self.price:
            warnings.append(f"No price for {self.underlying_instrument.computed_str}")
        if (
            not self.underlying_instrument.is_cash
            and not self.underlying_instrument.is_cash_equivalent
            and self._target_weight < -1e-8
        ):  # any value below -1e8 will be considered zero
            warnings.append(f"Negative target weight for {self.underlying_instrument.computed_str}")
        self.desired_target_weight = self._target_weight
        return warnings

    def to_dto(self) -> PositionDTO:
        return self.create_dto(
            self.underlying_instrument,
            self._target_weight,
            self.price,
            self.value_date,
            shares=self._target_shares,
            currency_fx_rate=self.currency_fx_rate,
            daily_return=self.daily_return,
        )

    @classmethod
    def create_dto(
        cls,
        instrument: Instrument,
        weighting: Decimal,
        price: Decimal,
        trade_date: date,
        shares: Decimal | None = None,
        **extra_param,
    ) -> PositionDTO:
        price_data = {}

        return PositionDTO(
            underlying_instrument=instrument.id,
            instrument_type=instrument.security_instrument_type.id,
            weighting=weighting,
            shares=shares,
            currency=instrument.currency.id,
            date=trade_date,
            asset_valuation_date=trade_date,
            is_cash=instrument.is_cash or instrument.is_cash_equivalent,
            price=price,
            exchange=instrument.exchange.id if instrument.exchange else None,
            country=instrument.country.id if instrument.country else None,
            **price_data,
            **extra_param,
        )


@receiver(models.signals.post_save, sender="wbportfolio.Trade")
def link_trade_to_order(sender, instance, created, raw, **kwargs):
    """Gets or create the fees for a given price and updates them if necessary"""
    if not raw and created and not instance.underlying_instrument.is_cash and not instance.is_customer_trade:
        with suppress(Order.DoesNotExist):
            order = Order.objects.get(
                portfolio=instance.portfolio,
                underlying_instrument=instance.underlying_instrument,
                value_date=instance.book_date,
            )
            order.execution_trade = instance
            order.execution_status = Order.ExecutionStatus.EXECUTED
            order.save()
