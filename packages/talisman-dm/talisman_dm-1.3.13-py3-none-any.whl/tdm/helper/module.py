import sys
from typing import TypeVar

_T = TypeVar('_T', bound=type)


def register_in_module(t: _T) -> _T:
    module = t.__module__
    name = t.__name__
    if hasattr(sys.modules[module], name):
        if getattr(sys.modules[module], name) is not t:
            raise RuntimeError
    else:
        setattr(sys.modules[module], name, t)
    return t
