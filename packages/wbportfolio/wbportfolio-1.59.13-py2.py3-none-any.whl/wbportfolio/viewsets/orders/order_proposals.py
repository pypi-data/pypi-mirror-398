from contextlib import suppress
from datetime import date
from decimal import Decimal

from django.contrib.messages import error, warning
from django.shortcuts import get_object_or_404
from django.utils.functional import cached_property
from pandas._libs.tslibs.offsets import BDay
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from wbcompliance.viewsets.risk_management.mixins import RiskCheckViewSetMixin
from wbcore import serializers as wb_serializers
from wbcore import viewsets
from wbcore.metadata.configs.display.instance_display import (
    Display,
    create_simple_display,
)
from wbcore.permissions.permissions import InternalUserPermissionMixin
from wbcore.utils.views import CloneMixin

from wbportfolio.models import AssetPosition, Order, OrderProposal
from wbportfolio.models.orders.order_proposals import (
    execute_orders_as_task,
    push_model_change_as_task,
    replay_as_task,
)
from wbportfolio.serializers import (
    OrderProposalModelSerializer,
    OrderProposalRepresentationSerializer,
    ReadOnlyOrderProposalModelSerializer,
)

from ...filters.orders import OrderProposalFilterSet
from ...order_routing import ExecutionStatus, RoutingException
from ...permissions import IsPortfolioManager
from ..mixins import UserPortfolioRequestPermissionMixin
from .configs import (
    OrderProposalButtonConfig,
    OrderProposalDisplayConfig,
    OrderProposalEndpointConfig,
    OrderProposalPortfolioEndpointConfig,
)


class OrderProposalRepresentationViewSet(InternalUserPermissionMixin, viewsets.RepresentationViewSet):
    IDENTIFIER = "wbportfolio:trade"
    queryset = OrderProposal.objects.all()
    serializer_class = OrderProposalRepresentationSerializer


class OrderProposalModelViewSet(CloneMixin, RiskCheckViewSetMixin, InternalUserPermissionMixin, viewsets.ModelViewSet):
    IDENTIFIER = "wbportfolio:order"
    ordering_fields = ("trade_date",)
    ordering = ("-trade_date",)
    search_fields = ("comment",)
    filterset_fields = {"trade_date": ["exact", "gte", "lte"], "status": ["exact"]}

    queryset = OrderProposal.objects.select_related("rebalancing_model", "portfolio")
    serializer_class = OrderProposalModelSerializer
    filterset_class = OrderProposalFilterSet
    display_config_class = OrderProposalDisplayConfig
    button_config_class = OrderProposalButtonConfig
    endpoint_config_class = OrderProposalEndpointConfig

    def get_serializer_class(self):
        if self.new_mode or (
            "pk" in self.kwargs and (obj := self.get_object()) and obj.status == OrderProposal.Status.DRAFT
        ):
            return OrderProposalModelSerializer
        return ReadOnlyOrderProposalModelSerializer

    # 2 methods to parametrize the clone button functionality
    def get_clone_button_serializer_class(self, instance):
        class CloneSerializer(wb_serializers.Serializer):
            clone_date = wb_serializers.DateField(
                default=(instance.trade_date + BDay(1)).date(), label="Trade Date"
            )  # we need to change the field name from the trade proposa fields, otherwise fontend conflicts
            clone_comment = wb_serializers.TextField(label="Comment")

        return CloneSerializer

    def get_clone_button_instance_display(self) -> Display:
        return create_simple_display(
            [
                ["clone_comment"],
                ["clone_date"],
            ]
        )

    def add_messages(self, request, instance: OrderProposal | None = None, **kwargs):
        if instance:
            if instance.status == OrderProposal.Status.PENDING and instance.has_non_successful_checks:
                warning(
                    request,
                    "This order proposal cannot be approved because there is unsuccessful pre-trade checks. Please rectify accordingly and resubmit a valid order proposal",
                )
            if (
                instance.status == OrderProposal.Status.EXECUTION
                and instance.orders.exclude(shares=0, weighting=0)
                .filter(execution_status=Order.ExecutionStatus.FAILED)
                .exists()
            ):
                warning(request, "Some orders failed confirmation. Check the list for further details.")
            if instance.execution_status in [
                ExecutionStatus.REJECTED,
                ExecutionStatus.FAILED,
                ExecutionStatus.UNKNOWN,
            ]:
                warning(
                    request,
                    f"The execution status is {ExecutionStatus[instance.execution_status].label}. Detail: {instance.execution_comment}",
                )
            elif instance.can_be_executed and instance.approver == request.user.profile:
                warning(
                    request,
                    "As the approver of these orders, you are not authorized to execute them yourself. Please assign execution to another qualified individual.",
                )

    @classmethod
    def _get_risk_checks_button_title(cls) -> str:
        return "Pre-Trade Checks"

    @action(detail=True, methods=["PATCH"], permission_classes=[IsPortfolioManager])
    def reset(self, request, pk=None):
        order_proposal = get_object_or_404(OrderProposal, pk=pk)
        use_desired_target_weight = request.GET.get("use_desired_target_weight") == "true"
        if order_proposal.status == OrderProposal.Status.DRAFT:
            order_proposal.orders.all().update(weighting=0)
            order_proposal.reset_orders(use_desired_target_weight=use_desired_target_weight)
            return Response({"send": True})
        return Response({"status": "Order Proposal is not Draft"}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["PATCH"], permission_classes=[IsPortfolioManager])
    def normalize(self, request, pk=None):
        order_proposal = get_object_or_404(OrderProposal, pk=pk)
        total_cash_weight = Decimal(request.data.get("total_cash_weight", Decimal("0.0")))
        if order_proposal.status == OrderProposal.Status.DRAFT:
            order_proposal.normalize_orders(total_cash_weight)
            return Response({"send": True})
        return Response({"status": "Order Proposal is not Draft"}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["PATCH"], permission_classes=[IsPortfolioManager])
    def replay(self, request, pk=None):
        order_proposal = get_object_or_404(OrderProposal, pk=pk)
        if order_proposal.portfolio.is_manageable:
            replay_as_task.delay(order_proposal.id, user_id=self.request.user.id)
            return Response({"send": True})
        return Response({"status": "Order Proposal is not Draft"}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["PATCH"], permission_classes=[IsPortfolioManager])
    def pushmodelchange(self, request, pk=None):
        order_proposal = get_object_or_404(OrderProposal, pk=pk)
        only_for_portfolio_ids = list(
            map(lambda o: int(o), filter(lambda r: r, request.data.get("only_for_portfolio_ids", "").split(",")))
        )
        approve_automatically = request.data.get("approve_automatically") == "true"
        if order_proposal.status == OrderProposal.Status.APPROVED and order_proposal.portfolio.is_model:
            push_model_change_as_task.delay(
                order_proposal.id,
                request.user.id,
                only_for_portfolio_ids=only_for_portfolio_ids,
                approve_automatically=approve_automatically,
            )
            return Response({"send": True})
        return Response(
            {"status": "Order Proposal needs to be approved and linked to be a model portfolio"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @action(detail=True, methods=["PATCH"], permission_classes=[IsPortfolioManager])
    def execute(self, request, pk=None):
        order_proposal = get_object_or_404(OrderProposal, pk=pk)
        if order_proposal.can_execute(request.user):
            prioritize_target_weight = request.data.get("prioritize_target_weight") == "true"
            order_proposal.execution_status = ExecutionStatus.PENDING
            order_proposal.execution_comment = "Waiting for custodian confirmation"
            order_proposal.save()
            execute_orders_as_task.delay(order_proposal.id, prioritize_target_weight=prioritize_target_weight)
            return Response({"send": True})
        return Response({"status": "Order Proposal is not Draft"}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["PATCH"], permission_classes=[IsPortfolioManager])
    def cancelexecution(self, request, pk=None):
        order_proposal = get_object_or_404(OrderProposal, pk=pk)
        if order_proposal.execution_status and order_proposal.execution_status != ExecutionStatus.CANCELLED:
            try:
                if not order_proposal.cancel_rebalancing():
                    warning(
                        request,
                        "We could not cancel the rebalancing. It is probably already executed. Please refresh status or check with an administrator.",
                    )
            except (RoutingException, ValueError) as e:
                error(request, f"Could not cancel orders proposal {order_proposal}: {str(e)}")
            return Response({"send": True})
        return Response(
            {"status": "Order Proposal is not in an execution phase, therefore, it cannot be cancelled."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @action(detail=True, methods=["PATCH"], permission_classes=[IsPortfolioManager])
    def updateexecutionstatus(self, request, pk=None):
        order_proposal = get_object_or_404(OrderProposal, pk=pk)
        if order_proposal.execution_status:
            try:
                if not order_proposal.custodian_router:
                    raise RoutingException(
                        "There is no custodian router for this portfolio. Please check with an administrator."
                    )
                order_proposal.refresh_execution_status()
            except (RoutingException, ValueError) as e:
                error(request, f"Could not update rebalancing status: {str(e)}")
            return Response(
                {
                    "send": True,
                }
            )
        return Response(
            {"status": "Order Proposal is not in an execution phase, therefore, its status cannot be fetched."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    @action(detail=True, methods=["PATCH"], permission_classes=[IsPortfolioManager])
    def refreshreturn(self, request, pk=None):
        order_proposal = get_object_or_404(OrderProposal, pk=pk)
        order_proposal.refresh_returns()
        return Response(
            {"status": "Returns were refreshed with success"},
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["PATCH"], permission_classes=[IsPortfolioManager])
    def refreshpretradechecks(self, request, pk=None):
        order_proposal = get_object_or_404(OrderProposal, pk=pk)
        if order_proposal.status == OrderProposal.Status.DRAFT:
            order_proposal.evaluate_pretrade_checks()
        return Response(
            {"status": "Evaluate pretrade checks"},
            status=status.HTTP_200_OK,
        )


class OrderProposalPortfolioModelViewSet(UserPortfolioRequestPermissionMixin, OrderProposalModelViewSet):
    endpoint_config_class = OrderProposalPortfolioEndpointConfig

    @cached_property
    def default_trade_date(self) -> date | None:
        with suppress(AssetPosition.DoesNotExist):
            return (self.portfolio.assets.latest("date").date + BDay(1)).date()

    def get_queryset(self):
        return OrderProposal.objects.filter(portfolio=self.kwargs["portfolio_id"])
