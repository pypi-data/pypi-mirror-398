from abc import ABC, abstractmethod


class BaseKonicRewardComposer(ABC):
    """An abstract base class for KonicRewardComposer"""

    @abstractmethod
    def reward(self) -> float:
        """Abstract method to compute the base reward value."""
        pass
