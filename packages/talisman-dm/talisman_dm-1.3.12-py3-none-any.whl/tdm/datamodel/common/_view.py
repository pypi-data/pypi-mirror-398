from abc import abstractmethod
from dataclasses import dataclass, fields, is_dataclass, make_dataclass, replace
from typing import Callable, Dict, Generic, Set, Tuple, Type, TypeVar, Union

from typing_extensions import Self

from tdm.abstract.datamodel import EnsureIdentifiable
from tdm.helper import generics_mapping, is_subclass, register_in_module

_T = TypeVar('_T', bound=EnsureIdentifiable)


@dataclass(frozen=True)
class AbstractView(Generic[_T]):
    __depends_on__: Set[str]

    @abstractmethod
    def get_object(self, objects: Dict[str, Union[EnsureIdentifiable, 'AbstractView']]) -> _T:
        pass

    @abstractmethod
    def validate_update(self, other: 'AbstractView[_T]') -> bool:
        pass

    @abstractmethod
    def substitute_id(self, old: str, new: str) -> Self:
        pass

    @abstractmethod
    def orig_type(self) -> Type[_T]:
        pass

    def is_hanging(self, view_container) -> bool:
        return False

    @abstractmethod
    def get_dependencies(self, obj: _T) -> Set[EnsureIdentifiable]:
        pass


def generate_depends_on(id_fields: Set[str], view_fields: Set[str]):
    def depends_on(view) -> Set[str]:
        result = {view[field_name] for field_name in id_fields}
        for field_name in view_fields:
            result.update(view[field_name].__depends_on__)
        return result

    return depends_on


_CACHE = {}
_ST = TypeVar('_ST')
_TT = TypeVar('_TT')


def generate_dataclass_view(type_: Type[_ST]) -> Tuple[Type[_TT], Callable[[_ST], _TT]]:
    if type_ in _CACHE:
        return _CACHE[type_]
    if not is_dataclass(type_):
        return type_, lambda x: x

    class_fields = []
    id_fields = set()
    restore_fields = set()
    constructor_fields = {}
    constant_fields = type_.constant_fields() if issubclass(type_, EnsureIdentifiable) else set()
    changed = False
    type_vars = generics_mapping(type_)
    for field in fields(type_):
        if not field.init:
            continue
        field_type = type_vars.get(field.type, field.type)
        if is_subclass(field_type, EnsureIdentifiable):  # we can use id instead of view of object
            field_type = str
            id_fields.add(field.name)
            constructor_fields[field.name] = lambda x: x.id
            changed = True
        else:
            orig_type = field_type
            field_type, field_constructor = generate_dataclass_view(field_type)
            if field_type is not orig_type:
                restore_fields.add(field.name)
                changed = True
                constructor_fields[field.name] = object_view
            else:
                constructor_fields[field.name] = lambda x: x
        class_fields.append((field.name, field_type))

    if not changed and not constant_fields and not issubclass(type_, EnsureIdentifiable):
        _CACHE[type_] = type_, lambda x: x
        return _CACHE[type_]

    def get_object(self, objects: Dict[str, EnsureIdentifiable]) -> type_:
        kwargs = dict(self.__dict__)
        kwargs.pop('__depends_on__')
        for name in id_fields:
            kwargs[name] = restore_object(objects[kwargs[name]], objects)
        for name in restore_fields:
            kwargs[name] = restore_object(kwargs[name], objects)
        return type_(**kwargs)

    def validate_update(self, other) -> None:
        old = self.orig_type()
        new = other.orig_type()
        if not (issubclass(old, new) or issubclass(new, old)):
            raise ValueError(f"Changing type of element is forbidden (old type: {old}, new type: {new})")
        for field in constant_fields:
            old = getattr(self, field)
            new = getattr(other, field)
            if old != new:
                raise ValueError(f"Changing {field} is forbidden (old value: {old}, new value: {new})")

    def substitute_id(self, old: str, new: str):
        replacement = {field_name: new for field_name in id_fields if getattr(self, field_name) == old}
        return replace(self, **replacement)

    def get_dependencies(self, obj) -> Set[EnsureIdentifiable]:
        r = {getattr(obj, field_name) for field_name in id_fields}
        for field_name in restore_fields:
            r.update(getattr(self, field_name).get_dependencies(getattr(obj, field_name)))
        return r

    def eq(self, other) -> bool:
        if not isinstance(other, AbstractView):
            return NotImplemented
        self_orig = self.orig_type()
        other_orig = other.orig_type()
        return (issubclass(self_orig, other_orig) or issubclass(other_orig, self_orig)) and self.__dict__ == other.__dict__

    cls_name = f"{type_.__module__.replace('.', '_')}_{type_.__name__}View"

    view_type = make_dataclass(
        cls_name=cls_name,
        fields=class_fields,
        bases=(AbstractView,),
        eq=False,
        namespace={
            'get_object': get_object,
            'validate_update': validate_update,
            'substitute_id': substitute_id,
            'orig_type': lambda _: type_,
            'get_dependencies': get_dependencies,
            'pruned': type_.__dict__.get('is_hanging', AbstractView.is_hanging),
            '__eq__': eq
        },
        frozen=True
    )

    view_type = register_in_module(view_type)

    __depends_on__ = generate_depends_on(id_fields, restore_fields)

    def constructor(obj: _ST) -> _TT:
        view = {name: fc(getattr(obj, name)) for name, fc in constructor_fields.items()}
        return view_type(__depends_on__=__depends_on__(view), **view)

    _CACHE[type_] = view_type, constructor
    return _CACHE[type_]


def object_view(obj) -> AbstractView:
    _, constructor = generate_dataclass_view(type(obj))
    return constructor(obj)


def restore_object(view, objects: Dict[str, Union[EnsureIdentifiable, AbstractView]]):
    if isinstance(view, AbstractView):
        return view.get_object(objects)
    return view
