from abc import ABCMeta
from dataclasses import dataclass, replace
from typing import Callable, Hashable, Iterable, Iterator, Optional, Set, Tuple, Union

from tdm.abstract.datamodel import AbstractDomain, AbstractFact, AbstractLinkFact, EnsureIdentifiable, FactStatus, Identifiable
from tdm.abstract.datamodel.duplicatable import Duplicatable
from tdm.abstract.datamodel.fact import AbstractValueFact
from tdm.abstract.datamodel.value import AbstractValue
from tdm.abstract.json_schema import generate_model
from tdm.datamodel.common import PrunableMixin, ViewContainer
from tdm.datamodel.domain import AtomValueType, ComponentValueType, CompositeValueType


@generate_model(label='atom')
@dataclass(frozen=True)
class AtomValueFact(Identifiable, AbstractValueFact[AtomValueType, AbstractValue], PrunableMixin):
    """
    Represents a fact that holds an atomic value.

    If the fact status is FactStatus.NEW `value` should be a tuple.
    If the fact status is FactStatus.APPROVED `value` should be single-valued.
    """

    def _tuple_value(self) -> tuple:
        return tuple(v.get_none_confidenced_value() for v in (self.value if isinstance(self.value, tuple) else [self.value]))

    def replace_with_domain(self, domain: AbstractDomain) -> 'AtomValueFact':
        if isinstance(self.type_id, str):
            domain_type = domain.get_type(self.type_id)
            if not isinstance(domain_type, AtomValueType):
                raise ValueError(f"Invalid type id `{self.type_id}` for fact {self}. Expected `AtomValueType`, but got `{domain_type}`.")
            return replace(self, type_id=domain_type)
        return self

    def _as_tuple(self) -> tuple:
        return self.id, self.str_type_id, self.value

    def __eq__(self, other):
        if not isinstance(other, AtomValueFact):
            return NotImplemented
        return self._as_tuple() == other._as_tuple()

    def __hash__(self):
        return hash(self._as_tuple())

    def _collect_links(self, links: Iterable) -> Iterator[Hashable]:
        for link in links:
            if isinstance(link, AbstractLinkFact) and link.target.id == self.id:
                yield link.str_type_id, link.source

    def _collect_mentions(self, links: Iterable) -> Iterator[Hashable]:
        from tdm.datamodel.facts import MentionFact

        for m in links:
            if isinstance(m, MentionFact):
                yield m.mention

    @staticmethod
    def empty_value_filter() -> Callable[['AtomValueFact'], bool]:
        """
        Create a filter function to filter `AtomValueFact` instances with empty values.

        :return: A filter function for `AtomValueFact` instances with empty values.
        """
        return lambda f: isinstance(f.value, tuple) and not f.value

    @staticmethod
    def tuple_value_filter() -> Callable[['AtomValueFact'], bool]:
        """
        Create a filter function to filter `AtomValueFact` instances with tuple values.

        :return: A filter function for `AtomValueFact` instances with tuple values.
        """
        return lambda f: isinstance(f.value, tuple)

    @staticmethod
    def single_value_filter() -> Callable[['AtomValueFact'], bool]:
        """
        Create a filter function to filter `AtomValueFact` instances with a single value.

        :return: A filter function for `AtomValueFact` instances with a single value.
        """
        return lambda f: isinstance(f.value, AbstractValue)

    def is_hanging(self, doc: ViewContainer) -> bool:
        from .mention import MentionFact
        return self.status is not FactStatus.APPROVED \
            and not self.value \
            and not tuple(doc.related_elements(AbstractFact, self, MentionFact, tuple()))

    def choose_one(
            self,
            other,
            to_hash: Callable[[str], Hashable],
            related: Callable[[str], Iterable[str]],
            restore_element: Callable[[str], EnsureIdentifiable]
    ) -> Optional[Tuple[str, str]]:
        if not isinstance(other, type(self)) or self.str_type_id != other.str_type_id:
            return None
        if self.status is FactStatus.APPROVED and other.status is FactStatus.APPROVED:
            return None
        if self._tuple_value() != other._tuple_value():
            return None

        rel = list(related(self.id))
        other_rel = list(related(other.id))
        pseudolinks = {to_hash(_id) for _id in rel}
        other_pseudolinks = {to_hash(_id) for _id in other_rel}

        def fix_pseudolinks(pseudolinks, fact_id):
            res = set()
            for elem in pseudolinks:
                if len(elem) == 3 and elem[2] == fact_id:   # imitation of _collect_links
                    res.add((elem[0], elem[1]))
                if len(elem) == 2:                          # imitation of _collect_mentions
                    res.add((elem[1],))
            return res

        pseudolinks = fix_pseudolinks(pseudolinks, self.id)
        other_pseudolinks = fix_pseudolinks(other_pseudolinks, other.id)

        if not (pseudolinks <= other_pseudolinks or other_pseudolinks <= pseudolinks):
            return None

        links = set(self._collect_links(map(restore_element, rel)))
        other_links = set(other._collect_links(map(restore_element, other_rel)))

        # fact wo properties is not duplicate of fact with properties
        if bool(links) != bool(other_links):
            return None
        if not (links <= other_links or other_links <= links):
            return None

        if not self.value:
            mentions = set(self._collect_mentions(map(restore_element, rel)))
            other_mentions = set(other._collect_mentions(map(restore_element, other_rel)))
            if not (mentions <= other_mentions or other_mentions <= mentions):
                return None

        if self.status != other.status or not self.value:
            return (self.id, other.id) if self.status < other.status else (other.id, self.id)

        self_conf = self.most_confident_value.confidence or 0.0
        other_conf = other.most_confident_value.confidence or 0.0
        return (self.id, other.id) if self_conf > other_conf else (other.id, self.id)


@dataclass(frozen=True)
class _CompositeValueFact(AbstractFact, metaclass=ABCMeta):
    """
    Auxiliary class for `CompositeValueFact` to fix dataclass fields order.

    Attributes
    ----------
    type_id:
        The type identifier or domain composite value type of the composite value fact.
    """
    type_id: Union[str, CompositeValueType]

    @classmethod
    def constant_fields(cls) -> Set[str]:
        return {'type_id'}

    @property
    def str_type_id(self) -> str:
        return self.type_id if isinstance(self.type_id, str) else self.type_id.id


@generate_model(label='composite')
@dataclass(frozen=True)
class CompositeValueFact(Identifiable, _CompositeValueFact, PrunableMixin, Duplicatable):
    """
    Represents a fact that holds a composite value.

    The whole value is represented as `CompositeValueFact` with related `ComponentFact`s.
    """

    def replace_with_domain(self, domain: AbstractDomain) -> 'CompositeValueFact':
        if isinstance(self.type_id, str):
            domain_type = domain.get_type(self.type_id)
            if not isinstance(domain_type, CompositeValueType):
                raise ValueError(f"Invalid type id `{self.type_id}` for fact {self}. "
                                 f"Expected `CompositeValueType`, but got `{domain_type}`.")
            return replace(self, type_id=domain_type)
        return self

    def _as_tuple(self) -> tuple:
        return self.id, self.str_type_id

    def __eq__(self, other):
        if not isinstance(other, CompositeValueFact):
            return NotImplemented
        return self._as_tuple() == other._as_tuple()

    def __hash__(self):
        return hash(self._as_tuple())

    def is_hanging(self, doc: ViewContainer) -> bool:
        return self.status is not FactStatus.APPROVED and \
            not [x.target for x in doc.related_elements(AbstractFact, self, ComponentFact, tuple())]

    def duplicate_hash(self) -> Hashable:
        return self.str_type_id

    def _collect_components(self, props: Iterable) -> Iterator:
        for p in props:
            if isinstance(p, ComponentFact) and p.source.id == self.id:
                # use duplicate_hash for normalized AbstractValueFact, because AbstractValueFact would be dedup after CompositeValueFact
                yield p.str_type_id, p.target.duplicate_hash() if isinstance(p.target, AbstractValueFact) and p.target.value else p.target

    def _collect_links(self, links: Iterable) -> Iterator[Hashable]:
        for link in links:
            if isinstance(link, AbstractLinkFact) and link.target.id == self.id:
                yield link.str_type_id, link.source

    def choose_one(
            self,
            other,
            to_hash: Callable[[str], Hashable],
            related: Callable[[str], Iterable[str]],
            restore_element: Callable[[str], EnsureIdentifiable]
    ) -> Optional[Tuple[str, str]]:
        if not isinstance(other, CompositeValueFact) or self.str_type_id != other.str_type_id:
            return None
        if self.status is FactStatus.APPROVED and other.status is FactStatus.APPROVED:
            return None

        rel = list(related(self.id))
        other_rel = list(related(other.id))
        pseudolinks = {to_hash(_id) for _id in rel}
        other_pseudolinks = {to_hash(_id) for _id in other_rel}

        def fix_pseudolinks(pseudolinks, facts_id):
            res = set()
            for elem in pseudolinks:
                if len(elem) == 3:
                    if elem[1] == facts_id:          # imitation of _collect_components
                        res.add((elem[0], to_hash(elem[2])))
                    if elem[2] == facts_id:          # imitation of _collect_links
                        res.add((elem[0], elem[1]))
            return res

        pseudolinks = fix_pseudolinks(pseudolinks, self.id)
        other_pseudolinks = fix_pseudolinks(other_pseudolinks, other.id)

        if not (pseudolinks <= other_pseudolinks or other_pseudolinks <= pseudolinks):
            return None

        links = set(self._collect_links(map(restore_element, rel)))
        other_links = set(other._collect_links(map(restore_element, other_rel)))

        # fact wo properties is not duplicate of fact with properties
        if bool(links) != bool(other_links):
            return None

        if not (links <= other_links or other_links <= links):
            return None

        components = set(self._collect_components(map(restore_element, rel)))
        other_components = set(other._collect_components(map(restore_element, other_rel)))
        if not (components <= other_components or other_components <= components):
            return None

        return (self.id, other.id) if self.status < other.status else (other.id, self.id)


ValueFact = Union[AtomValueFact, CompositeValueFact]


@generate_model(label='component')
@dataclass(frozen=True, eq=False)
class ComponentFact(Identifiable, AbstractLinkFact[CompositeValueFact, ValueFact, ComponentValueType]):
    """
    Represents a composite value component fact.
    It links composite value fact with another value fact (its component).
    """
    pass
