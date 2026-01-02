"""
Full-Featured Konic Agent

This comprehensive template demonstrates all Konic features:
- Custom KonicEnvironment with action/observation spaces
- Reward and termination composers with decorators
- Custom KonicRLCallback with metric tracking
"""

from typing import Any

import numpy as np

from konic.agent import KonicAgent
from konic.callback import KonicRLCallback, custom_metric
from konic.environment import KonicEnvironment
from konic.environment.reward import KonicRewardComposer, custom_reward
from konic.environment.space import KonicBound, KonicDiscrete, KonicSpace
from konic.environment.termination import KonicTerminationComposer, custom_termination
from konic.runtime import register_agent

# =============================================================================
# Action and Observation Spaces
# =============================================================================


class MyActionSpace(KonicSpace):
    action: KonicDiscrete = 3  # 0=left, 1=stay, 2=right


class MyObservationSpace(KonicSpace):
    agent_position: KonicBound = ((1,), 0.0, 10.0)
    target_position: KonicBound = ((1,), 0.0, 10.0)
    distance_to_target: KonicBound = ((1,), -10.0, 10.0)


# =============================================================================
# Reward Composer
# =============================================================================


class MyRewardComposer(KonicRewardComposer["MyEnvironment"]):
    @custom_reward
    def target_reached(self) -> float:
        """Big reward for reaching the target."""
        if abs(self.env.agent_position - self.env.target_position) < 0.5:
            return 100.0
        return 0.0

    @custom_reward
    def distance_reward(self) -> float:
        """Reward for getting closer to target."""
        current_distance = abs(self.env.agent_position - self.env.target_position)
        if hasattr(self.env, "previous_distance"):
            improvement = self.env.previous_distance - current_distance
            return improvement * 10.0
        return 0.0

    @custom_reward
    def time_penalty(self) -> float:
        """Small penalty per step to encourage efficiency."""
        return -0.05


# =============================================================================
# Termination Composer
# =============================================================================


class MyTerminationComposer(KonicTerminationComposer["MyEnvironment"]):
    def terminated(self) -> bool:
        return False

    @custom_termination
    def target_reached(self) -> bool:
        """Episode ends when agent reaches target."""
        return abs(self.env.agent_position - self.env.target_position) < 0.5

    @custom_termination
    def out_of_bounds(self) -> bool:
        """Episode ends if agent goes out of bounds."""
        return self.env.agent_position < 0 or self.env.agent_position > 10

    @custom_termination
    def max_steps_reached(self) -> bool:
        """Episode ends after max steps."""
        return self.env.steps >= self.env.max_steps


# =============================================================================
# Custom Environment
# =============================================================================


class MyEnvironment(KonicEnvironment):
    def __init__(self, max_steps: int = 200, flatten_spaces: bool = True):
        super().__init__(
            action_space=MyActionSpace(),
            observation_space=MyObservationSpace(),
            reward_composer=MyRewardComposer(),
            termination_composer=MyTerminationComposer(),
            flatten_spaces=flatten_spaces,
        )

        self.max_steps = max_steps
        self.agent_position = 0.0
        self.target_position = 0.0
        self.previous_distance = 0.0
        self.steps = 0

    def _reset(self, seed: int | None = None, options: dict | None = None):
        if seed is not None:
            np.random.seed(seed)

        self.agent_position = np.random.uniform(0, 10)
        self.target_position = np.random.uniform(0, 10)
        self.previous_distance = abs(self.agent_position - self.target_position)
        self.steps = 0

        return self.get_obs(), self.get_info()

    def _step(self, action: dict[str, Any]):
        self.previous_distance = abs(self.agent_position - self.target_position)

        action_value = action["action"]

        # Apply action: 0=left, 1=stay, 2=right
        if action_value == 0:
            self.agent_position -= 0.5
        elif action_value == 2:
            self.agent_position += 0.5

        self.agent_position = np.clip(self.agent_position, 0, 10)
        self.steps += 1

        observation = self.get_obs()
        reward = self.reward_composer.compose()
        terminated = self.termination_composer.compose()
        truncated = False
        info = self.get_info()

        return observation, reward, terminated, truncated, info

    def get_obs(self):
        return {
            "agent_position": np.array([self.agent_position], dtype=np.float32),
            "target_position": np.array([self.target_position], dtype=np.float32),
            "distance_to_target": np.array(
                [self.agent_position - self.target_position], dtype=np.float32
            ),
        }

    def get_info(self):
        return {
            "agent_position": self.agent_position,
            "target_position": self.target_position,
            "steps": self.steps,
            "distance": abs(self.agent_position - self.target_position),
        }


# =============================================================================
# Custom Callback
# =============================================================================


class MyCallback(KonicRLCallback):
    """Custom callback for tracking training metrics."""

    def __init__(self):
        super().__init__()
        self.targets_reached = 0
        self.best_distance = float("inf")

    @custom_metric
    def track_targets_reached(self, episode) -> dict[str, float]:
        """Track total targets reached."""
        info = episode.get_infos()[-1] if episode.get_infos() else {}
        if info.get("distance", float("inf")) < 0.5:
            self.targets_reached += 1

        return {"targets_reached": float(self.targets_reached)}

    @custom_metric
    def track_final_distance(self, episode) -> dict[str, float]:
        """Track final distance to target."""
        info = episode.get_infos()[-1] if episode.get_infos() else {}
        final_distance = info.get("distance", float("inf"))

        if final_distance < self.best_distance:
            self.best_distance = final_distance

        return {
            "final_distance": final_distance,
            "best_distance": self.best_distance,
        }


# =============================================================================
# Agent Registration
# =============================================================================

env = MyEnvironment()
agent = KonicAgent(environment=env)

register_agent(agent, name="{{cookiecutter.name.replace(' ', '-').lower()}}")
