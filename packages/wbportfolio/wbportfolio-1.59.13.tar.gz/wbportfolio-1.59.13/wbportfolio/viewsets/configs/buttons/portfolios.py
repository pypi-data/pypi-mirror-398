from contextlib import suppress
from datetime import date

from pandas._libs.tslibs.offsets import BDay
from rest_framework.reverse import reverse
from wbcore import serializers as wb_serializers
from wbcore.contrib.currency.serializers import CurrencyRepresentationSerializer
from wbcore.contrib.icons import WBIcon
from wbcore.enums import RequestType
from wbcore.metadata.configs import buttons as bt
from wbcore.metadata.configs.buttons.view_config import ButtonViewConfig
from wbcore.metadata.configs.display.instance_display.shortcuts import (
    create_simple_display,
)
from wbfdm.models import Instrument
from wbfdm.serializers import InvestableUniverseRepresentationSerializer

from wbportfolio.models import AssetPosition, Portfolio
from wbportfolio.serializers import PortfolioRepresentationSerializer, RebalancerModelSerializer
from wbportfolio.viewsets.configs.display.rebalancing import RebalancerDisplayConfig


class CreateModelPortfolioSerializer(wb_serializers.ModelSerializer):
    create_index = wb_serializers.BooleanField(default=False, label="Create Underlying Index")
    name = wb_serializers.CharField(required=True)
    _currency = CurrencyRepresentationSerializer(source="currency")

    class Meta:
        model = Portfolio
        fields = (
            "name",
            "currency",
            "create_index",
            "_currency",
        )


class AdjustQuoteSerializer(wb_serializers.Serializer):
    old_quote = wb_serializers.PrimaryKeyRelatedField(queryset=Instrument.objects.all())
    _old_quote = InvestableUniverseRepresentationSerializer(source="old_quote")

    new_quote = wb_serializers.PrimaryKeyRelatedField(queryset=Instrument.objects.all())
    _new_quote = InvestableUniverseRepresentationSerializer(
        source="new_quote",
        optional_get_parameters={"old_quote": "sibling_of"},
        depends_on=[{"field": "old_quote", "options": {}}],
    )

    only_portfolios = wb_serializers.PrimaryKeyRelatedField(queryset=Portfolio.objects.all(), required=False)
    _only_portfolios = PortfolioRepresentationSerializer(
        source="only_portfolios",
        optional_get_parameters={"old_quote": "invests_in"},
        depends_on=[{"field": "new_quote", "options": {}}],
        many=True,
    )

    adjust_after = wb_serializers.DateField(required=False)


def _get_portfolio_start_end_serializer_class(portfolio):
    today = date.today()

    class StartEndDateSerializer(wb_serializers.Serializer):
        start = wb_serializers.DateField(
            label="Start",
            default=portfolio.assets.earliest("date").date if portfolio.assets.exists() else today,
        )
        end = wb_serializers.DateField(
            label="End", default=portfolio.assets.latest("date").date if portfolio.assets.exists() else today
        )

    return StartEndDateSerializer


def _get_rebalance_serializer_class(portfolio):
    try:
        default_trade_date = (portfolio.assets.latest("date").date + BDay(1)).date()
    except AssetPosition.DoesNotExist:
        default_trade_date = date.today()

    class RebalanceSerializer(wb_serializers.Serializer):
        trade_date = wb_serializers.DateField(default=default_trade_date)

    return RebalanceSerializer


class PortfolioButtonConfig(ButtonViewConfig):
    def get_custom_buttons(self) -> set:
        return {
            bt.ActionButton(
                method=RequestType.POST,
                identifiers=("wbportfolio:portfolio",),
                endpoint=reverse("wbportfolio:portfolio-adjustquote", args=[], request=self.request),
                label="Adjust quote",
                serializer=AdjustQuoteSerializer,
                action_label="Action triggered",
                title="Adjust Quote",
                instance_display=create_simple_display(
                    [
                        ["old_quote", "new_quote", "adjust_after"],
                        ["only_portfolios", "only_portfolios", "only_portfolios"],
                    ]
                ),
            ),
        }

    def get_custom_instance_buttons(self):
        admin_buttons = [
            bt.ActionButton(
                method=RequestType.POST,
                identifiers=("wbportfolio:portfolio",),
                key="add_automatic_rebalancer",
                label="Attach Rebalancer",
                serializer=RebalancerModelSerializer,
                action_label="Attach Rebalancer",
                title="Attach Rebalancer",
                instance_display=RebalancerDisplayConfig(
                    self.view, self.request, self.instance
                ).get_instance_display(),
            )
        ]
        buttons = [bt.WidgetButton(key="treegraphchart", label="Visualize Tree Graph Chart")]
        with suppress(Portfolio.DoesNotExist, KeyError):
            portfolio = Portfolio.objects.get(id=self.view.kwargs["pk"])
            buttons.append(
                bt.ActionButton(
                    method=RequestType.POST,
                    identifiers=("wbportfolio:portfolio",),
                    key="rebalance",
                    label="Rebalance",
                    serializer=_get_rebalance_serializer_class(portfolio),
                    action_label="Rebalance",
                    title="Rebalance",
                    instance_display=create_simple_display([["trade_date"]]),
                )
            )

            if primary_portfolio := portfolio.primary_portfolio:
                admin_buttons.append(
                    bt.ActionButton(
                        method=RequestType.POST,
                        identifiers=("wbportfolio:portfolio",),
                        key="recompute_lookthrough",
                        label="Recompute Look-Through Portfolio",
                        serializer=_get_portfolio_start_end_serializer_class(primary_portfolio),
                        action_label="Recompute Look-Through Portfolio",
                        title="Recompute Look-Through Portfolio",
                        instance_display=create_simple_display([["start", "end"]]),
                    )
                )
            buttons.append(
                bt.DropDownButton(label="Admin", icon=WBIcon.UNFOLD.icon, buttons=tuple(admin_buttons)),
            )
        return set(buttons)

    def get_custom_list_instance_buttons(self):
        return self.get_custom_instance_buttons()

    # def get_custom_buttons(self):
    #     if not self.view.kwargs.get("pk", None):
    #         return {
    #             bt.ActionButton(
    #                 method=RequestType.POST,
    #                 identifiers=("wbportfolio:portfolio",),
    #                 endpoint=reverse("wbportfolio:portfolio-createmodelportfolio", request=self.request),
    #                 label="Create New Model Portfolio",
    #                 serializer=CreateModelPortfolioSerializer,
    #                 action_label="create",
    #                 title="Create Model Portfolio",
    #                 instance_display=create_simple_display([["name", "currency"], ["create_index", "."]]),
    #             )
    #         }
    #     return set()
