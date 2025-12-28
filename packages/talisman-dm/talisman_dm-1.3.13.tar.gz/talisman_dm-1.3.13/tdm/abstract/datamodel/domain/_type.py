from dataclasses import dataclass
from typing import Callable, Set, Type, TypeVar

from tdm.abstract.datamodel.identifiable import EnsureIdentifiable


_T = TypeVar('_T', bound='AbstractDomainType')


@dataclass(frozen=True)
class AbstractDomainType(EnsureIdentifiable):
    """
    Base class for knowledge base domain types

    Attributes
    --------
    name:
        The name of the domain type.
    """
    name: str

    def pretty(self, verbose: bool = False) -> str:
        """
        Create a beautiful text representation of object.

        :param verbose: flag to create more detailed representation
        :return: object text representation
        """
        return f"{type(self).__name__}[{self.id}]({self.name})"

    @classmethod
    def constant_fields(cls) -> Set[str]:
        return set()

    @classmethod
    def name_filter(cls: Type[_T], name: str) -> Callable[[_T], bool]:
        def _filter(t: _T) -> bool:
            return t.name == name

        return _filter
