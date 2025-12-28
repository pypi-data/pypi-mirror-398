from pydantic import BaseModel
from typing import Any
from typing_extensions import Self

ALL_SUCCESS: str
ANY_SUCCESS: str
IGNORE: str

class SubProcessConfig(BaseModel):
    title: str
    description: str
    template_name: str | None

class NodeConfig(BaseModel):
    title: str
    depends_on: list[str]
    dependency_condition: str
    node_class_name: str
    config: dict
    def validate(cls, value: Any) -> Self: ...

class DAGDefinition(BaseModel):
    title: str
    description: str | None
    nodes: list[NodeConfig]
