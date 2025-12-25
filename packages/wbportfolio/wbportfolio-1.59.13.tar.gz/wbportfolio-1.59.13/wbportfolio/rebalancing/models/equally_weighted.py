from decimal import Decimal

from wbportfolio.pms.typing import Portfolio, Position
from wbportfolio.rebalancing.base import AbstractRebalancingModel
from wbportfolio.rebalancing.decorators import register
from wbportfolio.rebalancing.models.mixins import InstrumentMixin


@register("Equally Weighted Rebalancing")
class EquallyWeightedRebalancing(InstrumentMixin, AbstractRebalancingModel):
    def __init__(self, *args, **kwargs):
        super(EquallyWeightedRebalancing, self).__init__(*args, **kwargs)
        if not self.effective_portfolio:
            self.effective_portfolio = self.portfolio._build_dto(self.trade_date)
        self.instruments = self.get_instruments(**kwargs)
        self.prices, self.returns_df = self.instruments.get_returns_df(
            from_date=self.last_effective_date, to_date=self.trade_date, use_dl=True
        )
        try:
            self.prices = self.prices[self.trade_date]
        except KeyError:
            self.prices = {}
        try:
            self.returns_df = self.returns_df.loc[self.trade_date, :].to_dict()
        except KeyError:
            self.returns_df = {}

    def is_valid(self) -> bool:
        return self.instruments.exists() and self.prices

    def get_target_portfolio(self) -> Portfolio:
        positions = []
        instrument_count = len(self.instruments)
        for underlying_instrument in self.instruments:
            positions.append(
                Position(
                    date=self.trade_date,
                    asset_valuation_date=self.trade_date,
                    underlying_instrument=underlying_instrument.id,
                    weighting=Decimal(1 / instrument_count),
                    price=self.prices.get(underlying_instrument.id, None),
                    daily_return=self.returns_df.get(underlying_instrument.id, Decimal("0")),
                )
            )
        return Portfolio(positions)
