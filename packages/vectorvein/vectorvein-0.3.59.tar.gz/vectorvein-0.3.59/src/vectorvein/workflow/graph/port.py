from enum import Enum
from typing import Any
from collections.abc import Callable


class PortType(Enum):
    TEXT = "text"
    NUMBER = "number"
    CHECKBOX = "checkbox"
    SELECT = "select"
    RADIO = "radio"
    TEXTAREA = "textarea"
    INPUT = "input"
    FILE = "file"
    LIST = "list"
    COLOR = "color"
    TEMPERATURE = "temperature"


class Port:
    def __init__(
        self,
        name: str,
        port_type: "PortType | str",
        required: bool = True,
        show: bool = False,
        value: Any = None,
        options: list[Any] | None = None,
        field_type: str | None = None,
        is_output: bool = False,
        condition: str | None = None,
        condition_python: Callable[[dict[str, "Port"]], bool] | None = None,
        max_length: int | None = None,
        support_file_types: list[str] | None = None,
        multiple: bool | None = None,
        group: str | None = None,
        group_collpased: bool = False,
        has_tooltip: bool = False,
        max: int | float | None = None,
        min: int | float | None = None,
        max_count: int | None = None,
        list: bool = False,
    ) -> None:
        self.name = name
        self.port_type = port_type
        self.required = required
        self.show = show
        self._value = value
        self.options = options
        self.field_type = field_type
        self.is_output = is_output
        self.condition = condition
        self.condition_python = condition_python
        self.max_length = max_length
        self.support_file_types = support_file_types
        self.multiple = multiple
        self.group = group
        self.group_collpased = group_collpased
        self.has_tooltip = has_tooltip
        self.max = max
        self.min = min
        self.max_count = max_count
        self.list = list

    @property
    def python_type(self):
        if self.port_type == PortType.CHECKBOX or self.port_type == "checkbox":
            return "bool"
        elif self.port_type == PortType.NUMBER or self.port_type == "number":
            return "float"
        elif self.port_type == PortType.TEMPERATURE or self.port_type == "temperature":
            return "float"
        else:
            return "str"

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "display_name": self.name,
            "field_type": self.port_type.value if isinstance(self.port_type, PortType) else self.port_type,
            "required": False if not isinstance(self.value, bool) and self.value else self.required,
            "show": self.show,
            "value": self._value,
            "options": self.options,
            "type": self.field_type or self.python_type,
            "is_output": self.is_output,
            # "condition": f"(fieldsData) => {{ {self.condition} }}" if self.condition else "",
            "max_length": self.max_length,
            "support_file_types": ", ".join(self.support_file_types) if self.support_file_types else None,
            "multiple": self.multiple,
            "group": self.group,
            "group_collpased": self.group_collpased,
            "has_tooltip": self.has_tooltip,
            "max": self.max,
            "min": self.min,
            "list": self.list,
        }

    @property
    def value(self) -> Any:
        return self._value

    @value.setter
    def value(self, value: Any) -> None:
        if self.options:
            if value not in (x["value"] for x in self.options):
                raise ValueError(f"Value `{value}` is not in Port `{self.name}` options {self.options}")
        self._value = value

    def __str__(self) -> str:
        return f"Port(name={self.name}, port_type={self.port_type})"

    def __repr__(self) -> str:
        return self.__str__()


class InputPort(Port):
    def __init__(
        self,
        name: str,
        port_type: PortType | str,
        required: bool = True,
        show: bool = False,
        value: Any = None,
        options: list[Any] | None = None,
        field_type: str | None = None,
        condition: str | None = None,
        condition_python: Callable[[dict[str, "Port"]], bool] | None = None,
        max_length: int | None = None,
        support_file_types: list[str] | None = None,
        multiple: bool | None = None,
        group: str | None = None,
        group_collpased: bool = False,
        has_tooltip: bool = False,
        max: int | float | None = None,
        min: int | float | None = None,
        max_count: int | None = None,
        list: bool = False,
    ) -> None:
        super().__init__(
            name=name,
            port_type=port_type,
            required=required,
            show=show,
            value=value,
            options=options,
            field_type=field_type,
            is_output=False,
            condition=condition,
            condition_python=condition_python,
            max_length=max_length,
            support_file_types=support_file_types,
            multiple=multiple,
            group=group,
            group_collpased=group_collpased,
            has_tooltip=has_tooltip,
            max=max,
            min=min,
            max_count=max_count,
            list=list,
        )


class OutputPort(Port):
    def __init__(
        self,
        name: str = "output",
        port_type: PortType | str = PortType.TEXT,
        required: bool = False,
        show: bool = False,
        value: Any = None,
        options: list[Any] | None = None,
        field_type: str | None = None,
        condition: str | None = None,
        condition_python: Callable[[dict[str, "Port"]], bool] | None = None,
        max_length: int | None = None,
        support_file_types: list[str] | None = None,
        multiple: bool | None = None,
        group: str | None = None,
        group_collpased: bool = False,
        has_tooltip: bool = False,
        max: int | float | None = None,
        min: int | float | None = None,
        max_count: int | None = None,
        list: bool = False,
    ) -> None:
        super().__init__(
            name=name,
            port_type=port_type,
            required=required,
            show=show,
            value=value,
            options=options,
            field_type=field_type,
            is_output=True,
            condition=condition,
            condition_python=condition_python,
            max_length=max_length,
            support_file_types=support_file_types,
            multiple=multiple,
            group=group,
            group_collpased=group_collpased,
            has_tooltip=has_tooltip,
            max=max,
            min=min,
            max_count=max_count,
            list=list,
        )
