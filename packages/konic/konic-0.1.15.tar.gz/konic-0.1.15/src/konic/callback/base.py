from abc import ABC, abstractmethod
from typing import Any


class BaseKonicRLCallback(ABC):
    """
    Abstract base class for Konic RL callbacks.

    This defines the interface for RL training callbacks. Users can inherit
    from KonicRLCallback (the concrete implementation) to create custom callbacks.
    """

    @abstractmethod
    def on_episode_start(self, *, episode: Any, **kwargs) -> None:
        """Called when an episode starts (after env.reset())."""
        pass

    @abstractmethod
    def on_episode_step(self, *, episode: Any, **kwargs) -> None:
        """Called after each step in an episode (after env.step())."""
        pass

    @abstractmethod
    def on_episode_end(self, *, episode: Any, **kwargs) -> None:
        """Called when an episode ends (terminated or truncated)."""
        pass

    @abstractmethod
    def on_train_result(self, *, algorithm: Any, result: dict, **kwargs) -> None:
        """Called after each training iteration."""
        pass
