from dataclasses import dataclass, replace
from typing import Hashable, Optional, Union

from typing_extensions import Self


@dataclass(frozen=True)
class EnsureConfidenced(object):
    """
    Base interface for objects with confidence that contains non-default fields.
    Python dataclasses before 3.10 couldn't define kwargs-only fields and ``Confidenced`` class contains one (confidence).

    In cases AbstractValue object contains non-default fields one should create intermediate ``class _MyValue(EnsureConfidenced)`` where
    fields are defined.
    Final class will inherit both classes ``class MyValue(Confidenced, _MyValue)``
    """

    def __post_init__(self):
        if not isinstance(self, Confidenced):
            raise TypeError(f"{type(self)} should inherit {AbstractValue}. Actual mro is {type(self).mro()}")


@dataclass(frozen=True)
class Confidenced(object):
    """
    Base class for values with confidence.

    Attributes
    ----------
    confidence:
        Confidence value associated with the value.
    """
    confidence: Optional[Union[float, int]] = None

    def get_none_confidenced_value(self) -> Hashable:
        return replace(self, confidence=None)

    def __post_init__(self):
        if self.confidence == 0:
            object.__setattr__(self, "confidence", None)

        if self.confidence is not None and not 0 < self.confidence <= 1:
            raise ValueError(f"value confidence should be in interval (0; 1], {self.confidence} is given")
        for type_ in type(self).mro():
            if issubclass(type_, Confidenced):
                continue
            if hasattr(type_, '__post_init__'):
                type_.__post_init__(self)


@dataclass(frozen=True)
class AbstractConceptValue(Confidenced):
    """
    Base class for values containing KB concept identifiers
    """
    pass


@dataclass(frozen=True)
class AbstractValue(Confidenced):
    """
    Base class for normalized values in the knowledge base.
    """
    @classmethod
    def from_dict(cls, value: dict) -> Self:
        """
        Create an instance of value from a dictionary.

        :param value: Dictionary representing the value.
        :return: An instance of the value class created from the dictionary.
        """
        return cls(**value)
