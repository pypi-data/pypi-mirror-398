from typing import Any, Dict, Type

from tdm.abstract.datamodel import AbstractMarkup, FrozenMarkup
from tdm.helper import unfreeze
from .abstract import AbstractElementSerializer


class MarkupSerializer(AbstractElementSerializer[AbstractMarkup, dict]):
    def serialize(self, element: AbstractMarkup) -> dict:
        return unfreeze(element.markup)

    def deserialize(self, serialized: dict, typed_id2element: Dict[type, Dict[str, Any]]) -> FrozenMarkup:
        return FrozenMarkup.freeze(serialized)

    def field_type(self, element_type: Type[AbstractMarkup]) -> Type[dict]:
        return dict
