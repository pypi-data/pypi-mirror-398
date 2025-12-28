from abc import abstractmethod
from typing import Generic, TypeVar

from typing_extensions import Self

from tdm.abstract.datamodel import AbstractNode

_Node = TypeVar('_Node', bound=AbstractNode)


class AbstractNodeWrapper(AbstractNode, Generic[_Node]):
    """
    Abstract class for node wrappers inheriting from AbstractNode.

    Use `tdm.wrapper.node.generate_wrapper` decorator to generate implementation

    """

    @classmethod
    @abstractmethod
    def wrap(cls, node: _Node) -> Self:
        """
        Wrap the node.

        :param node: The node to be wrapped.
        :return: A wrapped node.
        """
        pass
