from dataclasses import dataclass
from typing import Generic, TypeVar, Union

from tdm.abstract.datamodel.value import AbstractValue, EnsureConfidenced
from tdm.abstract.json_schema import generate_model

_S = TypeVar('_S')


@dataclass(frozen=True)
class _ScalarValue(EnsureConfidenced, Generic[_S]):
    """
    Represents the internal structure of a scalar value.

    Attributes
    ----------
    value:
        Normalized scalar value
    """
    value: _S

    def __post_init__(self):
        if type(self) is _ScalarValue:
            raise TypeError


@generate_model
@dataclass(frozen=True)
class StringValue(AbstractValue, _ScalarValue[str]):
    """
    Represents a normalized KB value for strings.
    """
    pass


@generate_model
@dataclass(frozen=True)
class IntValue(AbstractValue, _ScalarValue[int]):
    """
    Represents a normalized KB value for integers.
    """
    pass


@generate_model
@dataclass(frozen=True)
class DoubleValue(AbstractValue, _ScalarValue[Union[float, int]]):
    """
    Represents a normalized KB value for float values.
    """
    pass


@generate_model
@dataclass(frozen=True)
class TimestampValue(AbstractValue, _ScalarValue[int]):
    """
    Represents a normalized KB value for unix timestamps.
    """
    pass
