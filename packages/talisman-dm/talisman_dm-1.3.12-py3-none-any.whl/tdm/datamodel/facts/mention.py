from abc import ABCMeta
from dataclasses import dataclass, replace
from typing import Callable, Hashable, Iterable, Optional, Set, Tuple, Union

from tdm.abstract.datamodel import AbstractDomain, AbstractFact, AbstractNode, AbstractNodeMention, EnsureIdentifiable, Identifiable
from tdm.abstract.datamodel.duplicatable import Duplicatable
from tdm.abstract.json_schema import generate_model
from .value import AtomValueFact


@dataclass(frozen=True)
class _MentionFact(AbstractFact, metaclass=ABCMeta):
    """
    Auxiliary class for `MentionFact` to fix dataclass fields order.

    Attributes
    ----------
    mention:
        The part of the node that contains value fact mention.
    value:
        The value fact mentioned in document node.
    """
    mention: AbstractNodeMention
    value: AtomValueFact

    @classmethod
    def constant_fields(cls) -> Set[str]:
        return {'mention', 'value'}


@generate_model(label='mention')
@dataclass(frozen=True)
class MentionFact(Identifiable, _MentionFact, Duplicatable):
    """
    Represents fact that some `AtomValueFact` is mentioned in the document node.

    """

    def replace_with_domain(self, domain: AbstractDomain) -> 'MentionFact':
        value = self.value.replace_with_domain(domain)
        if value is self.value:
            return self
        return replace(self, value=value)

    @staticmethod
    def node_filter(node: Union[AbstractNode, str]) -> Callable[['MentionFact'], bool]:
        """
        Create a filter function to filter `MentionFact` instances based on the document node.

        :param node: The document node or its identifier to filter by.
        :return: A filter function for `MentionFact` instances.
        """
        node_id = node.id if isinstance(node, AbstractNode) else node

        def _filter(fact: MentionFact) -> bool:
            return fact.mention.node_id == node_id

        return _filter

    @staticmethod
    def value_filter(filter_: Callable[[AtomValueFact], bool]) -> Callable[['MentionFact'], bool]:
        """
        Create a filter function to filter `MentionFact` instances based on the value.

        :param filter_: A filter function for mentioned `AtomValueFact`.
        :return: A filter function for `MentionFact` instances.
        """

        def _filter(fact: MentionFact) -> bool:
            return filter_(fact.value)

        return _filter

    def duplicate_hash(self) -> Hashable:
        return (
            self.value.duplicate_hash() if isinstance(self.value, Duplicatable) else self.value.id,
            self.mention.duplicate_hash() if isinstance(self.mention, Duplicatable) else self.mention.node_id
        )

    def choose_one(
            self,
            other,
            to_hash: Callable[[str], Hashable],
            related: Callable[[str], Iterable[str]],
            restore_element: Callable[[str], EnsureIdentifiable]
    ) -> Optional[Tuple[str, str]]:
        if isinstance(other, MentionFact) and self.mention == other.mention and self.value.id == other.value.id:
            return (self.id, other.id) if self.status < other.status else (other.id, self.id)
        return None
