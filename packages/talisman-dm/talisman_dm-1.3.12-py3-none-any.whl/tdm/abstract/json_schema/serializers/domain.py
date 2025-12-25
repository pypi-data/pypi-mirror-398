from typing import Any, Dict, Type, Union

from tdm.abstract.datamodel import AbstractDomainType
from .abstract import AbstractElementSerializer


class DomainTypeSerializer(AbstractElementSerializer[Union[str, AbstractDomainType], str]):
    def serialize(self, element: Union[str, AbstractDomainType]) -> str:
        return element if isinstance(element, str) else element.id

    def deserialize(self, serialized: str, typed_id2element: Dict[type, Dict[str, Any]]) -> Union[str, AbstractDomainType]:
        return typed_id2element.get(AbstractDomainType, {}).get(serialized, serialized)

    def field_type(self, element_type: Type[Union[str, AbstractDomainType]]) -> Type[str]:
        return str
