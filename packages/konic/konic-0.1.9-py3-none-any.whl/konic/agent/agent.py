from typing import Any

import gymnasium as gym

from konic.agent.base import BaseKonicAgent
from konic.common.errors import KonicAssertionError, KonicConfigurationError
from konic.environment import KonicEnvironment
from konic.module import BaseTorchModule, KonicTorchPPO


class KonicAgent(BaseKonicAgent):
    def __init__(
        self,
        environment: KonicEnvironment | gym.Env | None = None,
        environment_config: dict[str, Any] | None = None,
        algorithm_config: dict[str, Any] | None = None,
        module: type[BaseTorchModule] | None = KonicTorchPPO,
        training_config: dict[str, Any] | None = None,
    ):
        self._environment = environment
        self._environment_config = environment_config
        self._algorithm_config = algorithm_config
        self._module = module
        self._training_config = training_config

        self._has_environment = environment is not None
        self._has_environment_config = environment_config is not None
        self._has_algorithm_config = algorithm_config is not None
        self._has_training_config = training_config is not None

    def get_environment(self) -> KonicEnvironment | gym.Env:
        """Return the environment class to be used for training."""
        if self._has_environment:
            if self._environment is None:
                raise KonicAssertionError(
                    "Environment should not be None when _has_environment is True"
                )
            return self._environment
        raise KonicConfigurationError(
            "Environment must be provided either in __init__ or by overriding get_environment()",
            config_key="environment",
        )

    def get_environment_config(self) -> dict[str, Any]:
        """Return configuration parameters for environment initialization."""
        if self._has_environment_config:
            if self._environment_config is None:
                raise KonicAssertionError(
                    "Environment config should not be None when _has_environment_config is True"
                )
            return self._environment_config
        return {}

    def get_algorithm_config(self) -> dict[str, Any]:
        """Return algorithm-specific configuration."""
        if self._has_algorithm_config:
            if self._algorithm_config is None:
                raise KonicAssertionError(
                    "Algorithm config should not be None when _has_algorithm_config is True"
                )
            return self._algorithm_config
        return {}

    def get_module(self) -> type[BaseTorchModule]:
        """Return neural network module (defaults to KonicTorchPPO)."""
        if self._module is None:
            raise KonicAssertionError("Module should not be None")
        return self._module

    def get_training_config(self) -> dict[str, Any]:
        """Return training configuration (num_iterations, batch_size, etc.)."""
        if self._has_training_config:
            if self._training_config is None:
                raise KonicAssertionError(
                    "Training config should not be None when _has_training_config is True"
                )
            return self._training_config
        return {}
