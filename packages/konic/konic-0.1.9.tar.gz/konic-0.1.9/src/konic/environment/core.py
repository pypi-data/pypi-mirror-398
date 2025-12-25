from typing import Any

import gymnasium as gym
import numpy as np

from konic.environment.base import BaseKonicEnvironment
from konic.environment.reward import KonicRewardComposer
from konic.environment.space import KonicSpace
from konic.environment.termination import KonicTerminationComposer
from konic.environment.type import KonicResetStateObservation, KonicStepStateObservation


class KonicEnvironment(BaseKonicEnvironment):
    """
    Base Konic Environment compatible with RLlib.

    This environment automatically handles Dict observation/action spaces for RLlib compatibility.
    Set `flatten_spaces=True` to automatically flatten Dict spaces to Box spaces, which is
    recommended for most RLlib algorithms.
    """

    def __init__(
        self,
        action_space: KonicSpace,
        observation_space: KonicSpace,
        reward_composer: KonicRewardComposer,
        termination_composer: KonicTerminationComposer,
        flatten_spaces: bool = False,
    ):
        super().__init__()

        self._konic_action_space = action_space
        self._konic_observation_space = observation_space

        self._action_space = action_space.to_gym()
        self._observation_space = observation_space.to_gym()

        self._flatten_spaces = flatten_spaces
        if flatten_spaces:
            self._apply_space_flattening()

        self._reward_composer = reward_composer
        self._reward_composer.set_env(self)

        self._termination_composer = termination_composer
        if self._termination_composer is not None:
            self._termination_composer.set_env(self)

    def _apply_space_flattening(self):
        """Apply FlattenObservation-style flattening to Dict spaces for RLlib compatibility."""
        if isinstance(self._observation_space, gym.spaces.Dict):
            obs_dim = sum(
                int(np.prod(space.shape))
                for space in self._observation_space.spaces.values()
                if isinstance(space, gym.spaces.Box)
            )

            self._observation_space = gym.spaces.Box(
                low=-np.inf, high=np.inf, shape=(obs_dim,), dtype=np.float32
            )

        if isinstance(self._action_space, gym.spaces.Dict):
            first_action_space = next(iter(self._action_space.spaces.values()))

            if isinstance(first_action_space, gym.spaces.Discrete):
                self._action_space = first_action_space

    def _flatten_dict_obs(self, obs: dict) -> np.ndarray:
        """Flatten a dictionary observation to a 1D numpy array."""
        if not isinstance(obs, dict):
            return obs

        flattened = []
        for key in sorted(obs.keys()):
            value = obs[key]
            if isinstance(value, np.ndarray):
                flattened.append(value.flatten())
            else:
                flattened.append(np.array([value]).flatten())

        return np.concatenate(flattened, dtype=np.float32)

    def _extract_dict_action(self, action) -> dict:
        """Convert flattened action back to dict format if needed."""
        if isinstance(action, dict):
            return action

        if isinstance(self._action_space, gym.spaces.Discrete):
            first_key = next(iter(self._konic_action_space.to_gym().spaces.keys()))
            return {first_key: action}

        return action

    @property
    def action_space(self) -> gym.spaces.Space:
        return self._action_space

    @property
    def observation_space(self) -> gym.spaces.Space:
        return self._observation_space

    @property
    def reward_composer(self) -> KonicRewardComposer:
        return self._reward_composer

    @property
    def termination_composer(self) -> KonicTerminationComposer:
        return self._termination_composer

    def step(self, action: dict[str, Any] | Any) -> KonicStepStateObservation:
        """
        Execute one step in the environment.

        If flatten_spaces=True, this method handles flattening/unflattening automatically.
        Subclasses should implement their step logic in terms of the original Dict spaces.
        """
        if self._flatten_spaces:
            action = self._extract_dict_action(action)

        obs, reward, terminated, truncated, info = self._step(action)

        if self._flatten_spaces and isinstance(obs, dict):
            obs = self._flatten_dict_obs(obs)

        return obs, reward, terminated, truncated, info

    def _step(self, action: dict[str, Any]) -> KonicStepStateObservation:
        """
        Internal step implementation that subclasses should override.
        This method always receives actions in Dict format.
        """
        raise NotImplementedError(
            "step() or _step() is not implemented for this environment. "
            "Override KonicEnvironment._step(self, action) to advance the environment and return "
            "a KonicStepStateObservation (observation, reward, terminated, truncated, info). "
            f"Called with action={action!r}."
        )

    def reset(
        self, seed: int | None = None, options: dict | None = None
    ) -> KonicResetStateObservation:
        """
        Reset the environment.

        If flatten_spaces=True, this method handles flattening automatically.
        Subclasses should implement their reset logic in terms of the original Dict spaces.
        """
        obs, info = self._reset(seed, options)

        if self._flatten_spaces and isinstance(obs, dict):
            obs = self._flatten_dict_obs(obs)

        return obs, info

    def _reset(
        self, seed: int | None = None, options: dict | None = None
    ) -> KonicResetStateObservation:
        """
        Internal reset implementation that subclasses should override.
        This method should return observations in Dict format.
        """
        raise NotImplementedError(
            "reset() or _reset() is not implemented for this environment. "
            "Override KonicEnvironment._reset(self, seed: int | None = None) to initialize "
            "the environment and return a KonicResetStateObservation (observation, info). "
            f"Called with seed={seed!r}."
        )

    def get_obs(self):
        raise NotImplementedError(
            "get_obs() is not implemented for this environment. "
            "Override KonicEnvironment.get_obs() to return the current observation "
            "matching the configured observation_space."
        )

    def get_info(self):
        return {}
