from abc import abstractmethod
from dataclasses import dataclass, field
from typing import Generic, Type, TypeVar

from typing_extensions import Self

from tdm.abstract.datamodel import AbstractMarkup, AbstractNode
from ._interface import AbstractNodeWrapper

_Node = TypeVar('_Node', bound=AbstractNode)
_Markup = TypeVar('_Markup', bound=AbstractMarkup)


@dataclass(frozen=True)
class AbstractNodeWrapperImpl(AbstractNodeWrapper[_Node], Generic[_Node, _Markup]):
    markup: _Markup = field(default_factory=lambda: None)

    def _convert_markup(self, markup: AbstractMarkup) -> _Markup:
        markup_type: Type[_Markup] = self._markup_type()
        if isinstance(markup, markup_type):
            return markup
        return markup_type.from_markup(markup)

    @classmethod
    def wrap(cls, node: _Node) -> Self:
        if isinstance(node, cls):
            return node  # do nothing
        if not isinstance(node, cls._node_type()):
            raise ValueError  # wrap only appropriate nodes
        args = dict(node.__dict__)
        args['markup'] = cls._markup_type().from_markup(node.markup)
        return cls(**args)  # replace markup

    @classmethod
    @abstractmethod
    def _node_type(cls) -> Type[_Node]:
        pass

    @classmethod
    @abstractmethod
    def _markup_type(cls) -> Type[_Markup]:
        pass

    def __eq__(self, other):
        node_type = self._node_type()
        if not isinstance(other, node_type):
            return NotImplemented
        return self.__dict__ == other.__dict__
