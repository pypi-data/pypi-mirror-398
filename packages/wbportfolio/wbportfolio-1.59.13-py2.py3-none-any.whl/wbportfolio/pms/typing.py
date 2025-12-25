import enum
from dataclasses import asdict, dataclass, field, fields
from datetime import date
from datetime import date as date_lib
from decimal import Decimal
from typing import Self

import pandas as pd
from django.core.exceptions import ValidationError

from wbportfolio.order_routing import ExecutionInstruction


@dataclass(frozen=True)
class Valuation:
    instrument: int
    net_value: Decimal
    outstanding_shares: Decimal = Decimal(0)


@dataclass()
class Position:
    underlying_instrument: int
    weighting: Decimal
    date: date_lib

    daily_return: Decimal = Decimal("0")
    currency: int | None = None
    instrument_type: int | None = None
    asset_valuation_date: date_lib | None = None
    portfolio_created: int = None
    exchange: int = None
    is_estimated: bool = False
    country: int = None
    shares: Decimal | None = None
    is_cash: bool = False
    primary_classification: int = None
    favorite_classification: int = None
    market_capitalization_usd: float = None
    currency_fx_rate: float = 1
    market_share: float = None
    daily_liquidity: float = None
    volume_usd: float = None
    price: float = None

    def __post_init__(self):
        self.daily_return = round(self.daily_return, 16)
        self.weighting = round(self.weighting, 8)

    def __add__(self, other):
        return Position(
            weighting=self.weighting + other.weighting,
            shares=self.shares + other.shares if (self.shares is not None and other.shares is not None) else None,
            **{f.name: getattr(self, f.name) for f in fields(Position) if f.name not in ["weighting", "shares"]},
        )

    def copy(self, **kwargs):
        attrs = {f.name: getattr(self, f.name) for f in fields(Position)}
        attrs.update(kwargs)
        return Position(**attrs)


@dataclass(frozen=True)
class Order:
    class AssetType(enum.Enum):
        EQUITY = "EQUITY"
        AMERICAN_DEPOSITORY_RECEIPT = "AMERICAN_DEPOSITORY_RECEIPT"

    id: int | str
    trade_date: date
    target_weight: float

    # Instrument identifier
    asset_class: AssetType
    refinitiv_identifier_code: str | None = None
    bloomberg_ticker: str | None = None
    sedol: str | None = None

    weighting: float | None = None
    target_shares: float | None = None
    shares: float | None = None
    execution_price: float | None = None
    execution_instruction: ExecutionInstruction = ExecutionInstruction.MARKET_ON_CLOSE.value
    execution_instruction_parameters: dict | None = None
    comment: str = ""


@dataclass()
class Trade:
    underlying_instrument: int
    instrument_type: int
    currency: int
    date: date_lib
    price: Decimal
    effective_weight: Decimal
    target_weight: Decimal
    currency_fx_rate: Decimal = Decimal("1")
    effective_shares: Decimal = Decimal("0")
    target_shares: Decimal = Decimal("0")
    daily_return: Decimal = Decimal("0")
    effective_quantization_error: Decimal = Decimal("0")
    target_quantization_error: Decimal = Decimal("0")

    id: int | None = None
    is_cash: bool = False

    def __post_init__(self):
        self.effective_weight = round(self.effective_weight, 8)
        # ensure a trade target weight cannot be lower than 0
        self.target_weight = max(round(self.target_weight, 8), Decimal("0"))
        self.daily_return = round(self.daily_return, 16)

    def __add__(self, other):
        return Trade(
            underlying_instrument=self.underlying_instrument,
            effective_weight=self.effective_weight,
            target_weight=self.target_weight + other.target_weight,
            effective_shares=self.effective_shares,
            target_shares=self.target_shares + other.target_shares,
            daily_return=self.daily_return,
            **{
                f.name: getattr(self, f.name)
                for f in fields(Trade)
                if f.name
                not in [
                    "effective_weight",
                    "target_weight",
                    "effective_shares",
                    "target_shares",
                    "underlying_instrument",
                    "daily_return",
                ]
            },
        )

    def copy(self, **kwargs):
        attrs = {f.name: getattr(self, f.name) for f in fields(Trade)}
        attrs.update(kwargs)
        return Trade(**attrs)

    @property
    def delta_weight(self) -> Decimal:
        return (self.target_weight + self.target_quantization_error) - self.effective_weight

    @property
    def delta_shares(self) -> Decimal:
        return self.target_shares - self.effective_shares

    @property
    def price_fx_portfolio(self) -> Decimal:
        return self.price * self.currency_fx_rate

    def validate(self):
        return True
        # if self.effective_weight < 0 or self.effective_weight > 1.0:
        #     raise ValidationError("Effective Weight needs to be in range [0, 1]")
        # if self.target_weight < 0 or self.target_weight > 1.0:
        #     raise ValidationError("Target Weight needs to be in range [0, 1]")

    def normalize_target(
        self, factor: Decimal | None = None, target_shares: Decimal | int | None = None, target_weight: Decimal = None
    ):
        if factor is None:
            if target_shares is not None:
                factor = target_shares / self.target_shares if self.target_shares else Decimal("1")
            elif target_weight is not None:
                factor = target_weight / self.target_weight if self.target_weight else Decimal("1")
            else:
                raise ValueError("Target weight and shares cannot be both None")
        return self.copy(target_weight=self.target_weight * factor, target_shares=self.target_shares * factor)


@dataclass(frozen=True)
class TradeBatch:
    trades: list[Trade]
    trades_map: dict[Trade] = field(init=False, repr=False)

    def __post_init__(self):
        trade_map = {}
        if self.total_effective_weight and (quant_error := Decimal("1") - self.total_effective_weight):
            self.largest_effective_order.effective_quantization_error = quant_error
        if self.total_target_weight and (quant_error := Decimal("1") - self.total_target_weight):
            self.largest_effective_order.target_quantization_error = quant_error
        for trade in self.trades:
            if trade.underlying_instrument in trade_map:
                trade_map[trade.underlying_instrument] += trade
            else:
                trade_map[trade.underlying_instrument] = trade
        object.__setattr__(self, "trades_map", trade_map)

    @property
    def largest_effective_order(self) -> Trade:
        return max(self.trades, key=lambda obj: obj.effective_weight)

    @property
    def total_target_weight(self) -> Decimal:
        return sum([trade.target_weight for trade in self.trades], Decimal("0"))

    @property
    def total_effective_weight(self) -> Decimal:
        return sum([trade.effective_weight for trade in self.trades], Decimal("0"))

    @property
    def total_abs_delta_weight(self) -> Decimal:
        return sum([abs(trade.delta_weight) for trade in self.trades], Decimal("0"))

    def __add__(self, other):
        return TradeBatch(tuple(self.trades + other.trades))

    def __len__(self):
        return len(self.trades)

    def __iter__(self):
        return iter(self.trades_map.values())

    def validate(self):
        if round(float(self.total_target_weight), 4) != 1:  # we do that to remove decimal over precision
            raise ValidationError(f"Total Weight cannot be different than 1 ({float(self.total_target_weight)})")


@dataclass(frozen=True)
class Portfolio:
    positions: list[Position] | list
    positions_map: dict[int, Position] = field(init=False, repr=False)

    def __post_init__(self):
        positions_map = {}

        for pos in self.positions:
            if pos.underlying_instrument in positions_map:
                positions_map[pos.underlying_instrument] += pos
            else:
                positions_map[pos.underlying_instrument] = pos
        object.__setattr__(self, "positions_map", positions_map)

    @property
    def total_weight(self):
        return sum([pos.weighting for pos in self.positions])

    @property
    def total_shares(self):
        return sum([pos.target_shares for pos in self.positions if pos.target_shares is not None])

    def to_df(self, exclude_cash: bool = False) -> pd.DataFrame:
        return pd.DataFrame([asdict(pos) for pos in self.positions if not exclude_cash or not pos.is_cash])

    def to_dict(self) -> dict[int, Decimal]:
        return {underlying_instrument: pos.weighting for underlying_instrument, pos in self.positions_map.items()}

    def get_orders(self, target_portfolio: Self) -> TradeBatch:
        instruments = self.positions_map.copy()
        instruments.update(target_portfolio.positions_map)

        trades: list[Trade] = []
        for instrument_id, pos in instruments.items():
            effective_weight = target_weight = 0
            effective_shares = target_shares = 0
            daily_return = 0
            price = Decimal("0")
            is_cash = False
            trade_date = None
            if effective_pos := self.positions_map.get(instrument_id, None):
                effective_weight = effective_pos.weighting
                effective_shares = effective_pos.shares
                daily_return = effective_pos.daily_return
                is_cash = effective_pos.is_cash
                price = effective_pos.price
                trade_date = effective_pos.date

            if target_pos := target_portfolio.positions_map.get(instrument_id, None):
                target_weight = target_pos.weighting
                is_cash = target_pos.is_cash
                if target_pos.shares is not None:
                    target_shares = target_pos.shares
                if target_pos.price:
                    price = target_pos.price
                trade_date = target_pos.date

            trade = Trade(
                underlying_instrument=instrument_id,
                effective_weight=effective_weight,
                target_weight=target_weight,
                effective_shares=effective_shares,
                target_shares=target_shares,
                date=trade_date,
                instrument_type=pos.instrument_type,
                currency=pos.currency,
                price=Decimal(price) if price else Decimal("0"),
                currency_fx_rate=Decimal(pos.currency_fx_rate),
                daily_return=Decimal(daily_return),
                is_cash=is_cash,
            )
            trades.append(trade)
        return TradeBatch(trades)

    def __len__(self):
        return len(self.positions)

    def __bool__(self):
        return len(self.positions) > 0

    def normalize_cash(self, target_cash_weight: Decimal):
        """
        Normalize the instantiate portfolio so that the sum of the cash position equals to the new target cash position
        """
        positions = list(filter(lambda pos: not pos.is_cash, self.positions))
        cash_position = next(filter(lambda pos: pos.is_cash, self.positions), None)
        total_non_cash_weight = sum(map(lambda pos: pos.weighting, positions))
        target_weight = Decimal("1") - target_cash_weight
        for pos in positions:
            pos.weighting = pos.weighting * target_weight / total_non_cash_weight
        if cash_position:
            cash_position.weighting = target_cash_weight
            positions.append(cash_position)
        return Portfolio(positions)
