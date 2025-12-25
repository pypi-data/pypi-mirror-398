from dataclasses import dataclass

from tdm.abstract.datamodel import AbstractNodeMention
from tdm.abstract.json_schema import generate_model
from tdm.datamodel.nodes import AudioNode
from ._abstract import AbstractSegment


@generate_model
@dataclass(frozen=True)
class AudioNodeMention(AbstractSegment, AbstractNodeMention):
    """
    Represents audio segment node mention [start; end).

    Attributes
    --------
    node:
        The audio node being mentioned.
    start:
        The start of the segment (ms).
    end:
        The end of the segment (ms).
    """
    node: AudioNode

    def __post_init__(self):
        if not isinstance(self.node, AudioNode):
            raise ValueError(f"Incorrect node type {type(self.node)}. Expected {AudioNode}")
        self._validate_segment(self.node.metadata)
