from dataclasses import dataclass
from typing import Set

from typing_extensions import Self

from tdm.abstract.datamodel import AbstractLinkDomainType, Identifiable
from ._concept import AbstractConceptType


@dataclass(frozen=True)
class _RelationType(AbstractLinkDomainType[AbstractConceptType, AbstractConceptType]):
    """
    Auxiliary class for ``RelationType`` to fix dataclass fields order.

    Attributes
    ----------
    directed:
        indication of ordered link
    """
    directed: bool = True

    @classmethod
    def constant_fields(cls) -> Set[str]:
        return super().constant_fields().union(('directed',))

    pass


@dataclass(frozen=True)
class RelationType(Identifiable, _RelationType):
    """
    Domain type for relation facts.
    """

    def pretty(self, verbose: bool = False) -> str:
        arrow = '-->' if self.directed else '<->'
        return f"{type(self).__name__}[{self.id}]({self.name}){{{self.source.pretty(verbose)} {arrow} {self.target.pretty(verbose)}}}"

    def inversed(self) -> Self:
        return type(self)(
            **{
                **self.__dict__,
                'source': self.target,
                'target': self.source
            }
        )
