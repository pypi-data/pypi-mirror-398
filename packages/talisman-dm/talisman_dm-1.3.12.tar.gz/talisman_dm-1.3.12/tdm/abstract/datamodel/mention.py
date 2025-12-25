from abc import ABCMeta
from dataclasses import dataclass

from .node import AbstractNode


@dataclass(frozen=True)
class AbstractNodeMention(metaclass=ABCMeta):
    """
    Abstract class for node mentions.

    Attributes
    --------
    node:
        mentioned node
    """
    node: AbstractNode

    @property
    def node_id(self) -> str:
        """
        :return: mentioned node identifier
        """
        return self.node.id
