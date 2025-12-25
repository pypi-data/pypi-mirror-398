from typing import Type

from tdm.abstract.datamodel import AbstractNodeMention
from .abstract import AbstractElementModel, AbstractModelSerializer


class NodeMentionSerializer(AbstractModelSerializer[AbstractNodeMention]):
    def serialize(self, element: AbstractNodeMention) -> AbstractElementModel[AbstractNodeMention]:
        from tdm.json_schema.mentions import serialize_mention
        return serialize_mention(element)

    def field_type(self, element_type: Type[AbstractNodeMention]) -> Type[AbstractElementModel[AbstractNodeMention]]:
        from tdm.json_schema.mentions import MENTION_MODELS
        return MENTION_MODELS[element_type]
