from typing import Any, TYPE_CHECKING


if TYPE_CHECKING:
    from vectorvein.workflow.graph.node import Node
    from vectorvein.workflow.graph.edge import Edge


def layout(nodes: list["Node"], edges: list["Edge"], options: dict[str, Any] | None = None):
    """对工作流中的节点进行自动布局，计算并更新每个节点的位置。

    此方法实现了一个简单的分层布局算法，将节点按照有向图的拓扑结构进行排列。

    Args:
        options: 布局选项，包括:
            - direction: 布局方向 ('TB', 'BT', 'LR', 'RL')，默认 'TB'
            - node_spacing: 同一层级节点间的间距，默认 150
            - layer_spacing: 不同层级间的间距，默认 100
            - margin_x: 图形左右边距，默认 20
            - margin_y: 图形上下边距，默认 20

    Returns:
        布局后的工作流对象
    """
    # 设置默认选项
    default_options = {
        "direction": "LR",  # 从上到下的布局
        "node_spacing": 400,  # 同一层级节点间的间距
        "layer_spacing": 500,  # 不同层级间的间距
        "margin_x": 20,  # 图形左右边距
        "margin_y": 20,  # 图形上下边距
    }

    # 合并用户提供的选项
    if options:
        default_options.update(options)

    # 构建邻接表
    adjacency = {node.id: [] for node in nodes}
    in_degree = {node.id: 0 for node in nodes}

    for edge in edges:
        if edge.source in adjacency:
            adjacency[edge.source].append(edge.target)
            in_degree[edge.target] = in_degree.get(edge.target, 0) + 1

    # 找出所有入度为0的节点（根节点）
    roots = [node_id for node_id, degree in in_degree.items() if degree == 0]

    # 如果没有根节点，选择第一个节点作为起点
    if not roots and nodes:
        roots = [nodes[0].id]

    # 按层级排列节点
    layers = []
    visited = set()

    current_layer = roots
    while current_layer:
        layers.append(current_layer)
        next_layer = []
        for node_id in current_layer:
            visited.add(node_id)
            for neighbor in adjacency.get(node_id, []):
                if neighbor not in visited and all(parent in visited for parent in [e.source for e in edges if e.target == neighbor]):
                    next_layer.append(neighbor)
        current_layer = next_layer

    # 还有未访问的节点（可能是孤立节点或环的一部分）
    remaining = [node.id for node in nodes if node.id not in visited]
    if remaining:
        layers.append(remaining)

    # 根据层级信息设置节点位置
    layer_spacing = default_options["layer_spacing"]
    node_spacing = default_options["node_spacing"]
    margin_x = default_options["margin_x"]
    margin_y = default_options["margin_y"]

    # 布局方向
    is_vertical = default_options["direction"] in ["TB", "BT"]
    is_reversed = default_options["direction"] in ["BT", "RL"]

    for layer_idx, layer in enumerate(layers):
        for node_idx, node_id in enumerate(layer):
            # 根据布局方向计算位置
            if is_vertical:
                # 垂直布局 (TB 或 BT)
                x = node_idx * node_spacing + margin_x
                y = layer_idx * layer_spacing + margin_y
                if is_reversed:  # BT 布局需要反转 y 坐标
                    y = (len(layers) - 1 - layer_idx) * layer_spacing + margin_y
            else:
                # 水平布局 (LR 或 RL)
                x = layer_idx * layer_spacing + margin_x
                y = node_idx * node_spacing + margin_y
                if is_reversed:  # RL 布局需要反转 x 坐标
                    x = (len(layers) - 1 - layer_idx) * layer_spacing + margin_x

            # 找到节点对象并设置位置
            for node in nodes:
                if node.id == node_id:
                    # 确保节点有 position 属性
                    if not hasattr(node, "position"):
                        node.position = {"x": x, "y": y}
                    else:
                        # 如果已经有 position 属性，更新它
                        if isinstance(node.position, dict):
                            node.position.update({"x": x, "y": y})
                        else:
                            node.position = {"x": x, "y": y}
                    break
