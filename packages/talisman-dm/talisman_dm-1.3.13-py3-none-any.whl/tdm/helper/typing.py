from typing import Collection, Dict, Generic, Mapping, Optional, Tuple, TypeVar, Union


def unfold_union(type_: type) -> Tuple[type, ...]:
    # check if it is union
    if hasattr(type_, '__origin__') and type_.__origin__ is Union:
        return type_.__args__
    return type_,


def uniform_collection(t) -> Tuple[Optional[type], type]:
    if not hasattr(t, '__origin__'):  # not a generic, just plain type
        return None, t
    if issubclass(t.__origin__, Mapping):
        key_type, value_type = t.__args__
        if key_type is not str:
            raise TypeError(f"Only Mapping[str, ...] coul be serialized. Actual: {t}")
        return t.__origin__, value_type
    if issubclass(t.__origin__, Collection):
        args = tuple(filter(lambda t: t is not ..., t.__args__))
        if len(args) != 1:
            raise NotImplementedError
        return t.__origin__, args[0]
    if t.__origin__ is type:  # Type[...]
        return type, t.__args__[0]
    raise TypeError


def check_base_type(type_: type, base_type: type) -> bool:
    if issubclass(type_, base_type):  # check simple subclass
        return True
    if not hasattr(type_, '__origin__'):  # check if it is some generic (Union, Tuple, etc)
        return False
    origin = type_.__origin__
    if not issubclass(origin, Tuple):  # check if it is tuple
        return False
    for arg in filter(lambda t: t is not ..., type_.__args__):  # check each argument except Ellipsis
        if not issubclass(arg, base_type):  # Now we assume only Tuple[type_, ...]
            return False
    return True


def is_subclass(type_: type, base_type: type) -> bool:
    try:
        return all(check_base_type(t, base_type) for t in unfold_union(type_))
    except TypeError:
        return False


def generics_mapping(type_: type) -> Dict[TypeVar, type]:
    if issubclass(type_, Generic):  # actually it works (should be rewritten in more pythonic way)
        # assume type vars are not intersect
        result = {}
        for orig_base in type_.__orig_bases__:
            if '__origin__' in orig_base.__dict__ and '__args__' in orig_base.__dict__:
                if not hasattr(orig_base.__origin__, '__parameters__'):
                    print('here')
                result.update(dict(zip(orig_base.__origin__.__parameters__, orig_base.__args__)))
        return result
    return {}
