"""
KonicRLCallback - Customizable RL training callback for Konic.

This module provides a callback system for RL training that tracks important
metrics and allows users to extend with custom metrics using decorators.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ray.rllib.callbacks.callbacks import RLlibCallback

from konic.callback.utils import get_custom_metric_fns

if TYPE_CHECKING:
    from ray.rllib.algorithms.algorithm import Algorithm
    from ray.rllib.env.single_agent_episode import SingleAgentEpisode
    from ray.rllib.utils.metrics.metrics_logger import MetricsLogger


class KonicRLCallback(RLlibCallback):
    """
    Konic's customizable RL training callback.

    This callback provides sensible defaults for logging important RL metrics
    while allowing users to extend it with custom metrics using the @custom_metric
    decorator or by overriding methods.

    Default Metrics Tracked:
        Episode-Level (per episode):
            - konic/episode_return: Total reward per episode (window=100)
            - konic/episode_length: Steps per episode (window=100)
            - konic/total_episodes: Cumulative episodes completed
            - konic/total_steps: Cumulative steps taken

        Episode Stats (from env_runners, per train result):
            - konic/episode/return_mean: Mean episode return
            - konic/episode/return_min: Min episode return
            - konic/episode/return_max: Max episode return
            - konic/episode/length_mean: Mean episode length
            - konic/episode/length_min: Min episode length
            - konic/episode/length_max: Max episode length

        Training-Level (via on_train_result):
            - konic/learner/*/policy_loss: Policy gradient loss
            - konic/learner/*/value_loss: Value function loss
            - konic/learner/*/entropy: Policy entropy (exploration)
            - konic/learner/*/kl_divergence: KL between old/new policy
            - konic/learner/*/learning_rate: Current learning rate
            - konic/learner/*/grad_norm: Gradient norm
            - konic/learner/*/vf_loss_unclipped: Unclipped value function loss
            - konic/learner/*/vf_explained_var: Value function explained variance
            - konic/learner/*/kl_coeff: Current KL penalty coefficient
            - konic/learner/*/steps_trained: Steps trained this iteration

        Throughput & Timing:
            - konic/throughput/fps: Frames per second
            - konic/throughput/total_env_steps: Total environment steps
            - konic/throughput/total_episodes: Total episodes (lifetime)
            - konic/time/total_s: Total training time in seconds
            - konic/time/this_iter_s: Time for this iteration

    Example:
        config.callbacks(callbacks_class=KonicRLCallback)

        class MyCallback(KonicRLCallback):
            @custom_metric
            def track_custom_value(self, episode) -> dict[str, float]:
                return {"my_metric": episode.custom_data.get("value", 0.0)}

            def on_episode_end(self, *, episode, metrics_logger, **kwargs):
                super().on_episode_end(episode=episode, metrics_logger=metrics_logger, **kwargs)
                print(f"Episode finished with return: {episode.get_return()}")
    """

    def __init__(self):
        super().__init__()
        self.total_episodes: int = 0
        self.total_steps: int = 0
        self.episode_returns: list[float] = []
        self.episode_lengths: list[int] = []

    def on_algorithm_init(
        self,
        *,
        algorithm: Algorithm,
        metrics_logger: MetricsLogger,
        **kwargs,
    ) -> None:
        """
        Called when the algorithm is initialized.

        Override this method to perform setup that requires access to
        the algorithm instance.

        Args:
            algorithm: The RLlib Algorithm instance.
            metrics_logger: The MetricsLogger for logging metrics.
        """
        pass

    def on_episode_created(
        self,
        *,
        episode: SingleAgentEpisode,
        metrics_logger: MetricsLogger,
        **kwargs,
    ) -> None:
        """
        Called when a new episode is created but not yet started.

        Initializes episode custom data storage for Konic metrics.

        Args:
            episode: The newly created episode object.
            metrics_logger: The MetricsLogger for logging metrics.
        """
        episode.custom_data["konic_step_rewards"] = []
        episode.custom_data["konic_step_count"] = 0

    def on_episode_start(
        self,
        *,
        episode: SingleAgentEpisode,
        metrics_logger: MetricsLogger,
        **kwargs,
    ) -> None:
        """
        Called right after an episode has started (after env.reset()).

        Override this method to perform actions at episode start.

        Args:
            episode: The episode object that just started.
            metrics_logger: The MetricsLogger for logging metrics.
        """
        pass

    def on_episode_step(
        self,
        *,
        episode: SingleAgentEpisode,
        metrics_logger: MetricsLogger,
        **kwargs,
    ) -> None:
        """
        Called after each step in an episode (after env.step()).

        Tracks step-level data including rewards.

        Args:
            episode: The current episode object.
            metrics_logger: The MetricsLogger for logging metrics.
        """
        episode.custom_data["konic_step_count"] += 1

        rewards = episode.get_rewards()
        if len(rewards) > 0:
            episode.custom_data["konic_step_rewards"].append(rewards[-1])

    def on_episode_end(
        self,
        *,
        episode: SingleAgentEpisode,
        metrics_logger: MetricsLogger,
        **kwargs,
    ) -> None:
        """
        Called when an episode ends (terminated or truncated).

        Logs episode-level metrics and processes custom metrics.

        Args:
            episode: The episode object that just ended.
            metrics_logger: The MetricsLogger for logging metrics.
        """
        episode_return = episode.get_return()
        episode_length = episode.custom_data.get("konic_step_count", len(episode.get_rewards()))

        self.total_episodes += 1
        self.total_steps += episode_length
        self.episode_returns.append(episode_return)
        self.episode_lengths.append(episode_length)

        metrics_logger.log_value("konic/episode_return", episode_return, reduce="mean", window=100)
        metrics_logger.log_value("konic/episode_length", episode_length, reduce="mean", window=100)
        metrics_logger.log_value("konic/total_episodes", self.total_episodes)
        metrics_logger.log_value("konic/total_steps", self.total_steps)

        self._process_custom_metrics(episode, metrics_logger)

    def on_train_result(
        self,
        *,
        algorithm: Algorithm,
        metrics_logger: MetricsLogger,
        result: dict[str, Any],
        **kwargs,
    ) -> None:
        """
        Called at the end of Algorithm.train().

        Extracts and logs important training metrics from the result dict.

        Args:
            algorithm: The RLlib Algorithm instance.
            metrics_logger: The MetricsLogger for logging metrics.
            result: The training result dictionary.
        """
        self._log_training_metrics(result, metrics_logger)

    def on_evaluate_start(
        self,
        *,
        algorithm: Algorithm,
        metrics_logger: MetricsLogger,
        **kwargs,
    ) -> None:
        """
        Called before evaluation starts.

        Override this method to perform actions before evaluation.

        Args:
            algorithm: The RLlib Algorithm instance.
            metrics_logger: The MetricsLogger for logging metrics.
        """
        pass

    def on_evaluate_end(
        self,
        *,
        algorithm: Algorithm,
        metrics_logger: MetricsLogger,
        **kwargs,
    ) -> None:
        """
        Called after evaluation ends.

        Override this method to perform actions after evaluation.

        Args:
            algorithm: The RLlib Algorithm instance.
            metrics_logger: The MetricsLogger for logging metrics.
        """
        pass

    def on_checkpoint_loaded(
        self,
        *,
        algorithm: Algorithm,
        metrics_logger: MetricsLogger,
        **kwargs,
    ) -> None:
        """
        Called when a checkpoint has been loaded.

        Override this method to perform actions after loading a checkpoint.

        Args:
            algorithm: The RLlib Algorithm instance.
            metrics_logger: The MetricsLogger for logging metrics.
        """
        pass

    def on_sample_end(
        self,
        *,
        metrics_logger: MetricsLogger,
        **kwargs,
    ) -> None:
        """
        Called at the end of EnvRunner.sample().

        Override this method to perform actions after sampling.

        Args:
            metrics_logger: The MetricsLogger for logging metrics.
        """
        pass

    def _process_custom_metrics(
        self,
        episode: SingleAgentEpisode,
        metrics_logger: MetricsLogger,
    ) -> None:
        """
        Process and log custom metrics from @custom_metric decorated methods.

        Args:
            episode: The current episode object.
            metrics_logger: The MetricsLogger for logging metrics.
        """
        custom_fns = get_custom_metric_fns(self)
        for fn in custom_fns:
            try:
                metrics = fn(episode)
                if isinstance(metrics, dict):
                    for key, value in metrics.items():
                        metrics_logger.log_value(
                            f"konic/custom/{key}",
                            value,
                            reduce="mean",
                            window=50,
                        )
            except Exception as e:
                print(f"Warning: Custom metric function {fn.__name__} failed: {e}")

    def _log_training_metrics(
        self,
        result: dict[str, Any],
        metrics_logger: MetricsLogger,
    ) -> None:
        """
        Extract and log important training metrics from the result dict.

        Args:
            result: The training result dictionary from Algorithm.train().
            metrics_logger: The MetricsLogger for logging metrics.
        """
        self._log_episode_metrics(result, metrics_logger)

        learner_results = result.get("learners", {})
        for learner_id, learner_data in learner_results.items():
            self._log_learner_metrics(learner_id, learner_data, metrics_logger)

        self._log_throughput_metrics(result, metrics_logger)

    def _log_learner_metrics(
        self,
        learner_id: str,
        learner_data: dict[str, Any],
        metrics_logger: MetricsLogger,
    ) -> None:
        """
        Log metrics from a specific learner.

        Args:
            learner_id: The learner identifier.
            learner_data: The learner's metrics dictionary.
            metrics_logger: The MetricsLogger for logging metrics.
        """
        metric_mappings = {
            "policy_loss": "policy_loss",
            "vf_loss": "value_loss",
            "entropy": "entropy",
            "kl": "kl_divergence",
            "curr_lr": "learning_rate",
            "grad_gnorm": "grad_norm",
            "total_loss": "total_loss",
            "mean_kl_loss": "mean_kl_loss",
            "curr_entropy_coeff": "entropy_coeff",
            "vf_loss_unclipped": "vf_loss_unclipped",
            "vf_explained_var": "vf_explained_var",
            "curr_kl_coeff": "kl_coeff",
            "num_module_steps_trained": "steps_trained",
        }

        for source_key, target_key in metric_mappings.items():
            if source_key in learner_data:
                metrics_logger.log_value(
                    f"konic/learner/{learner_id}/{target_key}",
                    learner_data[source_key],
                )

    def _log_episode_metrics(
        self,
        result: dict[str, Any],
        metrics_logger: MetricsLogger,
    ) -> None:
        """
        Log episode-level metrics from env_runners.

        Args:
            result: The training result dictionary.
            metrics_logger: The MetricsLogger for logging metrics.
        """
        env_runners = result.get("env_runners", {})

        episode_metric_mappings = {
            "episode_return_mean": "return_mean",
            "episode_return_min": "return_min",
            "episode_return_max": "return_max",
            "episode_len_mean": "length_mean",
            "episode_len_min": "length_min",
            "episode_len_max": "length_max",
        }

        for source_key, target_key in episode_metric_mappings.items():
            if source_key in env_runners:
                metrics_logger.log_value(
                    f"konic/episode/{target_key}",
                    env_runners[source_key],
                )

    def _log_throughput_metrics(
        self,
        result: dict[str, Any],
        metrics_logger: MetricsLogger,
    ) -> None:
        """
        Log throughput and timing related metrics.

        Args:
            result: The training result dictionary.
            metrics_logger: The MetricsLogger for logging metrics.
        """
        if "time_total_s" in result and "num_env_steps_sampled_lifetime" in result:
            fps = result["num_env_steps_sampled_lifetime"] / max(result["time_total_s"], 1)
            metrics_logger.log_value("konic/throughput/fps", fps)

        if "num_env_steps_sampled_lifetime" in result:
            metrics_logger.log_value(
                "konic/throughput/total_env_steps",
                result["num_env_steps_sampled_lifetime"],
            )

        if "num_episodes_lifetime" in result:
            metrics_logger.log_value(
                "konic/throughput/total_episodes",
                result["num_episodes_lifetime"],
            )

        if "training_iteration" in result:
            metrics_logger.log_value(
                "konic/throughput/training_iteration",
                result["training_iteration"],
            )

        if "time_total_s" in result:
            metrics_logger.log_value(
                "konic/time/total_s",
                result["time_total_s"],
            )

        if "time_this_iter_s" in result:
            metrics_logger.log_value(
                "konic/time/this_iter_s",
                result["time_this_iter_s"],
            )

    def get_episode_returns(self) -> list[float]:
        """Get the list of all episode returns tracked so far."""
        return self.episode_returns.copy()

    def get_episode_lengths(self) -> list[int]:
        """Get the list of all episode lengths tracked so far."""
        return self.episode_lengths.copy()

    def get_mean_return(self, window: int = 100) -> float:
        """
        Get the mean return over the last `window` episodes.

        Args:
            window: Number of recent episodes to average.

        Returns:
            Mean return, or 0.0 if no episodes recorded.
        """
        if not self.episode_returns:
            return 0.0
        recent = self.episode_returns[-window:]
        return sum(recent) / len(recent)

    def get_mean_length(self, window: int = 100) -> float:
        """
        Get the mean episode length over the last `window` episodes.

        Args:
            window: Number of recent episodes to average.

        Returns:
            Mean length, or 0.0 if no episodes recorded.
        """
        if not self.episode_lengths:
            return 0.0
        recent = self.episode_lengths[-window:]
        return sum(recent) / len(recent)
