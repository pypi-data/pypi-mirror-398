from dataclasses import is_dataclass
from typing import Mapping, Sequence

from immutabledict import immutabledict
from pydantic import BaseModel


def freeze_dict(obj: Mapping) -> immutabledict:
    return immutabledict((k, freeze(v)) for k, v in obj.items())


def freeze_sequence(obj: Sequence) -> tuple:
    return tuple(freeze(v) for v in obj)


def freeze(obj):
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if is_dataclass(obj) and obj.__dataclass_params__.frozen:
        return obj
    if isinstance(obj, Mapping):
        return freeze_dict(obj)
    if isinstance(obj, set):
        return frozenset(freeze(v) for v in obj)
    if isinstance(obj, Sequence):
        return freeze_sequence(obj)
    raise ValueError


def unfreeze(obj):
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, Mapping):
        return {k: unfreeze(v) for k, v in obj.items()}
    if isinstance(obj, (frozenset, set)):
        return {unfreeze(v) for v in obj}
    if isinstance(obj, Sequence):
        t = type(obj)
        return t(unfreeze(v) for v in obj)
    if isinstance(obj, BaseModel):
        return unfreeze(obj.model_dump())
    if is_dataclass(obj):
        return obj
