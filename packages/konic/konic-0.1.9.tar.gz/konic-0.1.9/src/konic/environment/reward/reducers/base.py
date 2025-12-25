from abc import ABC, abstractmethod
from collections.abc import Callable


class BaseKonicRewardReducer(ABC):
    "Base class of KonicRewardReducer strategy class"

    @abstractmethod
    def reduce(self, fns: list[Callable[..., float]]) -> float:
        """Abstract method to reduce a list of callable reward functions into a single float value."""
        pass
