from ..graph.node import Node
from ..graph.port import PortType, InputPort, OutputPort


class CogVideoX(Node):
    def __init__(self, id: str | None = None):
        super().__init__(
            node_type="CogVideoX",
            category="videoGeneration",
            task_name="video_generation.cog_video_x",
            node_id=id,
            ports={
                "prompt": InputPort(
                    name="prompt",
                    port_type=PortType.TEXTAREA,
                    value="",
                    has_tooltip=True,
                ),
                "image": InputPort(
                    name="image",
                    port_type=PortType.FILE,
                    value=[],
                    required=False,
                    has_tooltip=True,
                    support_file_types=[".jpg", ".jpeg", ".png"],
                ),
                "auto_crop": InputPort(
                    name="auto_crop",
                    port_type=PortType.CHECKBOX,
                    value=True,
                    required=False,
                    has_tooltip=True,
                ),
                "model": InputPort(
                    name="model",
                    port_type=PortType.SELECT,
                    value="cogvideox",
                    options=[{"value": "cogvideox", "label": "cogvideox"}],
                    required=False,
                ),
                "output_type": InputPort(
                    name="output_type",
                    port_type=PortType.SELECT,
                    value="only_link",
                    options=[{"value": "only_link", "label": "only_link"}, {"value": "html", "label": "html"}],
                    required=False,
                ),
                "output": OutputPort(),
            },
        )


class KlingVideo(Node):
    def __init__(self, id: str | None = None):
        super().__init__(
            node_type="KlingVideo",
            category="videoGeneration",
            task_name="video_generation.kling_video",
            node_id=id,
            ports={
                "prompt": InputPort(
                    name="prompt",
                    port_type=PortType.TEXTAREA,
                    value="",
                    has_tooltip=True,
                ),
                "image": InputPort(
                    name="image",
                    port_type=PortType.FILE,
                    value=[],
                    required=False,
                    support_file_types=[".jpg", ".jpeg", ".png"],
                ),
                "duration": InputPort(
                    name="duration",
                    port_type=PortType.SELECT,
                    value=5,
                    options=[{"value": 5, "label": "5"}, {"value": 10, "label": "10"}],
                    required=False,
                ),
                "aspect_ratio": InputPort(
                    name="aspect_ratio",
                    port_type=PortType.SELECT,
                    value="16:9",
                    options=[{"value": "16:9", "label": "16:9"}, {"value": "9:16", "label": "9:16"}, {"value": "1:1", "label": "1:1"}],
                    required=False,
                ),
                "model": InputPort(
                    name="model",
                    port_type=PortType.SELECT,
                    value="v2_1_master",
                    options=[{"value": "v2_1_master", "label": "v2_1_master"}, {"value": "v1_pro", "label": "v1_pro"}, {"value": "v1_standard", "label": "v1_standard"}],
                ),
                "output_type": InputPort(
                    name="output_type",
                    port_type=PortType.SELECT,
                    value="only_link",
                    options=[{"value": "only_link", "label": "only_link"}, {"value": "html", "label": "html"}],
                    required=False,
                ),
                "output": OutputPort(),
            },
        )


class OmniHuman(Node):
    def __init__(self, id: str | None = None):
        super().__init__(
            node_type="OmniHuman",
            category="videoGeneration",
            task_name="video_generation.omni_human",
            node_id=id,
            ports={
                "image": InputPort(
                    name="image",
                    port_type=PortType.FILE,
                    value=[],
                    show=True,
                    has_tooltip=True,
                    support_file_types=[".jpg", ".jpeg", ".png"],
                ),
                "audio": InputPort(
                    name="audio",
                    port_type=PortType.FILE,
                    value=[],
                    show=True,
                    has_tooltip=True,
                    support_file_types=[".mp3", ".wav"],
                ),
                "output_type": InputPort(
                    name="output_type",
                    port_type=PortType.SELECT,
                    value="only_link",
                    options=[{"value": "only_link", "label": "only_link"}, {"value": "html", "label": "html"}],
                    required=False,
                ),
                "output": OutputPort(),
            },
        )
