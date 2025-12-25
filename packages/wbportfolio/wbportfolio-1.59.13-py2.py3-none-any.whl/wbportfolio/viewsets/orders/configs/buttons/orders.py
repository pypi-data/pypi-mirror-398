from wbcore import serializers as wb_serializers
from wbcore.contrib.icons import WBIcon
from wbcore.enums import RequestType
from wbcore.metadata.configs import buttons as bt
from wbcore.metadata.configs.buttons.enums import Button
from wbcore.metadata.configs.buttons.view_config import ButtonViewConfig
from wbcore.metadata.configs.display import create_simple_display

from wbportfolio.order_routing import ExecutionInstruction


class ExecutionInstructionSerializer(wb_serializers.Serializer):
    execution_instruction = wb_serializers.ChoiceField(
        choices=ExecutionInstruction.choices,
        default=ExecutionInstruction.MARKET_ON_CLOSE.value,
        clear_dependent_fields=False,
    )
    apply_execution_instruction_to_all_orders = wb_serializers.BooleanField(
        default=False, label="Apply Execution instruction to all orders"
    )

    percentage = wb_serializers.FloatField(
        label="Percentage [1% - 25%]",
        percent=True,
        required=False,
        allow_null=True,
        on_unsatisfied_deps="hide",
        depends_on=[
            {
                "field": "execution_instruction",
                "options": {"activates_on": [ExecutionInstruction.IN_LINE_WITH_VOLUME.value]},
            }
        ],
    )
    price = wb_serializers.FloatField(
        label="Price (optional)",
        required=False,
        allow_null=True,
        on_unsatisfied_deps="hide",
        depends_on=[
            {
                "field": "execution_instruction",
                "options": {"activates_on": [ExecutionInstruction.LIMIT_ORDER.value]},
            }
        ],
    )
    good_for_date = wb_serializers.DateField(
        label="Good For Date (optional)",
        required=False,
        allow_null=True,
        on_unsatisfied_deps="hide",
        depends_on=[
            {
                "field": "execution_instruction",
                "options": {"activates_on": [ExecutionInstruction.LIMIT_ORDER.value]},
            }
        ],
    )
    period = wb_serializers.IntegerField(
        label="Period in minutes",
        required=False,
        allow_null=True,
        on_unsatisfied_deps="hide",
        depends_on=[
            {
                "field": "execution_instruction",
                "options": {"activates_on": [ExecutionInstruction.VWAP.value, ExecutionInstruction.TWAP.value]},
            }
        ],
    )
    time = wb_serializers.TimeField(
        label="Time (UTC)",
        format="%H:%M",
        required=False,
        allow_null=True,
        on_unsatisfied_deps="hide",
        depends_on=[
            {
                "field": "execution_instruction",
                "options": {"activates_on": [ExecutionInstruction.VWAP.value, ExecutionInstruction.TWAP.value]},
            }
        ],
    )


class OrderOrderProposalButtonConfig(ButtonViewConfig):
    def get_create_buttons(self):
        return {
            Button.SAVE_AND_CLOSE.value,
        }

    def get_custom_list_instance_buttons(self) -> set:
        return {
            bt.ActionButton(
                method=RequestType.PUT,
                identifiers=("wbportfolio:order",),
                icon=WBIcon.DEAL_MONEY.icon,
                key="execution_instruction",
                label="Change Execution",
                action_label="Execution changed",
                description_fields="<p>Change Execution</p>",
                serializer=ExecutionInstructionSerializer,
                instance_display=create_simple_display(
                    [
                        ["execution_instruction", "execution_instruction"],
                        ["percentage", "percentage"],
                        ["price", "good_for_date"],
                        ["period", "time"],
                        ["apply_execution_instruction_to_all_orders", "."],
                    ]
                ),
            )
        }
