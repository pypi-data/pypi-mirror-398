from typing import Generator

from wbcompliance.models.risk_management import backend
from wbcompliance.models.risk_management.dispatch import register
from wbcore import serializers as wb_serializers
from wbfdm.analysis.esg.enums import ESGAggregation
from wbfdm.analysis.esg.esg_analysis import DataLoader
from wbfdm.models import Instrument

from wbportfolio.pms.typing import Portfolio as PortfolioDTO

from .mixins import ActivePortfolioRelationshipMixin


@register("ESG Aggregation Portfolio Rule Backend", rule_group_key="portfolio")
class RuleBackend(ActivePortfolioRelationshipMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.esg_aggregation = ESGAggregation[self.esg_aggregation]

    @classmethod
    def get_serializer_class(cls) -> wb_serializers.Serializer:
        class RuleBackendSerializer(wb_serializers.Serializer):
            esg_aggregation = wb_serializers.ChoiceField(
                choices=ESGAggregation.choices(),
                default=ESGAggregation.GHG_EMISSIONS_SCOPE_1.name,
            )

            @classmethod
            def get_parameter_fields(cls):
                return [
                    "esg_aggregation",
                ]

        return RuleBackendSerializer

    def _process_dto(self, portfolio: PortfolioDTO, **kwargs) -> Generator[backend.IncidentResult, None, None]:
        esg_data = self.esg_aggregation.get_esg_data(Instrument.objects.filter(id__in=portfolio.positions_map.keys()))
        df = portfolio.to_df(exclude_cash=True)
        df["total_value"] = (df["price"] * df["shares"] * df["currency_fx_rate"]).astype(float)
        df = df[["total_value", "weighting", "underlying_instrument"]].set_index("underlying_instrument")
        df["weighting"] = df["weighting"] / df["weighting"].sum()
        dataloader = DataLoader(
            df["weighting"].astype(float), esg_data, self.evaluation_date, total_value_fx_usd=df["total_value"]
        )
        metrics = dataloader.compute(self.esg_aggregation)
        for threshold in self.thresholds:
            numerical_range = threshold.numerical_range
            incident_df = metrics[(metrics >= numerical_range[0]) & (metrics < numerical_range[1])]
            for instrument_id, metric in incident_df.to_dict().items():
                instrument = Instrument.objects.get(id=instrument_id)
                breached_value = metric

                if metric < 0:
                    breached_value = f'<span style="color:red">{breached_value}</span>'
                else:
                    breached_value = f'<span style="color:green">{breached_value}</span>'
                yield backend.IncidentResult(
                    breached_object=instrument,
                    breached_object_repr=str(instrument),
                    breached_value=breached_value,
                    report_details={"Aggregation": self.esg_aggregation.value},
                    severity=threshold.severity,
                )
