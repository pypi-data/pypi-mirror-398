from abc import ABCMeta, abstractmethod
from typing import Callable, Hashable, Iterable, Optional, Tuple

from .identifiable import EnsureIdentifiable


class Duplicatable(metaclass=ABCMeta):
    @abstractmethod
    def duplicate_hash(self) -> Hashable:
        pass

    @abstractmethod
    def choose_one(
            self,
            other,
            to_hash: Callable[[str], Hashable],
            related: Callable[[str], Iterable[str]],
            restore_element: Callable[[str], EnsureIdentifiable]
    ) -> Optional[Tuple[str, str]]:
        pass
