from dataclasses import dataclass

from immutabledict import immutabledict
from typing_extensions import Self

from tdm.helper import freeze_dict
from .abstract import AbstractMarkup


@dataclass(frozen=True)
class FrozenMarkup(AbstractMarkup):
    """
    A class for representing node markup.

    This class is a default implementation for node markup.
    Objects of this class should be instantiated via `freeze` method to guarantee markup immutability.
    """
    _markup: immutabledict = immutabledict()

    @property
    def markup(self) -> immutabledict:
        return self._markup

    @classmethod
    def from_markup(cls, markup: AbstractMarkup) -> Self:
        if isinstance(markup, FrozenMarkup):
            return markup
        return cls(markup.markup)

    def __hash__(self):
        return hash(self._markup)

    @classmethod
    def freeze(cls, markup: dict) -> Self:
        """
        Create a frozen markup instance from a dictionary.

        :param markup: The dictionary representing the markup structure.
        :return: A new instance of the FrozenMarkup class with the frozen markup structure.
        """
        if not isinstance(markup, dict):
            raise ValueError
        return cls(freeze_dict(markup))
