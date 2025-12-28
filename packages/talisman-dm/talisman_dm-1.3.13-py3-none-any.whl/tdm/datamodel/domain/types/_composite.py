from dataclasses import dataclass

from tdm.abstract.datamodel import AbstractDomainType, Identifiable


@dataclass(frozen=True)
class CompositeValueType(Identifiable, AbstractDomainType):
    """
    Domain type for composite value facts.
    """
    pass
