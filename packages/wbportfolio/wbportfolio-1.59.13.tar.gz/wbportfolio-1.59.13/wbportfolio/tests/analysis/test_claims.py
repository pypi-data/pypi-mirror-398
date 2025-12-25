from datetime import date, timedelta

import pytest
from pandas._libs.tslibs.offsets import BDay

from wbportfolio.analysis.claims import ConsolidatedTradeSummary
from wbportfolio.models import Claim


@pytest.mark.django_db
class TestConsolidatedTradeSummary:
    def test_base(self, claim_factory, customer_trade_factory, product, instrument_price_factory):
        d1 = date(2024, 1, 1)
        d2 = date(2025, 1, 1)
        p1 = instrument_price_factory.create(date=d1, instrument=product)  # noqa
        p2 = instrument_price_factory.create(date=d2, instrument=product)
        t1 = customer_trade_factory.create(
            shares=1000, transaction_date=d1, underlying_instrument=product, portfolio=product.primary_portfolio
        )
        t2 = customer_trade_factory.create(
            shares=500, transaction_date=d2, underlying_instrument=product, portfolio=product.primary_portfolio
        )

        c0 = claim_factory.create()  # noqa
        c1 = claim_factory.create(shares=1000, status="APPROVED", trade=t1, date=d2, product=product)
        c2 = claim_factory.create(shares=500, status="APPROVED", trade=t2, date=d1, product=product)
        cts = ConsolidatedTradeSummary(Claim.objects.all(), d1, d2, "account", "account__title")

        valid_date = dict(cts.queryset.values_list("id", "valid_date"))
        assert valid_date == {c1.id: d2, c2.id: d2}

        date_considered = dict(cts.queryset.values_list("id", "date_considered"))
        assert date_considered == {c1.id: d2 + timedelta(days=1), c2.id: d2 + timedelta(days=1)}

        aum = dict(cts.queryset.values_list("id", "aum"))
        assert aum == {c1.id: p2.net_value * c1.shares, c2.id: p2.net_value * c2.shares}

    def test_get_aum_df(self, claim_factory, product, instrument_price_factory, customer_trade_factory):
        t1 = customer_trade_factory.create(
            shares=10,
            transaction_date=date(2024, 12, 31),
            underlying_instrument=product,
            portfolio=product.primary_portfolio,
        )
        t2 = customer_trade_factory.create(
            shares=100,
            transaction_date=date(2025, 2, 3),
            underlying_instrument=product,
            portfolio=product.primary_portfolio,
        )
        c1 = claim_factory.create(trade=t1, status="APPROVED")
        c2 = claim_factory.create(trade=t2, status="APPROVED", account=c1.account)
        d1 = date(2025, 1, 1)
        d2 = date(2025, 3, 3)
        product.prices.all().delete()
        p1 = instrument_price_factory.create(
            date=(d1 - BDay(7)).date(), instrument=product
        )  # we test that the CTS uses the earliest date
        p2 = instrument_price_factory.create(date=c2.date, instrument=product)  # noqa
        p3 = instrument_price_factory.create(date=d2, instrument=product)

        cts = ConsolidatedTradeSummary(Claim.objects.all(), d1, d2, "account", "account__title")
        aum_start = float(round(p1.net_value * c1.shares))
        aum_end = float(round(p3.net_value * (c1.shares + c2.shares)))
        assert cts.get_aum_df().to_dict(orient="index") == {
            c1.account.id: {
                "sum_shares_start": c1.shares,
                "sum_shares_end": c1.shares + c2.shares,
                "sum_aum_start": aum_start,
                "sum_aum_end": aum_end,
                "sum_shares_diff": c2.shares,
                "sum_shares_perf": (c1.shares + c2.shares) / c1.shares - 1,
                "sum_aum_diff": aum_end - aum_start,
                "sum_aum_perf": aum_end / aum_start - 1,
            }
        }

        p0 = instrument_price_factory.create(date=c1.date, instrument=product)  # noqa

        assert cts.get_nnm_df().to_dict(orient="index") == {
            c1.account.id: {
                "sum_nnm_2025-02": float(round(c2.shares * p2.net_value)),
                "sum_nnm_total": float(round(c2.shares * p2.net_value)),
            }
        }, "Ensure the first claim that is considered in t+1 (on the CTS lower bound range) is excluded from the NNM"
