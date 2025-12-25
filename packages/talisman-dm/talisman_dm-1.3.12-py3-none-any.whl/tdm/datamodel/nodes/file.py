from dataclasses import dataclass
from typing import Optional

from tdm.abstract.datamodel import AbstractContentNode, BaseNodeMetadata
from tdm.abstract.json_schema import generate_model


@dataclass(frozen=True)
class FileNodeMetadata(BaseNodeMetadata):
    """
    File node metadata

    Attributes
    --------
    name:
        file name
    size:
        file size (bytes)
    """
    name: Optional[str] = None
    size: Optional[int] = None


@generate_model(label='file')
@dataclass(frozen=True)
class FileNode(AbstractContentNode[FileNodeMetadata, str]):
    """
    Node for file representation.
    ``content`` contains file URI.
    """
    pass


@dataclass(frozen=True)
class ImageNodeMetadata(FileNodeMetadata):
    """
    Image node metadata

    Attributes
    --------
    width:
        image width (px)
    height:
        image height (px)
    """
    width: Optional[int] = None
    height: Optional[int] = None


@generate_model(label='image')
@dataclass(frozen=True)
class ImageNode(AbstractContentNode[ImageNodeMetadata, str]):
    """
    Node for image representation.
    ``content`` contains image file URI.
    """
    pass


@dataclass(frozen=True)
class AudioNodeMetadata(FileNodeMetadata):
    """
    Audio node metadata

    Attributes
    --------
    duration:
        audio duration (ms)
    """
    duration: Optional[int] = None


@generate_model(label='audio')
@dataclass(frozen=True)
class AudioNode(AbstractContentNode[AudioNodeMetadata, str]):
    """
    Node for audio representation.
    ``content`` contains audio file URI.
    """
    pass


@dataclass(frozen=True)
class VideoNodeMetadata(FileNodeMetadata):
    """
    Video node metadata

    Attributes
    --------
    width:
        video frame width (px)
    height:
        video frame height (px)
    duration:
        video duration (ms)
    """
    width: Optional[int] = None
    height: Optional[int] = None
    duration: Optional[int] = None


@generate_model(label='video')
@dataclass(frozen=True)
class VideoNode(AbstractContentNode[VideoNodeMetadata, str]):
    """
    Node for video representation.
    ``content`` contains video file URI.
    """
    pass
