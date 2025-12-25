import logging
from datetime import date
from decimal import Decimal
from typing import Iterator

from celery import shared_task
from django.db.models import F, QuerySet, Window
from django.db.models.functions import RowNumber
from tqdm import tqdm
from wbcore.workers import Queue
from wbfdm.models import Instrument

from wbportfolio.models import AssetPosition, Index, Order, OrderProposal, Portfolio, Product

logger = logging.getLogger("pms")


def get_casted_portfolio_instrument(instrument: Instrument) -> Product | Index | None:
    try:
        return Product.objects.get(id=instrument.id)
    except Product.DoesNotExist:
        try:
            return Index.objects.get(id=instrument.id)
        except Index.DoesNotExist:
            return None


def get_adjusted_shares(old_shares: Decimal, old_price: Decimal, new_price: Decimal) -> Decimal:
    return old_shares * (old_price / new_price)


def adjust_assets(qs: Iterator[AssetPosition], underlying_quote: Instrument):
    objs = []
    logger.info("adjusting asset positions...")
    for a in qs:
        old_price: Decimal = a.initial_price
        a.initial_price = a.underlying_instrument = a.underlying_quote_price = None
        a.underlying_quote = underlying_quote
        a.pre_save()
        if a.initial_shares and a.initial_price and old_price != a.initial_price:
            a.initial_shares = get_adjusted_shares(a.initial_shares, old_price, a.initial_price)
        objs.append(a)
    AssetPosition.objects.bulk_update(
        objs,
        ["underlying_quote", "underlying_quote_price", "underlying_instrument", "initial_price", "initial_shares"],
        batch_size=1000,
    )


def adjust_orders(qs: Iterator[Order], underlying_quote: Instrument):
    objs = []
    logger.info("adjusting orders...")
    for o in qs:
        old_price: Decimal = o.price
        o.underlying_instrument = underlying_quote
        o.set_price()
        if o.price and old_price != o.price and o.shares:
            o.shares = get_adjusted_shares(o.shares, old_price, o.price)
        objs.append(o)
    Order.objects.bulk_update(objs, ["price", "shares", "underlying_instrument"], batch_size=1000)


def adjust_quote(
    old_quote: Instrument,
    new_quote: Instrument,
    adjust_after: date | None = None,
    only_portfolios: QuerySet[Portfolio] | None = None,
    debug: bool = False,
):
    if old_quote.currency != new_quote.currency:
        raise ValueError("cannot safely switch quotes that are not of the same currency")
    assets_to_change = AssetPosition.objects.filter(underlying_quote=old_quote)
    orders_to_change = Order.objects.filter(underlying_instrument=old_quote)
    new_quote.import_prices()
    if adjust_after:
        assets_to_change = assets_to_change.filter(date__gt=adjust_after)
        orders_to_change = orders_to_change.filter(value_date__gt=adjust_after)
    if only_portfolios is not None:
        assets_to_change = assets_to_change.filter(portfolio__in=only_portfolios)
        orders_to_change = orders_to_change.filter(order_proposal__portfolio__in=only_portfolios)
    if debug:
        assets_to_change = tqdm(assets_to_change, total=assets_to_change.count())
        orders_to_change = tqdm(orders_to_change, total=orders_to_change.count())

    # gather the list of order proposal to replay (if the quote led to missing position, we want to replay it to correct automatically the issue)
    latest_orders = orders_to_change.annotate(
        row_number=Window(
            expression=RowNumber(), partition_by=[F("order_proposal__portfolio")], order_by=F("value_date").desc()
        )
    ).filter(row_number=1)
    order_proposals_to_replay = OrderProposal.objects.filter(
        portfolio__is_manageable=True, id__in=latest_orders.values("order_proposal")
    )

    # Adjust assets to the new quote
    adjust_assets(assets_to_change, new_quote)

    # Adjust orders to the new quote
    adjust_orders(orders_to_change, new_quote)

    # replay latest order proposal
    for op in order_proposals_to_replay:
        op.replay(reapply_order_proposal=True)


@shared_task(queue=Queue.BACKGROUND.value)
def adjust_quote_as_task(
    old_quote_id: int, new_quote_id: int, adjust_after: date | None = None, only_portfolio_ids: list[int] | None = None
):
    old_quote = Instrument.objects.get(id=old_quote_id)
    new_quote = Instrument.objects.get(id=new_quote_id)
    only_portfolios = Portfolio.objects.filter(id__in=only_portfolio_ids) if only_portfolio_ids else None
    adjust_quote(old_quote, new_quote, adjust_after=adjust_after, only_portfolios=only_portfolios)
