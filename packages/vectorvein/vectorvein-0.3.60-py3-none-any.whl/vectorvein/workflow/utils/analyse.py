import json
from typing import TypedDict, Any, overload


class PortRecord(TypedDict):
    """
    端口记录
    """

    name: str
    type: str
    show: bool
    value: Any
    connected: bool


class NodeRecord(TypedDict):
    """
    节点记录
    """

    id: str
    name: str
    type: str
    category: str
    ports: list[PortRecord]


class AnalyseResult(TypedDict):
    """
    分析结果
    """

    nodes: list[NodeRecord]


def analyse_workflow_record(json_str: str, connected_only: bool = False, reserver_programming_function_ports: bool = False) -> AnalyseResult:
    """
    分析工作流JSON字符串，提取节点和端口信息

    Args:
        json_str: 工作流JSON字符串

    Returns:
        分析结果
    """
    # 解析JSON
    workflow_data = json.loads(json_str)

    # 收集所有连接的端口
    connected_ports = set()
    for edge in workflow_data["edges"]:
        source_id = edge["source"]
        target_id = edge["target"]
        source_handle = edge["sourceHandle"]
        target_handle = edge["targetHandle"]
        connected_ports.add((source_id, source_handle))
        connected_ports.add((target_id, target_handle))

    # 分析节点
    nodes_records = []

    for node in workflow_data["nodes"]:
        node_id = node["id"]
        node_type = node["type"]
        category = node["category"]

        # 跳过辅助节点
        if category == "assistedNodes":
            continue

        # 获取任务名称
        task_name = node["data"]["task_name"].split(".")[-1] if "task_name" in node["data"] else ""

        # 收集端口信息
        ports_records = []

        if "template" in node["data"]:
            for port in node["data"]["template"].values():
                if "name" not in port:
                    continue

                port_is_connected = (node_id, port["name"]) in connected_ports

                if node_type != "ProgrammingFunction" or not reserver_programming_function_ports:
                    if connected_only and not port_is_connected:
                        continue

                port_record: PortRecord = {
                    "name": port["name"],
                    "type": port.get("field_type", port.get("type", "")),
                    "show": port.get("show", False),
                    "value": port.get("value", None),
                    "connected": port_is_connected,
                }

                ports_records.append(port_record)

        # 创建节点记录
        node_record: NodeRecord = {
            "id": node_id,
            "name": task_name,
            "type": node_type,
            "category": category,
            "ports": ports_records,
        }

        nodes_records.append(node_record)

    # 返回分析结果
    result: AnalyseResult = {"nodes": nodes_records}

    return result


@overload
def prettify_value(
    value: str,
    max_length: int,
    preserve_escapes: bool = True,
    only_control_chars: bool = True,
) -> str: ...


@overload
def prettify_value(
    value: list,
    max_length: int,
    preserve_escapes: bool = True,
    only_control_chars: bool = True,
) -> list: ...


@overload
def prettify_value(
    value: dict,
    max_length: int,
    preserve_escapes: bool = True,
    only_control_chars: bool = True,
) -> dict: ...


@overload
def prettify_value(
    value: Any,
    max_length: int,
    preserve_escapes: bool = True,
    only_control_chars: bool = True,
) -> Any: ...


def prettify_value(
    value: Any,
    max_length: int,
    preserve_escapes: bool = False,
    only_control_chars: bool = True,
) -> Any:
    """
    截断字符串或列表值，使其不超过指定的最大长度

    Args:
        value: 要截断的值，可以是字符串或列表
        max_length: 最大长度限制
        preserve_escapes: 是否保留转义字符
        only_control_chars: 如果为True，仅转义控制字符；如果为False，转义所有非ASCII字符

    Returns:
        截断后的值
    """
    if value is None:
        return None

    # 处理字符串
    if isinstance(value, str):
        # 如果需要保留转义字符
        display_value = value
        if preserve_escapes:
            if only_control_chars:
                # 只转义控制字符，保留其他字符原样
                control_chars = {
                    "\n": "\\n",
                    "\r": "\\r",
                    "\t": "\\t",
                    "\b": "\\b",
                    "\f": "\\f",
                    "\\": "\\\\",
                    "\v": "\\v",  # 垂直制表符
                    "\a": "\\a",  # 响铃
                    "\0": "\\0",  # 空字符
                }
                for char, escape in control_chars.items():
                    display_value = display_value.replace(char, escape)
            else:
                # 转义所有特殊字符（包括非ASCII字符如中文）
                display_value = value.encode("unicode_escape").decode("utf-8")

        if len(display_value) <= max_length:
            return display_value

        # 如果超过长度，截断中间部分，保留开头和结尾
        half_length = max_length // 2 - 2  # 减2是为了留出"..."的空间
        half_length = max(half_length, 5)  # 确保至少有5个字符
        return f"{display_value[:half_length]}...{display_value[-half_length:]}"

    # 处理列表 - 保留所有元素但截断每个元素的值
    elif isinstance(value, list):
        if not value:
            return []

        # 计算每个元素最大长度 - 确保每个元素都有展示空间
        item_max_length = max(max_length // len(value), 10)  # 确保至少有10个字符

        return [prettify_value(item, item_max_length, preserve_escapes, only_control_chars) for item in value]

    # 处理字典 - 保留所有键值对但截断值
    elif isinstance(value, dict):
        result = {}
        item_max_length = max_length // len(value) if value else max_length
        for k, v in value.items():
            # 截断每个值
            result[k] = prettify_value(v, item_max_length, preserve_escapes, only_control_chars)
        return result

    # 其他类型直接返回
    return value


def format_analysis_result(analysis_result: AnalyseResult, max_value_length: int = 100) -> str:
    """
    格式化工作流分析结果，生成一个简洁的字符串表示

    Args:
        analysis_result: 工作流分析结果字典
        max_value_length: 值的最大长度，超过此长度将被截断

    Returns:
        格式化后的字符串
    """
    if not analysis_result:
        return "空分析结果"

    formatted_parts = []

    # 添加节点信息
    if "nodes" in analysis_result:
        nodes = analysis_result["nodes"]
        formatted_parts.append(f"节点数量: {len(nodes)}")

        for idx, node in enumerate(nodes):
            truncated_node = {
                "id": node.get("id", "未知ID"),
                "name": node.get("name", "未知名称"),
                "type": node.get("type", "未知类型"),
                "category": node.get("category", "未知类别"),
            }

            # 添加端口信息摘要
            if "ports" in node:
                ports = node.get("ports", [])
                port_summary = []

                for port in ports:
                    port_info = {
                        "name": port.get("name", "未知端口"),
                        "type": port.get("type", "未知类型"),
                        "connected": port.get("connected", False),
                    }

                    # 如果有值且不是隐藏的端口，添加值的摘要
                    if "value" in port and port.get("show", True):
                        port_info["value"] = prettify_value(port.get("value"), max_value_length)

                    port_summary.append(port_info)

                truncated_node["ports_summary"] = f"{len(ports)}个端口，其中{sum(1 for p in ports if p.get('connected'))}个已连接"

            node_str = f"节点{idx + 1}: {json.dumps(truncated_node, ensure_ascii=False, indent=2)}"
            formatted_parts.append(node_str)

    # 添加其他可能的顶级信息
    for key, value in analysis_result.items():
        if key != "nodes":
            if isinstance(value, dict | list):
                summary = f"{key}: 包含{len(value)}个项目"
            else:
                summary = f"{key}: {prettify_value(value, max_value_length)}"
            formatted_parts.append(summary)

    return "\n".join(formatted_parts)


def format_workflow_analysis_for_llm(analysis_result: AnalyseResult, max_value_length: int = 100) -> str:
    """
    将工作流分析结果格式化为适合LLM分析的字符串，使用更紧凑的Python风格表示

    Args:
        analysis_result: 工作流分析结果字典或其JSON字符串表示
        max_value_length: 值的最大长度，超过此长度将被截断

    Returns:
        格式化后的字符串
    """
    if not isinstance(analysis_result, dict):
        return f"无效的分析结果类型: {type(analysis_result)}"

    # 构建LLM友好的格式
    llm_friendly_format = []

    # 处理节点信息
    if "nodes" in analysis_result:
        nodes = analysis_result["nodes"]
        llm_friendly_format.append("\n## 节点信息")

        for node in nodes:
            node_id = node.get("id", "未知ID")
            node_name = node.get("name", "未知名称")
            node_type = node.get("type", "未知类型")
            node_category = node.get("category", "未知类别")

            # 截断节点ID，仅保留前3位和后3位
            short_id = f"{node_id[:3]}...{node_id[-3:]}" if len(node_id) > 6 else node_id

            node_info = [
                f"- {node_name} <ID: {short_id}>",
                f"  - 类型: {node_type}",
                f"  - 类别: {node_category}",
                "  - 端口",
            ]

            # 添加端口信息
            if "ports" in node:
                ports = node.get("ports", [])

                # 遍历所有端口
                for port in ports:
                    port_name = port.get("name", "未知端口")
                    port_type = port.get("type", "未知类型")

                    port_line = f"    - `{port_name}` ({port_type})"
                    node_info.append(port_line)

                    # 添加值的紧凑描述
                    if "value" in port:
                        value = port.get("value")
                        if isinstance(value, list):
                            # 列表值，使用Python风格显示
                            truncated_list = []
                            item_max_length = max(max_value_length // len(value) if value else max_value_length, 10)
                            node_info.append(f"      - value(list): {json.dumps(prettify_value(value, item_max_length), ensure_ascii=False)}")
                        elif isinstance(value, dict):
                            # 字典值，使用Python风格显示
                            dict_items = []
                            key_max_length = max(max_value_length // len(value) if value else max_value_length, 10)
                            node_info.append(f"      - value(dict): {json.dumps(prettify_value(value, key_max_length), ensure_ascii=False)}")
                        elif isinstance(value, str):
                            # 字符串值，带引号
                            truncated = prettify_value(value, max_value_length)
                            node_info.append(f'      - value(str): "{truncated}"')
                        else:
                            # 其他类型的值
                            type_name = type(value).__name__
                            node_info.append(f"      - value({type_name}): {value}")
            else:
                # 如果没有端口，移除端口标题
                node_info.pop()

            llm_friendly_format.append("\n".join(node_info))

    # 添加其他可能的顶级信息
    other_info = []
    for key, value in analysis_result.items():
        if key != "nodes":
            if isinstance(value, dict):
                # 字典，Python风格显示
                dict_items = []
                key_max_length = max(max_value_length // len(value) if value else max_value_length, 10)

                for k, v in value.items():
                    if isinstance(v, str):
                        truncated_v = f'"{prettify_value(v, key_max_length)}"'
                    else:
                        truncated_v = str(prettify_value(v, key_max_length))
                    dict_items.append(f'"{k}": {truncated_v}')

                dict_repr = "{" + ", ".join(dict_items) + "}"
                other_info.append(f"- **{key}**(dict): {dict_repr}")
            elif isinstance(value, list):
                # 列表，Python风格显示
                truncated_list = []
                item_max_length = max(max_value_length // len(value) if value else max_value_length, 10)

                for item in value:
                    if isinstance(item, str):
                        truncated_item = f'"{prettify_value(item, item_max_length)}"'
                    else:
                        truncated_item = str(prettify_value(item, item_max_length))
                    truncated_list.append(truncated_item)

                list_repr = "[" + ", ".join(truncated_list) + "]"
                other_info.append(f"- **{key}**(list): {list_repr}")
            else:
                # 基本类型
                type_name = type(value).__name__
                if isinstance(value, str):
                    truncated = prettify_value(value, max_value_length)
                    other_info.append(f'- **{key}**({type_name}): "{truncated}"')
                else:
                    other_info.append(f"- **{key}**({type_name}): {prettify_value(value, max_value_length)}")

    if other_info:
        llm_friendly_format.append("\n### 其他信息")
        llm_friendly_format.append("\n".join(other_info))

    return "\n".join(llm_friendly_format)
