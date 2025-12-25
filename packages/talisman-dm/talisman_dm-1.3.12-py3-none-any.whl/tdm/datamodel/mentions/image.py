from dataclasses import dataclass

from typing_extensions import Self

from tdm.abstract.datamodel import AbstractNodeMention
from tdm.abstract.json_schema import generate_model
from tdm.datamodel.nodes import ImageNode
from ._abstract import AbstractBBox


@generate_model
@dataclass(frozen=True)
class ImageNodeMention(AbstractBBox, AbstractNodeMention):
    """
    Represents bounding box image node mention.

    Attributes
    --------
    node:
        The image node being mentioned.
    left:
        The left position of the bounding box (px).
    top:
        The top position of the bounding box (px).
    right:
         The right position of the bounding box (px).
    bottom:
        The bottom position of the bounding box (px).
    """
    node: ImageNode

    def __post_init__(self):
        if not isinstance(self.node, ImageNode):
            raise ValueError(f"Incorrect node type {type(self.node)}. Expected {ImageNode}")
        self._validate_bbox(self.node.metadata)

    @classmethod
    def build(cls, node: ImageNode, left: int, top: int, width: int, height: int) -> Self:
        return cls(node, left, top, left + width, top + height)
