from dataclasses import dataclass
from typing import Any


@dataclass
class PyFuncVariant:
    pyfunc_classname: str
    extra_values: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.pyfunc_classname, str):
            raise TypeError("pyfunc_classname must be a string")
        if self.extra_values is not None and not isinstance(self.extra_values, dict):
            raise TypeError("extra_values must be a dictionary")
