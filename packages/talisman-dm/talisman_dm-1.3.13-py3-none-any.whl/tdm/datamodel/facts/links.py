from dataclasses import dataclass

from tdm.abstract.datamodel import AbstractLinkFact, Identifiable
from tdm.abstract.json_schema import generate_model
from tdm.datamodel.domain import RelationPropertyType, RelationType
from .concept import ConceptFact
from .value import ValueFact


@generate_model(label='relation')
@dataclass(frozen=True, eq=False)
class RelationFact(Identifiable, AbstractLinkFact[ConceptFact, ConceptFact, RelationType]):
    """
    Represents a relation fact that links together two concept facts.
    """
    pass


@generate_model(label='r_property')
@dataclass(frozen=True, eq=False)
class RelationPropertyFact(Identifiable, AbstractLinkFact[RelationFact, ValueFact, RelationPropertyType]):
    """
    Represents a relation property fact.
    It links relation fact with some value fact.
    """
    pass
