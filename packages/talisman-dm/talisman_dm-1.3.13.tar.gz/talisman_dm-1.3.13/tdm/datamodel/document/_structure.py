from dataclasses import dataclass, field, replace
from typing import Dict, Iterable, List, Optional, Set


@dataclass(frozen=True)
class NodesStructure(object):
    nodes: Set[str] = field(default_factory=set)
    roots: Set[str] = field(default_factory=set)
    children: Dict[str, List[str]] = field(default_factory=dict)
    parent: Dict[str, str] = field(default_factory=dict)
    main_root: Optional[str] = None

    def with_nodes(self, nodes: Set[str]) -> 'NodesStructure':
        if not nodes:
            return self
        new_nodes = nodes.difference(self.nodes)
        roots = self.roots.union(new_nodes)
        return replace(self, nodes=self.nodes.union(new_nodes), roots=roots)

    def remove_ids(self, ids: Set[str]) -> 'NodesStructure':
        if not ids:
            return self
        ids = ids.intersection(self.nodes)  # ignore excess ids
        nodes = self.nodes.difference(ids)
        roots = self.roots.difference(ids)
        parent = dict(self.parent)
        children = dict(self.children)
        main_root = None if self.main_root in ids else self.main_root
        updated = set()
        for id_ in ids:
            parent_id = parent.pop(id_, None)
            if parent_id is not None:
                _copy_if_not_updated(children, parent_id, updated).remove(id_)
            for child_id in children.pop(id_, ()):
                parent.pop(child_id)
                roots.add(child_id)
        return NodesStructure(nodes, roots, _prune(children, updated), parent, main_root)

    def update_nodes(self, nodes: Set[str]) -> 'NodesStructure':
        removed = self.nodes.difference(nodes)
        added = nodes.difference(self.nodes)
        return self.remove_ids(removed).with_nodes(added)

    def with_main_root(self, main_root: Optional[str]) -> 'NodesStructure':
        if main_root is None or main_root in self.roots:
            return replace(self, main_root=main_root)
        raise ValueError(f"Node {main_root} is not one of the roots")

    def with_children(self, links: Dict[str, Iterable[str]], *, force: bool = False) -> 'NodesStructure':
        roots: Set[str] = set(self.roots)
        parents: Dict[str, str] = dict(self.parent)  # child -> parent
        children: Dict[str, List[str]] = dict(self.children)  # parent -> [child]
        updated: Set[str] = set()
        seed: Set[str] = set()  # added parents to control loops in graph

        for parent_id, children_ids in links.items():
            if parent_id not in self.nodes:
                raise ValueError(f"Node {parent_id} not contained in the document")
            children_ids = list(children_ids)
            for child_id in children_ids:
                if child_id not in self.nodes:
                    raise ValueError(f"Node {child_id} not contained in the document")
            roots.difference_update(children_ids)

            if not force:
                # check if some node has another parent
                for child_id in set(children_ids).intersection(parents):
                    if parents[child_id] != parent_id:
                        raise ValueError(f"Couldn't link {child_id} with {parent_id} as it already linked with {parents[child_id]}")

            # update children collection
            old_children = _copy_if_not_updated(children, parent_id, updated)
            intersection = set(old_children).intersection(children_ids)
            if force:
                # remove intersecting ids from old collection
                for child_id in intersection:
                    old_children.remove(child_id)
            else:
                # remove intersecting ids from new collection
                children_ids = [child_id for child_id in children_ids if child_id not in intersection]
            old_children.extend(children_ids)

            # update parents collection
            for child_id in children_ids:
                old_parent = parents.get(child_id)
                if old_parent is not None:  # child had parent, so we should remove link from parent collection
                    if old_parent == parent_id:
                        continue
                    _copy_if_not_updated(children, old_parent, updated).remove(child_id)
                parents[child_id] = parent_id
                seed.add(child_id)

        _check_circle(parents, seed)

        if not force and self.main_root is not None and self.main_root not in roots:
            raise ValueError(f"Main root {self.main_root} couldn't be child node")

        return NodesStructure(self.nodes, roots, _prune(children, updated), parents, self.main_root if self.main_root in roots else None)

    def with_parent(self, parent: str, child: str, *, force: bool = False) -> 'NodesStructure':
        return self.with_children({parent: (child,)}, force=force)

    def without_children(self, links: Dict[str, Set[str]]) -> 'NodesStructure':
        roots = set(self.roots)
        parents: Dict[str, str] = dict(self.parent)  # child -> parent
        children: Dict[str, List[str]] = dict(self.children)  # parent -> [child]
        updated: Set[str] = set()

        for parent_id, children_ids in links.items():
            if parent_id not in children:  # nothing to remove
                continue
            children_ids = children_ids.intersection(children[parent_id])
            children[parent_id] = [child_id for child_id in children[parent_id] if child_id not in children_ids]
            updated.add(parent_id)
            for child_id in self.nodes.intersection(children_ids):
                parents.pop(child_id, None)
                roots.add(child_id)

        return replace(self, roots=roots, parent=parents, children=_prune(children, updated))

    def as_roots(self, nodes: Iterable[str]) -> 'NodesStructure':
        nodes = self.nodes.intersection(nodes)
        roots = self.roots.union(nodes)
        parents: Dict[str, str] = dict(self.parent)  # child -> parent
        children: Dict[str, List[str]] = dict(self.children)  # parent -> [child]
        updated: Set[str] = set()

        for child_id in nodes:
            parent_id = parents.pop(child_id, None)
            if parent_id is not None:
                _copy_if_not_updated(children, parent_id, updated).remove(child_id)

        return replace(self, roots=roots, parent=parents, children=_prune(children, updated))


def _copy_if_not_updated(children: Dict[str, List[str]], key: str, updated: Set[str]) -> List[str]:
    if key not in updated:
        children[key] = list(children.get(key, ()))
        updated.add(key)
    return children[key]


def _prune(children: Dict[str, List[str]], updated: Set[str]) -> Dict[str, List[str]]:
    for key in updated:
        if not children.get(key):
            children.pop(key, None)
    return children


def _check_circle(graph: Dict[str, str], seed: Set[str]) -> None:
    state = {key: graph.get(key) for key in seed}
    while state:
        s = {}
        for key, obj in state.items():
            if obj is None:
                continue
            if key == obj:
                raise ValueError(f"Circle dependency with element {key}")
            s[key] = graph.get(obj)
        state = s
