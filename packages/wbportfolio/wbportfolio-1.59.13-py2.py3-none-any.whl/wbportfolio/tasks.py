from contextlib import suppress
from datetime import date, timedelta

from celery import shared_task
from django.db.models import ProtectedError, Q
from tqdm import tqdm
from wbcore.workers import Queue
from wbfdm.models import Controversy, Instrument

from wbportfolio.models import AssetPosition, Portfolio, Product, Trade


@shared_task(queue=Queue.BACKGROUND.value)
def daily_active_product_task(today: date | None = None):
    if not today:
        today = date.today()
    qs = Product.active_objects.all()
    for product in tqdm(qs, total=qs.count()):
        product.update_outstanding_shares()
        product.check_and_notify_product_termination_on_date(today)


@shared_task(queue=Queue.BACKGROUND.value)
def periodically_clean_marked_for_deletion_trades(max_allowed_iterations: int = 5):
    # Get all trade marked for deletion or pending and older than 7 days (i.e. After 7 days, we consider the pending trade obselete)
    qs = Trade.objects.filter(
        Q(marked_for_deletion=True) | (Q(pending=True) & Q(transaction_date__lt=date.today() - timedelta(days=7)))
    )
    i = 0

    # We try several times in case the trades deletion mechanism shifts the marked for deletion tag forwards
    while i < max_allowed_iterations and qs.exists():
        for t in qs:
            with suppress(ProtectedError):
                t.delete()
        qs = Trade.objects.filter(marked_for_deletion=True)
        i += 1


# A Task to run every day to update automatically the preferred classification
# per instrument of each wbportfolio containing assets.
@shared_task(queue=Queue.BACKGROUND.value)
def update_preferred_classification_per_instrument_and_portfolio_as_task():
    for portfolio in Portfolio.tracked_objects.all():
        portfolio.update_preferred_classification_per_instrument()


# This task needs to run at fix interval. It will trigger the basic wbportfolio synchronization update:
# - Fetch for stainly price at t-1
# - propagate (or update) t-2 asset positions into t-1
# - Synchronize wbportfolio at t-1
# - Compute Instrument Price estimate at t-1


@shared_task(queue=Queue.BACKGROUND.value)
def synchronize_portfolio_controversies():
    active_portfolios = Portfolio.objects.filter_active_and_tracked()
    qs = (
        AssetPosition.objects.filter(portfolio__in=active_portfolios)
        .values("underlying_instrument")
        .distinct("underlying_instrument")
    )
    objs = {}
    securities = Instrument.objects.filter(id__in=qs.values("underlying_instrument"))
    securities_mapping = {security.id: security.get_root() for security in securities}
    for controversy in securities.dl.esg_controversies():
        instrument = securities_mapping[controversy["instrument_id"]]
        obj = Controversy.dict_to_model(controversy, instrument)
        objs[obj.external_id] = obj

    Controversy.objects.bulk_create(
        objs.values(),
        update_fields=[
            "instrument",
            "headline",
            "description",
            "source",
            "direct_involvement",
            "company_response",
            "review",
            "initiated",
            "flag",
            "status",
            "type",
            "severity",
        ],
        unique_fields=["external_id"],
        update_conflicts=True,
        batch_size=10000,
    )
