from typing import Any


class Edge:
    def __init__(
        self,
        id: str,
        source: str,
        source_handle: str,
        target: str,
        target_handle: str,
        animated: bool = True,
        type: str = "default",
    ) -> None:
        self.id: str = id
        self.source: str = source
        self.source_handle: str = source_handle
        self.target: str = target
        self.target_handle: str = target_handle
        self.animated: bool = animated
        self.type: str = type
        self.style: dict[str, str | int] = {"stroke": "#28c5e5", "strokeWidth": 3}

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "source": self.source,
            "sourceHandle": self.source_handle,
            "target": self.target,
            "targetHandle": self.target_handle,
            "animated": self.animated,
            "type": self.type,
            "style": self.style,
            "data": {},
            "label": "",
        }
