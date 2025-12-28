from typing import Any, Dict, Iterable, Union

from .abstract import AbstractElementSerializer


class CompositeElementSerializer(AbstractElementSerializer):
    def __init__(self, serializers: Iterable[AbstractElementSerializer]):
        self._serializers = tuple(serializers)

    def serialize(self, element):
        for serializer in self._serializers:
            try:
                return serializer.serialize(element)
            except Exception:
                pass
        raise ValueError(f'No suitable serializer for element {repr(element)} (type: {type(element).__name__})')

    def deserialize(self, serialized, typed_id2element: Dict[type, Dict[str, Any]]):
        for serializer in self._serializers:
            try:
                return serializer.deserialize(serialized, typed_id2element)
            except Exception:
                pass
        raise ValueError(f'No suitable deserializer for element {repr(serialized)} (type: {type(serialized).__name__})')

    def field_type(self, element_type):
        types = tuple(serializer.field_type(element_type) for serializer in self._serializers)
        return Union[types]

    @classmethod
    def build(cls, serializers: Iterable[AbstractElementSerializer]) -> AbstractElementSerializer:
        serializers = tuple(serializers)
        if len(serializers) == 1:
            return serializers[0]
        return CompositeElementSerializer(serializers)
