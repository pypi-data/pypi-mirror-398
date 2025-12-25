from ..graph.node import Node
from ..graph.port import PortType, InputPort, OutputPort


class BilibiliCrawler(Node):
    def __init__(self, id: str | None = None):
        super().__init__(
            node_type="BilibiliCrawler",
            category="webCrawlers",
            task_name="web_crawlers.bilibili_crawler",
            node_id=id,
            ports={
                "url_or_bvid": InputPort(
                    name="url_or_bvid",
                    port_type=PortType.INPUT,
                    value="",
                    show=True,
                ),
                "download_video": InputPort(
                    name="download_video",
                    port_type=PortType.CHECKBOX,
                    value=False,
                    required=False,
                ),
                "output_type": InputPort(
                    name="output_type",
                    port_type=PortType.SELECT,
                    value="str",
                    options=[{"value": "str", "label": "str"}, {"value": "list", "label": "list"}],
                    required=False,
                ),
                "output_title": OutputPort(name="output_title"),
                "output_subtitle": OutputPort(name="output_subtitle"),
                "output_video": OutputPort(
                    name="output_video",
                    condition="return fieldsData.download_video.value",
                    condition_python=lambda ports: ports["download_video"].value,
                ),
            },
        )


class DouyinCrawler(Node):
    def __init__(self, id: str | None = None):
        super().__init__(
            node_type="DouyinCrawler",
            category="webCrawlers",
            task_name="web_crawlers.douyin_crawler",
            node_id=id,
            ports={
                "url": InputPort(
                    name="url",
                    port_type=PortType.INPUT,
                    value="",
                    show=True,
                ),
                "output_title": OutputPort(name="output_title"),
                "output_video": OutputPort(name="output_video"),
                "output_audio": OutputPort(name="output_audio"),
            },
        )


class TextCrawler(Node):
    def __init__(self, id: str | None = None):
        super().__init__(
            node_type="TextCrawler",
            category="webCrawlers",
            task_name="web_crawlers.text_crawler",
            node_id=id,
            ports={
                "url": InputPort(
                    name="url",
                    port_type=PortType.INPUT,
                    value="",
                    show=True,
                ),
                "output_type": InputPort(
                    name="output_type",
                    port_type=PortType.SELECT,
                    value="text",
                    options=[{"value": "text", "label": "Text"}, {"value": "html", "label": "HTML"}],
                    required=False,
                ),
                "use_oversea_crawler": InputPort(
                    name="use_oversea_crawler",
                    port_type=PortType.CHECKBOX,
                    value=False,
                    required=False,
                ),
                "advanced_mode": InputPort(
                    name="advanced_mode",
                    port_type=PortType.CHECKBOX,
                    value=False,
                    required=False,
                    has_tooltip=True,
                ),
                "remove_image": InputPort(
                    name="remove_image",
                    port_type=PortType.CHECKBOX,
                    value=False,
                    required=False,
                    has_tooltip=True,
                ),
                "output_title": OutputPort(name="output_title"),
                "output_text": OutputPort(name="output_text"),
            },
        )


class YoutubeCrawler(Node):
    def __init__(self, id: str | None = None):
        super().__init__(
            node_type="YoutubeCrawler",
            category="webCrawlers",
            task_name="web_crawlers.youtube_crawler",
            node_id=id,
            ports={
                "url_or_video_id": InputPort(
                    name="url_or_video_id",
                    port_type=PortType.INPUT,
                    value="",
                    show=True,
                ),
                "get_comments": InputPort(
                    name="get_comments",
                    port_type=PortType.CHECKBOX,
                    value=False,
                ),
                "comments_type": InputPort(
                    name="comments_type",
                    port_type=PortType.RADIO,
                    value="text_only",
                    options=[{"value": "text_only", "label": "text_only"}, {"value": "detailed", "label": "detailed"}],
                    condition="return fieldsData.get_comments.value",
                    condition_python=lambda ports: ports["get_comments"].value,
                ),
                "subtitle_format": InputPort(
                    name="subtitle_format",
                    port_type=PortType.SELECT,
                    value="text",
                    options=[{"value": "text", "label": "text"}, {"value": "srt", "label": "srt"}],
                    required=False,
                ),
                "output_type": InputPort(
                    name="output_type",
                    port_type=PortType.SELECT,
                    value="str",
                    options=[{"value": "str", "label": "str"}, {"value": "list", "label": "list"}],
                    required=False,
                ),
                "output_title": OutputPort(name="output_title"),
                "output_subtitle": OutputPort(name="output_subtitle"),
                "output_comments": OutputPort(
                    name="output_comments",
                    condition="return fieldsData.get_comments.value",
                    condition_python=lambda ports: ports["get_comments"].value,
                ),
            },
        )
