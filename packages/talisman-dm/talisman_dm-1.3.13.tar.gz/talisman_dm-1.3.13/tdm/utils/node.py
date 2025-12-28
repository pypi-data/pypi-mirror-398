from queue import LifoQueue
from typing import Callable, Iterable, Iterator, Optional, Type, TypeVar, Union

from typing_extensions import Protocol

from tdm import TalismanDocument, and_filter
from tdm.abstract.datamodel import AbstractNode

_Node = TypeVar('_Node', bound=AbstractNode)


class StopCriteria(Protocol):
    def __call__(self, node: AbstractNode) -> bool:
        pass


class NodeFilter(Protocol):
    def __call__(self, node: _Node) -> bool:
        pass


def _dfs(document: TalismanDocument, root: AbstractNode, stop_criteria: Optional[StopCriteria] = None) -> Iterator[AbstractNode]:
    if stop_criteria is None:
        def stop_criteria(_: AbstractNode) -> bool:
            return False

    queue = LifoQueue()
    queue.put(root)

    while not queue.empty():
        dfs_lookup_node = queue.get()
        yield dfs_lookup_node
        if stop_criteria(dfs_lookup_node):
            continue

        # new nodes are visited left to right to preserve reading order
        for child_node in reversed(document.child_nodes(dfs_lookup_node)):
            queue.put(child_node)


def dfs(
        document: TalismanDocument,
        root: Optional[Union[AbstractNode, Iterable[AbstractNode]]] = None,
        type_: Type[_Node] = AbstractNode,
        *,
        stop_criteria: Optional[StopCriteria] = None,
        filter_: Union[NodeFilter, Iterable[NodeFilter]] = tuple()
) -> Iterator[_Node]:
    """
    Perform a Depth-First Search (DFS) on the nodes of a Talisman document.

    :param document: The document to traverse.
    :param root: The starting node or nodes for the DFS. If no starting node is specified, document main root is used as starting node.
    :param type_: The type of nodes to consider during the search.
    :param stop_criteria: A criteria function to determine when to stop the search.
    :param filter_: Node filters to apply during the search.
    :return: An iterator over the nodes of specified type that satisfy the filter.
    """

    def check_type(obj):
        return isinstance(obj, type_)

    if isinstance(filter_, Callable):
        filter_ = (filter_,)
    filter_ = and_filter(check_type, *filter_)

    if root is None:
        root = document.main_root

    if not isinstance(root, Iterable):
        root = (root,)

    for start_node in root:
        yield from filter(filter_, _dfs(document, start_node, stop_criteria))
