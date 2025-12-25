from abc import abstractmethod

from immutabledict import immutabledict
from typing_extensions import Self


class AbstractMarkup(object):
    """
    An abstract base class for custom node markup creation and manipulation.

    All the implementations should be immutable.
    """
    @property
    @abstractmethod
    def markup(self) -> immutabledict:
        """
        Retrieve the current markup associated with the instance.

        This property is utilized for equality check.

        :return: The current markup (immutable)
        """
        pass

    @classmethod
    @abstractmethod
    def from_markup(cls, markup: 'AbstractMarkup') -> Self:
        """
        Create a new instance of the node markup based on an existing markup.

        :param markup: The existing markup to base the new instance on.
        :return: A new instance of the node markup class.
        """
        pass

    def __hash__(self):
        return hash(self.markup)

    def __eq__(self, other):
        if not isinstance(other, AbstractMarkup):
            return NotImplemented
        return self.markup == other.markup
