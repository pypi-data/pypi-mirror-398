from typing import Type

from tdm.abstract.datamodel import BaseNodeMetadata
from .abstract import AbstractElementModel, AbstractModelSerializer


class NodeMetadataSerializer(AbstractModelSerializer[BaseNodeMetadata]):
    def serialize(self, element: BaseNodeMetadata) -> AbstractElementModel[BaseNodeMetadata]:
        return self.field_type(type(element)).serialize(element)

    def field_type(self, element_type: Type[BaseNodeMetadata]) -> Type[AbstractElementModel[BaseNodeMetadata]]:
        from tdm.abstract.json_schema.model import create_model_for_type
        return create_model_for_type(element_type)  # actually it is cached
