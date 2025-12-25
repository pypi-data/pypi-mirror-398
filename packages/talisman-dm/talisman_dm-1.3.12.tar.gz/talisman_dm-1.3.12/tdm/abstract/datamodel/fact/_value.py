from abc import ABCMeta
from dataclasses import dataclass
from typing import Generic, Hashable, Optional, Sequence, Set, Tuple, TypeVar, Union

from tdm.abstract.datamodel.domain import AbstractValueDomainType
from tdm.abstract.datamodel.duplicatable import Duplicatable
from tdm.abstract.datamodel.value import EnsureConfidenced
from tdm.helper import generics_mapping, is_subclass, unfold_union
from ._fact import AbstractFact, FactStatus

_V = TypeVar('_V', bound=EnsureConfidenced)
_DT = TypeVar('_DT', bound=AbstractValueDomainType)


@dataclass(frozen=True)
class AbstractValueFact(AbstractFact, Duplicatable, Generic[_DT, _V], metaclass=ABCMeta):
    """
    Base class for value facts that represent some KB values.

    If the fact status is FactStatus.NEW `value` should be a tuple.
    If the fact status is FactStatus.APPROVED `value` should be single-valued.

    Attributes
    ----------
    type_id:
        The fact type identifier or instance of the value domain type.
    value:
        The normalized value or tuple of values (sorted by confidence) associated with the value fact.
    """
    type_id: Union[str, _DT]
    value: Union[Tuple[_V, ...], _V] = tuple()

    @property
    def str_type_id(self) -> str:
        return self.type_id if isinstance(self.type_id, str) else self.type_id.id

    @property
    def most_confident_value(self) -> Optional[_V]:
        if not self.value:
            return None
        if isinstance(self.value, Tuple):
            return self.value[0]
        return self.value

    def _tuple_value(self) -> tuple:
        return self.value if isinstance(self.value, tuple) else (self.value,)

    def duplicate_hash(self) -> Hashable:
        return self.str_type_id, self._tuple_value()

    def __post_init__(self):
        mapping = generics_mapping(type(self))
        domain_type = mapping.get(_DT)
        value_type = mapping.get(_V)
        if not issubclass(domain_type, AbstractValueDomainType):
            raise ValueError(f"Invalid type id for fact {self}. Expected a subclass of `AbstractValueDomainType`, but got `{domain_type}`.")

        if not is_subclass(value_type, domain_type.get_value_type()):
            raise ValueError(f"Invalid value type for fact {self} with the new domain type. "
                             f"Expected a subclass of `{domain_type.get_value_type()}`, but got `{value_type}`.")

        if not isinstance(self.type_id, str):
            if not isinstance(self.type_id, domain_type):
                raise ValueError(f"Illegal type id `{self.type_id}` for fact {self}. {domain_type.pretty()} is expected")
            value_type = self.type_id.value_type
        value_type = unfold_union(value_type)

        if isinstance(self.value, Sequence) and not isinstance(self.value, value_type):  # value could implement Sequence?
            if any(not isinstance(v, value_type) for v in self.value):
                raise ValueError(f"Fact {self} value should be {value_type} or tuple of {value_type}")
            object.__setattr__(self, 'value', tuple(self.value))
        elif not isinstance(self.value, value_type):
            raise ValueError(f"Fact {self} value should be {value_type} or tuple of {value_type}")

        if self.status is FactStatus.NEW and isinstance(self.value, value_type):
            object.__setattr__(self, 'value', (self.value,))
        elif self.status is FactStatus.APPROVED and isinstance(self.value, tuple) and not isinstance(self.value, value_type):
            if len(self.value) != 1 or not isinstance(self.value[0], value_type):
                raise ValueError(f"Approved fact {self} should have single value")
            object.__setattr__(self, 'value', self.value[0])

        if isinstance(self.value, Tuple):
            if all(v.confidence is not None for v in self.value):
                object.__setattr__(self, 'value', tuple(sorted(self.value, key=lambda v: v.confidence, reverse=True)))
            elif not all(v.confidence is None for v in self.value):
                raise ValueError(f"Fact {self} couldn't contain values with confidence and values without confidence at same time")

    @classmethod
    def constant_fields(cls) -> Set[str]:
        return {'type_id'}
