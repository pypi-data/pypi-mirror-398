from typing import Any, Dict, Generic, Type, TypeVar

from tdm.abstract.datamodel import EnsureIdentifiable
from .abstract import AbstractElementSerializer

_Identifiable = TypeVar('_Identifiable', bound=EnsureIdentifiable)


class IdSerializer(AbstractElementSerializer[_Identifiable, str], Generic[_Identifiable]):
    def __init__(self, type_: Type[_Identifiable]):
        self._type = type_

    def serialize(self, element: _Identifiable) -> str:
        return element.id

    def deserialize(self, serialized: str, typed_id2element: Dict[type, Dict[str, Any]]) -> _Identifiable:
        return typed_id2element[self._type][serialized]

    def field_type(self, element_type: Type[_Identifiable]) -> Type[str]:
        return str
