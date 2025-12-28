import uuid
from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from typing import Set


@dataclass(frozen=True)
class EnsureIdentifiable(object):  # we need such ugly inheritance to guarantee default valued fields follows fields without defaults
    """
    Base interface for identifiable objects that contains non-default fields.
    Python dataclasses before 3.10 couldn't define kwargs-only fields and ``Identifiable`` class contains one (id).

    In cases identifiable object contains non-default fields one should create intermediate ``class _MyClass(EnsureIdentifiable)`` where
    fields are defined.
    Final class will inherit both classes ``class MyClass(Identifiable, _MyClass)``
    """

    def __post_init__(self):
        if not isinstance(self, Identifiable):
            raise TypeError(f"{type(self)} should inherit {Identifiable}. Actual mro is {type(self).mro()}")

    @classmethod
    @abstractmethod
    def constant_fields(cls) -> Set[str]:
        """
        Get set of fields that are constant for identifiable object.
        Some identifiable objects could depend on other objects (and values stored in these objects).
        So changing these fields could lead to document inconsistency.
        If some constant fields should be changed, remove objects from document and then add any desired objects.

        :return: set of fields that should be never changed
        """
        pass


@dataclass(frozen=True, eq=False)
class Identifiable(EnsureIdentifiable, metaclass=ABCMeta):
    """
    Base interface for identifiable objects that could be stored in document.

    This class should be the first class with ``__post_init__`` method implemented in inherited class mro to guarantee correct identifier
    generation.
    In other cases ``Identifiable.__post_init__(self)`` should be called explicitly.

    Attributes
    --------
    id:
        Object unique identifier. It will be automatically generated if no passed to object constructor
    """
    id: str = field(default_factory=lambda: None)

    def __post_init__(self):
        if self.id is None:
            object.__setattr__(self, 'id', self.generate_id())
        for type_ in type(self).mro():
            if issubclass(type_, Identifiable):
                continue
            if hasattr(type_, '__post_init__'):
                type_.__post_init__(self)

    @staticmethod
    def generate_id() -> str:
        return str(uuid.uuid4())
