from typing import Any, Generic, Optional, Type, TypeVar

from .abstract import AbstractElementModel, AbstractModelSerializer

_E = TypeVar('_E')


class DataclassSerializer(AbstractModelSerializer[_E], Generic[_E]):

    def __init__(self, t: Optional[Type[_E]] = None):
        self._model_type = self._generate_model(t) if t is not None else None

    def serialize(self, element: _E) -> AbstractElementModel[Any]:
        if self._model_type is None:
            return self.field_type(type(element)).serialize(element)
        return self._model_type.serialize(element)

    def field_type(self, element_type: Type[_E]) -> Type[AbstractElementModel[_E]]:
        if self._model_type is None:
            return self._generate_model(element_type)
        return self._model_type

    @staticmethod
    def _generate_model(t: Type[_E]) -> Type[AbstractElementModel[_E]]:
        from tdm.abstract.json_schema.model import create_model_for_type
        return create_model_for_type(t)
