from dataclasses import dataclass

from tdm.abstract.datamodel.value import AbstractValue, EnsureConfidenced
from tdm.abstract.json_schema import generate_model


@dataclass(frozen=True)
class _LinkValue(EnsureConfidenced):
    """
    Auxiliary class for `LinkValue` to fix dataclass fields order.

    Represents the internal structure of a `LinkValue`.

    Attributes
    ----------
    link:
        Normalized URL.
    """
    link: str


@generate_model
@dataclass(frozen=True)
class LinkValue(AbstractValue, _LinkValue):
    """
    Represents a normalized KB value for URL.
    """
    pass
