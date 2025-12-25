from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Generic, Type, TypeVar

from typing_extensions import Self

_Element = TypeVar('_Element')
_Serialized = TypeVar('_Serialized')


class AbstractElementModel(Generic[_Element]):
    @abstractmethod
    def deserialize(self, typed_id2element: Dict[type, Dict[str, Any]]) -> _Element:
        pass

    @classmethod
    @abstractmethod
    def serialize(cls, element: _Element) -> Self:
        pass


@dataclass
class AbstractElementSerializer(Generic[_Element, _Serialized]):
    @abstractmethod
    def serialize(self, element: _Element) -> _Serialized:
        pass

    @abstractmethod
    def deserialize(self, serialized: _Serialized, typed_id2element: Dict[type, Dict[str, Any]]) -> _Element:
        pass

    @abstractmethod
    def field_type(self, element_type: Type[_Element]) -> Type[_Serialized]:
        pass


class AbstractModelSerializer(AbstractElementSerializer[_Element, AbstractElementModel[_Element]], Generic[_Element], metaclass=ABCMeta):

    def deserialize(self, serialized: AbstractElementModel[_Element], typed_id2element: Dict[type, Dict[str, Any]]) -> _Element:
        return serialized.deserialize(typed_id2element)
