from dataclasses import dataclass
from abc import ABC
import re


def validate_dtype(dtype: str) -> bool:
    pattern = r"^(Array\[.+\]|NDContainer\[.+\])$"
    if not re.match(pattern, dtype):
        raise ValueError("dtype must be format 'Array[...]' or 'NDContainer[...]'")
    return True


@dataclass(kw_only=True)
class ModelIO(ABC):
    name: str
    content_type: str
    dtype: str
    tags: list[str] | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.name, str):
            raise TypeError("name must be a string")
        if not isinstance(self.content_type, str):
            raise TypeError("content_type must be a string")
        if not isinstance(self.dtype, str):
            raise TypeError("dtype must be a string")
        if self.tags is not None and not isinstance(self.tags, list):
            raise TypeError("tags must be a list of strings")
        if self.tags is not None and not all(isinstance(tag, str) for tag in self.tags):
            raise TypeError("all tags must be strings")


@dataclass(kw_only=True)
class JSON(ModelIO):
    content_type: str = "JSON"

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.content_type != "JSON":
            raise ValueError("content_type must be 'JSON'")


@dataclass(kw_only=True)
class NDJSON(ModelIO):
    shape: list[str | int]
    content_type: str = "NDJSON"

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.content_type != "NDJSON":
            raise ValueError("content_type must be 'NDJSON'")
        validate_dtype(self.dtype)
        if not isinstance(self.shape, list):
            raise TypeError("shape must be a list")
        if not all(isinstance(x, (str, int)) for x in self.shape):
            raise TypeError("shape elements must be strings or integers")


@dataclass
class Var:
    name: str
    description: str
    tags: list[str] | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.name, str):
            raise TypeError("name must be a string")
        if not isinstance(self.description, str):
            raise TypeError("description must be a string")
        if self.tags is not None and not isinstance(self.tags, list):
            raise TypeError("tags must be a list of strings")
        if self.tags is not None and not all(isinstance(tag, str) for tag in self.tags):
            raise TypeError("all tags must be strings")


@dataclass
class Manifest:
    variant: str
    producer_name: str
    producer_version: str
    producer_tags: list[str]
    inputs: list[NDJSON | JSON]
    outputs: list[NDJSON | JSON]
    dynamic_attributes: list[Var]
    env_vars: list[Var]
    name: str | None = None
    version: str | None = None
    description: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.variant, str):
            raise TypeError("variant must be a string")
        if not isinstance(self.producer_name, str):
            raise TypeError("producer_name must be a string")
        if not isinstance(self.producer_version, str):
            raise TypeError("producer_version must be a string")
        if not isinstance(self.producer_tags, list):
            raise TypeError("producer_tags must be a list")
        if not all(isinstance(tag, str) for tag in self.producer_tags):
            raise TypeError("all producer_tags must be strings")
        if not isinstance(self.inputs, list):
            raise TypeError("inputs must be a list")
        if not all(isinstance(x, (NDJSON, JSON)) for x in self.inputs):
            raise TypeError("inputs must be NDJSON or JSON instances")
        if not isinstance(self.outputs, list):
            raise TypeError("outputs must be a list")
        if not all(isinstance(x, (NDJSON, JSON)) for x in self.outputs):
            raise TypeError("outputs must be NDJSON or JSON instances")
        if not isinstance(self.dynamic_attributes, list):
            raise TypeError("dynamic_attributes must be a list")
        if not all(isinstance(x, Var) for x in self.dynamic_attributes):
            raise TypeError("dynamic_attributes must be Var instances")
        if not isinstance(self.env_vars, list):
            raise TypeError("env_vars must be a list")
        if not all(isinstance(x, Var) for x in self.env_vars):
            raise TypeError("env_vars must be Var instances")
        if self.name is not None and not isinstance(self.name, str):
            raise TypeError("name must be a string")
        if self.version is not None and not isinstance(self.version, str):
            raise TypeError("version must be a string")
        if self.description is not None and not isinstance(self.description, str):
            raise TypeError("description must be a string")

    @classmethod
    def from_dict(cls, data: dict) -> "Manifest":

        data = data.copy()

        inputs = [
            NDJSON(**inp) if inp["content_type"] == "NDJSON" else JSON(**inp)
            for inp in data.pop("inputs")
        ]
        outputs = [
            NDJSON(**out) if out["content_type"] == "NDJSON" else JSON(**out)
            for out in data.pop("outputs")
        ]

        dynamic_attributes = [Var(**attr) for attr in data.pop("dynamic_attributes")]
        env_vars = [Var(**env) for env in data.pop("env_vars")]

        return cls(
            inputs=inputs,
            outputs=outputs,
            dynamic_attributes=dynamic_attributes,
            env_vars=env_vars,
            **data
        )
