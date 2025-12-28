from typing import Any, Dict, Generic, List, Mapping, Set, Type, TypeVar

from .abstract import AbstractElementSerializer

_SEQUENCES: Mapping[type, type] = {
    tuple: List,  # in other case Tuple[A, ...] is converted to Tuple[A]. Deserializes to tuple
    set: Set,
    list: List
}


class SequenceElementSerializer(AbstractElementSerializer):
    def __init__(self, real_type: type, serializer: AbstractElementSerializer):
        self._real_type = real_type
        self._typing_type = _SEQUENCES[real_type]
        self._serializer = serializer

    def serialize(self, element):
        return self._real_type(self._serializer.serialize(e) for e in element)

    def deserialize(self, serialized, typed_id2element: Dict[type, Dict[str, Any]]):
        return self._real_type(self._serializer.deserialize(s, typed_id2element) for s in serialized)

    def field_type(self, element_type):
        return self._typing_type[element_type]


_E = TypeVar('_E')
_S = TypeVar('_S')


class MappingElementSerializer(AbstractElementSerializer[Mapping[str, _E], Dict[str, _S]], Generic[_E, _S]):
    def __init__(self, real_type: type, serializer: AbstractElementSerializer[_E, _S]):
        self._real_type = real_type
        self._serializer = serializer

    def serialize(self, element: Mapping[str, _E]) -> Dict[str, _S]:
        return {key: self._serializer.serialize(value) for key, value in element.items()}

    def deserialize(self, serialized: Dict[str, _S], typed_id2element: Dict[type, Dict[str, Any]]) -> Mapping[str, _E]:
        return {key: self._serializer.deserialize(value, typed_id2element) for key, value in serialized.items()}

    def field_type(self, element_type) -> Type[Dict[str, _S]]:
        return Dict[str, element_type]
