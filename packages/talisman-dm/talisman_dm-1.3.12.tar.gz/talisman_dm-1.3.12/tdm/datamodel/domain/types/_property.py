from dataclasses import dataclass
from typing import Union

from tdm.abstract.datamodel import AbstractLinkDomainType, Identifiable
from ._composite import CompositeValueType
from ._concept import AbstractConceptType
from ._relation import RelationType
from ._value import AtomValueType

ValueType = Union[CompositeValueType, AtomValueType]


@dataclass(frozen=True)
class PropertyType(Identifiable, AbstractLinkDomainType[AbstractConceptType, ValueType]):
    """
    Domain type for property facts
    """

    def __hash__(self):
        return hash(self.id)


@dataclass(frozen=True)
class RelationPropertyType(Identifiable, AbstractLinkDomainType[RelationType, ValueType]):
    """
    Domain type for relation property facts
    """
    pass
