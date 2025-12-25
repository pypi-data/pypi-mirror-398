from ..graph.node import Node
from ..graph.port import PortType, InputPort, OutputPort


class Conditional(Node):
    def __init__(self, id: str | None = None):
        super().__init__(
            node_type="Conditional",
            category="controlFlows",
            task_name="control_flows.conditional",
            node_id=id,
            ports={
                "field_type": InputPort(
                    name="field_type",
                    port_type=PortType.SELECT,
                    value="string",
                    options=[{"value": "string", "label": "Str"}, {"value": "number", "label": "Number"}],
                ),
                "left_field": InputPort(
                    name="left_field",
                    port_type=PortType.INPUT,
                    value="",
                ),
                "operator": InputPort(
                    name="operator",
                    port_type=PortType.SELECT,
                    value="equal",
                    options=[
                        {"value": "equal", "label": "equal", "field_type": ["string", "number"]},
                        {"value": "not_equal", "label": "not_equal", "field_type": ["string", "number"]},
                        {"value": "greater_than", "label": "greater_than", "field_type": ["number"]},
                        {"value": "less_than", "label": "less_than", "field_type": ["number"]},
                        {"value": "greater_than_or_equal", "label": "greater_than_or_equal", "field_type": ["number"]},
                        {"value": "less_than_or_equal", "label": "less_than_or_equal", "field_type": ["number"]},
                        {"value": "include", "label": "include", "field_type": ["string"]},
                        {"value": "not_include", "label": "not_include", "field_type": ["string"]},
                        {"value": "is_empty", "label": "is_empty", "field_type": ["string"]},
                        {"value": "is_not_empty", "label": "is_not_empty", "field_type": ["string"]},
                        {"value": "starts_with", "label": "starts_with", "field_type": ["string"]},
                        {"value": "ends_with", "label": "ends_with", "field_type": ["string"]},
                    ],
                ),
                "right_field": InputPort(
                    name="right_field",
                    port_type=PortType.INPUT,
                    value="",
                ),
                "true_output": InputPort(
                    name="true_output",
                    port_type=PortType.INPUT,
                    value="",
                ),
                "false_output": InputPort(
                    name="false_output",
                    port_type=PortType.INPUT,
                    value="",
                ),
                "output": OutputPort(),
            },
        )


class Empty(Node):
    def __init__(self, id: str | None = None):
        super().__init__(
            node_type="Empty",
            category="controlFlows",
            task_name="control_flows.empty",
            node_id=id,
            ports={
                "input": InputPort(
                    name="input",
                    port_type=PortType.INPUT,
                    value="",
                ),
                "output": OutputPort(has_tooltip=True),
            },
        )


class HumanFeedback(Node):
    def __init__(self, id: str | None = None):
        super().__init__(
            node_type="HumanFeedback",
            category="controlFlows",
            task_name="control_flows.human_feedback",
            node_id=id,
            ports={
                "hint_message": InputPort(
                    name="hint_message",
                    port_type=PortType.TEXTAREA,
                    value="",
                    show=True,
                    has_tooltip=True,
                ),
                "human_input": InputPort(
                    name="human_input",
                    port_type=PortType.TEXTAREA,
                    value="",
                    show=True,
                ),
                "output": OutputPort(),
            },
        )


class JsonProcess(Node):
    def __init__(self, id: str | None = None):
        super().__init__(
            node_type="JsonProcess",
            category="controlFlows",
            task_name="control_flows.json_process",
            node_id=id,
            can_add_output_ports=True,
            ports={
                "input": InputPort(
                    name="input",
                    port_type=PortType.INPUT,
                    value="",
                ),
                "process_mode": InputPort(
                    name="process_mode",
                    port_type=PortType.SELECT,
                    value="get_value",
                    options=[
                        {"value": "get_value", "label": "get_value"},
                        {"value": "get_multiple_values", "label": "get_multiple_values"},
                        {"value": "list_values", "label": "list_values"},
                        {"value": "list_keys", "label": "list_keys"},
                    ],
                    required=False,
                ),
                "key": InputPort(
                    name="key",
                    port_type=PortType.INPUT,
                    value="",
                    condition="return fieldsData.process_mode.value == 'get_value'",
                    condition_python=lambda ports: ports["process_mode"].value == "get_value",
                ),
                "keys": InputPort(
                    name="keys",
                    port_type=PortType.INPUT,
                    value=[],
                    required=False,
                ),
                "default_value": InputPort(
                    name="default_value",
                    port_type=PortType.INPUT,
                    value="",
                    condition="return fieldsData.process_mode.value == 'get_value'",
                    condition_python=lambda ports: ports["process_mode"].value == "get_value",
                ),
                "output": OutputPort(),
            },
        )


class RandomChoice(Node):
    def __init__(self, id: str | None = None):
        super().__init__(
            node_type="RandomChoice",
            category="controlFlows",
            task_name="control_flows.random_choice",
            node_id=id,
            ports={
                "input": InputPort(
                    name="input",
                    port_type=PortType.LIST,
                    value=[],
                ),
                "output": OutputPort(),
            },
        )


class WorkflowLoop(Node):
    def __init__(self, id: str | None = None):
        super().__init__(
            node_type="WorkflowLoop",
            category="controlFlows",
            task_name="control_flows.workflow_loop",
            node_id=id,
            ports={
                "workflow_id": InputPort(
                    name="workflow_id",
                    port_type=PortType.INPUT,
                    value="",
                ),
                "loop_count": InputPort(
                    name="loop_count",
                    port_type=PortType.NUMBER,
                    value="",
                ),
                "max_loop_count": InputPort(
                    name="max_loop_count",
                    port_type=PortType.NUMBER,
                    value=10,
                ),
                "initial_values": InputPort(
                    name="initial_values",
                    port_type=PortType.INPUT,
                    value="",
                ),
                "assignment_in_loop": InputPort(
                    name="assignment_in_loop",
                    port_type=PortType.INPUT,
                    value={},
                ),
                "loop_end_condition": InputPort(
                    name="loop_end_condition",
                    port_type=PortType.SELECT,
                    value="loop_count",
                    options=[
                        {"label": "loop_count", "value": "loop_count"},
                        {"label": "output_field_condition", "value": "output_field_condition"},
                        {"label": "ai_model_judgement", "value": "ai_model_judgement"},
                    ],
                ),
                "output_field_condition_field": InputPort(
                    name="output_field_condition_field",
                    port_type=PortType.SELECT,
                    value="",
                    options=[],
                    required=False,
                ),
                "output_field_condition_operator": InputPort(
                    name="output_field_condition_operator",
                    port_type=PortType.SELECT,
                    value="equal",
                    options=[
                        {"value": "equal", "label": "equal", "field_type": ["string", "number"]},
                        {"value": "not_equal", "label": "not_equal", "field_type": ["string", "number"]},
                        {"value": "greater_than", "label": "greater_than", "field_type": ["number"]},
                        {"value": "less_than", "label": "less_than", "field_type": ["number"]},
                        {"value": "greater_than_or_equal", "label": "greater_than_or_equal", "field_type": ["number"]},
                        {"value": "less_than_or_equal", "label": "less_than_or_equal", "field_type": ["number"]},
                        {"value": "include", "label": "include", "field_type": ["string"]},
                        {"value": "not_include", "label": "not_include", "field_type": ["string"]},
                        {"value": "is_empty", "label": "is_empty", "field_type": ["string"]},
                        {"value": "is_not_empty", "label": "is_not_empty", "field_type": ["string"]},
                        {"value": "starts_with", "label": "starts_with", "field_type": ["string"]},
                        {"value": "ends_with", "label": "ends_with", "field_type": ["string"]},
                    ],
                    required=False,
                ),
                "output_field_condition_value": InputPort(
                    name="output_field_condition_value",
                    port_type=PortType.INPUT,
                    value="",
                    required=False,
                ),
                "judgement_model": InputPort(
                    name="judgement_model",
                    port_type=PortType.SELECT,
                    value="OpenAI/gpt-4o-mini",
                    options=[],
                    required=False,
                ),
                "judgement_prompt": InputPort(
                    name="judgement_prompt",
                    port_type=PortType.TEXTAREA,
                    value="",
                    required=False,
                ),
                "judgement_end_output": InputPort(
                    name="judgement_end_output",
                    port_type=PortType.INPUT,
                    value="",
                    required=False,
                ),
            },
        )


class WorkflowSelector(Node):
    def __init__(self, id: str | None = None):
        super().__init__(
            node_type="WorkflowSelector",
            category="controlFlows",
            task_name="control_flows.workflow_selector",
            node_id=id,
            ports={
                "template": InputPort(
                    name="template",
                    port_type=PortType.TEXTAREA,
                    value="",
                ),
                "workflow_ids": InputPort(
                    name="workflow_ids",
                    port_type=PortType.SELECT,
                    value=[],
                ),
                "llm_model": InputPort(
                    name="llm_model",
                    port_type=PortType.SELECT,
                    value="OpenAI/gpt-4o-mini",
                    options=[],
                    required=False,
                ),
                "output": OutputPort(),
            },
        )
