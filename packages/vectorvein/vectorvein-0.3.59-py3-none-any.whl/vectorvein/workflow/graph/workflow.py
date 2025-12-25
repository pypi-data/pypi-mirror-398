import json
from typing import Any

from .node import Node
from .edge import Edge
from .port import InputPort, OutputPort
from ..utils.layout import layout
from ..utils.check import (
    WorkflowCheckResult,
    check_dag,
    check_ui,
    check_useless_nodes,
    check_required_ports,
    check_override_ports,
    check_output_nodes_with_no_inputs,
)


class Workflow:
    def __init__(self) -> None:
        self.nodes: list[Node] = []
        self.edges: list[Edge] = []

    def add_node(self, node: Node):
        self.nodes.append(node)

    def add_nodes(self, nodes: list[Node]):
        self.nodes.extend(nodes)

    def add_edge(self, edge: Edge):
        self.edges.append(edge)

    def connect(
        self,
        source_node: str | Node,
        source_port: str,
        target_node: str | Node,
        target_port: str,
    ):
        # 获取源节点ID
        if isinstance(source_node, Node):
            source_node_id = source_node.id
        else:
            source_node_id = source_node

        # 获取目标节点ID
        if isinstance(target_node, Node):
            target_node_id = target_node.id
        else:
            target_node_id = target_node

        # 检查源节点是否存在
        source_node_exists = any(node.id == source_node_id for node in self.nodes)
        if not source_node_exists:
            raise ValueError(f"Source node not found: {source_node_id}")

        # 检查目标节点是否存在
        target_node_exists = any(node.id == target_node_id for node in self.nodes)
        if not target_node_exists:
            raise ValueError(f"Target node not found: {target_node_id}")

        # 检查源节点的端口是否存在
        source_node_obj = next(node for node in self.nodes if node.id == source_node_id)
        if not source_node_obj.has_output_port(source_port):
            raise ValueError(f"Source node {source_node_id} has no output port: {source_port}")

        # 检查目标节点的端口是否存在
        target_node_obj = next(node for node in self.nodes if node.id == target_node_id)
        if not target_node_obj.has_input_port(target_port):
            raise ValueError(f"Target node {target_node_id} has no input port: {target_port}")

        # 确保目标端口是InputPort而不是OutputPort
        target_port_obj = target_node_obj.ports[target_port]
        if isinstance(target_port_obj, OutputPort):
            raise ValueError(f"The target port {target_port} of node {target_node_id} is an output port. OutputPort cannot be a connection target.")

        # 检查目标端口是否已有被连接的线
        for edge in self.edges:
            if edge.target == target_node_id and edge.target_handle == target_port:
                raise ValueError(
                    f"The input port {target_port} of the target node {target_node_id} is already connected: {edge.source}({edge.source_handle}) → {edge.target}({edge.target_handle})"
                )

        # 创建并添加边
        edge_id = f"vueflow__edge-{source_node_id}{source_port}-{target_node_id}{target_port}"
        edge = Edge(edge_id, source_node_id, source_port, target_node_id, target_port)
        self.add_edge(edge)

    def to_dict(self):
        return {
            "nodes": [node.to_dict() for node in self.nodes],
            "edges": [edge.to_dict() for edge in self.edges],
            "viewport": {"x": 0, "y": 0, "zoom": 1},
        }

    def to_json(self, ensure_ascii=False):
        return json.dumps(self.to_dict(), ensure_ascii=ensure_ascii)

    def to_mermaid(self) -> str:
        """生成 Mermaid 格式的流程图。

        Returns:
            str: Mermaid 格式的流程图文本
        """
        lines = ["flowchart TD"]

        # 创建节点类型到序号的映射
        type_counters = {}
        node_id_to_label = {}

        # 首先为所有节点生成标签
        for node in self.nodes:
            node_type = node.type.lower()
            if node_type not in type_counters:
                type_counters[node_type] = 0
            node_label = f"{node_type}_{type_counters[node_type]}"
            node_id_to_label[node.id] = node_label
            type_counters[node_type] += 1

        # 添加节点定义
        for node in self.nodes:
            node_label = node_id_to_label[node.id]
            lines.append(f'    {node_label}["{node_label} ({node.type})"]')

        lines.append("")  # 添加一个空行分隔节点和边的定义

        # 添加边的定义
        for edge in self.edges:
            source_label = node_id_to_label[edge.source]
            target_label = node_id_to_label[edge.target]
            label = f"{edge.source_handle} → {edge.target_handle}"
            lines.append(f"    {source_label} -->|{label}| {target_label}")

        return "\n".join(lines)

    def check(self) -> WorkflowCheckResult:
        """检查流程图的有效性。

        Returns:
            WorkflowCheckResult: 包含各种检查结果的字典
        """
        dag_check = check_dag(self)  # 检查流程图是否为有向无环图，并检测是否存在孤立节点。
        ui_check = check_ui(self)
        useless_nodes = check_useless_nodes(self)
        required_ports = check_required_ports(self)
        override_ports = check_override_ports(self)
        output_nodes_with_no_inputs = check_output_nodes_with_no_inputs(self)

        # 合并结果
        result: WorkflowCheckResult = {
            "no_cycle": dag_check["no_cycle"],
            "no_isolated_nodes": dag_check["no_isolated_nodes"],
            "ui_warnings": ui_check,
            "useless_nodes": useless_nodes,
            "required_ports": required_ports,
            "override_ports": override_ports,
            "output_nodes_with_no_inputs": output_nodes_with_no_inputs,
        }

        return result

    def layout(self, options: dict[str, Any] | None = None) -> "Workflow":
        """对工作流中的节点进行自动布局，计算并更新每个节点的位置。

        此方法实现了一个简单的分层布局算法，将节点按照有向图的拓扑结构进行排列。

        Args:
            options: 布局选项，包括:
                - direction: 布局方向 ('TB', 'BT', 'LR', 'RL')，默认 'LR'
                - node_spacing: 同一层级节点间的间距，默认 500
                - layer_spacing: 不同层级间的间距，默认 400
                - margin_x: 图形左右边距，默认 20
                - margin_y: 图形上下边距，默认 20

        Returns:
            布局后的工作流对象
        """
        layout(self.nodes, self.edges, options)
        return self

    @classmethod
    def from_json(cls, json_str: str) -> "Workflow":
        """从 JSON 字符串创建工作流对象。

        Args:
            json_str: JSON 字符串

        Returns:
            Workflow: 工作流对象
        """
        workflow = cls()
        data = json.loads(json_str)

        # 创建节点
        for node_data in data.get("nodes", []):
            node_type = node_data["type"]
            category = node_data["category"]
            task_name = node_data["data"]["task_name"]

            # 尝试动态导入节点类
            NodeClass = None
            try:
                # 如果task_name包含分类信息
                if "." in task_name:
                    category, _ = task_name.split(".")
                    module_path = f"vectorvein.workflow.nodes.{category}"
                    module = __import__(module_path, fromlist=[node_type])
                    if hasattr(module, node_type):
                        NodeClass = getattr(module, node_type)
            except (ImportError, AttributeError):
                pass

            if not NodeClass:
                raise ValueError(f"Node class not found: {node_type}")
            # 创建节点实例以获取默认值
            node_instance = NodeClass()

            # 使用节点实例的基本属性
            node = Node(
                node_type=node_type,
                category=category,
                task_name=task_name,
                description=node_data["data"].get("description", node_instance.description if hasattr(node_instance, "description") else ""),
                node_id=node_data["id"],
                position=node_data.get("position", {"x": 0, "y": 0}),
                seleted_workflow_title=node_data["data"].get("seleted_workflow_title", ""),
                is_template=node_data["data"].get("is_template", False),
                initialized=node_data.get("initialized", False),
                can_add_input_ports=node_data["data"].get("has_inputs", False),
                can_add_output_ports=node_data["data"].get("has_outputs", False),
            )

            # 处理端口
            for port_name, port_data in node_data["data"].get("template", {}).items():
                # 如果端口已存在于节点实例中，直接修改其属性
                if port_name in node_instance.ports:
                    # 直接修改原始端口的属性，而不是创建新端口
                    port = node_instance.ports[port_name]

                    # 更新端口的属性
                    if "field_type" in port_data:
                        port.port_type = port_data["field_type"]
                    if "required" in port_data:
                        port.required = port_data["required"]
                    if "show" in port_data:
                        port.show = port_data["show"]
                    if "value" in port_data:
                        port.value = port_data["value"]
                    if "options" in port_data:
                        port.options = port_data["options"]
                    if "type" in port_data:
                        port.field_type = port_data["type"]
                    if "max_length" in port_data:
                        port.max_length = port_data["max_length"]
                    if "support_file_types" in port_data and port_data["support_file_types"]:
                        port.support_file_types = port_data["support_file_types"].split(", ")
                    if "multiple" in port_data:
                        port.multiple = port_data["multiple"]
                    if "group" in port_data:
                        port.group = port_data["group"]
                    if "group_collpased" in port_data:
                        port.group_collpased = port_data["group_collpased"]
                    if "has_tooltip" in port_data:
                        port.has_tooltip = port_data["has_tooltip"]
                    if "max" in port_data:
                        port.max = port_data["max"]
                    if "min" in port_data:
                        port.min = port_data["min"]
                    if "list" in port_data:
                        port.list = port_data["list"]
                else:
                    # 对于新添加的端口，检查是否允许添加
                    port_type = port_data.get("field_type", "text")
                    is_output = port_data.get("is_output", False)

                    # 检查节点是否允许添加该类型的端口
                    if (is_output and not node.can_add_output_ports) or (not is_output and not node.can_add_input_ports):
                        # 如果不允许添加，跳过该端口
                        continue

                    # 创建并添加新端口
                    if is_output:
                        port = OutputPort(
                            name=port_name,
                            port_type=port_type,
                            required=port_data.get("required", False),
                            show=port_data.get("show", False),
                            value=port_data.get("value"),
                            options=port_data.get("options"),
                            field_type=port_data.get("type"),
                            max_length=port_data.get("max_length"),
                            support_file_types=port_data.get("support_file_types", "").split(", ") if port_data.get("support_file_types") else None,
                            multiple=port_data.get("multiple"),
                            group=port_data.get("group"),
                            group_collpased=port_data.get("group_collpased", False),
                            has_tooltip=port_data.get("has_tooltip", False),
                            max=port_data.get("max"),
                            min=port_data.get("min"),
                            list=port_data.get("list", False),
                        )
                    else:
                        port = InputPort(
                            name=port_name,
                            port_type=port_type,
                            required=port_data.get("required", True),
                            show=port_data.get("show", False),
                            value=port_data.get("value"),
                            options=port_data.get("options"),
                            field_type=port_data.get("type"),
                            max_length=port_data.get("max_length"),
                            support_file_types=port_data.get("support_file_types", "").split(", ") if port_data.get("support_file_types") else None,
                            multiple=port_data.get("multiple"),
                            group=port_data.get("group"),
                            group_collpased=port_data.get("group_collpased", False),
                            has_tooltip=port_data.get("has_tooltip", False),
                            max=port_data.get("max"),
                            min=port_data.get("min"),
                            list=port_data.get("list", False),
                        )

                    # 添加新端口到节点
                    node.ports[port_name] = port

            workflow.add_node(node)

        # 创建边
        for edge_data in data.get("edges", []):
            # 获取目标节点和端口
            target_node_id = edge_data["target"]
            target_port_name = edge_data["targetHandle"]

            # 查找目标节点
            target_node = next((node for node in workflow.nodes if node.id == target_node_id), None)
            if target_node is None:
                raise ValueError(f"Target node not found: {target_node_id}")

            # 检查目标端口是否是OutputPort
            if target_node.has_port(target_port_name):
                target_port = target_node.ports[target_port_name]
                if isinstance(target_port, OutputPort):
                    raise ValueError(f"The target port {target_port_name} of node {target_node_id} is an output port. OutputPort cannot be a connection target.")

            edge = Edge(
                id=edge_data["id"],
                source=edge_data["source"],
                source_handle=edge_data["sourceHandle"],
                target=target_node_id,
                target_handle=target_port_name,
                animated=edge_data.get("animated", True),
                type=edge_data.get("type", "default"),
            )
            workflow.add_edge(edge)

        return workflow
