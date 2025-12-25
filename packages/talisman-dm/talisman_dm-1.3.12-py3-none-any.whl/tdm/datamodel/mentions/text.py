from dataclasses import dataclass

from tdm.abstract.datamodel import AbstractNodeMention
from tdm.abstract.json_schema import generate_model
from tdm.datamodel.nodes import TextNode


@generate_model
@dataclass(frozen=True)
class TextNodeMention(AbstractNodeMention):
    """
    Represents text node continuous mention [start; end)

    Attributes
    --------
    node:
        mentioned text node
    start:
        index of start symbol (inclusive)
    end:
        index of end symbol (exclusive)
    """
    node: TextNode
    start: int
    end: int

    def __post_init__(self):
        if not isinstance(self.node, TextNode):
            raise ValueError(f"Incorrect node type {type(self.node)}. Expected {TextNode}")
        if self.start < 0 or self.end <= self.start:
            raise ValueError(f"Incorrect span [{self.start}, {self.end})")
        if self.end > len(self.node.content):
            raise ValueError(f"Span spreads out of the text (text len: {len(self.node.content)})")
