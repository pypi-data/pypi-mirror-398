from dataclasses import dataclass
from typing import Type

from tdm.abstract.datamodel import AbstractDomainType, Identifiable
from tdm.abstract.datamodel.domain import AbstractValueDomainType
from tdm.abstract.datamodel.value import AbstractConceptValue


@dataclass(frozen=True)
class AbstractConceptType(Identifiable, AbstractValueDomainType[AbstractConceptValue]):
    """
    Base class for concept-like domain types
    """
    value_type: Type[AbstractConceptValue] = AbstractConceptValue

    def pretty(self, verbose: bool = False) -> str:
        return AbstractDomainType.pretty(self, verbose)


@dataclass(frozen=True)
class ConceptType(AbstractConceptType):
    """
    Concept domain type
    """
    pass


@dataclass(frozen=True)
class DocumentType(AbstractConceptType):
    """
    Concept domain type for document representation
    """
    pass


#  following classes could be removed after v0 support stop

@dataclass(frozen=True)
class AccountType(AbstractConceptType):
    """
    Concept domain type for account representation
    """
    pass


@dataclass(frozen=True)
class PlatformType(AbstractConceptType):
    """
    Concept domain type for platform representation
    """
    pass
