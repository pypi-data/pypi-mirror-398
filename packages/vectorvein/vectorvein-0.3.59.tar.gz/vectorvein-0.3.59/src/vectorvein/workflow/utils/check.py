from typing import TypedDict, TYPE_CHECKING

from ..graph.port import InputPort

if TYPE_CHECKING:
    from ..graph.workflow import Workflow
    from ..graph.node import Node
    from ..graph.port import Port


class UIWarning(TypedDict, total=False):
    """UI警告类型。"""

    input_ports_shown_but_connected: list[dict]  # 显示的输入端口但被连接
    has_shown_input_ports: bool  # 是否存在显示的输入端口
    has_output_nodes: bool  # 是否存在输出节点


class WorkflowCheckResult(TypedDict):
    """工作流检查结果类型。"""

    no_cycle: bool  # 工作流是否不包含环
    no_isolated_nodes: bool  # 工作流是否不包含孤立节点
    useless_nodes: list["Node"]  # 工作流中无用的节点
    ui_warnings: UIWarning  # UI相关警告
    required_ports: list[tuple["Node", "Port"]]  # 未连接的必填端口
    override_ports: list[tuple["Node", "Port"]]  # 被覆盖的端口
    output_nodes_with_no_inputs: list["Node"]  # 输出端口没有输入端口连接的节点


def check_dag(workflow: "Workflow"):
    """检查流程图是否为有向无环图，并检测是否存在孤立节点。

    Returns:
        包含检查结果的字典
            - no_cycle (bool): 如果流程图是有向无环图返回 True，否则返回 False
            - no_isolated_nodes (bool): 如果不存在孤立节点返回 True，否则返回 False
    """
    result = {"no_cycle": True, "no_isolated_nodes": True}

    # 过滤掉触发器节点和辅助节点
    trigger_nodes = [node.id for node in workflow.nodes if hasattr(node, "category") and (node.category == "triggers" or node.category == "assistedNodes")]

    # 获取需要检查的节点和边
    regular_nodes = [node.id for node in workflow.nodes if node.id not in trigger_nodes]
    regular_edges = [edge for edge in workflow.edges if edge.source not in trigger_nodes and edge.target not in trigger_nodes]

    # ---------- 检查有向图是否有环 ----------
    # 构建邻接表
    adjacency = {node_id: [] for node_id in regular_nodes}
    for edge in regular_edges:
        if edge.source in adjacency:  # 确保节点在字典中
            adjacency[edge.source].append(edge.target)

    # 三种状态: 0 = 未访问, 1 = 正在访问, 2 = 已访问完成
    visited = dict.fromkeys(regular_nodes, 0)

    def dfs_cycle_detection(node_id):
        # 如果节点正在被访问，说明找到了环
        if visited[node_id] == 1:
            return False

        # 如果节点已经访问完成，无需再次访问
        if visited[node_id] == 2:
            return True

        # 标记为正在访问
        visited[node_id] = 1

        # 访问所有邻居
        for neighbor in adjacency[node_id]:
            if neighbor in visited and not dfs_cycle_detection(neighbor):
                return False

        # 标记为已访问完成
        visited[node_id] = 2
        return True

    # 对每个未访问的节点进行 DFS 检测环
    for node_id in regular_nodes:
        if visited[node_id] == 0:
            if not dfs_cycle_detection(node_id):
                result["no_cycle"] = False
                break

    # ---------- 检查是否存在孤立节点 ----------
    # 构建无向图邻接表
    undirected_adjacency = {node_id: [] for node_id in regular_nodes}
    for edge in regular_edges:
        if edge.source in undirected_adjacency and edge.target in undirected_adjacency:
            undirected_adjacency[edge.source].append(edge.target)
            undirected_adjacency[edge.target].append(edge.source)

    # 深度优先搜索来检测连通分量
    undirected_visited = set()

    def dfs_connected_components(node_id):
        undirected_visited.add(node_id)
        for neighbor in undirected_adjacency[node_id]:
            if neighbor not in undirected_visited:
                dfs_connected_components(neighbor)

    # 计算连通分量数量
    connected_components_count = 0
    for node_id in regular_nodes:
        if node_id not in undirected_visited:
            connected_components_count += 1
            dfs_connected_components(node_id)

    # 如果连通分量数量大于1，说明存在孤立节点
    if connected_components_count > 1 and len(regular_nodes) > 0:
        result["no_isolated_nodes"] = False

    return result


def check_ui(workflow: "Workflow") -> UIWarning:
    """
    检查工作流的 UI 情况。
    以下情况会警告：
    1. 某个输入端口的 show=True，但是又有连线连接到该端口（实际运行时会被覆盖）。
    2. 整个工作流没有任何输入端口是 show=True 的，说明没有让用户输入的地方。
    3. 整个工作流没有任何输出节点，这样工作流结果无法呈现。
    """
    warnings: UIWarning = {
        "input_ports_shown_but_connected": [],
        "has_shown_input_ports": False,
        "has_output_nodes": False,
    }

    # 检查是否有任何显示的输入端口
    has_shown_input_ports = False

    # 找出所有连接的目标端口
    connected_ports = {(edge.target, edge.target_handle) for edge in workflow.edges}

    # 遍历所有节点
    for node in workflow.nodes:
        # 检查是否为输出节点
        if hasattr(node, "category") and node.category == "outputs":
            warnings["has_output_nodes"] = True
            continue  # 输出节点不检查连接覆盖问题

        # 检查节点的输入端口
        ports = node.ports if hasattr(node, "ports") else {}
        for port_name in ports.keys():
            port = ports.get(port_name)
            # 确保是输入端口且设置为显示
            if hasattr(port, "show") and getattr(port, "show", False) and isinstance(port, InputPort):
                has_shown_input_ports = True

                # 检查显示的端口是否也被连接
                if (node.id, port_name) in connected_ports:
                    warnings["input_ports_shown_but_connected"].append({"node_id": node.id, "node_type": node.type, "port_name": port_name})

    # 如果没有任何显示的输入端口
    warnings["has_shown_input_ports"] = has_shown_input_ports

    return warnings


def check_useless_nodes(workflow: "Workflow") -> list["Node"]:
    """检查工作流中是否存在无用的节点。

    无用的节点定义：
    1. 节点非 output 类节点，并且节点的输出端口没有任何连线，说明该节点数据不会传给下一个节点或者显示出来。
    """
    useless_nodes = []
    source_nodes = {edge.source for edge in workflow.edges}

    for node in workflow.nodes:
        if hasattr(node, "category") and node.category == "outputs":
            continue

        if node.id not in source_nodes:
            useless_nodes.append(node)

    return useless_nodes


def check_required_ports(workflow: "Workflow") -> "list[tuple[Node, Port]]":
    """检查工作流中是否存在未连接的空的必填端口。"""
    required_but_not_connected = []

    # 找出所有连接的目标端口
    connected_ports = {(edge.target, edge.target_handle) for edge in workflow.edges}

    # 遍历所有节点及其端口
    for node in workflow.nodes:
        ports = node.ports if hasattr(node, "ports") else {}
        for port_name, port in ports.items():
            # 检查条件是否适用
            condition_applies = True
            if hasattr(port, "condition_python") and port.condition_python is not None:
                try:
                    # 检查是否为可调用函数
                    if callable(port.condition_python):
                        # 如果是函数，传入ports作为参数
                        condition_result = port.condition_python(ports)
                    else:
                        raise ValueError(f"condition_python 必须是可调用函数，当前类型为 {type(port.condition_python)}")

                    if not condition_result:
                        condition_applies = False
                except Exception:
                    # 如果条件评估出错，假设条件不适用
                    condition_applies = False

            # 检查端口是否必填
            is_required = getattr(port, "required", False)

            # 检查值是否为空
            value_is_empty = getattr(port, "value", "") == ""

            # 检查是否没有连线连接到这个端口
            not_connected = (node.id, port_name) not in connected_ports

            # 如果满足所有条件，将其添加到结果列表
            if condition_applies and is_required and value_is_empty and not_connected:
                required_but_not_connected.append((node, port))

    return required_but_not_connected


def check_override_ports(workflow: "Workflow") -> list[tuple["Node", "Port"]]:
    """检查工作流中是否存在覆盖的端口。

    一个端口如果其 value 值不是布尔值，且不为空（空字符串、空列表、空字典），
    然后还被一个连线作为输出端口连接了，那么这个端口的 value 值会被覆盖。
    """
    override_ports = []

    # 找出所有作为输出端口的连接
    target_ports = {(edge.target, edge.target_handle) for edge in workflow.edges}

    for node in workflow.nodes:
        for port_name, port in node.ports.items():
            # 检查端口是否被作为输出端口连接
            if (node.id, port_name) in target_ports:
                value = port.value

                # 检查 value 是否为布尔值
                if isinstance(value, bool):
                    continue

                # 检查 value 是否为空
                is_empty = value == "" or value == [] or value == {} or value is None

                if not is_empty:
                    override_ports.append((node, port))

    return override_ports


def check_output_nodes_with_no_inputs(workflow: "Workflow") -> list["Node"]:
    """检查工作流中是否存在输出端口没有输入端口连接的节点。"""
    output_nodes_with_no_inputs = []

    # 找出所有连接的目标节点和端口
    connected_targets = {(edge.target, edge.target_handle) for edge in workflow.edges}

    # 遍历所有节点
    for node in workflow.nodes:
        # 只检查输出类节点
        if hasattr(node, "category") and node.category == "outputs":
            # 检查该节点是否有任何连接到其输入端口的边
            has_input_connection = False

            for port_name, port in node.ports.items():
                if isinstance(port, InputPort):
                    if (node.id, port_name) in connected_targets:
                        has_input_connection = True
                        break

            # 如果该输出节点没有任何输入连接，则添加到结果列表
            if not has_input_connection:
                output_nodes_with_no_inputs.append(node)

    return output_nodes_with_no_inputs
