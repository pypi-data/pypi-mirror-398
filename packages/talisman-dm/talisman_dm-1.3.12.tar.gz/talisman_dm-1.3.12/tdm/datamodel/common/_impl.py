from abc import abstractmethod
from collections import defaultdict, deque
from itertools import chain
from operator import itemgetter
from typing import Callable, Dict, Hashable, Iterable, Iterator, List, Optional, Set, Tuple, Type, TypeVar, Union

from typing_extensions import Self

from tdm.abstract.datamodel import AbstractFact, EnsureIdentifiable, Identifiable, and_filter
from tdm.abstract.datamodel.duplicatable import Duplicatable
from tdm.helper import unfold_union
from ._container import TypedIdsContainer
from ._state import pack_view_state, unpack_view_state
from ._types import get_base_type
from ._util import LazyUpdatingDict
from ._view import AbstractView, object_view, restore_object

_I = TypeVar('_I', bound=Identifiable)
_Base = TypeVar('_Base', bound=EnsureIdentifiable)


class ViewContainer(object):
    __slots__ = (
        '_id2view', '_dependencies', '_containers', '_hash2ids', '_id2hash', '_duplicate2id', '_id2duplicates', '_duplicates_object_cache'
    )

    def __setstate__(self, state):
        d, s = state
        if d is not None:
            self.__dict__.update(d)
        s['_id2view'] = unpack_view_state(s['_id2view'])
        for component in chain.from_iterable(getattr(cls, '__slots__', ()) for cls in type(self).mro()):
            setattr(self, component, s.get(component, None))

    def __getstate__(self):
        result = {component: getattr(self, component, None) for component in
                  chain.from_iterable(getattr(cls, '__slots__', ()) for cls in type(self).mro())}
        result['_id2view'] = pack_view_state(result.get('_id2view', {}))
        d = self.__dict__ if hasattr(self, '__dict__') else None
        return d, result

    def __init__(
            self,
            id2view: Dict[str, Union[EnsureIdentifiable, AbstractView]],
            dependencies: Dict[str, Set[Tuple[str, Type[EnsureIdentifiable]]]],
            containers: Dict[Type[EnsureIdentifiable], TypedIdsContainer],
            hash2ids: Dict[Hashable, Set[str]],
            id2hash: Dict[str, Hashable],
            duplicate2id: Dict[str, str],
            id2duplicates: Dict[str, Set[str]]
    ):
        self._id2view = id2view
        self._dependencies = dependencies
        self._containers = containers
        self._hash2ids = hash2ids
        self._id2hash = id2hash
        self._duplicate2id = duplicate2id
        self._id2duplicates = id2duplicates
        self._duplicates_object_cache = dict()

    def _replace(self, **kwargs) -> Self:
        return type(self)(
            **{
                'id2view': self._id2view,
                'dependencies': self._dependencies,
                'containers': self._containers,
                'hash2ids': self._hash2ids,
                'id2hash': self._id2hash,
                'duplicate2id': self._duplicate2id,
                'id2duplicates': self._id2duplicates,
                **kwargs
            }
        )

    def id2element(self, base_type: Type[_Base]) -> Dict[str, _Base]:
        return {i: restore_object(self._id2view[self._duplicate2id.get(i, i)], self._id2view) for i, _ in self._containers[base_type]}

    def elements(self, base_type: Type[_Base]) -> Dict[Type[_Base], Iterable[_Base]]:
        return {
            t: {restore_object(self._id2view[i], self._id2view) for i in ids}
            for t, ids in self._containers[base_type].type2ids.items()
        }

    def get_element(self, base_type: Type[EnsureIdentifiable], id_: str) -> _I:
        while id_ in self._duplicate2id:
            id_ = self._duplicate2id[id_]
        if id_ not in self._containers[base_type]:
            raise KeyError(f"ID `{id_}` not found in containers for base type {base_type.__name__} in {repr(self)}")
        return restore_object(self._id2view[id_], self._id2view)

    def get_elements(
            self, base_type: Type[EnsureIdentifiable], type_: Type[_I],
            filter_: Union[Callable[[_I], bool], Iterable[Callable[[_I], bool]]]
    ) -> Iterator[_I]:
        if isinstance(filter_, Iterable):
            filter_ = and_filter(*filter_)

        type_ = unfold_union(type_)
        if not all(issubclass(t, base_type) for t in type_):
            raise ValueError(f"All types must be subclasses of {base_type.__name__} in {repr(self)}, but got {type_}")

        for t, ids in self._containers[base_type].type2ids.items():
            if not issubclass(t, type_):
                continue
            yield from filter(filter_, (restore_object(self._id2view[id_], self._id2view) for id_ in ids))

    def related_elements(
            self, base_type: Type[EnsureIdentifiable], obj: Union[Identifiable, str], type_: Type[_I],
            filter_: Union[Callable[[_I], bool], Iterable[Callable[[_I], bool]]]
    ) -> Iterator[_I]:
        if isinstance(obj, Identifiable):
            obj = obj.id
        if not isinstance(obj, str):
            raise ValueError(f"obj must be Identifiable or str type in {repr(self)}, but got {repr(obj)} with type {type(obj).__name__}")

        if isinstance(filter_, Iterable):
            filter_ = and_filter(*filter_)

        type_ = unfold_union(type_)
        if not all(issubclass(t, base_type) for t in type_):
            raise ValueError(f"All types in {repr(self)} must be subclasses of {base_type.__name__}, but got {type_}")

        for element_id, element_type in self._dependencies.get(obj, tuple()):
            if not issubclass(element_type, base_type):
                continue
            view = self._id2view[element_id]
            if not issubclass(view.orig_type(), type_):
                continue
            fact = restore_object(view, self._id2view)
            if filter_(fact):
                yield fact

    def _check_duplicate(self, element, hash2ids, id2hash, id2view, dependencies) -> Optional[Tuple[str, str]]:
        element_hash = id2hash[element.id]
        for candidate_id in hash2ids.iterate(element_hash):
            if candidate_id == element.id:
                continue

            def cacheable_restore_object(object_id):
                if object_id in self._duplicates_object_cache:
                    obj = self._duplicates_object_cache[object_id]
                else:
                    obj = restore_object(id2view[object_id], id2view)
                    self._duplicates_object_cache[object_id] = obj
                return obj

            candidate = cacheable_restore_object(candidate_id)

            duplicate = element.choose_one(
                candidate,
                lambda i: id2hash[i],
                lambda i: map(itemgetter(0), dependencies.iterate(i)),
                cacheable_restore_object
            )
            if duplicate is not None:
                self._duplicates_object_cache = dict()  # drop cache
                return duplicate
        return None

    def with_elements(self, elements: Iterable[EnsureIdentifiable], *, update: bool = False) -> Self:
        containers: Dict[Type[EnsureIdentifiable], TypedIdsContainer] = dict(self._containers)
        id2view = dict(self._id2view)

        id2hash = dict(self._id2hash)
        hash2ids = LazyUpdatingDict(self._hash2ids)

        duplicate2id = dict(self._duplicate2id)
        id2duplicates = LazyUpdatingDict(self._id2duplicates)

        dependencies = LazyUpdatingDict(self._dependencies)

        possible_duplicates: Set[Duplicatable] = set()

        elements = self._order_dependencies(set(elements), update)
        prunable: List[PrunableMixin] = []

        for element_type, element, element_view in elements:
            assert isinstance(element_view, AbstractView)
            if element.id in duplicate2id:  # actually this element should silently overwrite duplicated identifier
                id_ = duplicate2id.pop(element.id)
                id2duplicates.remove(id_, element.id)
            if isinstance(element, PrunableMixin):
                prunable.append(element)
            container = containers[element_type]
            if element.id in container:
                # remove element from duplicate hash store. it should be rehashed as some features could be changed
                if isinstance(element, Duplicatable):
                    h = id2hash.pop(element.id)
                    hash2ids.remove(h, element.id)
                try:
                    id2view[element.id].validate_update(element_view)
                except ValueError as e:
                    raise ValueError(f"Couldn't update element {element} in {repr(self)}") from e
            elif element.id in id2view:
                raise ValueError(f"Element {element} identifiers collision: document ({repr(self)}) already "
                                 f"contains {id2view[element.id].orig_type()} with same id")

            if isinstance(element, Duplicatable):
                element_hash = element.duplicate_hash()
                if element_hash in hash2ids:  # there are some similar objects
                    possible_duplicates.add(element)
                id2hash[element.id] = element_hash
                hash2ids.add(element_hash, element.id)
                if isinstance(element_view, AbstractView):
                    for dep_id in element_view.__depends_on__:
                        if dep_id not in id2hash:
                            continue
                        dep_hash = id2hash[dep_id]
                        if hash2ids.len(dep_hash) > 1:
                            possible_duplicates.add(restore_object(id2view[dep_id], id2view))

            if isinstance(element_view, AbstractView):
                for dep in element_view.__depends_on__:
                    dependencies.add(dep, (element.id, element_type))
            id2view[element.id] = element_view
            containers[element_type] = containers[element_type].with_ids([(element.id, type(element))])

        # now lets try to resolve duplicates
        while possible_duplicates:
            next_turn = set()
            for element in possible_duplicates:
                if element.id not in id2hash:
                    continue  # already removed
                duplicate = self._check_duplicate(element, hash2ids, id2hash, id2view, dependencies)
                if duplicate is None:
                    continue
                actual_id, obsolete_id = duplicate
                duplicate2id[obsolete_id] = actual_id
                id2duplicates.add(actual_id, obsolete_id)
                # cleanup obsolete element
                # - remove it view
                obsolete_view = id2view.pop(obsolete_id)  # remove view
                base_type = get_base_type(obsolete_view.orig_type())
                # - remove dependencies reverse links
                for dep in obsolete_view.__depends_on__:
                    dependencies.remove(dep, (obsolete_id, base_type))
                for dep_id, bt in dependencies.iterate(obsolete_id):
                    # get elements that depends on duplicate to force update dependencies
                    obj = restore_object(id2view[dep_id].substitute_id(obsolete_id, actual_id), id2view)
                    updated_view = object_view(obj)
                    id2view[dep_id] = updated_view
                    dependencies.add(actual_id, (dep_id, bt))
                    if dep_id in id2hash:  # rehash duplicatable dependencies
                        dep_hash = id2hash[dep_id]
                        hash2ids.remove(dep_hash, dep_id)
                        obj_hash = obj.duplicate_hash()
                        id2hash[dep_id] = obj_hash
                        hash2ids.add(obj_hash, dep_id)
                        next_turn.add(obj)
                        for second_dep in updated_view.__depends_on__:
                            # we should check nodes after links. when values merge, value <- property -> concept should be checked
                            if second_dep != actual_id:  # no need to check same object once again
                                next_turn.add(restore_object(id2view[second_dep], id2view))
                # remove from identifier container
                containers[base_type] = containers[base_type].without_ids([obsolete_id])
                # remove from hash store
                obsolete_hash = id2hash.pop(obsolete_id)
                hash2ids.remove(obsolete_hash, obsolete_id)
            possible_duplicates = next_turn

        res = self._replace(
            id2view=id2view or self._id2view,
            dependencies=dependencies.extract_data(),
            containers=containers or self._containers,
            id2hash=id2hash or self._id2hash,
            hash2ids=hash2ids.extract_data(),
            id2duplicates=id2duplicates.extract_data(),
            duplicate2id=duplicate2id
        )

        pruned = False
        while not pruned:
            res, prunable, pruned = self.prune(res, prunable)

        return res

    @staticmethod
    def prune(res: 'ViewContainer', facts: Iterable['PrunableMixin']) -> Tuple['ViewContainer', Iterable['PrunableMixin'], bool]:
        hanging_ids = set()
        non_pruned_facts = []
        try:
            for element in facts:
                if isinstance(element, PrunableMixin) and (element.is_hanging(res)):
                    hanging_ids.add(element.id)
                else:
                    non_pruned_facts.append(element)
        except KeyError:  # some documents do not have AbstractFact in their .containers at all
            return res, [], True

        if hanging_ids:
            return res.without_elements(hanging_ids, cascade=True), non_pruned_facts, False
        return res, [], True

    def without_elements(self, ids: Iterable[str], *, cascade: bool = False) -> Self:
        ids = set(self._id2view.keys()).intersection(map(_to_id, ids))  # ignore excess ids
        if not cascade:
            # check no hang links
            for id_ in ids:
                for dep, _ in self._dependencies.get(id_, ()):
                    if dep not in ids:
                        raise ValueError(f"Couldn't remove element {id_} from {repr(self)} as it depends on element {dep}")
        remove_from_containers = defaultdict(set)
        id2view = dict(self._id2view)

        id2hash = dict(self._id2hash)
        hash2ids = LazyUpdatingDict(self._hash2ids)

        duplicate2id = dict(self._duplicate2id)
        id2duplicates = LazyUpdatingDict(self._id2duplicates)

        dependencies = LazyUpdatingDict(self._dependencies)

        remove = defaultdict(set)
        removed_ids = set()

        recheck_ids = set()

        for id_ in ids:
            remove[get_base_type(id2view[id_].orig_type())].add(id_)
            for i in id2duplicates.iterate(id_):
                duplicate2id.pop(i, None)
            id2duplicates.pop(id_)
        while remove:
            to_remove = defaultdict(set)
            for base_type, ids in remove.items():
                for id_ in ids:
                    if id_ in removed_ids:
                        continue
                    removed_ids.add(id_)
                    for dep_id, dep_type in dependencies.iterate(id_):
                        to_remove[dep_type].add(dep_id)
                    view = id2view.pop(id_)
                    if issubclass(view.orig_type(), Duplicatable):
                        # remove element from duplicate hash store
                        duplicate_hash = id2hash.pop(id_)
                        hash2ids.remove(duplicate_hash, id_)
                    dependencies.pop(id_)
                    remove_from_containers[base_type].add(id_)
                    if not isinstance(view, AbstractView):
                        continue
                    for dep in view.__depends_on__:
                        if dep in id2hash:  # it is duplicable
                            recheck_ids.add(dep)
                        if dep in dependencies:
                            dependencies.remove(dep, (id_, base_type))

            remove = to_remove

        containers = dict(self._containers)
        for base_type, ids in remove_from_containers.items():
            containers[base_type] = containers[base_type].without_ids(ids)

        res = self._replace(
            id2view=id2view,
            dependencies=dependencies.extract_data(),
            containers=containers,
            id2hash=id2hash,
            hash2ids=hash2ids.extract_data()
        )

        pruned = False
        facts = list(chain(*(res.elements(AbstractFact).values())))
        while not pruned:
            res, facts, pruned = self.prune(res, facts)

        # FIXME: extremely inefficient solution. We should check duplicates without useless elements updating
        recheck_duplicates = {
            restore_object(res._id2view[id_], res._id2view) for id_ in recheck_ids if id_ in res._id2view
        }
        if recheck_duplicates:
            return res.with_elements(recheck_duplicates)
        return res

    def _order_dependencies(
            self, elements: Set[EnsureIdentifiable], update: bool = False
    ) -> Iterable[Tuple[Type[EnsureIdentifiable], EnsureIdentifiable, AbstractView]]:
        visited = set()
        id2data: Dict[str, Tuple[Type[EnsureIdentifiable], EnsureIdentifiable, AbstractView]] = {}
        graph: Dict[str, List[str]] = defaultdict(list)
        in_degree: Dict[str, int] = defaultdict(int)

        # build dependency graph
        while elements:
            to_process = set()
            for element in map(self._transform_element, elements):
                visited.add(element)
                view = object_view(element)
                id2data[element.id] = (get_base_type(element), element, view)

                if not isinstance(view, AbstractView):
                    continue  # no dependencies

                dependencies = view.get_dependencies(element)
                if update:
                    for dependency in dependencies:
                        graph[dependency.id].append(element.id)
                        in_degree[element.id] += 1
                dependencies.difference_update(elements)
                dependencies.difference_update(visited)
                if update:
                    to_process.update(dependencies)
                else:
                    self._validate_elements(dependencies)
            elements = to_process

        queue = deque(e.id for e in visited if in_degree[e.id] == 0)
        result = []
        while queue:
            element_id = queue.popleft()
            result.append(id2data[element_id])

            for dep_id in graph[element_id]:
                in_degree[dep_id] -= 1
                if in_degree[dep_id] == 0:
                    queue.append(dep_id)

        return result

    def _transform_element(self, element: _Base) -> _Base:
        return element

    def _validate_elements(self, elements: Set[EnsureIdentifiable]) -> None:
        for element in elements:
            if element.id not in self._id2view:
                raise ValueError(f"Document ({repr(self)}) contains no {element}")
            view = self._id2view[element.id]
            element_type = type(element)
            view_type = view.orig_type() if isinstance(view, AbstractView) else type(view)
            if not issubclass(element_type, view_type) or not issubclass(view_type, element_type):
                raise ValueError(f"Type mismatch for {element} in {repr(self)}. Expected: {view_type}, actual: {element_type}")


def _to_id(obj: Union[str, EnsureIdentifiable]) -> str:
    return obj if isinstance(obj, str) else obj.id


class PrunableMixin:
    @abstractmethod
    def is_hanging(self, doc: ViewContainer) -> bool:
        pass
