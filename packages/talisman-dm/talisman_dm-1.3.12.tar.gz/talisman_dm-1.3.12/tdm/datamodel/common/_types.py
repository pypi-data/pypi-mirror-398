from typing import Dict, Type, Union

from tdm.abstract.datamodel import AbstractDomainType, AbstractFact, AbstractNode, AbstractNodeLink, EnsureIdentifiable

_BASE_TYPES = {AbstractNode, AbstractNodeLink, AbstractFact, AbstractDomainType}

_CACHE: Dict[Type[EnsureIdentifiable], Type[EnsureIdentifiable]] = {}


def get_base_type(element: Union[EnsureIdentifiable, Type[EnsureIdentifiable]]) -> Type[EnsureIdentifiable]:
    if isinstance(element, EnsureIdentifiable):
        element = type(element)
    if element in _CACHE:
        return _CACHE[element]
    bases = {t for t in _BASE_TYPES if issubclass(element, t)}
    if len(bases) != 1:
        raise TypeError(f"Unsupported element type {element}")
    _CACHE[element] = bases.pop()
    return _CACHE[element]
