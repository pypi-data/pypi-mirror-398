from dataclasses import dataclass, field
from typing import ClassVar, Optional

from tdm.abstract.datamodel import AbstractContentNode, BaseNodeMetadata
from tdm.abstract.json_schema import generate_model


@dataclass(frozen=True)
class TextNodeMetadata(BaseNodeMetadata):
    """
    Text node metadata

    Attributes
    --------
    language:
        node content language
    header:
        header indicator
    header_level:
        level of the header (could be not None if ``header`` is True)
    """

    language: Optional[str] = None
    header: bool = False
    header_level: Optional[int] = None

    UNKNOWN_LANG: ClassVar[str] = field(default='unknown', init=False, hash=False, repr=False, compare=False)

    def __post_init__(self):
        if self.header_level is not None:
            if self.header_level < 0:
                raise ValueError(f"header_level could not be negative (actual: {self.header_level})")
            if not self.header:
                raise ValueError("header_level could be specified only with header flag")


@generate_model(label='text')
@dataclass(frozen=True)
class TextNode(AbstractContentNode[TextNodeMetadata, str]):
    """
    Text node implementation.
    ``content`` contains node text.
    """
    pass


@dataclass(frozen=True)
class KeyNodeMetadata(BaseNodeMetadata):
    """
    Key node metadata

    Attributes
    --------
    language:
        node content language
    """
    language: Optional[str] = None


@generate_model(label='key')
@dataclass(frozen=True)
class KeyNode(AbstractContentNode[TextNodeMetadata, str]):
    """
    Node for key representation in key-value pair.
    ``content`` contains key text.

    KeyNode could be direct child only for a ``JSONNode``.
    """
    pass
