from typing import Callable, TypeVar

from .fact import AbstractFact

_FT = TypeVar('_FT', bound=AbstractFact)


def and_filter(*args: Callable[[_FT], bool]) -> Callable[[_FT], bool]:
    def _filter(fact: _FT) -> bool:
        return all(f(fact) for f in args)

    return _filter


def or_filter(*args: Callable[[_FT], bool]) -> Callable[[_FT], bool]:
    def _filter(fact: _FT) -> bool:
        return any(f(fact) for f in args)

    return _filter


def not_filter(f: Callable[[_FT], bool]) -> Callable[[_FT], bool]:
    def _filter(fact: _FT) -> bool:
        return not f(fact)

    return _filter
