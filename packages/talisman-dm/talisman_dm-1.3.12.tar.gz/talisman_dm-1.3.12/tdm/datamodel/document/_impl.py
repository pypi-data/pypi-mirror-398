import inspect
from functools import wraps
from typing import Any, Callable, Dict, Hashable, Iterable, Iterator, Optional, Set, Tuple, Type, TypeVar, Union

from typing_extensions import ParamSpec, Self

from tdm.abstract.datamodel import AbstractDomain, AbstractFact, AbstractNode, AbstractNodeLink, EnsureIdentifiable, \
    Identifiable, TalismanDocument
from tdm.datamodel.common import AbstractView, TypedIdsContainer, ViewContainer, restore_object
from ._structure import NodesStructure

_D = TypeVar('_D', bound=EnsureIdentifiable)

_Node = TypeVar('_Node', bound=AbstractNode)
_NodeLink = TypeVar('_NodeLink', bound=AbstractNodeLink)
_Fact = TypeVar('_Fact', bound=AbstractFact)

_I = TypeVar('_I', bound=Identifiable)

_P = ParamSpec('_P')


def _filter_elements(base_type: Type[_D]):
    def decorator(f: Callable[_P, 'TalismanDocumentImpl']) -> Callable[_P, 'TalismanDocumentImpl']:
        signature = inspect.signature(f)
        target_parameter = tuple(signature.parameters)[1]

        @wraps(f)
        def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> 'TalismanDocumentImpl':
            arguments = signature.bind(*args, **kwargs).arguments
            self = arguments['self']
            arguments[target_parameter] = _filter(self._containers[base_type], self._id2view, arguments[target_parameter], base_type)
            return f(**arguments)

        return wrapper

    return decorator


class TalismanDocumentImpl(TalismanDocument, ViewContainer):
    __slots__ = (
        '_id', '_domain', '_structure'
    )

    def __init__(
            self,
            id2view: Dict[str, Union[EnsureIdentifiable, AbstractView]],
            dependencies: Dict[str, Set[Tuple[str, Type[EnsureIdentifiable]]]],
            containers: Dict[Type[EnsureIdentifiable], TypedIdsContainer],
            hash2ids: Optional[Dict[Hashable, str]],
            id2hash: Optional[Dict[str, Hashable]],
            duplicate2id: Dict[str, str],
            id2duplicates: Dict[str, Set[str]],
            structure: NodesStructure,
            *, id_: str, domain: Optional[AbstractDomain] = None,

    ):
        super().__init__(id2view, dependencies, containers, hash2ids, id2hash, duplicate2id, id2duplicates)
        self._id = id_
        self._domain = domain
        self._structure = structure

    def _replace(self, **kwargs) -> Self:
        return super()._replace(
            **{
                'structure': self._structure,
                'id_': self._id,
                'domain': self._domain,
                **kwargs
            }
        )

    def _update_structure(self, other: ViewContainer) -> Self:
        if not isinstance(other, TalismanDocumentImpl):
            raise ValueError(f"Cannot update structure of document {repr(self)} with structure of {repr(other)}")
        if other._containers[AbstractNode] is not self._containers[AbstractNode]:  # something has changed
            other._structure = self._structure.update_nodes(other._containers[AbstractNode].ids)
        return other

    def __repr__(self) -> str:
        return f'{type(self).__name__}[{self.id}]'

    def with_elements(self, elements: Iterable[EnsureIdentifiable], *, update: bool = False) -> Self:
        return self._update_structure(super().with_elements(elements, update=update))

    def without_elements(self, ids: Iterable[str], *, cascade: bool = False) -> Self:
        return self._update_structure(super().without_elements(ids, cascade=cascade))

    def _transform_element(self, element: _D) -> _D:
        if self._domain is not None and isinstance(element, AbstractFact):
            return element.replace_with_domain(self._domain)
        return element

    @property
    def id(self) -> str:
        return self._id

    @property
    def id2node(self) -> Dict[str, AbstractNode]:
        return self.id2element(AbstractNode)

    @property
    def nodes(self) -> Dict[Type[AbstractNode], Iterable[AbstractNode]]:
        return self.elements(AbstractNode)

    def get_node(self, id_: str) -> AbstractNode:
        return self.get_element(AbstractNode, id_)

    def get_nodes(
            self, type_: Type[_Node] = AbstractNode, *,
            filter_: Union[Callable[[_Node], bool], Iterable[Callable[[_Node], bool]]] = tuple()
    ) -> Iterator[_Node]:
        return self.get_elements(AbstractNode, type_, filter_=filter_)

    def related_nodes(
            self, obj: Union[Identifiable, str], type_: Type[_Node] = AbstractNode, *,
            filter_: Union[Callable[[_Node], bool], Iterable[Callable[[_Node], bool]]] = tuple()
    ) -> Iterator[_Node]:
        return self.related_elements(AbstractNode, obj, type_, filter_=filter_)

    @_filter_elements(AbstractNode)
    def with_nodes(self, nodes: Iterable[AbstractNode]) -> Self:
        return self.with_elements(nodes, update=True)

    @_filter_elements(AbstractNode)
    def without_nodes(self, nodes: Iterable[Union[str, AbstractNode]], *, cascade: bool = False) -> Self:
        return self.without_elements(nodes, cascade=cascade)

    # structure methods

    @property
    def roots(self) -> Set[AbstractNode]:
        return {restore_object(self._id2view[id_], self._id2view) for id_ in self._structure.roots}

    @property
    def main_root(self) -> Optional[AbstractNode]:
        main_root = self._structure.main_root
        return restore_object(self._id2view[main_root], self._id2view) if main_root is not None else None

    def with_main_root(self, node: Optional[Union[str, AbstractNode]], *, update: bool = False) -> Self:
        if node is None:
            return self._replace(structure=self._structure.with_main_root(None))
        if update:
            if not isinstance(node, AbstractNode):
                raise ValueError(f"Could not update node {node} in {repr(self)} with id only")
            result = self.with_nodes((node,))
            result._structure = result._structure.with_main_root(node.id)
            return result
        return self._replace(structure=self._structure.with_main_root(_to_id(node)))

    def parent(self, node: Union[str, AbstractNode]) -> Optional[AbstractNode]:
        node_id = _to_id(node)
        parent_id = self._structure.parent.get(node_id)
        if parent_id is not None:
            return restore_object(self._id2view[parent_id], self._id2view)
        return None

    def child_nodes(self, node: Union[str, AbstractNode]) -> Tuple[AbstractNode, ...]:
        return tuple(restore_object(self._id2view[id_], self._id2view) for id_ in self._structure.children.get(_to_id(node), ()))

    def with_structure(
            self, structure: Dict[Union[str, AbstractNode], Iterable[Union[str, AbstractNode]]],
            *, force: bool = False, update: bool = False
    ) -> Self:
        _structure = {}
        nodes = set()

        for parent, children in structure.items():
            children = list(children)
            if update:
                if isinstance(parent, AbstractNode):
                    nodes.add(parent)
                nodes.update(node for node in children if isinstance(node, AbstractNode))
            _structure[_to_id(parent)] = [_to_id(node) for node in children]

        result = self
        if update:
            result = self.with_nodes(nodes)

        return result._replace(structure=result._structure.with_children(_structure, force=force))

    def with_node_parent(
            self, child: Union[str, AbstractNode], parent: Union[str, AbstractNode],
            *, force: bool = False, update: bool = False
    ) -> Self:
        result = self

        if update:
            nodes = {node for node in (child, parent) if isinstance(node, AbstractNode)}
            result = result.with_nodes(nodes)

        return result._replace(structure=result._structure.with_parent(_to_id(parent), _to_id(child), force=force))

    def with_roots(self, nodes: Iterable[Union[str, AbstractNode]], *, update: bool = False) -> Self:
        result = self

        if update:
            nodes = tuple(nodes)
            result = result.with_nodes({node for node in nodes if isinstance(node, AbstractNode)})

        return result._replace(structure=self._structure.as_roots(map(_to_id, nodes)))

    # semantic link methods

    @property
    def id2node_link(self) -> Dict[str, AbstractNodeLink]:
        return self.id2element(AbstractNodeLink)

    @property
    def node_links(self) -> Dict[Type[AbstractNodeLink], Iterable[AbstractNodeLink]]:
        return self.elements(AbstractNodeLink)

    def get_node_link(self, id_: str) -> AbstractNodeLink:
        return self.get_element(AbstractNodeLink, id_)

    def get_node_links(
            self, type_: Type[_NodeLink] = AbstractNodeLink, *,
            filter_: Union[Callable[[_NodeLink], bool], Iterable[Callable[[_NodeLink], bool]]] = tuple()
    ) -> Iterator[_NodeLink]:
        return self.get_elements(AbstractNodeLink, type_, filter_=filter_)

    def related_node_links(
            self, obj: Union[Identifiable, str], type_: Type[_NodeLink] = AbstractNodeLink, *,
            filter_: Union[Callable[[_NodeLink], bool], Iterable[Callable[[_NodeLink], bool]]] = tuple()
    ) -> Iterator[_NodeLink]:
        return self.related_elements(AbstractNodeLink, obj, type_, filter_=filter_)

    @_filter_elements(AbstractNodeLink)
    def with_node_links(self, links: Iterable[AbstractNodeLink], *, update: bool = False) -> Self:
        return self.with_elements(links, update=update)

    @_filter_elements(AbstractNodeLink)
    def without_node_links(self, links: Iterable[Union[str, AbstractNodeLink]], *, cascade: bool = False) -> Self:
        return self.without_elements(map(_to_id, links), cascade=cascade)

    # facts methods

    @property
    def id2fact(self) -> Dict[str, AbstractFact]:
        return self.id2element(AbstractFact)

    @property
    def facts(self) -> Dict[Type[AbstractFact], Iterable[AbstractFact]]:
        return self.elements(AbstractFact)

    def get_fact(self, id_: str) -> AbstractFact:
        return self.get_element(AbstractFact, id_)

    def get_facts(
            self, type_: Type[_Fact] = AbstractFact, *,
            filter_: Union[Callable[[_Fact], bool], Iterable[Callable[[_Fact], bool]]] = tuple()
    ) -> Iterator[_Fact]:
        return self.get_elements(AbstractFact, type_, filter_=filter_)

    def related_facts(
            self, obj: Union[Identifiable, str], type_: Type[_Fact] = AbstractFact, *,
            filter_: Union[Callable[[_Fact], bool], Iterable[Callable[[_Fact], bool]]] = tuple()
    ) -> Iterator[_Fact]:
        return self.related_elements(AbstractFact, obj, type_, filter_=filter_)

    @_filter_elements(AbstractFact)
    def with_facts(self, facts: Iterable[AbstractFact], *, update: bool = False) -> Self:
        return self.with_elements(facts, update=update)

    @_filter_elements(AbstractFact)
    def without_facts(self, facts: Iterable[Union[str, AbstractFact]], *, cascade: bool = False) -> Self:
        return self.without_elements(map(_to_id, facts), cascade=cascade)

    def __hash__(self):
        return hash((self._id, self._containers[AbstractNode], self._containers[AbstractFact]))

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, TalismanDocumentImpl):
            return NotImplemented
        return self._id == o._id and self._id2view == o._id2view and self._containers == o._containers and \
            self._structure == o._structure


def _to_id(obj: Union[str, EnsureIdentifiable]) -> str:
    return obj if isinstance(obj, str) else obj.id


def _filter(
        container: TypedIdsContainer[_D], known_ids: Dict[str, Any], elements: Iterable[Union[str, _D]], base_type: Type[_D]
) -> Iterator[Union[str, _D]]:
    for element in elements:
        if isinstance(element, str):
            if element in known_ids and element not in container:
                raise ValueError(f'Unexpected type for element {element}. Expected: {base_type}')
        else:
            if not isinstance(element, base_type):
                raise ValueError(f'Unexpected type for element {element}. Expected: {base_type}')
            if element.id in known_ids and element.id not in container:
                raise ValueError(f'Identifier collision for {element}')
        yield element
