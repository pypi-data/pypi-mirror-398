from abc import ABC, abstractmethod


class BaseKonicTerminationComposer(ABC):
    """An abstract base class for KonicTerminationComposer"""

    @abstractmethod
    def terminated(self) -> bool:
        """Abstract method to compute the base termination value."""
        pass
