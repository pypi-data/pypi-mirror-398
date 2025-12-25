import enum
import inspect
from abc import ABCMeta
from collections import defaultdict
from dataclasses import dataclass, make_dataclass
from typing import Callable, Type, TypeVar, Union

from immutabledict import immutabledict

from tdm.abstract.datamodel import AbstractMarkup, AbstractNode, FrozenMarkup
from tdm.helper import generics_mapping, register_in_module
from ._delegate import getter_delegate, modifier_delegate, property_delegate
from ._impl import AbstractNodeWrapperImpl
from ._interface import _Node as _NodeType

_Node = TypeVar('_Node', bound=AbstractNode)
_Markup = TypeVar('_Markup', bound=AbstractMarkup)


class MethodType(str, enum.Enum):
    getter = 'getter'
    modifier = 'modifier'


class NodeWrapperDecorator(object):
    _validators = defaultdict(list)
    _post_processors = defaultdict(list)
    _method2type = {}

    @classmethod
    def generate_wrapper(cls, markup: Type[_Markup]):
        """
        Generate document node wrapper with specified markup class.
        Decorated class should be subclass of:
        * some `AbstractNode` implementation,
        * markup interface with methods decorated with `getter` and `modifier`,
        * `AbstractWrapper`.

        :param markup: Markup class to be associated with wrapped node.
        :return: A decorator function to generate the wrapper class.
        """
        def generate_type(cls_: Type[_Node]) -> Type[_Node]:
            node_type = generics_mapping(cls_)[_NodeType]
            validators = defaultdict(list)
            post_processors = defaultdict(list)

            for _, f in inspect.getmembers(cls_):
                if not isinstance(f, Callable) and not isinstance(f, property):
                    continue
                if f in cls._validators:
                    for target in cls._validators[f]:
                        validators[target].append(f)
                if f in cls._post_processors:
                    for target in cls._post_processors[f]:
                        post_processors[target].append(f)

            methods = {
                '_node_type': classmethod(lambda _: node_type),
                '_markup_type': classmethod(lambda _: markup),
                '__hash__': lambda self: node_type.__hash__(self)
            }

            for name in cls_.__abstractmethods__:  # delegate all abstract methods to markup
                try:
                    methods[name] = cls._delegate(name, getattr(cls_, name), validators, post_processors)
                except KeyError:
                    pass

            class _Impl(AbstractNodeWrapperImpl[node_type, markup], cls_, metaclass=ABCMeta):
                pass

            return register_in_module(dataclass(frozen=True, eq=False)(type(f'{cls_.__name__}With{markup.__name__}', (_Impl,), methods)))

        return generate_type

    @classmethod
    def composite_markup(cls, **kwargs: Type[AbstractMarkup]):
        """
        Generate a composite markup class by combining multiple markup classes.

        :param kwargs: Keyword arguments where keys are labels and values are markup classes to be combined.
        :return: A decorator function to generate the composite markup class.
        """
        fields = tuple(kwargs.items())

        methods_mapping = {}
        for key, type_ in fields:
            for base in type_.mro():
                if issubclass(base, AbstractMarkup) or not hasattr(base, '__abstractmethods__'):
                    continue  # find base interface
                for name in base.__abstractmethods__:
                    if name in methods_mapping:
                        raise TypeError
                    methods_mapping[name] = key

        def generate_composite_markup(cls_: Type[_Markup]) -> Type[_Markup]:
            def markup(self) -> immutabledict:
                return immutabledict(**{
                    key: getattr(self, key).markup for key, _ in fields
                }, **self.__other__)

            def from_markup(cls__, markup: AbstractMarkup):
                markup = dict(markup.markup)
                values = {key: type_.from_markup(FrozenMarkup(_markup=markup.pop(key, immutabledict()))) for key, type_ in fields}
                return cls__(**values, __other__=immutabledict(markup))

            namespace = {
                'markup': property(markup),
                'from_markup': classmethod(from_markup)
            }

            for name in cls_.__abstractmethods__:
                if name not in methods_mapping:
                    continue
                base = methods_mapping[name]
                namespace[name] = cls._delegate(name, getattr(cls_, name), {}, {}, base=base)

            result = register_in_module(make_dataclass(
                f"Generated{cls_.__name__}", [*fields, ('__other__', immutabledict)],
                bases=(cls_,),
                namespace=namespace,
                frozen=True,
                eq=False
            ))

            if not issubclass(result, cls_):
                raise TypeError
            return result

        return generate_composite_markup

    @classmethod
    def validate(cls, orig: Callable):
        """
        Decorator to associate validation functions with methods.

        :param orig: The function to be validated.
        :return: A decorator function to associate the validation function with methods.
        """
        def decorate(f):
            # TODO: check signature
            cls._validators[f].append(orig)
            return f

        return decorate

    @classmethod
    def post_process(cls, orig: Union[Callable, property]):
        """
        Decorator to associate post-processing functions with methods.

        :param orig: The post-processing function or property to be associated.
        :return: A decorator function to associate the post-processing function with methods.
        """
        def decorate(f):
            # TODO: check signature
            cls._post_processors[f].append(orig)
            return f

        return decorate

    @classmethod
    def _delegate(cls, name, f, validators, post_processors, *, base: str = 'markup'):
        if isinstance(f, property):
            return property_delegate(name, post_processors.get(f, []), base=base)
        mode = cls._method2type[f]
        if mode is MethodType.getter:
            return getter_delegate(name, post_processors.get(f, []), base=base)
        elif mode is MethodType.modifier:
            return modifier_delegate(name, validators.get(f, []), base=base)
        raise ValueError

    @classmethod
    def set_method_type(cls, method: MethodType):
        def wrap(f):
            cls._method2type[f] = method
            return f

        return wrap
