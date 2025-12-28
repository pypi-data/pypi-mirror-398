from dataclasses import dataclass
from typing import Callable, Generic, Set, TypeVar

from .identifiable import EnsureIdentifiable
from .mention import AbstractNodeMention

_ST = TypeVar('_ST', bound=AbstractNodeMention)
_TT = TypeVar('_TT', bound=AbstractNodeMention)


@dataclass(frozen=True)
class AbstractNodeLink(EnsureIdentifiable, Generic[_ST, _TT]):
    """
    Represents semantic link between two nodes.

    Attributes:
        source (_ST): The source node mention of the link.
        target (_TT): The target node mention of the link.
    """
    source: _ST
    target: _TT

    @classmethod
    def constant_fields(cls) -> Set[str]:
        return {'source', 'target'}

    @staticmethod
    def source_filter(filter_: Callable[[_ST], bool]) -> Callable[['AbstractNodeLink'], bool]:
        """
        Returns a semantic link filter function based on the source node mention.
        :param filter_: The filter function for the source node mention.
        :return: The filter function for the AbstractNodeLink objects
        """
        def _filter(fact: AbstractNodeLink) -> bool:
            return filter_(fact.source)

        return _filter

    @staticmethod
    def target_filter(filter_: Callable[[_TT], bool]) -> Callable[['AbstractNodeLink'], bool]:
        """
        Returns a semantic link filter function based on the target node mention.
        :param filter_: The filter function for the target node mention.
        :return: The filter function for the AbstractNodeLink objects
        """
        def _filter(fact: AbstractNodeLink) -> bool:
            return filter_(fact.target)

        return _filter
