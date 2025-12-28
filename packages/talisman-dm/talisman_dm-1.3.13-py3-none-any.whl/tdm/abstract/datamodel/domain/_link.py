from abc import ABCMeta
from dataclasses import dataclass
from typing import Generic, Set, TypeVar

from tdm.helper import generics_mapping, unfold_union
from ._type import AbstractDomainType

_ST = TypeVar('_ST', bound=AbstractDomainType)
_TT = TypeVar('_TT', bound=AbstractDomainType)


@dataclass(frozen=True)
class AbstractLinkDomainType(AbstractDomainType, Generic[_ST, _TT], metaclass=ABCMeta):
    """
    Base class for knowledge base link types (connecting between other domain types).

    Attributes
    --------
    source:
        The source domain type.
    target:
        The target domain type.
    """
    source: _ST
    target: _TT

    def __post_init__(self):
        types_mapping = generics_mapping(type(self))
        if not isinstance(self.source, unfold_union(types_mapping.get(_ST))):
            raise ValueError(f"Illegal source for {type(self)}. Expected: {types_mapping.get(_ST)}, actual: {type(self.source)}")
        if not isinstance(self.target, unfold_union(types_mapping.get(_TT))):
            raise ValueError(f"Illegal target for {type(self)}. Expected: {types_mapping.get(_TT)}, actual: {type(self.target)}")

    def pretty(self, verbose: bool = False) -> str:
        return f"{type(self).__name__}[{self.id}]({self.name}){{{self.source.pretty(verbose)} --> {self.target.pretty(verbose)}}}"

    @classmethod
    def constant_fields(cls) -> Set[str]:
        return {'source', 'target'}
