from typing import Type

from tdm.abstract.datamodel.value import AbstractValue
from .abstract import AbstractElementModel, AbstractModelSerializer


class ValueSerializer(AbstractModelSerializer[AbstractValue]):
    def serialize(self, element: AbstractValue) -> AbstractElementModel[AbstractValue]:
        from tdm.json_schema.values import serialize_value
        return serialize_value(element)

    def field_type(self, element_type: Type[AbstractValue]) -> Type[AbstractElementModel[AbstractValue]]:
        from tdm.json_schema.values import VALUE_MODELS
        return VALUE_MODELS[element_type]
