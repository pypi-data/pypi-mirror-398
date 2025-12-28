from abc import ABCMeta, abstractmethod
from typing import Callable, Dict, Iterable, Iterator, Type, TypeVar, Union

from tdm.abstract.datamodel.identifiable import Identifiable
from ._type import AbstractDomainType

_DomainType = TypeVar('_DomainType', bound=AbstractDomainType)


class AbstractDomain(metaclass=ABCMeta):
    """
    Represents an abstract domain in the knowledge base.

    This is an abstract base class that provides the basic structure and methods for a domain.

    Attributes:
        id2type (Dict[str, AbstractDomainType]): A dictionary mapping IDs to domain types.
        types (Dict[Type[AbstractDomainType], Iterable[AbstractDomainType]]): A dictionary mapping domain types to their instances.

    """
    __slots__ = ()

    @property
    @abstractmethod
    def id2type(self) -> Dict[str, AbstractDomainType]:
        """
        Provides a dictionary mapping identifiers to domain types.

        :return: A dictionary mapping identifiers to domain types.
        """
        pass

    @property
    @abstractmethod
    def types(self) -> Dict[Type[AbstractDomainType], Iterable[AbstractDomainType]]:
        """
        Provides a dictionary mapping domain types to their instances.

        :return: A dictionary mapping domain types to their instances.
        """
        pass

    @abstractmethod
    def get_type(self, id_: str) -> AbstractDomainType:
        """
        Retrieves a domain type by its identifier.

        :param id_: The identifier of the domain type.
        :return: The domain type associated with the provided identifier.

        """
        pass

    @abstractmethod
    def get_types(
            self, type_: Type[_DomainType] = AbstractDomainType, *,
            filter_: Union[Callable[[_DomainType], bool], Iterable[Callable[[_DomainType], bool]]] = tuple()
    ) -> Iterator[_DomainType]:
        """
        Retrieves instances of domain types based on the provided filters.

        :param type_: The type of domain types to retrieve. Defaults to AbstractDomainType (all domain types).
        :param filter_: A filter or a list of filters to apply on each individual retrieved domain types.
        :return: An iterator yielding instances of domain types.
        """
        pass

    @abstractmethod
    def related_types(
            self, obj: Union[Identifiable, str], type_: Type[_DomainType] = AbstractDomainType, *,
            filter_: Union[Callable[[_DomainType], bool], Iterable[Callable[[_DomainType], bool]]] = tuple()
    ) -> Iterator[_DomainType]:
        """
        Retrieves related domain types based on the provided object and filters.

        :param obj: An object or its identifier to retrieve related domain types for.
        :param type_: The type of domain types to retrieve. Defaults to AbstractDomainType (all domain types).
        :param filter_: A filter or a list of filters to apply on each individual retrieved domain types.

        :return: An iterator yielding instances of related domain types.
        """
        pass
