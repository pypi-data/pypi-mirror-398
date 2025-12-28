from typing import Any, Dict, Generic, Type, TypeVar

from .abstract import AbstractElementSerializer

_T = TypeVar('_T')


class IdentitySerializer(AbstractElementSerializer[_T, _T], Generic[_T]):
    def __init__(self, t: Type[_T]):
        self._type = t

    def serialize(self, element: _T) -> _T:
        if not isinstance(element, self._type):
            raise ValueError(f"Illegal value {element} of {type(element).__name__}. {self._type} is expected")
        return element

    def deserialize(self, serialized: _T, typed_id2element: Dict[type, Dict[str, Any]]) -> _T:
        if not isinstance(serialized, self._type):
            raise ValueError(f"Illegal value {serialized} of {type(serialized).__name__}. {self._type} is expected")
        return serialized

    def field_type(self, element_type: Type[_T]) -> Type[_T]:
        return element_type
