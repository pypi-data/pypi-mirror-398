from dataclasses import dataclass

from typing_extensions import Protocol


class _BBoxableNodeMetadata(Protocol):
    width: int
    height: int


@dataclass(frozen=True)
class AbstractBBox:
    """
    Abstract class for bounding box representation as [(left, top); (right, bottom)].

    Attributes
    --------
    left:
        The left position of the bounding box (px).
    top:
        The top position of the bounding box (px).
    right:
         The right position of the bounding box (px).
    bottom:
        The bottom position of the bounding box (px).
    """
    left: int
    top: int
    right: int
    bottom: int

    @property
    def width(self) -> int:
        """
        :return: bounding box width (px).
        """
        return self.right - self.left

    @property
    def height(self) -> int:
        """
        :return: bounding box height (px).
        """
        return self.bottom - self.top

    def _validate_bbox(self, metadata: _BBoxableNodeMetadata) -> None:
        if self.top < 0 or self.bottom <= self.top or self.left < 0 or self.right <= self.left:
            raise ValueError(f"Incorrect bbox [({self.left}, {self.top}); ({self.right}, {self.bottom})]")
        node_width = metadata.width
        if node_width is not None and self.right > node_width:
            raise ValueError(f"Bbox spreads out of the image (image width: {node_width}, bbox right border: {self.right})")
        node_height = metadata.height
        if node_height is not None and self.bottom > node_height:
            raise ValueError(f"Bbox spreads out of the image (image height: {node_height}, bbox bottom border: {self.bottom})")


class _SegmentableNodeMetadata(Protocol):
    duration: int


@dataclass(frozen=True)
class AbstractSegment:
    """
    Abstract class for audio segment representation as [start; end).

    Attributes
    --------
    start:
        The start of the segment (ms).
    end:
        The end of the segment (ms).
    """
    start: int
    end: int

    @property
    def duration(self) -> int:
        """
        :return: duration of the segment (ms).
        """
        return self.end - self.start

    def _validate_segment(self, metadata: _SegmentableNodeMetadata) -> None:
        if self.start < 0 or self.end <= self.start:
            raise ValueError(f"Incorrect interval [{self.start}; {self.end})")
        node_duration = metadata.duration
        if node_duration is not None and self.end > node_duration:
            raise ValueError(f"Audio segment [{self.start}; {self.end}) spreads out of the audio (duration: {node_duration})")
