from abc import ABC, abstractmethod
from typing import Any

import gymnasium as gym

from konic.environment import KonicEnvironment
from konic.module import BaseTorchModule


class BaseKonicAgent(ABC):
    """Abstract base class for KonicAgent"""

    @abstractmethod
    def get_environment(self) -> KonicEnvironment | gym.Env:
        """Return the environment class to be used for training."""
        pass

    @abstractmethod
    def get_environment_config(self) -> dict[str, Any]:
        """Return configuration parameters for environment initialization."""
        pass

    @abstractmethod
    def get_algorithm_config(self) -> dict[str, Any]:
        """Return algorithm-specific configuration."""
        pass

    @abstractmethod
    def get_module(self) -> type[BaseTorchModule] | None:
        """Return custom neural network module if needed."""
        pass

    @abstractmethod
    def get_training_config(self) -> dict[str, Any]:
        """Return training configuration (num_iterations, batch_size, etc.)."""
        pass
