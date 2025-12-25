from abc import ABCMeta, abstractmethod
from typing import Callable, Dict, Iterable, Iterator, Optional, Set, Tuple, Type, TypeVar, Union

from typing_extensions import Self

from .fact import AbstractFact
from .identifiable import Identifiable
from .node import AbstractNode
from .node_link import AbstractNodeLink

_Fact = TypeVar('_Fact', bound=AbstractFact)
_NodeLink = TypeVar('_NodeLink', bound=AbstractNodeLink)
_Node = TypeVar('_Node', bound=AbstractNode)

NodeOrId = Union[str, AbstractNode]


class TalismanDocument(metaclass=ABCMeta):
    __slots__ = ()

    @property
    @abstractmethod
    def id(self) -> str:
        """
        Document identifier.
        """
        pass

    # nodes methods

    @property
    @abstractmethod
    def id2node(self) -> Dict[str, AbstractNode]:
        """
        Get all document nodes.

        :return: mapping from node identifier to node
        """
        pass

    @property
    @abstractmethod
    def nodes(self) -> Dict[Type[AbstractNode], Iterable[AbstractNode]]:
        """
        Get all document nodes.

        :return: mapping from node type to nodes of corresponding type
        """
        pass

    @abstractmethod
    def get_node(self, id_: str) -> AbstractNode:
        """
        Get node by its identifier.
        If no such node contained in the document, ``KeyError`` will be raised.

        :param id_: node identifier
        :return: node
        """
        pass

    @abstractmethod
    def get_nodes(
            self, type_: Type[_Node] = AbstractNode, *,
            filter_: Union[Callable[[_Node], bool], Iterable[Callable[[_Node], bool]]] = tuple()
    ) -> Iterator[_Node]:
        """
        Get all nodes of specified type that satisfy the filter condition.

        :param type_: type of the desired nodes
        :param filter_: predicate to test each individual document node
        :return: iterator of the nodes
        """
        pass

    @abstractmethod
    def related_nodes(
            self, obj: Union[Identifiable, str], type_: Type[_Node] = AbstractNode, *,
            filter_: Union[Callable[[_Node], bool], Iterable[Callable[[_Node], bool]]] = tuple()
    ) -> Iterator[_Node]:
        """
        Get all nodes of specified type that depend on identifiable object (nodes, facts, etc.) and satisfy the filter condition.

        :param obj: identifier or identifiable object (only identifier matters) to filter nodes.
        :param type_: type of the desired nodes
        :param filter_: predicate to test each individual node
        :return: iterator of the nodes
        """
        pass

    @abstractmethod
    def with_nodes(self, nodes: Iterable[AbstractNode]) -> Self:
        """
        Create the same document with new nodes.
        This method replaces nodes already contained in the document if it is possible. Otherwise, ``ValueError`` is risen.
        Each node type declare a set of fields that couldn't be changed (see ``AbstractNode.constant_fields`` method).

        :param nodes: document nodes to be added/updated
        :return: document with nodes added
        """
        pass

    @abstractmethod
    def without_nodes(self, nodes: Iterable[NodeOrId], *, cascade: bool = True) -> Self:
        """
        Create the same document without specified nodes.
        Only identifiers are taken into account.
        In other words, if document contains ``ImageNode(..., id='123')``, and ``TextNode(..., id='123')`` is tried to be removed,
        ``ImageNode`` will be successfully removed without any warnings.
        All nodes not contained in the document are skipped silently.

        Enabling ``cascade`` flag leads to subsequently remove all document objects that depends on nodes to be removed
        (e.g. semantic links or mention facts).
        If no ``cascade`` flag is enabled, and some object depends on node to be removed, ``ValueError`` will be risen.

        :param nodes: iterable of `AbstractNode`s or node identifiers
        :param cascade: enable cascade removing (all objects associated with specified nodes will be removed too)
        :return: the same document without specified nodes and associated objects
        """
        pass

    # structure methods

    @property
    @abstractmethod
    def roots(self) -> Set[AbstractNode]:
        """
        Get set of nodes that have not parent nodes.
        This property is derived from document structure automatically.
        """
        pass

    @property
    @abstractmethod
    def main_root(self) -> Optional[AbstractNode]:
        """
        Get main root node.
        Main node should be set manually (via ``TalismanDocument.with_main_root`` method).
        """
        pass

    @abstractmethod
    def with_main_root(self, node: Optional[NodeOrId], *, update: bool = False) -> Self:
        """
        Create the same document with node set to be main root.
        Document without main root can't be properly serialized.
        Enabling ``update`` flag is the same as subsequent calls ``with_nodes([node]).with_main_root(node.id)``.

        :param node: node or node identifier to be set as main root
        :param update: flag to update node in the document (not valid for node identifier)
        :return: the same document with main root and optionally updated node
        """
        pass

    @abstractmethod
    def parent(self, node: NodeOrId) -> Optional[AbstractNode]:
        """
        Get parent node of the specified node (if exists)

        :param node: node or node id
        :return: direct parent node or None
        """
        pass

    @abstractmethod
    def child_nodes(self, node: Union[str, AbstractNode]) -> Tuple[AbstractNode, ...]:
        """
        Get children nodes for specified node

        :param node: node or node id
        :return: tuple of direct children nodes
        """
        pass

    @abstractmethod
    def with_structure(self, structure: Dict[NodeOrId, Iterable[NodeOrId]], *, force: bool = False, update: bool = False) -> Self:
        """
        Create the same document with updated structure.
        Structure is a mapping from node to iterable of children nodes.
        Each node could have the only parent node. If some node is marked as main root, it couldn't have any parent.
        Circular dependencies are not permitted.

        Enabling ``force`` flag leads to all conflict dependencies overwriting (except circular dependencies that couldn't be resolved
        automatically).
        If ``force`` is enabled, all conflict child->parent links presented in original document will be removed in result document.
        In any case structure mapping should not be self-conflicting.

        Enabling ``update`` flag leads to nodes replacement (or adding).

        :param structure: mapping from parent node (or identifier) to children nodes (or its identifiers)
        :param force: enable structure overwriting
        :param update: enable specified nodes updates
        :return: the same document with structure updated
        """
        pass

    @abstractmethod
    def with_node_parent(self, child: NodeOrId, parent: NodeOrId, *, force: bool = False, update: bool = False) -> Self:
        """
        Create the same document with updated structure.
        Child node is appended as last children of the parent node.
        Each node could have the only parent node.
        If some node is marked as main root, it couldn't have any parent.
        Circular dependencies are not permitted.

        Enabling ``force`` flag leads to child's parent overwriting.

        Enabling ``update`` flag leads to both parent and child nodes replacement (or adding).

        :param child: child node or node identifier
        :param parent: parent node or node identifier
        :param force: enable structure overwriting
        :param update: enable child and parent nodes updates
        :return: the same document with structure updated
        """
        pass

    @abstractmethod
    def with_roots(self, nodes: Iterable[NodeOrId], *, update: bool = False) -> Self:
        """
        Create the same document with updated structure.
        Removes parent links for specified nodes.

        :param nodes: nodes or node identifiers to be set as roots
        :param update: enable passed nodes to be updated
        :return: the same document with structure updated
        """
        pass

    # semantic link methods

    @property
    @abstractmethod
    def id2node_link(self) -> Dict[str, AbstractNodeLink]:
        """
        Get all document node semantic links

        :return: mapping from link identifier to link
        """
        pass

    @property
    @abstractmethod
    def node_links(self) -> Dict[Type[AbstractNodeLink], Iterable[AbstractNodeLink]]:
        """
        Get all document node semantic links

        :return: mapping from link type to iterable of corresponding type links
        """
        pass

    @abstractmethod
    def get_node_link(self, id_: str) -> AbstractNodeLink:
        """
        Get node link by its identifier.
        If no such link contained in the document, ``KeyError`` will be raised.

        :param id_: link identifier
        :return: semantic link
        """
        pass

    @abstractmethod
    def get_node_links(
            self, type_: Type[_NodeLink] = AbstractNodeLink, *,
            filter_: Union[Callable[[_NodeLink], bool], Iterable[Callable[[_NodeLink], bool]]] = tuple()
    ) -> Iterator[_NodeLink]:
        """
        Get all semantic links of specified type that satisfy the filter condition.

        :param type_: type of the desired links
        :param filter_: predicate to test each individual semantic link
        :return: iterator of the links
        """
        pass

    @abstractmethod
    def related_node_links(
            self, obj: Union[Identifiable, str], type_: Type[_NodeLink] = AbstractNodeLink, *,
            filter_: Union[Callable[[_NodeLink], bool], Iterable[Callable[[_NodeLink], bool]]] = tuple()
    ) -> Iterator[_NodeLink]:
        """
        Get all semantic links of specified type that depend on identifiable object (nodes, facts, etc.) and satisfy the filter condition.

        :param obj: identifier or identifiable object (only identifier matters) to filter semantic links
        :param type_: type of the desired links
        :param filter_: predicate to test each individual semantic link
        :return: iterator of the links
        """
        pass

    @abstractmethod
    def with_node_links(self, links: Iterable[AbstractNodeLink], *, update: bool = False) -> Self:
        """
        Create the same document with new node semantic links.
        This method replaces links already contained in the document if it is possible. Otherwise, ``ValueError`` is risen.
        Each semantic link type declare a set of fields that couldn't be changed (see AbstractNodeLink.constant_fields method).

        Enabling ``update`` flag leads to adding or updating all the objects, stored in specified links (e.g. nodes).

        :param links: document node semantic links to be added/updated
        :param update: add or update all identifiable objects contained in specified node semantic links
        :return: document with node semantic links added
        """
        pass

    @abstractmethod
    def without_node_links(self, links: Iterable[Union[str, AbstractNodeLink]], *, cascade: bool = False) -> Self:
        """
        Create the same document without specified node semantic links.
        Only identifiers are taken into account.
        In other words, if document contains ``EquivalenceNodeLink(..., id='123')``, and ``TranslationNodeLink(..., id='123')``
        is tried to be removed, ``EquivalenceNodeLink`` will be successfully removed without any warnings.
        All links not contained in the document are skipped silently.

        Enabling ``cascade`` flag leads to subsequently remove all document objects that depends on links to be removed.
        If no ``cascade`` flag is enabled, and some object depends on link to be removed, ``ValueError`` will be risen.

        :param links: iterable of ``AbstractNodeLink`` or link identifiers
        :param cascade: enable cascade removing (all objects associated with specified links will be removed too)
        :return: the same document without specified links and associated objects
        """
        pass

    # facts methods

    @property
    @abstractmethod
    def id2fact(self) -> Dict[str, AbstractFact]:
        """
        Get all document facts

        :return: mapping from fact identifier to fact
        """
        pass

    @property
    @abstractmethod
    def facts(self) -> Dict[Type[AbstractFact], Iterable[AbstractFact]]:
        """
        Get all document facts

        :return: mapping from fact type to iterable of corresponding type facts
        """
        pass

    @abstractmethod
    def get_fact(self, id_: str) -> AbstractFact:
        """
        Get fact by its identifier. If no such fact contained in the document, ``KeyError`` will be raised.

        :param id_: fact identifier
        :return: fact
        """
        pass

    @abstractmethod
    def get_facts(
            self, type_: Type[_Fact] = AbstractFact, *,
            filter_: Union[Callable[[_Fact], bool], Iterable[Callable[[_Fact], bool]]] = tuple()
    ) -> Iterator[_Fact]:
        """
        Get all facts of specified type that satisfy the filter condition.

        :param type_: type of the desired facts
        :param filter_: predicate to test each individual fact
        :return: iterator of the facts
        """
        pass

    @abstractmethod
    def related_facts(
            self, obj: Union[Identifiable, str], type_: Type[_Fact] = AbstractFact, *,
            filter_: Union[Callable[[_Fact], bool], Iterable[Callable[[_Fact], bool]]] = tuple()
    ) -> Iterator[_Fact]:
        """
        Get all facts of specified type that depend on identifiable object (nodes, facts, etc.) and satisfy the filter condition.

        :param obj: identifier or identifiable object (only identifier matters) to filter facts
        :param type_: type of the desired facts
        :param filter_: predicate to test each individual fact
        :return: iterator of the facts
        """
        pass

    @abstractmethod
    def with_facts(self, facts: Iterable[AbstractFact], *, update: bool = False) -> Self:
        """
        Create the same document with new facts.
        This method replaces facts already contained in the document if it is possible. Otherwise, ``ValueError`` is risen.
        Each fact type declare a set of fields that couldn't be changed (see ``AbstractFact.constant_fields method``).

        Enabling ``update`` flag leads to adding or updating all the objects, stored in specified facts (e.g. other facts, nodes).

        :param facts: document facts to be added/updated
        :param update: add or update all identifiable objects contained in specified facts
        :return: document with facts added
        """
        pass

    @abstractmethod
    def without_facts(self, facts: Iterable[Union[str, AbstractFact]], *, cascade: bool = False) -> Self:
        """
        Create the same document without specified facts.
        Only identifiers are taken into account.
        In other words, if document contains ``ConceptFact(..., id='123')``, and ``PropertyFact(..., id='123')`` is tried to be removed,
        ``ConceptFact`` will be successfully removed without any warnings.
        All links not contained in the document are skipped silently.

        Enabling ``cascade`` flag leads to subsequently remove all document objects that depends on facts to be removed.
        If no ``cascade`` flag is enabled, and some object depends on fact to be removed, ``ValueError`` will be risen.

        :param facts: iterable of ``AbstractFact`` or fact identifiers
        :param cascade: enable cascade removing (all objects associated with specified facts will be removed too)
        :return: the same document without specified facts and associated objects
        """
        pass


class AbstractDocumentFactory(metaclass=ABCMeta):
    @abstractmethod
    def create_document(self, *, id_: Optional[str] = None, doc_type: Optional[str] = None) -> TalismanDocument:
        """
        create empty document with specified identifier.
        If no identifier specified, it will be generated automatically.

        If doc_type is present, document fact will be added to the document.

        :param id_: new document identifier
        :param doc_type: document type identifier
        :return: empty document
        """
        pass
