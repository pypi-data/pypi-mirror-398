from dataclasses import dataclass, field
from typing import Generic, Hashable, Set, TypeVar

from tdm.helper import generics_mapping
from .identifiable import Identifiable
from .markup import AbstractMarkup, FrozenMarkup


@dataclass(frozen=True)
class BaseNodeMetadata:
    """
    The most base node metadata

    Attributes
    ---------
    hidden:
        node hiding indicator
    """
    hidden: bool = False


_NodeMetadata = TypeVar("_NodeMetadata", bound=BaseNodeMetadata)


@dataclass(frozen=True)
class AbstractNode(Identifiable, Generic[_NodeMetadata]):
    """
    Base interface for document nodes.
    All the document nodes should be frozen dataclasses.

    Attributes
    --------
    metadata:
        node metadata (defined by node implementation dataclass with fixed field set)
    markup:
        any structured node markup (no fixed schema)
    """

    metadata: _NodeMetadata = None
    markup: AbstractMarkup = field(default_factory=FrozenMarkup, hash=False)

    def __post_init__(self):
        super().__post_init__()
        if self.metadata is None:
            # hack for runtime metadata generation (if no value passed)
            object.__setattr__(self, 'metadata', self._generate_metadata())
        object.__setattr__(self, 'markup', self._convert_markup(self.markup))

    def _convert_markup(self, markup: AbstractMarkup) -> AbstractMarkup:
        if not isinstance(markup, AbstractMarkup):
            raise ValueError
        return markup

    def _generate_metadata(self) -> _NodeMetadata:
        type_vars = generics_mapping(type(self))
        return type_vars[_NodeMetadata]()

    @classmethod
    def constant_fields(cls) -> Set[str]:
        return set()

    def duplicate_hash(self) -> Hashable:
        return self


_Content = TypeVar('_Content')


@dataclass(frozen=True)
class _AbstractContentNode(Generic[_Content]):
    """
    Auxiliary class for ``AbstractContentNode`` to fix dataclass fields order

    Attributes
    --------
    content:
        Node content
    """
    content: _Content


@dataclass(frozen=True)
class AbstractContentNode(AbstractNode[_NodeMetadata], _AbstractContentNode[_Content], Generic[_NodeMetadata, _Content]):
    """
    Base class for all data nodes.
    """

    @classmethod
    def constant_fields(cls) -> Set[str]:
        return {'content'}
