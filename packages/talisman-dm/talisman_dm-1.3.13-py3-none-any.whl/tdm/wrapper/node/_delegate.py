from dataclasses import replace
from typing import Callable, Iterable


def getter_delegate(name: str, post_processors: Iterable[Callable] = tuple(), *, base: str = 'markup'):
    def f(self, *args, **kwargs):
        result = getattr(getattr(self, base), name)(*args, **kwargs)
        for post in post_processors:
            result = post(self, result)
        return result

    return f


def property_delegate(name: str, post_processors: Iterable[Callable] = tuple(), *, base: str = 'markup'):
    def f(self):
        result = getattr(getattr(self, base), name)
        for post in post_processors:
            result = post(self, result)
        return result

    return property(f)


def modifier_delegate(name: str, validators: Iterable[Callable] = tuple(), *, base: str = 'markup'):
    def f(self, *args, **kwargs):
        for validator in validators:
            ret = validator(self, *args, **kwargs)
            if ret is not None:
                args = ()
                kwargs = ret
        return replace(self, **{base: getattr(getattr(self, base), name)(*args, **kwargs)})

    return f
