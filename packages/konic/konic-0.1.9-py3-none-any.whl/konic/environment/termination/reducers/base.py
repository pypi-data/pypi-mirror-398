from abc import ABC, abstractmethod
from collections.abc import Callable


class BaseKonicTerminationReducer(ABC):
    "Base class of KonicTerminationReducer strategy class"

    @abstractmethod
    def reduce(self, fns: list[Callable[..., bool]]) -> bool:
        """Abstract method to reduce a list of callable termination functions into a single bool value."""
        pass
