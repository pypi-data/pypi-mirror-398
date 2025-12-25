from enum import Enum
from typing import Any, Optional, Tuple, Union

from pydantic import BaseModel
from typing_extensions import Literal

from tdm.abstract.datamodel import FactStatus
from .metadata import FactMetadataModel


class FactType(str, Enum):
    PROPERTY = "property"
    RELATION = "relation"
    CONCEPT = "concept"
    VALUE = "value"


class SpanModel(BaseModel):
    node_id: str
    value: str
    start: int
    end: int


class AbstractFactModel(BaseModel):
    id: str
    fact_type: FactType
    status: FactStatus
    type_id: str
    value: Any = tuple()  # to support older interface
    mention: Optional[Tuple[SpanModel, ...]] = None
    metadata: Optional[FactMetadataModel] = None

    def __hash__(self) -> int:
        return hash((self.id, self.fact_type, self.status, self.type_id))


class ConceptFactModel(AbstractFactModel):
    fact_type: Literal[FactType.CONCEPT] = FactType.CONCEPT


class ValueFactModel(AbstractFactModel):
    fact_type: Literal[FactType.VALUE] = FactType.VALUE


class PropertyLinkValueModel(BaseModel):
    property_id: Optional[str] = None
    from_fact: str
    to_fact: str


class PropertyFactModel(AbstractFactModel):
    fact_type: Literal[FactType.PROPERTY] = FactType.PROPERTY
    value: PropertyLinkValueModel


class RelationFactModel(AbstractFactModel):
    fact_type: Literal[FactType.RELATION] = FactType.RELATION
    value: PropertyLinkValueModel


FactModel = Union[ConceptFactModel, ValueFactModel, PropertyFactModel, RelationFactModel]
