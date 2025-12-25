"""
Callback Agent

This template demonstrates how to use KonicRLCallback to track custom metrics
during training with the @custom_metric decorator.
"""

import gymnasium as gym

from konic.agent import KonicAgent
from konic.callback import KonicRLCallback, custom_metric
from konic.runtime import register_agent


class MyCallback(KonicRLCallback):
    """Custom callback for tracking agent-specific metrics."""

    def __init__(self):
        super().__init__()
        self.best_return = float("-inf")
        self.returns_above_threshold = 0
        self.threshold = 100.0

    @custom_metric
    def track_best_return(self, episode) -> dict[str, float]:
        """Track the best episode return seen so far."""
        episode_return = episode.get_return()
        if episode_return > self.best_return:
            self.best_return = episode_return

        return {"best_return": self.best_return}

    @custom_metric
    def track_threshold_count(self, episode) -> dict[str, float]:
        """Track how many episodes exceeded the threshold."""
        if episode.get_return() > self.threshold:
            self.returns_above_threshold += 1

        return {"returns_above_threshold": float(self.returns_above_threshold)}

    @custom_metric
    def track_episode_stats(self, episode) -> dict[str, float]:
        """Track additional episode statistics."""
        rewards = episode.get_rewards()
        return {
            "max_step_reward": max(rewards) if rewards else 0.0,
            "min_step_reward": min(rewards) if rewards else 0.0,
        }

    def on_episode_end(self, *, episode, metrics_logger, **kwargs):
        """Called when an episode ends."""
        super().on_episode_end(episode=episode, metrics_logger=metrics_logger, **kwargs)
        # Add any custom logic here


# Create environment and agent
env = gym.make("CartPole-v1")
agent = KonicAgent(environment=env)

register_agent(agent, name="{{cookiecutter.name.replace(' ', '-').lower()}}")
