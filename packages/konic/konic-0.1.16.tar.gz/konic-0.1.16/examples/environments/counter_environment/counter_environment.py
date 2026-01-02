"""
Counter Environment Example

A simple environment where an agent tries to reach a target count.
The agent can increment or decrement a counter, starting from 0.

Actions:
    0: Decrement (-1)
    1: Increment (+1)

Goal:
    Reach the target count (default: 10)

Reward:
    - Positive reward for getting closer to the target
    - Negative reward for moving away from the target
    - Large bonus reward when reaching the target

Termination:
    - Episode ends when the target is reached
    - Episode ends after max_steps (default: 50)
"""

from __future__ import annotations

from typing import Any

import numpy as np

from konic.environment import KonicEnvironment
from konic.environment.reward import KonicRewardComposer, custom_reward
from konic.environment.space import KonicBound, KonicDiscrete, KonicSpace
from konic.environment.termination import KonicTerminationComposer, custom_termination


class CounterActionSpace(KonicSpace):
    action: KonicDiscrete = 2


class CounterObservationSpace(KonicSpace):
    current_count: KonicBound = ((1,), -100.0, 100.0)
    target_count: KonicBound = ((1,), -100.0, 100.0)
    steps_remaining: KonicBound = ((1,), 0.0, 100.0)


class CounterRewardComposer(KonicRewardComposer["CounterEnvironment"]):
    @custom_reward
    def target_reached_bonus(self) -> float:
        if self.env.current_count == self.env.target_count:
            return 10.0
        return 0.0

    @custom_reward
    def distance_penalty(self) -> float:
        distance = abs(self.env.current_count - self.env.target_count)
        return -0.01 * distance

    @custom_reward
    def progress_reward(self) -> float:
        if not hasattr(self.env, "previous_distance"):
            return 0.0

        current_distance = abs(self.env.current_count - self.env.target_count)
        previous_distance = self.env.previous_distance

        if current_distance < previous_distance:
            return 1.0
        elif current_distance > previous_distance:
            return -1.0
        return 0.0


class CounterTerminationComposer(KonicTerminationComposer["CounterEnvironment"]):
    def terminated(self) -> bool:
        return False

    @custom_termination
    def target_reached(self) -> bool:
        return self.env.current_count == self.env.target_count

    @custom_termination
    def max_steps_reached(self) -> bool:
        return self.env.steps >= self.env.max_steps


class CounterEnvironment(KonicEnvironment):
    def __init__(self, target_count: int = 10, max_steps: int = 50, flatten_spaces: bool = False):
        """
        Initialize the Counter Environment.

        Args:
            target_count: The target count to reach (default: 10)
            max_steps: Maximum number of steps per episode (default: 50)
            flatten_spaces: If True, automatically flatten Dict spaces for RLlib compatibility (default: False)
        """
        super().__init__(
            action_space=CounterActionSpace(),
            observation_space=CounterObservationSpace(),
            reward_composer=CounterRewardComposer(),
            termination_composer=CounterTerminationComposer(),
            flatten_spaces=flatten_spaces,
        )

        self.steps = 0
        self.current_count = 0
        self.max_steps = max_steps
        self.target_count = target_count
        self.previous_distance = abs(self.current_count - self.target_count)

    def _reset(self, seed: int | None = None, options: dict | None = None):
        if seed is not None:
            np.random.seed(seed)

        self.current_count = 0
        self.steps = 0
        self.previous_distance = abs(self.current_count - self.target_count)

        observation = self.get_obs()
        info = self.get_info()

        return observation, info

    def _step(self, action: dict[str, Any]):
        self.previous_distance = abs(self.current_count - self.target_count)

        action_value = action["action"]
        if action_value == 0:
            self.current_count -= 1
        elif action_value == 1:
            self.current_count += 1

        self.steps += 1

        observation = self.get_obs()
        reward = self.reward_composer.compose()
        terminated = self.termination_composer.compose()
        truncated = False
        info = self.get_info()

        return observation, reward, terminated, truncated, info

    def get_obs(self):
        return {
            "current_count": np.array([self.current_count], dtype=np.float32),
            "target_count": np.array([self.target_count], dtype=np.float32),
            "steps_remaining": np.array([self.max_steps - self.steps], dtype=np.float32),
        }

    def get_info(self):
        return {
            "current_count": self.current_count,
            "target_count": self.target_count,
            "steps": self.steps,
            "distance_to_target": abs(self.current_count - self.target_count),
        }


def main() -> None:
    seed = 42

    print("=== Example 1: Dict observation space ===")
    env_dict = CounterEnvironment(flatten_spaces=False)
    obs, info = env_dict.reset(seed=seed)
    print(f"Observation space: {env_dict.observation_space}")
    print(f"Action space: {env_dict.action_space}")
    print(f"Sample observation: {obs}")
    print()

    print("=== Example 2: Flattened observation space (RLlib-friendly) ===")
    env_flat = CounterEnvironment(flatten_spaces=True)
    obs, info = env_flat.reset(seed=seed)
    print(f"Observation space: {env_flat.observation_space}")
    print(f"Action space: {env_flat.action_space}")
    print(f"Sample observation (flattened): {obs}")
    print()

    print("=== Running 10 steps with flattened environment ===")
    for i in range(10):
        action = env_flat.action_space.sample()
        obs, reward, terminated, truncated, info = env_flat.step(action)
        print(f"Step {i+1}: Action={action}, Obs shape={obs.shape}, Reward={reward:.2f}")

        if terminated or truncated:
            break


if __name__ == "__main__":
    main()
