from decimal import Decimal
from unittest.mock import patch

import pytest
from pandas._libs.tslibs.offsets import BDay

from wbportfolio.models import AssetPosition, Order, OrderProposal, Portfolio
from wbportfolio.models.utils import adjust_assets, adjust_orders, adjust_quote, get_adjusted_shares


def test_get_adjusted_shares():
    assert get_adjusted_shares(Decimal("150"), Decimal("100"), Decimal("200")) == Decimal("75")


@pytest.mark.django_db
@patch.object(Order, "_get_price")
def test_adjust_orders(mock_get_price, weekday, order_factory, instrument_factory):
    mock_get_price.return_value = (Decimal("100"), Decimal("0"))
    old_quote = instrument_factory.create()
    new_quote = instrument_factory.create()
    o1 = order_factory.create(
        underlying_instrument=old_quote, order_proposal__trade_date=weekday, price=Decimal("100"), shares=Decimal("10")
    )
    o2 = order_factory.create(
        underlying_instrument=old_quote, order_proposal__trade_date=weekday, price=Decimal("100"), shares=Decimal("20")
    )
    adjust_orders(Order.objects.filter(underlying_instrument=old_quote), new_quote)

    o1.refresh_from_db()
    o2.refresh_from_db()

    assert o1.underlying_instrument == new_quote
    assert o2.underlying_instrument == new_quote
    assert o1.price == Decimal("100")
    assert o2.price == Decimal("100")
    assert o1.shares == Decimal("10")
    assert o2.shares == Decimal("20")

    mock_get_price.return_value = (Decimal("200"), Decimal("0"))
    adjust_orders(Order.objects.filter(underlying_instrument=new_quote), old_quote)

    o1.refresh_from_db()
    o2.refresh_from_db()

    assert o1.underlying_instrument == old_quote
    assert o2.underlying_instrument == old_quote
    assert o1.price == Decimal("200")
    assert o2.price == Decimal("200")
    assert o1.shares == Decimal("5")
    assert o2.shares == Decimal("10")


@pytest.mark.django_db
def test_adjust_assets(weekday, asset_position_factory, instrument_factory, instrument_price_factory):
    old_quote = instrument_factory.create()
    new_quote = instrument_factory.create()
    old_quote_price = instrument_price_factory.create(
        instrument=old_quote, net_value=Decimal("100"), date=weekday, calculated=False
    )
    new_quote_price = instrument_price_factory.create(
        instrument=new_quote, net_value=Decimal("100"), date=weekday, calculated=False
    )

    a1 = asset_position_factory.create(
        underlying_quote=old_quote, date=weekday, initial_price=Decimal("100"), initial_shares=Decimal("10")
    )
    a2 = asset_position_factory.create(
        underlying_quote=old_quote, date=weekday, initial_price=Decimal("100"), initial_shares=Decimal("20")
    )
    adjust_assets(AssetPosition.objects.filter(underlying_quote=old_quote), new_quote)

    a1.refresh_from_db()
    a2.refresh_from_db()

    assert a1.underlying_quote == new_quote
    assert a2.underlying_quote == new_quote
    assert a1.underlying_quote_price == new_quote_price
    assert a2.underlying_quote_price == new_quote_price
    assert a1.initial_price == Decimal("100")
    assert a2.initial_price == Decimal("100")
    assert a1.initial_shares == Decimal("10")
    assert a2.initial_shares == Decimal("20")

    old_quote_price.net_value = new_quote_price.net_value = Decimal("200")
    old_quote_price.save()
    new_quote_price.save()

    adjust_assets(AssetPosition.objects.filter(underlying_quote=new_quote), old_quote)

    a1.refresh_from_db()
    a2.refresh_from_db()

    assert a1.underlying_quote == old_quote
    assert a2.underlying_quote == old_quote
    assert a1.underlying_quote_price == old_quote_price
    assert a2.underlying_quote_price == old_quote_price
    assert a1.initial_price == Decimal("200")
    assert a2.initial_price == Decimal("200")
    assert a1.initial_shares == Decimal("5")
    assert a2.initial_shares == Decimal("10")


@pytest.mark.django_db
@patch("wbportfolio.models.utils.adjust_assets")
@patch("wbportfolio.models.utils.adjust_orders")
@patch.object(OrderProposal, "replay")
def test_adjust_quote(mock_replay, mock_adjust_orders, mock_adjust_assets, weekday, order_factory, instrument_factory):
    old_quote = instrument_factory.create()
    new_quote = instrument_factory.create()
    o1 = order_factory.create(  # noqa: F841
        underlying_instrument=old_quote, order_proposal__trade_date=weekday, price=Decimal("100"), shares=Decimal("10")
    )
    o2 = order_factory.create(  # noqa: F841
        underlying_instrument=old_quote,
        order_proposal__trade_date=(weekday + BDay(1)),
        price=Decimal("100"),
        shares=Decimal("10"),
    )
    o3 = order_factory.create(
        underlying_instrument=old_quote,
        order_proposal__trade_date=(weekday + BDay(1)),
        price=Decimal("100"),
        shares=Decimal("10"),
    )
    adjust_quote(
        old_quote,
        new_quote,
        adjust_after=weekday,
        only_portfolios=Portfolio.objects.filter(id=o3.order_proposal.portfolio.id),
    )

    mock_adjust_assets.asser_called_once()
    assert set(mock_adjust_assets.call_args[0][0]) == set(AssetPosition.objects.none())
    assert mock_adjust_assets.call_args[0][1] == new_quote

    mock_adjust_orders.assert_called_once()
    assert set(mock_adjust_orders.call_args[0][0]) == set(Order.objects.filter(id=o3.id))
    assert mock_adjust_orders.call_args[0][1] == new_quote

    mock_replay.assert_called_once_with(reapply_order_proposal=True)
