from collections import defaultdict
from itertools import chain
from typing import Dict, Generic, Iterable, Iterator, Set, Tuple, Type, TypeVar, Union

from immutabledict import immutabledict

_T = TypeVar('_T')


class TypedIdsContainer(Iterable[Tuple[str, type]], Generic[_T]):
    __slots__ = ('_base', '_id2type', '_type2ids')

    def __init__(self, base: Type[_T], data: Union[Dict[str, Type[_T]], Iterable[Tuple[str, Type[_T]]]]):
        self._base = base
        if not isinstance(data, dict):
            data = dict(data)
        if any(not issubclass(t, self._base) for t in data.values()):
            raise ValueError(f"All types must be subclasses of {self._base}, but got {set(data.values())}")
        self._id2type = immutabledict(data)
        # self._id2data = frozendict(data if isinstance(data, dict) else {item.id: item for item in data})
        self._type2ids = None

    @classmethod
    def create(cls, base: Type[_T], data: Iterable[Tuple[str, type]]):
        return data if isinstance(data, cls) and data._base is base else cls(base, data)

    def __iter__(self) -> Iterator[Tuple[str, type]]:
        return iter(self._id2type.items())

    @property
    def ids(self) -> Set[str]:
        return set(self._id2type)

    @property
    def type2ids(self) -> Dict[type, Iterable[str]]:
        if self._type2ids is None:
            result = defaultdict(list)
            for i, t in self._id2type.items():
                result[t].append(i)
            self._type2ids = {t: frozenset(ids) for t, ids in result.items()}
        return self._type2ids

    def with_ids(self, data: Iterable[Tuple[str, type]]):
        return TypedIdsContainer(self._base, chain(self._id2type.items(), data))

    def without_ids(self, data: Iterable[str]):
        ids = set(data)
        return TypedIdsContainer(self._base, filter(lambda e: e[0] not in ids, self._id2type.items()))

    def __contains__(self, item: Union[str, Tuple[str, type]]) -> bool:
        if isinstance(item, str):
            return item in self._id2type
        return self._id2type.get(item[0], None) == item[1]

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, TypedIdsContainer):
            return NotImplemented
        return self._base is o._base and self._id2type.keys() == o._id2type.keys() \
            and all(issubclass(s, t) or issubclass(t, s) for s, t in map(lambda k: (self._id2type[k], o._id2type[k]), self._id2type))

    def __hash__(self) -> int:
        return hash((self._base, len(self._id2type)))
