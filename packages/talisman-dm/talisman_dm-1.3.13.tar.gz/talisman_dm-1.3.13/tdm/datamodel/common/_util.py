from typing import Dict, Generic, Hashable, Iterator, Set, TypeVar

_K = TypeVar('_K', bound=Hashable)
_V = TypeVar('_V', bound=Hashable)


class LazyUpdatingDict(Generic[_K, _V]):
    def __init__(self, data: Dict[_K, Set[_V]]):
        self._data: Dict[_K, Set[_V]] = dict(data)
        self._updated: Set[_K] = set()

    def extract_data(self) -> Dict[_K, Set[_V]]:
        try:
            return self._data
        finally:
            self._data = None
            self._updated = None

    def _copy_if_not_updated(self, key: _K) -> Set[_V]:
        if key not in self._updated:
            self._data[key] = set(self._data.get(key, set()))
            self._updated.add(key)
        return self._data[key]

    def add(self, key: _K, value: _V) -> None:
        self._copy_if_not_updated(key).add(value)

    def remove(self, key: _K, value: _V) -> None:
        values = self._copy_if_not_updated(key)
        values.discard(value)
        if not values:
            self.pop(key)

    def pop(self, key: _K) -> None:
        self._data.pop(key, None)
        self._updated.discard(key)

    def iterate(self, key: _K) -> Iterator[_V]:
        yield from self._data.get(key, set())

    def len(self, key: _K) -> int:
        return len(self._data.get(key, ()))

    def __contains__(self, key: _K) -> bool:
        return key in self._data
