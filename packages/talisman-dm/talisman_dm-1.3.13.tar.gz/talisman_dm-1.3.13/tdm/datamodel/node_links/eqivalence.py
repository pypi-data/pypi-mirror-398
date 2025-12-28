from dataclasses import dataclass

from tdm.abstract.datamodel import AbstractNodeLink, AbstractNodeMention, Identifiable
from tdm.abstract.json_schema import generate_model


@generate_model(label='equivalent')
@dataclass(frozen=True)
class EquivalenceNodeLink(Identifiable, AbstractNodeLink[AbstractNodeMention, AbstractNodeMention]):
    """
    Represents a semantic link between two node mentions that refer to the same data (maybe in different forms)
    """
    pass
