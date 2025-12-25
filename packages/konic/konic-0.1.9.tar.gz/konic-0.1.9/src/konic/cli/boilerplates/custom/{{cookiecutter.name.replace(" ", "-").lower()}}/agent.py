"""
Custom KonicEnvironment Agent

This template demonstrates how to build a custom RL environment using Konic's
environment framework with custom action/observation spaces, reward composers,
and termination conditions.
"""

from typing import Any

import numpy as np

from konic.agent import KonicAgent
from konic.environment import KonicEnvironment
from konic.environment.reward import KonicRewardComposer, custom_reward
from konic.environment.space import KonicBound, KonicDiscrete, KonicSpace
from konic.environment.termination import KonicTerminationComposer, custom_termination
from konic.runtime import register_agent


# Define your action space
class MyActionSpace(KonicSpace):
    action: KonicDiscrete = 2  # 0 or 1


# Define your observation space
class MyObservationSpace(KonicSpace):
    position: KonicBound = ((1,), -10.0, 10.0)
    velocity: KonicBound = ((1,), -5.0, 5.0)


# Define your reward composer
class MyRewardComposer(KonicRewardComposer["MyEnvironment"]):
    @custom_reward
    def goal_reward(self) -> float:
        """Reward for reaching the goal."""
        if self.env.position >= self.env.goal:
            return 10.0
        return 0.0

    @custom_reward
    def step_penalty(self) -> float:
        """Small penalty for each step to encourage efficiency."""
        return -0.1


# Define your termination composer
class MyTerminationComposer(KonicTerminationComposer["MyEnvironment"]):
    def terminated(self) -> bool:
        return False

    @custom_termination
    def goal_reached(self) -> bool:
        """Episode ends when goal is reached."""
        return self.env.position >= self.env.goal

    @custom_termination
    def max_steps_reached(self) -> bool:
        """Episode ends after max steps."""
        return self.env.steps >= self.env.max_steps


# Define your custom environment
class MyEnvironment(KonicEnvironment):
    def __init__(self, goal: float = 5.0, max_steps: int = 100, flatten_spaces: bool = True):
        super().__init__(
            action_space=MyActionSpace(),
            observation_space=MyObservationSpace(),
            reward_composer=MyRewardComposer(),
            termination_composer=MyTerminationComposer(),
            flatten_spaces=flatten_spaces,
        )

        self.goal = goal
        self.max_steps = max_steps
        self.position = 0.0
        self.velocity = 0.0
        self.steps = 0

    def _reset(self, seed: int | None = None, options: dict | None = None):
        if seed is not None:
            np.random.seed(seed)

        self.position = 0.0
        self.velocity = 0.0
        self.steps = 0

        return self.get_obs(), self.get_info()

    def _step(self, action: dict[str, Any]):
        action_value = action["action"]

        # Apply action: 0 = decelerate, 1 = accelerate
        if action_value == 0:
            self.velocity = max(-5.0, self.velocity - 0.5)
        else:
            self.velocity = min(5.0, self.velocity + 0.5)

        self.position = np.clip(self.position + self.velocity, -10.0, 10.0)
        self.steps += 1

        observation = self.get_obs()
        reward = self.reward_composer.compose()
        terminated = self.termination_composer.compose()
        truncated = False
        info = self.get_info()

        return observation, reward, terminated, truncated, info

    def get_obs(self):
        return {
            "position": np.array([self.position], dtype=np.float32),
            "velocity": np.array([self.velocity], dtype=np.float32),
        }

    def get_info(self):
        return {
            "position": self.position,
            "velocity": self.velocity,
            "steps": self.steps,
            "goal": self.goal,
        }


# Create and register the agent
env = MyEnvironment()
agent = KonicAgent(environment=env)

register_agent(agent, name="{{cookiecutter.name.replace(' ', '-').lower()}}")
