from unittest.mock import patch

import pandas as pd
import pytest
from faker import Faker
from psycopg.types.range import NumericRange
from wbcompliance.factories.risk_management import RuleThresholdFactory
from wbfdm.analysis.esg.esg_analysis import DataLoader

from wbportfolio.risk_management.backends.esg_aggregation_portfolio import (
    RuleBackend as ESGAggregationPortfolioBackend,
)
from wbportfolio.tests.models.utils import PortfolioTestMixin

fake = Faker()


@pytest.mark.django_db
class TestEsgAggregationPortfolioRuleModel(PortfolioTestMixin):
    @patch.object(DataLoader, "compute")
    def test_eval(
        self,
        mock_fct,
        weekday,
        asset_position_factory,
        portfolio,
    ):
        parameters = {"esg_aggregation": "GHG_EMISSIONS_SCOPE_1"}
        backend = ESGAggregationPortfolioBackend(
            weekday,
            portfolio,
            parameters,
            [RuleThresholdFactory.create(range=NumericRange(lower=0.02, upper=0.03))],  # type: ignore
        )

        a1 = asset_position_factory.create(
            date=weekday,
            portfolio=portfolio,
        )  # Breached position

        a2 = asset_position_factory.create(
            date=weekday,
            portfolio=portfolio,
        )
        mock_fct.return_value = pd.Series(index=[a1.underlying_quote.id, a2.underlying_quote.id], data=[0.01, 0.025])
        incidents = list(backend.check_rule())
        assert len(incidents) == 1
        incident = incidents[0]
        assert incident.breached_object == a2.underlying_quote
