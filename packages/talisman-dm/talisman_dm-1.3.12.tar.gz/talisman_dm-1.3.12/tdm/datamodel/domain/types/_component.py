from dataclasses import dataclass

from tdm.abstract.datamodel import AbstractLinkDomainType, Identifiable
from ._composite import CompositeValueType
from ._property import ValueType


@dataclass(frozen=True)
class ComponentValueType(Identifiable, AbstractLinkDomainType[CompositeValueType, ValueType]):
    """
    Domain type for component facts
    """
    isRequired: bool = False  # noqa N815
