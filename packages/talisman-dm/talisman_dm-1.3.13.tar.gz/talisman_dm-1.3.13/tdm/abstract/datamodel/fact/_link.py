from abc import ABCMeta
from dataclasses import dataclass, replace
from typing import Callable, Generic, Hashable, Iterable, Optional, Set, Tuple, Type, TypeVar, Union

from typing_extensions import Self

from tdm.abstract.datamodel.domain import AbstractDomain, AbstractDomainType, AbstractLinkDomainType
from tdm.abstract.datamodel.duplicatable import Duplicatable
from tdm.abstract.datamodel.identifiable import EnsureIdentifiable
from tdm.helper import generics_mapping, unfold_union
from ._fact import AbstractFact

_ST = TypeVar('_ST', bound=AbstractFact)
_TT = TypeVar('_TT', bound=AbstractFact)
_LDT = TypeVar('_LDT', bound=AbstractLinkDomainType)


@dataclass(frozen=True)
class AbstractLinkFact(AbstractFact, Duplicatable, Generic[_ST, _TT, _LDT], metaclass=ABCMeta):
    """
    Base class for link facts that connect between other facts.

    Attributes
    ----------
    type_id:
        The fact type identifier or instance of the link domain type.
    source:
        The source linked fact.
    target:
        The target linked fact.
    value:
        KB link identifier for approved link fact.

    """
    type_id: Union[str, _LDT]
    source: _ST
    target: _TT
    value: Optional[str] = None

    @property
    def str_type_id(self) -> str:
        return self.type_id if isinstance(self.type_id, str) else self.type_id.id

    def replace_with_domain(self, domain: AbstractDomain) -> Self:
        """
        Create a new link fact with the domain type instead of its identifier.
        This method also validates domain type restrictions.

        :param domain: The domain to be used for fact validation.
        :return: A new link fact object with the domain type instead of its identifier.
        """
        domain_type: Type[_LDT] = generics_mapping(type(self)).get(_LDT)
        type_id = domain.get_type(self.type_id) if isinstance(self.type_id, str) else self.type_id
        if not isinstance(type_id, domain_type):
            raise ValueError(f"Illegal type id `{type_id.pretty()}` for fact {self}. {domain_type.pretty()} is expected")

        source = self.source.replace_with_domain(domain)
        target = self.target.replace_with_domain(domain)

        if self.type_id is type_id and self.source is source and self.target is target:
            return self
        return replace(self, type_id=type_id, source=source, target=target)

    def _as_tuple(self) -> tuple:
        return self.id, self.str_type_id, self.source, self.target, self.value

    def duplicate_hash(self) -> Hashable:
        return self.str_type_id, self.source.id, self.target.id

    def choose_one(
            self,
            other,
            to_hash: Callable[[str], Hashable],
            related: Callable[[str], Iterable[str]],
            restore_element: Callable[[str], EnsureIdentifiable]
    ) -> Optional[Tuple[str, str]]:
        if not isinstance(other, type(self)) or self.str_type_id != other.str_type_id:
            return None
        from tdm.abstract.datamodel import FactStatus
        if self.status is FactStatus.APPROVED and other.status is FactStatus.APPROVED:
            return None
        if self.source != other.source or self.target != other.target:
            return None
        return (self.id, other.id) if self.status < other.status else (other.id, self.id)

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return NotImplemented
        return self._as_tuple() == other._as_tuple()

    def __hash__(self):
        return hash(self._as_tuple())

    def __post_init__(self):
        mapping = generics_mapping(type(self))
        if not isinstance(self.type_id, str):
            domain_type = mapping.get(_LDT)
            if not issubclass(domain_type, AbstractLinkDomainType):
                raise ValueError(f"Invalid type id for fact {self}. "
                                 f"Expected a subclass of `AbstractLinkDomainType`, but got `{domain_type}`.")
            if not isinstance(self.type_id, domain_type):
                raise ValueError(f"Illegal type id {self.type_id} for fact {self}. {domain_type} is expected")
            self._check_argument(self.type_id.source, self.source.type_id, f'Incorrect source type for link {self}')
            self._check_argument(self.type_id.target, self.target.type_id, f'Incorrect target type for link {self}')
        if not isinstance(self.source, unfold_union(mapping.get(_ST))):
            raise ValueError(f"Illegal source fact: {self.source}, {mapping.get(_ST)} is expected")
        if not isinstance(self.target, unfold_union(mapping.get(_TT))):
            raise ValueError(f"Illegal target fact: {self.target}, {mapping.get(_TT)} is expected")

    @staticmethod
    def _check_argument(expected_type: AbstractDomainType, actual_type: Union[str, AbstractDomainType], base_error_msg: str) -> None:
        expected = expected_type.id if isinstance(actual_type, str) else expected_type
        if expected != actual_type:
            raise ValueError(f"{base_error_msg}: expected `{expected}`, but got `{actual_type}`.")

    @classmethod
    def constant_fields(cls) -> Set[str]:
        return {'source', 'target', 'type_id'}

    @staticmethod
    def type_id_filter(type_id: Union[str, Iterable[str]]) -> Callable[['AbstractLinkFact'], bool]:
        """
        Generate a filter function to filter link facts based on their type identifier or a collection of type identifiers.

        :param type_id: The type identifier or collection of type identifiers to filter.
        :return: The filter function that returns True for link facts with a matching type identifier.
        """
        if isinstance(type_id, str):
            def _filter(fact: AbstractLinkFact) -> bool:
                return fact.str_type_id == type_id
        else:
            type_ids = frozenset(type_id)

            def _filter(fact: AbstractLinkFact) -> bool:
                return fact.type_id in type_ids

        return _filter

    @staticmethod
    def source_filter(filter_: Callable[[_ST], bool]) -> Callable[['AbstractLinkFact'], bool]:
        """
        Generate a filter function to filter link facts based on the source fact filter.

        :param filter_: The filter function to apply on the source fact.
        :return: The filter function that returns True for link facts with a matching source fact.
        """

        def _filter(fact: AbstractLinkFact) -> bool:
            return filter_(fact.source)

        return _filter

    @staticmethod
    def target_filter(filter_: Callable[[_TT], bool]) -> Callable[['AbstractLinkFact'], bool]:
        """
        Generate a filter function to filter link facts based on the target fact filter.

        :param filter_: The filter function to apply on the target fact.
        :return: The filter function that returns True for link facts with a matching target fact.
        """

        def _filter(fact: AbstractLinkFact) -> bool:
            return filter_(fact.target)

        return _filter
