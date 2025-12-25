from typing import Callable, Dict, Iterable, Iterator, Type, TypeVar, Union

from tdm.abstract.datamodel import AbstractDomain, AbstractDomainType, Identifiable
from tdm.datamodel.common import TypedIdsContainer, ViewContainer

_DomainType = TypeVar('_DomainType', bound=AbstractDomainType)


class Domain(AbstractDomain, ViewContainer):
    def __init__(
            self,
            types: Iterable[AbstractDomainType]
    ):
        temp = ViewContainer(
            {}, {}, {AbstractDomainType: TypedIdsContainer(AbstractDomainType, ())}, {}, {}, {}, {}
        ).with_elements(types, update=True)
        super().__init__(temp._id2view, temp._dependencies, temp._containers, {}, {}, {}, {})

    def __repr__(self) -> str:
        return f"{type(self).__name__}"

    @property
    def id2type(self) -> Dict[str, AbstractDomainType]:
        return self.id2element(AbstractDomainType)

    @property
    def types(self) -> Dict[Type[AbstractDomainType], Iterable[AbstractDomainType]]:
        return self.elements(AbstractDomainType)

    def get_type(self, id_: str) -> AbstractDomainType:
        return self.get_element(AbstractDomainType, id_)

    def get_types(
            self, type_: Type[_DomainType] = AbstractDomainType, *,
            filter_: Union[Callable[[_DomainType], bool], Iterable[Callable[[_DomainType], bool]]] = tuple()
    ) -> Iterator[_DomainType]:
        return self.get_elements(AbstractDomainType, type_, filter_=filter_)

    def related_types(
            self, obj: Union[Identifiable, str], type_: Type[_DomainType] = AbstractDomainType, *,
            filter_: Union[Callable[[_DomainType], bool], Iterable[Callable[[_DomainType], bool]]] = tuple()
    ) -> Iterator[_DomainType]:
        return self.related_elements(AbstractDomainType, obj, type_, filter_=filter_)

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, Domain):
            return NotImplemented
        return self._id2view == o._id2view and self._containers == o._containers

    def __hash__(self) -> int:
        return hash(self._containers[AbstractDomainType])
