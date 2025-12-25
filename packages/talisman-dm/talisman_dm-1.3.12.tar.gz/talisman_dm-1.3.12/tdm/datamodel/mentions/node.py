from dataclasses import dataclass

from tdm.abstract.datamodel import AbstractNodeMention
from tdm.abstract.json_schema import generate_model


@generate_model
@dataclass(frozen=True)
class NodeMention(AbstractNodeMention):
    """
    Represents full node mention
    """
    pass
