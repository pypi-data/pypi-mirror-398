from abc import ABCMeta
from dataclasses import dataclass
from typing import Generic, Set, Type, TypeVar

from tdm.abstract.datamodel.value import EnsureConfidenced
from tdm.helper import generics_mapping
from ._type import AbstractDomainType

_VT = TypeVar('_VT', bound=EnsureConfidenced)


@dataclass(frozen=True)
class AbstractValueDomainType(AbstractDomainType, Generic[_VT], metaclass=ABCMeta):
    """
    Base class for knowledge base value-associated types

    Attributes
    --------
    value_type:
        Type of the associated value
    """
    value_type: Type[_VT]

    def pretty(self, verbose: bool = False) -> str:
        if verbose:
            return f"{type(self).__name__}{{{self.value_type.__name__}}}[{self.id}]({self.name})"
        return f"{type(self).__name__}[{self.id}]({self.name})"

    @classmethod
    def constant_fields(cls) -> Set[str]:
        return {'value_type'}

    @classmethod
    def get_value_type(cls) -> type:
        return generics_mapping(cls)[_VT]
