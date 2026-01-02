"""
CSV Streamer Environment Agent

This template demonstrates how to build a data-driven RL agent using Konic's
KonicCSVStreamerEnvironment for streaming through CSV data files.
"""

import os
from typing import Any

from konic.agent import KonicAgent
from konic.environment.environments import KonicCSVStreamerEnvironment
from konic.environment.reward import KonicRewardComposer, custom_reward
from konic.environment.space import KonicDiscrete, KonicSpace
from konic.environment.termination import KonicTerminationComposer, custom_termination
from konic.runtime import register_agent, register_data

register_data(
    cloud_name="my-dataset",  # Name of dataset in Konic Cloud (use: konic data push)
    env_var="DATA_PATH",  # Environment variable that will contain the file path
    version="latest",  # Use "latest" or specific version like "1.0.0"
)


# Define your action space
class StreamerActionSpace(KonicSpace):
    action: KonicDiscrete = 3  # e.g., 0=hold, 1=buy, 2=sell


# Define your reward composer
class StreamerRewardComposer(KonicRewardComposer["MyCSVStreamerEnvironment"]):
    @custom_reward
    def action_reward(self) -> float:
        """Reward based on action taken with current data."""
        # Access current data row via self.env.get_current_value("column_name")
        # Implement your reward logic based on the data
        return 0.0


# Define your termination composer
class StreamerTerminationComposer(KonicTerminationComposer["MyCSVStreamerEnvironment"]):
    def terminated(self) -> bool:
        return False

    @custom_termination
    def end_of_data(self) -> bool:
        """Episode ends when we reach end of CSV data."""
        return self.env.is_done


# Define your custom CSV streamer environment
class MyCSVStreamerEnvironment(KonicCSVStreamerEnvironment):
    def __init__(self, csv_file_path: str):
        super().__init__(
            csv_file_path=csv_file_path,
            action_space=StreamerActionSpace(),
            reward_composer=StreamerRewardComposer(),
            termination_composer=StreamerTerminationComposer(),
            flatten_spaces=False,
        )

        self.last_action: int | None = None

    def _step(self, action: dict[str, Any]):
        self.last_action = action.get("action")

        # Move to next row in CSV
        self.current_index += 1

        observation = self.get_obs()
        reward = self.reward_composer.compose()
        terminated = self.termination_composer.compose()
        truncated = self.is_done
        info = self.get_info()

        return observation, reward, terminated, truncated, info

    def get_info(self) -> dict[str, Any]:
        info = super().get_info()
        info["last_action"] = self.last_action
        return info


csv_path = os.environ.get("DATA_PATH", "data.csv")

env = MyCSVStreamerEnvironment(csv_file_path=csv_path)
agent = KonicAgent(environment=env)

register_agent(agent, name="{{cookiecutter.name.replace(' ', '-').lower()}}")
