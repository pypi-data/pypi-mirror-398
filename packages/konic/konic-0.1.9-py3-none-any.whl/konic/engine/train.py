import traceback
from collections.abc import Generator
from dataclasses import dataclass, field
from typing import Any

import ray
from ray.rllib.algorithms.algorithm import Algorithm
from ray.rllib.callbacks.callbacks import RLlibCallback
from ray.rllib.core.rl_module import RLModuleSpec
from ray.tune.registry import register_env

from konic.agent import KonicAgent
from konic.callback import KonicRLCallback
from konic.engine.utils import get_module_factory


@dataclass
class TrainingResult:
    """
    Result from a single training iteration.

    This dataclass provides access to training metrics for external logging
    to providers like WandB, TensorBoard, MLflow, etc.

    Attributes:
        iteration: The current training iteration number (1-indexed).
        episode_return_mean: Mean episode return from this iteration.
        episode_length_mean: Mean episode length from this iteration.
        num_episodes: Number of episodes completed in this iteration.
        num_env_steps: Number of environment steps in this iteration.
        num_env_steps_lifetime: Total environment steps across all iterations.
        num_episodes_lifetime: Total episodes across all iterations.
        time_total_s: Total training time in seconds.
        fps: Frames (steps) per second throughput.
        learner_metrics: Dict of learner-specific metrics (loss, entropy, etc.).
        raw_result: The raw RLlib result dict for advanced usage.
    """

    iteration: int
    episode_return_mean: float = 0.0
    episode_length_mean: float = 0.0
    num_episodes: int = 0
    num_env_steps: int = 0
    num_env_steps_lifetime: int = 0
    num_episodes_lifetime: int = 0
    time_total_s: float = 0.0
    fps: float = 0.0
    learner_metrics: dict[str, dict[str, float]] = field(default_factory=dict)
    raw_result: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_rllib_result(cls, result: dict[str, Any], iteration: int) -> "TrainingResult":
        """
        Create a TrainingResult from an RLlib training result dict.

        Args:
            result: The raw result dict from Algorithm.train().
            iteration: The current iteration number.

        Returns:
            A TrainingResult instance with extracted metrics.
        """
        env_runners = result.get("env_runners", {})

        learner_metrics = {}
        for learner_id, learner_data in result.get("learners", {}).items():
            learner_metrics[learner_id] = {
                "policy_loss": learner_data.get("policy_loss", 0.0),
                "value_loss": learner_data.get("vf_loss", 0.0),
                "entropy": learner_data.get("entropy", 0.0),
                "kl_divergence": learner_data.get("kl", 0.0),
                "learning_rate": learner_data.get("curr_lr", 0.0),
                "grad_norm": learner_data.get("grad_gnorm", 0.0),
                "total_loss": learner_data.get("total_loss", 0.0),
            }

        time_total = result.get("time_total_s", 1.0)
        steps_lifetime = result.get("num_env_steps_sampled_lifetime", 0)
        fps = steps_lifetime / max(time_total, 0.001)

        return cls(
            iteration=iteration,
            episode_return_mean=env_runners.get("episode_return_mean", 0.0),
            episode_length_mean=env_runners.get("episode_len_mean", 0.0),
            num_episodes=result.get("num_episodes", 0),
            num_env_steps=result.get("num_env_steps_sampled", 0),
            num_env_steps_lifetime=steps_lifetime,
            num_episodes_lifetime=result.get("num_episodes_lifetime", 0),
            time_total_s=time_total,
            fps=fps,
            learner_metrics=learner_metrics,
            raw_result=result,
        )

    def to_dict(self) -> dict[str, Any]:
        """
        Convert to a flat dictionary suitable for logging.

        Returns:
            A flat dict with all metrics, suitable for WandB, TensorBoard, etc.
        """
        metrics = {
            "iteration": self.iteration,
            "episode_return_mean": self.episode_return_mean,
            "episode_length_mean": self.episode_length_mean,
            "num_episodes": self.num_episodes,
            "num_env_steps": self.num_env_steps,
            "num_env_steps_lifetime": self.num_env_steps_lifetime,
            "num_episodes_lifetime": self.num_episodes_lifetime,
            "time_total_s": self.time_total_s,
            "fps": self.fps,
        }

        for learner_id, learner_data in self.learner_metrics.items():
            for key, value in learner_data.items():
                metrics[f"learner/{learner_id}/{key}"] = value

        return metrics


class KonicEngine:
    def __init__(
        self,
        agent: KonicAgent,
        callback: type[RLlibCallback] | None = None,
    ):
        """
        Initialize the Konic engine.

        Args:
            agent: The KonicAgent to train.
            callback: Optional custom callback class. If not provided,
                      defaults to KonicRLCallback which tracks standard
                      RL metrics (episode return, loss, entropy, etc.).
        """
        self.agent = agent
        self.callback = callback if callback is not None else KonicRLCallback
        self._algo: Algorithm | None = None
        self._training_results: list[TrainingResult] = []

    @property
    def algorithm(self) -> Algorithm | None:
        """Get the underlying RLlib Algorithm instance (available after training starts)."""
        return self._algo

    @property
    def training_results(self) -> list[TrainingResult]:
        """Get all training results collected so far."""
        return self._training_results.copy()

    @property
    def latest_result(self) -> TrainingResult | None:
        """Get the most recent training result, or None if no training has occurred."""
        return self._training_results[-1] if self._training_results else None

    def _build_algorithm(self) -> Algorithm:
        """Build and return the RLlib algorithm."""
        module = self.agent.get_module()
        algorithm = module.algorithm
        environment = self.agent.get_environment()

        algo_config = get_module_factory(algorithm)

        def _register_environment(config):
            return environment

        register_env("konic-environment", _register_environment)

        if not ray.is_initialized():
            ray.init(include_dashboard=False)

        config = (
            algo_config()
            .framework("torch")
            .environment("konic-environment")
            .api_stack(enable_rl_module_and_learner=True, enable_env_runner_and_connector_v2=True)
            .rl_module(
                rl_module_spec=RLModuleSpec(module_class=module),
            )
            .callbacks(callbacks_class=self.callback)
            .env_runners(num_env_runners=2)
            .training(
                train_batch_size_per_learner=512,
                minibatch_size=64,
            )
        )

        return config.build_algo()

    def train(self, iterations: int) -> list[TrainingResult]:
        """
        Train the agent for the specified number of iterations.

        This method blocks until training is complete and returns all results.

        Args:
            iterations: Number of training iterations to run.

        Returns:
            List of TrainingResult objects, one per iteration.
        """
        results = list(self.train_iter(iterations))
        return results

    def train_iter(self, iterations: int) -> Generator[TrainingResult, None, None]:
        """
        Train the agent, yielding results after each iteration.

        This generator allows you to process results as they come in,
        useful for logging to external providers during training.

        Args:
            iterations: Number of training iterations to run.

        Yields:
            TrainingResult for each completed iteration.

        Example:
            engine = KonicEngine(agent)

            for result in engine.train_iter(100):
                wandb.log(result.to_dict())
                print(f"Iter {result.iteration}: return={result.episode_return_mean:.2f}")
        """
        try:
            self._algo = self._build_algorithm()

            for i in range(iterations):
                raw_result = self._algo.train()
                result = TrainingResult.from_rllib_result(raw_result, iteration=i + 1)
                self._training_results.append(result)
                yield result

        except Exception:
            traceback.print_exc()
        finally:
            if ray.is_initialized():
                ray.shutdown()

    def stop(self) -> None:
        """Stop training and cleanup resources."""
        if self._algo is not None:
            self._algo.stop()
            self._algo = None
        if ray.is_initialized():
            ray.shutdown()
