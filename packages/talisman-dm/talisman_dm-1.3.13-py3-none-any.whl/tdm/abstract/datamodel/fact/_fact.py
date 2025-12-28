from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from enum import Enum
from functools import total_ordering
from typing import Callable, Iterable, Type, Union

from typing_extensions import Self

from tdm.abstract.datamodel.domain import AbstractDomain
from tdm.abstract.datamodel.identifiable import EnsureIdentifiable


@total_ordering
class FactStatus(str, Enum):
    """
    Enumeration class representing the status of a fact.

    Attributes
    ----------
    APPROVED:
        Fact is already approved to be correct and already stored in KB.
    DECLINED:
        Fact is already rejected (incorrect fact).
    AUTO:
        Fact is marked to be approved automatically (correct fact not stored in KB yet).
    HIDDEN:
        Fact is neither approved nor declined, but is not relevant for downstream task.
    NEW:
        Fact is neither approved nor declined.
    """

    def __new__(cls, name: str, priority: int):
        obj = str.__new__(cls, name)
        obj._value_ = name
        obj.priority = priority
        return obj

    APPROVED = ("approved", 0)
    DECLINED = ("declined", 1)
    AUTO = ("auto", 2)
    HIDDEN = ("hidden", 3)
    NEW = ("new", 4)

    def __lt__(self, other: 'FactStatus'):
        if not isinstance(other, FactStatus):
            return NotImplemented
        return self.priority < other.priority


@dataclass(frozen=True)
class AbstractFact(EnsureIdentifiable, metaclass=ABCMeta):
    """
    The most abstract class for facts.

    Attributes
    ----------
    status:
        Status of the fact
    """
    status: FactStatus

    @abstractmethod
    def replace_with_domain(self, domain: AbstractDomain) -> Self:
        """
        Create a new fact with domain type instead of its identifier.
        This method also validates domain type restrictions.

        :param domain: domain to be used for fact validation.
        :return: New fact object with domain type instead of its identifier.
        """
        pass

    @staticmethod
    def id_filter(obj: Union['AbstractFact', str]) -> Callable[['AbstractFact'], bool]:
        """
        Generate a filter function to filter facts based on their identifiers.

        :param obj: The fact object or identifier to filter.
        :return: The filter function that returns True for facts with a matching identifier.
        """
        id_ = obj.id if isinstance(obj, AbstractFact) else obj

        def _filter(fact: AbstractFact) -> bool:
            return fact.id == id_

        return _filter

    @staticmethod
    def status_filter(status: Union[FactStatus, Iterable[FactStatus]]) -> Callable[['AbstractFact'], bool]:
        """
        Generate a filter function to filter facts based on their status or a collection of statuses.

        :param status: The status or collection of statuses to filter.
        :return: The filter function that returns True for facts with a matching status.
        """
        if isinstance(status, FactStatus):
            def _filter(fact: AbstractFact) -> bool:
                return fact.status is status
        else:
            statuses = frozenset(status)

            def _filter(fact: AbstractFact) -> bool:
                return fact.status in statuses

        return _filter

    @staticmethod
    def type_filter(type_: Type['AbstractFact']) -> Callable[['AbstractFact'], bool]:
        """
        Generate a filter function to filter facts based on their type.

        :param type_: The type of facts to filter.
        :return: The filter function that returns True for facts of the specified type.
        """

        def _filter(fact: AbstractFact) -> bool:
            return isinstance(fact, type_)

        return _filter
