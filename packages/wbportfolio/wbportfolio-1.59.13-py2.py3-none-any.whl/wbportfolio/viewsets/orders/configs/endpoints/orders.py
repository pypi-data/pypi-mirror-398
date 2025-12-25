from rest_framework.reverse import reverse
from wbcore.metadata.configs.endpoints import EndpointViewConfig

from wbportfolio.models import OrderProposal


class OrderOrderProposalEndpointConfig(EndpointViewConfig):
    def get_endpoint(self, **kwargs):
        if order_proposal_id := self.view.kwargs.get("order_proposal_id", None):
            order_proposal = OrderProposal.objects.get(id=order_proposal_id)
            if order_proposal.status == OrderProposal.Status.DRAFT:
                return reverse(
                    "wbportfolio:orderproposal-order-list",
                    args=[self.view.kwargs["order_proposal_id"]],
                    request=self.request,
                )
        return None

    def get_update_endpoint(self, **kwargs):
        if order_proposal_id := self.view.kwargs.get("order_proposal_id", None):
            order_proposal = OrderProposal.objects.get(id=order_proposal_id)
            if order_proposal.status == OrderProposal.Status.DRAFT or order_proposal.can_be_confirmed:
                return reverse(
                    "wbportfolio:orderproposal-order-list",
                    args=[self.view.kwargs["order_proposal_id"]],
                    request=self.request,
                )
        return None
