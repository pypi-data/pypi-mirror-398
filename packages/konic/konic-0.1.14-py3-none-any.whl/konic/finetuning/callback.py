"""Callbacks for LLM finetuning training.

This module contains callback classes for monitoring and controlling RLHF training:
- BaseKonicFinetuningCallback: Abstract base class for callbacks
- KonicFinetuningCallback: Default callback with logging and early stopping
- CompositeCallback: Combines multiple callbacks into one
"""

from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from konic.finetuning.engine import FinetuningIterationResult, FinetuningResult


class BaseKonicFinetuningCallback(ABC):
    """Abstract base class for finetuning callbacks.

    Callbacks receive notifications at various points during training,
    allowing custom logging, checkpointing, early stopping, etc.

    Subclass this to implement custom training behaviors.

    Example:
        >>> class MyCallback(BaseKonicFinetuningCallback):
        ...     def on_iteration_end(self, result):
        ...         print(f"Iteration {result.iteration}: reward={result.reward_mean:.3f}")
        ...
        ...     def should_stop_early(self, result):
        ...         return result.kl_divergence > 0.5  # Stop if KL too high
    """

    def on_train_begin(self, config: dict[str, Any]) -> None:
        """Called at the start of training.

        Args:
            config: Training configuration dictionary.
        """
        pass

    def on_train_end(self, result: FinetuningResult) -> None:
        """Called at the end of training.

        Args:
            result: Final training result with full history.
        """
        pass

    def on_iteration_begin(self, iteration: int) -> None:
        """Called at the start of each iteration.

        Args:
            iteration: Current iteration number.
        """
        pass

    def on_iteration_end(self, result: FinetuningIterationResult) -> None:
        """Called at the end of each iteration.

        Args:
            result: Result from the completed iteration.
        """
        pass

    def on_generation_begin(self, prompts: list[str]) -> None:
        """Called before generating responses.

        Args:
            prompts: List of input prompts for generation.
        """
        pass

    def on_generation_end(
        self,
        prompts: list[str],
        responses: list[str],
    ) -> None:
        """Called after generating responses.

        Args:
            prompts: Input prompts.
            responses: Generated responses.
        """
        pass

    def on_reward_computed(
        self,
        rewards: list[float],
        reward_breakdown: dict[str, list[float]],
    ) -> None:
        """Called after computing rewards.

        Args:
            rewards: Total rewards for each sample.
            reward_breakdown: Per-component rewards for each sample.
        """
        pass

    def on_checkpoint_saved(self, path: str, iteration: int) -> None:
        """Called after saving a checkpoint.

        Args:
            path: Path where checkpoint was saved.
            iteration: Iteration number of the checkpoint.
        """
        pass

    def should_stop_early(self, result: FinetuningIterationResult) -> bool:
        """Determine if training should stop early.

        Override this to implement custom early stopping logic.

        Args:
            result: Result from the current iteration.

        Returns:
            True if training should stop, False otherwise.
        """
        return False


class KonicFinetuningCallback(BaseKonicFinetuningCallback):
    """Default callback for RLHF training with logging and early stopping.

    This callback provides:
    - Console logging of training progress
    - Optional MLflow metric logging
    - KL-based early stopping
    - Sample response logging for debugging

    Attributes:
        log_interval: How often to log (every N iterations).
        log_samples: Whether to log sample prompt/response pairs.
        max_samples_to_log: Maximum samples to log per iteration.
        use_mlflow: Whether to log to MLflow.
        early_stop_kl_threshold: KL threshold for early stopping.
        early_stop_patience: Iterations to wait before stopping.

    Example:
        >>> callback = KonicFinetuningCallback(
        ...     log_interval=10,
        ...     log_samples=True,
        ...     early_stop_kl_threshold=0.2,
        ... )
    """

    def __init__(
        self,
        log_interval: int = 1,
        log_samples: bool = False,
        max_samples_to_log: int = 3,
        use_mlflow: bool = True,
        early_stop_kl_threshold: float | None = None,
        early_stop_patience: int = 5,
        verbose: bool = True,
    ):
        """Initialize the callback.

        Args:
            log_interval: Log every N iterations.
            log_samples: Whether to log sample generations.
            max_samples_to_log: Max samples to log per iteration.
            use_mlflow: Whether to use MLflow for logging.
            early_stop_kl_threshold: Stop if KL exceeds this value.
            early_stop_patience: Wait this many iterations before stopping.
            verbose: Whether to print to console.
        """
        self.log_interval = log_interval
        self.log_samples = log_samples
        self.max_samples_to_log = max_samples_to_log
        self.use_mlflow = use_mlflow
        self.early_stop_kl_threshold = early_stop_kl_threshold
        self.early_stop_patience = early_stop_patience
        self.verbose = verbose

        # Track early stopping state
        self._high_kl_count = 0
        self._mlflow_initialized = False

        # Store samples for logging
        self._current_prompts: list[str] = []
        self._current_responses: list[str] = []

    def on_train_begin(self, config: dict[str, Any]) -> None:
        """Log training start."""
        if self.verbose:
            print("\n" + "=" * 60)
            print("Starting RLHF Training")
            print("=" * 60)
            print(f"Model: {config.get('model_name', 'unknown')}")
            print(f"LoRA: {config.get('use_lora', False)}")
            print(f"Learning Rate: {config.get('learning_rate', 'N/A')}")
            print(f"Batch Size: {config.get('batch_size', 'N/A')}")
            print(f"Max Iterations: {config.get('max_iterations', 'N/A')}")
            print("=" * 60 + "\n")

        if self.use_mlflow:
            self._init_mlflow(config)

    def on_train_end(self, result: FinetuningResult) -> None:
        """Log training completion."""
        if self.verbose:
            print("\n" + result.summary())

        if self.use_mlflow and self._mlflow_initialized:
            import mlflow

            mlflow.log_metric("final/reward_mean", result.final_reward_mean)
            mlflow.log_metric("final/best_reward", result.best_reward)
            mlflow.log_metric("final/best_iteration", result.best_iteration)
            mlflow.log_metric("final/total_time_sec", result.total_time_sec)

    def on_iteration_end(self, result: FinetuningIterationResult) -> None:
        """Log iteration metrics."""
        if result.iteration % self.log_interval == 0:
            if self.verbose:
                self._log_iteration_console(result)

            if self.use_mlflow and self._mlflow_initialized:
                self._log_iteration_mlflow(result)

        # Log samples if enabled
        if self.log_samples and self._current_prompts:
            self._log_samples(result.iteration)

    def on_generation_end(
        self,
        prompts: list[str],
        responses: list[str],
    ) -> None:
        """Store generations for logging."""
        self._current_prompts = prompts[: self.max_samples_to_log]
        self._current_responses = responses[: self.max_samples_to_log]

    def should_stop_early(self, result: FinetuningIterationResult) -> bool:
        """Check KL-based early stopping."""
        if self.early_stop_kl_threshold is None:
            return False

        if result.kl_divergence > self.early_stop_kl_threshold:
            self._high_kl_count += 1
            if self.verbose:
                print(
                    f"Warning: KL divergence ({result.kl_divergence:.4f}) exceeds "
                    f"threshold ({self.early_stop_kl_threshold}). "
                    f"Count: {self._high_kl_count}/{self.early_stop_patience}"
                )

            if self._high_kl_count >= self.early_stop_patience:
                if self.verbose:
                    print("Early stopping triggered due to high KL divergence.")
                return True
        else:
            self._high_kl_count = 0

        return False

    def on_checkpoint_saved(self, path: str, iteration: int) -> None:
        """Log checkpoint save."""
        if self.verbose:
            print(f"Checkpoint saved: {path} (iteration {iteration})")

        if self.use_mlflow and self._mlflow_initialized:
            import mlflow

            mlflow.log_artifact(path)

    def _log_iteration_console(self, result: FinetuningIterationResult) -> None:
        """Print iteration metrics to console."""
        print(
            f"[Iter {result.iteration:4d}] "
            f"Reward: {result.reward_mean:7.3f} (+/- {result.reward_std:.3f}) | "
            f"KL: {result.kl_divergence:.4f} | "
            f"Loss: {result.total_loss:.4f} | "
            f"Time: {result.total_time_sec:.1f}s"
        )

    def _log_iteration_mlflow(self, result: FinetuningIterationResult) -> None:
        """Log iteration metrics to MLflow."""
        import mlflow

        metrics = result.to_dict()
        step = result.iteration

        for key, value in metrics.items():
            if isinstance(value, (int | float)) and key != "iteration":
                mlflow.log_metric(key, value, step=step)

    def _log_samples(self, iteration: int) -> None:
        """Log sample generations."""
        if self.verbose:
            print(f"\n--- Sample Generations (Iteration {iteration}) ---")
            for i, (prompt, response) in enumerate(
                zip(self._current_prompts, self._current_responses)
            ):
                print(f"\n[Sample {i + 1}]")
                print(f"Prompt: {prompt[:200]}...")
                print(f"Response: {response[:500]}...")
            print("-" * 50 + "\n")

        # Clear stored samples
        self._current_prompts = []
        self._current_responses = []

    def _init_mlflow(self, config: dict[str, Any]) -> None:
        """Initialize MLflow logging."""
        try:
            import mlflow

            # Log config as params
            for key, value in config.items():
                if isinstance(value, (str | int | float | bool)):
                    mlflow.log_param(key, value)

            self._mlflow_initialized = True
        except ImportError:
            if self.verbose:
                print("MLflow not installed. Skipping MLflow logging.")
            self.use_mlflow = False
        except Exception as e:
            if self.verbose:
                print(f"Failed to initialize MLflow: {e}")
            self.use_mlflow = False


class CompositeCallback(BaseKonicFinetuningCallback):
    """Combines multiple callbacks into one.

    Useful for applying multiple callback behaviors simultaneously.

    Example:
        >>> callback = CompositeCallback([
        ...     KonicFinetuningCallback(log_interval=10),
        ...     MyCustomCallback(),
        ... ])
    """

    def __init__(self, callbacks: list[BaseKonicFinetuningCallback]):
        """Initialize with list of callbacks.

        Args:
            callbacks: List of callbacks to compose.
        """
        self.callbacks = callbacks

    def on_train_begin(self, config: dict[str, Any]) -> None:
        for cb in self.callbacks:
            cb.on_train_begin(config)

    def on_train_end(self, result: FinetuningResult) -> None:
        for cb in self.callbacks:
            cb.on_train_end(result)

    def on_iteration_begin(self, iteration: int) -> None:
        for cb in self.callbacks:
            cb.on_iteration_begin(iteration)

    def on_iteration_end(self, result: FinetuningIterationResult) -> None:
        for cb in self.callbacks:
            cb.on_iteration_end(result)

    def on_generation_begin(self, prompts: list[str]) -> None:
        for cb in self.callbacks:
            cb.on_generation_begin(prompts)

    def on_generation_end(
        self,
        prompts: list[str],
        responses: list[str],
    ) -> None:
        for cb in self.callbacks:
            cb.on_generation_end(prompts, responses)

    def on_reward_computed(
        self,
        rewards: list[float],
        reward_breakdown: dict[str, list[float]],
    ) -> None:
        for cb in self.callbacks:
            cb.on_reward_computed(rewards, reward_breakdown)

    def on_checkpoint_saved(self, path: str, iteration: int) -> None:
        for cb in self.callbacks:
            cb.on_checkpoint_saved(path, iteration)

    def should_stop_early(self, result: FinetuningIterationResult) -> bool:
        # Stop if any callback requests it
        return any(cb.should_stop_early(result) for cb in self.callbacks)
