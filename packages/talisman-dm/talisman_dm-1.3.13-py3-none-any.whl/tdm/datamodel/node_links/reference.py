from dataclasses import dataclass

from tdm.abstract.datamodel import AbstractNodeLink, AbstractNodeMention, Identifiable
from tdm.abstract.json_schema import generate_model


@generate_model(label='reference')
@dataclass(frozen=True)
class ReferenceNodeLink(Identifiable, AbstractNodeLink[AbstractNodeMention, AbstractNodeMention]):
    """
    Represents a reference link between two node mentions (footnote, bibliography, etc.).
    """
    pass
