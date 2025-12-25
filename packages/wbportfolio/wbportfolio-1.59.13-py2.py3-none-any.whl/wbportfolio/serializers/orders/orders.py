from decimal import Decimal

from rest_framework import serializers
from rest_framework.reverse import reverse
from rest_framework.validators import UniqueTogetherValidator
from wbcore import serializers as wb_serializers
from wbcore.metadata.configs.display.list_display import BaseTreeGroupLevelOption
from wbfdm.models import Instrument
from wbfdm.serializers import InvestableInstrumentRepresentationSerializer
from wbfdm.serializers.instruments.instruments import (
    CompanyRepresentationSerializer,
    SecurityRepresentationSerializer,
)

from wbportfolio.models import Order, OrderProposal


class GetSecurityDefault:
    requires_context = True

    def __call__(self, serializer_instance):
        try:
            instance = serializer_instance.view.get_object()
            return instance.underlying_instrument.parent or instance.underlying_instrument
        except Exception:
            return None


class GetCompanyDefault:
    requires_context = True

    def __call__(self, serializer_instance):
        try:
            instance = serializer_instance.view.get_object()
            security = instance.underlying_instrument.parent or instance.underlying_instrument
            return security.parent or security
        except Exception:
            return None


class OrderOrderProposalListModelSerializer(wb_serializers.ModelSerializer):
    underlying_instrument = wb_serializers.SlugRelatedField(read_only=True, slug_field="name")
    underlying_instrument_isin = wb_serializers.CharField(read_only=True)
    underlying_instrument_ticker = wb_serializers.CharField(read_only=True)
    underlying_instrument_refinitiv_identifier_code = wb_serializers.CharField(read_only=True)
    underlying_instrument_instrument_type = wb_serializers.CharField(read_only=True)
    underlying_instrument_exchange = wb_serializers.CharField(read_only=True)

    effective_weight = wb_serializers.DecimalField(
        read_only=True,
        max_digits=Order.ORDER_WEIGHTING_PRECISION + 1,
        decimal_places=Order.ORDER_WEIGHTING_PRECISION,
        default=0,
    )
    target_weight = wb_serializers.DecimalField(
        max_digits=Order.ORDER_WEIGHTING_PRECISION + 1,
        decimal_places=Order.ORDER_WEIGHTING_PRECISION,
        required=False,
    )

    effective_shares = wb_serializers.DecimalField(read_only=True, max_digits=16, decimal_places=6, default=0)
    target_shares = wb_serializers.DecimalField(required=False, max_digits=16, decimal_places=6)

    effective_total_value_fx_portfolio = wb_serializers.DecimalField(
        read_only=True, max_digits=16, decimal_places=2, default=0
    )
    target_total_value_fx_portfolio = wb_serializers.DecimalField(required=False, max_digits=16, decimal_places=2)
    total_value_fx_portfolio = wb_serializers.DecimalField(required=False, max_digits=16, decimal_places=2)

    portfolio_currency = wb_serializers.CharField(read_only=True)
    underlying_instrument_currency = wb_serializers.CharField(read_only=True)
    has_warnings = wb_serializers.BooleanField(read_only=True)
    execution_instruction_parameters_repr = wb_serializers.CharField(read_only=True)
    execution_date = wb_serializers.DateField(read_only=True)
    execution_price = wb_serializers.FloatField(read_only=True)
    execution_traded_shares = wb_serializers.FloatField(read_only=True)

    @wb_serializers.register_resource()
    def additional_resources(self, instance, request, user):
        if (view := request.parser_context.get("view")) and view.order_proposal.status in [
            OrderProposal.Status.DRAFT,
            OrderProposal.Status.PENDING,
            OrderProposal.Status.APPROVED,
        ]:
            return {
                "execution_instruction": reverse(
                    "wbportfolio:orderproposal-order-changeexecutioninstruction",
                    args=[view.order_proposal.id, instance.id],
                    request=request,
                )
            }
        return {}

    def validate(self, data):
        data.pop("company", None)
        data.pop("security", None)
        if self.instance and "underlying_instrument" in data:
            raise serializers.ValidationError(
                {
                    "underlying_instrument": "You cannot modify the underlying instrument other than creating a new entry"
                }
            )

        effective_weight = self.instance._effective_weight if self.instance else Decimal(0.0)
        effective_shares = self.instance._effective_shares if self.instance else Decimal(0.0)
        portfolio_value = (
            self.context["view"].order_proposal.portfolio_total_asset_value if "view" in self.context else Decimal(0.0)
        )
        if (total_value_fx_portfolio := data.pop("total_value_fx_portfolio", None)) is not None and portfolio_value:
            data["weighting"] = total_value_fx_portfolio / portfolio_value
        if (
            target_total_value_fx_portfolio := data.pop("target_total_value_fx_portfolio", None)
        ) is not None and portfolio_value:
            data["target_weight"] = target_total_value_fx_portfolio / portfolio_value

        if data.get("weighting") is not None or data.get("target_weight") is not None:
            weighting = data.pop("weighting", None)
            if (target_weight := data.pop("target_weight", None)) is not None:
                weighting = target_weight - effective_weight
                data["desired_target_weight"] = target_weight
            if weighting is not None:
                data["weighting"] = weighting
            data.pop("shares", None)
            data.pop("target_shares", None)

        if data.get("shares") is not None or data.get("target_shares") is not None:
            shares = data.pop("shares", None)
            if (target_shares := data.pop("target_shares", None)) is not None:
                shares = target_shares - effective_shares
            if shares is not None:
                data["shares"] = shares
        return super().validate(data)

    def update(self, instance, validated_data):
        weighting = validated_data.pop("weighting", None)
        shares = validated_data.pop("shares", None)
        portfolio_total_asset_value = instance.order_proposal.portfolio_total_asset_value
        if weighting is not None:
            instance.set_weighting(weighting, portfolio_total_asset_value)
        if shares is not None:
            instance.set_shares(shares, portfolio_total_asset_value)
        return super().update(instance, validated_data)

    def create(self, validated_data):
        weighting = validated_data.pop("weighting", None)
        shares = validated_data.pop("shares", None)
        instance = super().create(validated_data)
        portfolio_total_asset_value = instance.order_proposal.portfolio_total_asset_value
        if weighting is not None:
            instance.set_weighting(weighting, portfolio_total_asset_value)
        if shares is not None:
            instance.set_shares(shares, portfolio_total_asset_value)
        instance.save()
        return instance

    def get_unique_together_validators(self):
        return [
            UniqueTogetherValidator(
                queryset=Order.objects.all(),
                fields=("order_proposal", "underlying_instrument"),
                message="This instrument is already in the orders list.",
            )
        ]

    class Meta:
        model = Order
        percent_fields = ["effective_weight", "target_weight", "weighting", "desired_target_weight"]
        decorators = {
            "total_value_fx_portfolio": wb_serializers.decorator(
                decorator_type="text", position="left", value="{{portfolio_currency}}"
            ),
            "effective_total_value_fx_portfolio": wb_serializers.decorator(
                decorator_type="text", position="left", value="{{portfolio_currency}}"
            ),
            "target_total_value_fx_portfolio": wb_serializers.decorator(
                decorator_type="text", position="left", value="{{portfolio_currency}}"
            ),
            "price": wb_serializers.decorator(position="left", value="{{underlying_instrument_currency}}"),
        }
        read_only_fields = (
            "order_type",
            "effective_shares",
            "effective_total_value_fx_portfolio",
            "has_warnings",
            "desired_target_weight",
            "daily_return",
            "currency_fx_rate",
            "price",
            "execution_instruction",
            "execution_instruction_parameters_repr",
            "execution_date",
            "execution_price",
            "execution_traded_shares",
        )
        extra_kwargs = {
            "price": {"required": False},
        }
        fields = (
            "id",
            "shares",
            "underlying_instrument",
            "underlying_instrument_isin",
            "underlying_instrument_ticker",
            "underlying_instrument_refinitiv_identifier_code",
            "underlying_instrument_instrument_type",
            "underlying_instrument_exchange",
            "order_type",
            "comment",
            "effective_weight",
            "target_weight",
            "weighting",
            "order_proposal",
            "order",
            "effective_shares",
            "target_shares",
            "total_value_fx_portfolio",
            "effective_total_value_fx_portfolio",
            "target_total_value_fx_portfolio",
            "portfolio_currency",
            "underlying_instrument_currency",
            "has_warnings",
            "desired_target_weight",
            "daily_return",
            "currency_fx_rate",
            "price",
            "execution_status",
            "execution_instruction",
            "execution_instruction_parameters",
            "execution_comment",
            "execution_instruction_parameters_repr",
            "execution_date",
            "execution_price",
            "execution_traded_shares",
            "_additional_resources",
        )


class OrderOrderProposalModelSerializer(OrderOrderProposalListModelSerializer):
    company = wb_serializers.PrimaryKeyRelatedField(
        queryset=Instrument.objects.filter(level=0),
        required=False,
        read_only=lambda view: not view.new_mode,
        default=GetCompanyDefault(),
    )
    _company = CompanyRepresentationSerializer(source="company", required=False)

    security = wb_serializers.PrimaryKeyRelatedField(
        queryset=Instrument.objects.filter(is_security=True),
        required=False,
        read_only=lambda view: not view.new_mode,
        default=GetSecurityDefault(),
    )
    _security = SecurityRepresentationSerializer(
        source="security",
        optional_get_parameters={"company": "parent"},
        depends_on=[{"field": "company", "options": {}}],
        required=False,
        select_first_choice=True,
    )
    underlying_instrument = wb_serializers.PrimaryKeyRelatedField(
        queryset=Instrument.objects.all(), label="Quote", read_only=lambda view: not view.new_mode
    )
    _underlying_instrument = InvestableInstrumentRepresentationSerializer(
        source="underlying_instrument",
        optional_get_parameters={"security": "parent"},
        depends_on=[{"field": "security", "options": {}}],
        tree_config=BaseTreeGroupLevelOption(clear_filter=True, filter_key="parent"),
        select_first_choice=True,
    )

    class Meta(OrderOrderProposalListModelSerializer.Meta):
        fields = list(OrderOrderProposalListModelSerializer.Meta.fields) + [
            "company",
            "_company",
            "security",
            "_security",
            "_underlying_instrument",
        ]


class ReadOnlyOrderOrderProposalModelSerializer(OrderOrderProposalListModelSerializer):
    class Meta(OrderOrderProposalListModelSerializer.Meta):
        read_only_fields = OrderOrderProposalListModelSerializer.Meta.fields
