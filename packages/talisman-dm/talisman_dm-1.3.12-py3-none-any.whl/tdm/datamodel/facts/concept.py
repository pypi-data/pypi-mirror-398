import logging
from dataclasses import dataclass, replace
from typing import Callable, Hashable, Iterable, Iterator, Optional, Tuple, TypeVar, Union

from typing_extensions import Self

from tdm.abstract.datamodel import AbstractDomain, AbstractFact, AbstractLinkFact, AbstractValue, EnsureIdentifiable, FactStatus, \
    Identifiable
from tdm.abstract.datamodel.fact import AbstractValueFact
from tdm.abstract.datamodel.value import AbstractConceptValue, EnsureConfidenced
from tdm.abstract.json_schema import generate_model
from tdm.datamodel.common import PrunableMixin, ViewContainer
from tdm.datamodel.domain import PropertyType
from tdm.datamodel.domain.types import AbstractConceptType
from tdm.datamodel.facts.value import ValueFact

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class _KBConceptValue(EnsureConfidenced):
    """
    Auxiliary class for ``KBConceptValue`` to fix dataclass fields order.

    Attributes
    ----------
    concept:
        The concept identifier associated with the fact.
    """
    concept: str


@dataclass(frozen=True)
class KBConceptValue(AbstractConceptValue, _KBConceptValue):
    """
    Represents a concept fact value – concept identifier in the knowledge base.
    """

    @classmethod
    def build(cls, value: Union[str, 'KBConceptValue']) -> Self:
        """
        Build a ConceptValue object from a value.

        :param value: The value to build the KBConceptValue object from.
        :return: The KBConceptValue object.
        """
        if isinstance(value, KBConceptValue):
            return value
        if isinstance(value, str):
            return cls(concept=value)
        raise ValueError(f"Invalid type of {repr(value)} (type: {type(value).__name__}). Expected KBConceptValue or str type")


_PT = TypeVar('_PT', bound=PropertyType)
_VT = TypeVar('_VT', bound=AbstractValue)


@dataclass(frozen=True)
class ConceptPropertyValue(object):
    """
    Represents a concept property value.

    Attributes
    ----------
    type_id:
        Either a string or a PropertyType object representing the property type associated with the concept.
    value:
        An AbstractValue object representing the value associated with the concept property.
    """
    type_id: Union[str, PropertyType]
    value: AbstractValue

    @classmethod
    def from_property_fact(cls, fact: 'PropertyFact') -> Self:
        """
        Constructs a ConceptPropertyValue object from a PropertyFact object.

        :param fact: The PropertyFact object to construct the ConceptPropertyValue from.
        :return: The ConceptPropertyValue object
        """
        value = fact.target.value
        if isinstance(value, tuple):
            if len(value) > 1:
                logger.warning(f"Fact {fact} contains more than one possible value. Only most confident will be taken into account")
            value = value[0]
        return cls(type_id=fact.type_id, value=value)

    def __eq__(self, other):
        if not isinstance(other, ConceptPropertyValue):
            return NotImplemented
        type_id = self.type_id.id if isinstance(self.type_id, PropertyType) else self.type_id
        other_type_id = other.type_id.id if isinstance(other.type_id, PropertyType) else other.type_id
        return type_id == other_type_id and self.value == other.value

    def __hash__(self):
        return hash((self.type_id, self.value))


@dataclass(frozen=True)
class _MissedConceptValue(EnsureConfidenced):
    """
    Auxiliary class for ``MissedConceptValue`` to fix dataclass fields order.

    Attributes
    ----------
    filters:
        A non-empty tuple of ConceptPropertyValue objects representing the filters associated with the missed value.
    """
    filters: Tuple[ConceptPropertyValue, ...]

    def __post_init__(self):
        if not self.filters:
            raise ValueError


@dataclass(frozen=True)
class MissedConceptValue(AbstractConceptValue, _MissedConceptValue):
    """
    Represents a not-in-kb concept value.
    """
    pass


ConceptValue = Union[KBConceptValue, MissedConceptValue]


@generate_model(label='concept')
@dataclass(frozen=True)
class ConceptFact(Identifiable, AbstractValueFact[AbstractConceptType, ConceptValue], PrunableMixin):
    """
    Represents a fact about some KB concept.

    If the fact status is FactStatus.NEW `value` should be a tuple.
    If the fact status is FactStatus.APPROVED `value` should be single-valued.
    """

    def is_hanging(self, doc: ViewContainer) -> bool:
        return self.status is not FactStatus.APPROVED and \
            not tuple(doc.related_elements(AbstractFact, self, PropertyFact, tuple())) and \
            not self.value

    def __post_init__(self):
        Identifiable.__post_init__(self)
        if isinstance(self.value, tuple):
            if len([v for v in self.value if isinstance(v, MissedConceptValue)]) > 1:
                raise ValueError(f"Concept fact {self} can't contain more than 1 missed value")
        if isinstance(self.value, MissedConceptValue):
            if self.status is FactStatus.APPROVED:
                raise ValueError(f"Approved fact {self} can't be with missed value.")

    def replace_with_domain(self, domain: AbstractDomain) -> 'ConceptFact':
        if isinstance(self.type_id, str):
            domain_type = domain.get_type(self.type_id)
            if not isinstance(domain_type, AbstractConceptType):
                raise ValueError(f"Invalid type id for fact {self}. Expected `AbstractConceptType`, but got `{domain_type}`.")
            return replace(self, type_id=domain_type)
        return self

    def _as_tuple(self) -> tuple:
        return self.id, self.str_type_id, self.value

    def __eq__(self, other):
        if not isinstance(other, ConceptFact):
            return NotImplemented
        return self._as_tuple() == other._as_tuple()

    def __hash__(self):
        return hash(self._as_tuple())

    def _collect_links(self, links: Iterable) -> Iterator[Hashable]:
        for p in links:
            if isinstance(p, PropertyFact):
                yield p.str_type_id, p.target

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
        if not self.value:  # equal empty values => check links
            rel = list(related(self.id))
            other_rel = list(related(other.id))
            pseudolinks = {to_hash(_id) for _id in rel}
            other_pseudolinks = {to_hash(_id) for _id in other_rel}

            def fix_pseudolinks(pseudolinks, fact_id):
                res = set()
                for elem in pseudolinks:
                    if len(elem) == 3 and elem[1] == fact_id:
                        res.add((elem[0], elem[2]))
                return res

            pseudolinks = fix_pseudolinks(pseudolinks, self.id)
            other_pseudolinks = fix_pseudolinks(other_pseudolinks, other.id)

            if pseudolinks <= other_pseudolinks or other_pseudolinks <= pseudolinks:
                links = set(self._collect_links(map(restore_element, rel)))
                other_links = set(other._collect_links(map(restore_element, other_rel)))
                if not (links <= other_links or other_links <= links):
                    return None
            else:
                return None
        return (self.id, other.id) if self.status < other.status else (other.id, self.id)

    @staticmethod
    def empty_value_filter() -> Callable[['ConceptFact'], bool]:
        """
        Create a filter to check if a concept fact has no value.

        :return: The filter function.
        """
        return lambda f: isinstance(f.value, tuple) and not f.value

    @staticmethod
    def tuple_value_filter() -> Callable[['ConceptFact'], bool]:
        """
        Create a filter to check if a concept fact has a tuple value.

        :return: The filter function.
        """
        return lambda f: isinstance(f.value, tuple)

    @staticmethod
    def single_value_filter() -> Callable[['ConceptFact'], bool]:
        """
        Create a filter to check if a concept fact has a single value.

        :return: The filter function.
        """
        return lambda f: isinstance(f.value, ConceptValue)


@generate_model(label='property')
@dataclass(frozen=True, eq=False)
class PropertyFact(Identifiable, AbstractLinkFact[ConceptFact, ValueFact, PropertyType]):
    """
    Represents a concept property fact.
    It links concept fact with some value fact.
    """
    pass
