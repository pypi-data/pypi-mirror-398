from dataclasses import dataclass

from typing_extensions import Self

from tdm.abstract.datamodel import AbstractNodeMention
from tdm.abstract.json_schema import generate_model
from tdm.datamodel.nodes import VideoNode
from ._abstract import AbstractBBox, AbstractSegment


@generate_model
@dataclass(frozen=True)
class VideoNodeMention(AbstractSegment, AbstractBBox, AbstractNodeMention):
    """
    Represents spatiotemporal volume mention for video node.

    Attributes
    --------
    node:
        The video node being mentioned.
    left:
        The left position of the spatiotemporal volume (px).
    top:
        The top position of the spatiotemporal volume (px).
    right:
         The right position of the spatiotemporal volume (px).
    bottom:
        The bottom position of the spatiotemporal volume (px).
    start:
        The start of the spatiotemporal volume (ms).
    end:
        The end of the spatiotemporal volume (ms).
    """
    node: VideoNode

    def __post_init__(self):
        if not isinstance(self.node, VideoNode):
            raise ValueError(f"Incorrect node type {type(self.node)}. Expected {VideoNode}")
        self._validate_bbox(self.node.metadata)
        self._validate_segment(self.node.metadata)

    @classmethod
    def build(cls, node: VideoNode, left: int, top: int, width: int, height: int, start: int, end: int) -> Self:
        return cls(node, left, top, left + width, top + height, start, end)
