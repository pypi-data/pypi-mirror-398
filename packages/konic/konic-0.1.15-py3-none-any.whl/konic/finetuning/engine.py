"""Finetuning engine and result classes for RLHF training.

This module contains the training engine and result classes:
- FinetuningIterationResult: Metrics from a single training iteration
- FinetuningResult: Aggregated results from a complete training run
- KonicFinetuningEngine: Main engine for RLHF-based LLM finetuning
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import torch

from konic.common.errors import KonicValidationError
from konic.finetuning.callback import BaseKonicFinetuningCallback, KonicFinetuningCallback
from konic.finetuning.config import GenerationConfig, TrainingConfig
from konic.finetuning.dataset import DatasetLoader
from konic.finetuning.module import KonicTorchRLHF

if TYPE_CHECKING:
    from konic.finetuning.agent import BaseKonicFinetuningAgent
    from konic.finetuning.config import LoraConfig
    from konic.finetuning.dataset import DatasetConfig
    from konic.finetuning.reward import BaseKonicLLMRewardComposer

logger = logging.getLogger(__name__)


# Threshold for advantage standard deviation to avoid division by near-zero
# When advantages are nearly constant, we just center them instead of normalizing
ADVANTAGE_STD_THRESHOLD = 1e-6


@dataclass
class FinetuningIterationResult:
    """Result from a single finetuning iteration.

    Contains metrics from one PPO update cycle including reward statistics,
    loss values, and generation quality metrics.

    Attributes:
        iteration: Current iteration number.
        reward_mean: Mean reward across the batch.
        reward_std: Standard deviation of rewards.
        reward_min: Minimum reward in the batch.
        reward_max: Maximum reward in the batch.
        kl_divergence: Mean KL divergence from reference model.
        policy_loss: PPO policy (actor) loss.
        value_loss: PPO value (critic) loss.
        entropy_loss: Policy entropy loss (for exploration).
        total_loss: Combined loss value.
        response_length_mean: Mean length of generated responses.
        response_length_std: Standard deviation of response lengths.
        learning_rate: Current learning rate.
        clip_fraction: Fraction of updates clipped by PPO.
        approx_kl: Approximate KL divergence (for early stopping).
        explained_variance: How well value function predicts returns.
    """

    iteration: int
    reward_mean: float
    reward_std: float = 0.0
    reward_min: float = 0.0
    reward_max: float = 0.0
    kl_divergence: float = 0.0
    policy_loss: float = 0.0
    value_loss: float = 0.0
    entropy_loss: float = 0.0
    total_loss: float = 0.0
    response_length_mean: float = 0.0
    response_length_std: float = 0.0
    learning_rate: float = 0.0
    clip_fraction: float = 0.0
    approx_kl: float = 0.0
    explained_variance: float = 0.0

    # Additional metrics from reward breakdown
    reward_breakdown: dict[str, float] = field(default_factory=dict)

    # Timing information
    generation_time_sec: float = 0.0
    reward_compute_time_sec: float = 0.0
    update_time_sec: float = 0.0
    total_time_sec: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            "iteration": self.iteration,
            "reward/mean": self.reward_mean,
            "reward/std": self.reward_std,
            "reward/min": self.reward_min,
            "reward/max": self.reward_max,
            "kl/divergence": self.kl_divergence,
            "loss/policy": self.policy_loss,
            "loss/value": self.value_loss,
            "loss/entropy": self.entropy_loss,
            "loss/total": self.total_loss,
            "response/length_mean": self.response_length_mean,
            "response/length_std": self.response_length_std,
            "train/learning_rate": self.learning_rate,
            "train/clip_fraction": self.clip_fraction,
            "train/approx_kl": self.approx_kl,
            "train/explained_variance": self.explained_variance,
            "time/generation_sec": self.generation_time_sec,
            "time/reward_sec": self.reward_compute_time_sec,
            "time/update_sec": self.update_time_sec,
            "time/total_sec": self.total_time_sec,
            **{f"reward/{k}": v for k, v in self.reward_breakdown.items()},
        }


@dataclass
class FinetuningResult:
    """Final result from a complete finetuning run.

    Aggregates metrics across all iterations and includes final model
    information.

    Attributes:
        total_iterations: Total number of training iterations completed.
        best_iteration: Iteration with highest mean reward.
        best_reward: Highest mean reward achieved.
        final_reward_mean: Mean reward at final iteration.
        final_kl_divergence: KL divergence at final iteration.
        total_samples: Total number of samples processed.
        total_time_sec: Total training time in seconds.
        model_path: Path to saved model checkpoint.
        history: List of per-iteration results.
    """

    total_iterations: int
    best_iteration: int = 0
    best_reward: float = float("-inf")
    final_reward_mean: float = 0.0
    final_kl_divergence: float = 0.0
    total_samples: int = 0
    total_time_sec: float = 0.0
    model_path: str | None = None
    history: list[FinetuningIterationResult] = field(default_factory=list)

    # Configuration used
    model_name: str = ""
    lora_config: dict | None = None
    training_config: dict | None = None

    def add_iteration_result(self, result: FinetuningIterationResult) -> None:
        """Add an iteration result and update aggregates.

        Args:
            result: Result from a single iteration.
        """
        self.history.append(result)
        self.total_iterations = result.iteration

        # Update best if this is highest reward
        if result.reward_mean > self.best_reward:
            self.best_reward = result.reward_mean
            self.best_iteration = result.iteration

        # Update final values
        self.final_reward_mean = result.reward_mean
        self.final_kl_divergence = result.kl_divergence
        self.total_time_sec += result.total_time_sec

    def get_reward_curve(self) -> list[float]:
        """Get the reward progression over training.

        Returns:
            List of mean rewards per iteration.
        """
        return [r.reward_mean for r in self.history]

    def get_kl_curve(self) -> list[float]:
        """Get the KL divergence progression over training.

        Returns:
            List of KL divergences per iteration.
        """
        return [r.kl_divergence for r in self.history]

    def get_loss_curves(self) -> dict[str, list[float]]:
        """Get all loss curves.

        Returns:
            Dictionary mapping loss names to their progressions.
        """
        return {
            "policy": [r.policy_loss for r in self.history],
            "value": [r.value_loss for r in self.history],
            "entropy": [r.entropy_loss for r in self.history],
            "total": [r.total_loss for r in self.history],
        }

    def summary(self) -> str:
        """Get a human-readable summary of training results.

        Returns:
            Formatted summary string.
        """
        lines = [
            "=" * 50,
            "Finetuning Results Summary",
            "=" * 50,
            f"Model: {self.model_name}",
            f"Total Iterations: {self.total_iterations}",
            f"Total Samples: {self.total_samples}",
            f"Total Time: {self.total_time_sec:.1f}s",
            "-" * 50,
            f"Best Reward: {self.best_reward:.4f} (iteration {self.best_iteration})",
            f"Final Reward: {self.final_reward_mean:.4f}",
            f"Final KL Divergence: {self.final_kl_divergence:.4f}",
            "-" * 50,
        ]

        if self.model_path:
            lines.append(f"Model saved to: {self.model_path}")

        lines.append("=" * 50)
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "total_iterations": self.total_iterations,
            "best_iteration": self.best_iteration,
            "best_reward": self.best_reward,
            "final_reward_mean": self.final_reward_mean,
            "final_kl_divergence": self.final_kl_divergence,
            "total_samples": self.total_samples,
            "total_time_sec": self.total_time_sec,
            "model_path": self.model_path,
            "model_name": self.model_name,
            "lora_config": self.lora_config,
            "training_config": self.training_config,
            "history": [r.to_dict() for r in self.history],
        }


class KonicFinetuningEngine:
    """Engine for RLHF-based LLM finetuning.

    This engine orchestrates the complete RLHF training pipeline:
    1. Load base model and apply LoRA (if configured)
    2. Create frozen reference model for KL penalty
    3. Sample prompts from dataset
    4. Generate responses using current policy
    5. Compute rewards from reward composer
    6. Apply PPO updates with KL penalty

    The engine integrates with Ray for distributed training when available.

    Attributes:
        model_name: HuggingFace model identifier.
        lora_config: Optional LoRA configuration.
        training_config: Training hyperparameters.
        generation_config: Text generation parameters.
        reward_composer: Reward computation strategy.
        dataset_config: Training dataset configuration.

    Example:
        >>> from konic.finetuning import KonicFinetuningEngine
        >>> from konic.finetuning.config import LoraConfig, TrainingConfig
        >>>
        >>> engine = KonicFinetuningEngine(
        ...     model_name="meta-llama/Llama-2-7b-hf",
        ...     reward_composer=MyRewardComposer(),
        ...     dataset_config=DatasetConfig(name="imdb"),
        ...     lora_config=LoraConfig(r=16),
        ... )
        >>> result = engine.train(max_iterations=100)
    """

    def __init__(
        self,
        model_name: str,
        reward_composer: BaseKonicLLMRewardComposer,
        dataset_config: DatasetConfig,
        lora_config: LoraConfig | None = None,
        training_config: TrainingConfig | None = None,
        generation_config: GenerationConfig | None = None,
        callback: BaseKonicFinetuningCallback | None = None,
        checkpoint_dir: str | None = None,
        device: str | None = None,
    ):
        """Initialize the finetuning engine.

        Args:
            model_name: HuggingFace model identifier or local path.
            reward_composer: Reward composer for computing rewards.
            dataset_config: Configuration for training dataset.
            lora_config: Optional LoRA configuration.
            training_config: Training hyperparameters.
            generation_config: Text generation parameters.
            callback: Training callback for logging/early stopping.
            checkpoint_dir: Directory for saving checkpoints.
            device: Device to train on (auto-detected if None).
        """
        self.model_name = model_name
        self.reward_composer = reward_composer
        self.dataset_config = dataset_config
        self.lora_config = lora_config
        self.training_config = training_config or TrainingConfig()
        self.generation_config = generation_config or GenerationConfig()
        self.callback = callback or KonicFinetuningCallback()
        self.checkpoint_dir = checkpoint_dir

        # Device setup
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        # Components (initialized in setup)
        self._module: KonicTorchRLHF | None = None
        self._dataset_loader: DatasetLoader | None = None
        self._optimizer: torch.optim.Optimizer | None = None
        self._is_setup = False

    @classmethod
    def from_agent(cls, agent: BaseKonicFinetuningAgent) -> KonicFinetuningEngine:
        """Create engine from a finetuning agent.

        This is the primary way to create an engine from user-defined agents.

        Args:
            agent: A KonicFinetuningAgent instance.

        Returns:
            Configured KonicFinetuningEngine.
        """
        return cls(
            model_name=agent.get_base_model(),
            reward_composer=agent.get_reward_composer(),
            dataset_config=agent.get_dataset_config(),
            lora_config=agent.get_lora_config(),
            training_config=agent.get_training_config(),
            generation_config=agent.get_generation_config(),
        )

    def setup(self) -> None:
        """Initialize all components for training.

        This loads the model, applies LoRA, sets up the dataset loader,
        and creates the optimizer.
        """
        if self._is_setup:
            return

        # Validate training config before expensive operations
        if self.training_config.batch_size <= 0:
            raise KonicValidationError(
                f"batch_size must be positive, got {self.training_config.batch_size}",
                field="batch_size",
            )

        # Create RLHF module
        self._module = KonicTorchRLHF(
            model_name=self.model_name,
            lora_config=self.lora_config,
            generation_config=self.generation_config,
            device=self.device,
        )
        self._module.setup()

        # Create dataset loader
        self._dataset_loader = DatasetLoader(self.dataset_config)
        self._dataset_loader.load()

        # Create optimizer
        params = self._module.get_trainable_parameters()
        self._optimizer = torch.optim.AdamW(
            params,
            lr=self.training_config.learning_rate,
            weight_decay=self.training_config.weight_decay,
        )

        # Create checkpoint directory
        if self.checkpoint_dir:
            os.makedirs(self.checkpoint_dir, exist_ok=True)

        self._is_setup = True

    def train(
        self,
        max_iterations: int = 100,
        save_every: int | None = None,
    ) -> FinetuningResult:
        """Run the complete RLHF training loop.

        Args:
            max_iterations: Maximum number of training iterations.
            save_every: Save checkpoint every N iterations (None to disable).

        Returns:
            FinetuningResult with training history and final metrics.
        """
        self.setup()

        # Initialize result tracking
        result = FinetuningResult(
            total_iterations=0,
            model_name=self.model_name,
            lora_config=self.lora_config.to_dict() if self.lora_config else None,
            training_config=self.training_config.to_dict(),
        )

        # Build config for callback
        config = {
            "model_name": self.model_name,
            "use_lora": self.lora_config is not None,
            "learning_rate": self.training_config.learning_rate,
            "batch_size": self.training_config.batch_size,
            "max_iterations": max_iterations,
            "kl_penalty_weight": self.training_config.kl_penalty_weight,
        }
        self.callback.on_train_begin(config)

        try:
            for iteration in range(1, max_iterations + 1):
                self.callback.on_iteration_begin(iteration)

                # Run single training iteration
                try:
                    iter_result = self.train_iter(iteration)
                except StopIteration:
                    logger.info("Dataset exhausted, ending training")
                    break

                result.add_iteration_result(iter_result)
                result.total_samples += self.training_config.batch_size

                self.callback.on_iteration_end(iter_result)

                # Check early stopping
                if self.callback.should_stop_early(iter_result):
                    break

                # Save checkpoint
                if save_every and iteration % save_every == 0:
                    self._save_checkpoint(iteration)

        except KeyboardInterrupt:
            print("\nTraining interrupted by user.")

        # Save final model
        if self.checkpoint_dir:
            final_path = os.path.join(self.checkpoint_dir, "final")
            self._module.save_pretrained(final_path)
            result.model_path = final_path
            self.callback.on_checkpoint_saved(final_path, result.total_iterations)

        self.callback.on_train_end(result)
        return result

    def train_iter(self, iteration: int) -> FinetuningIterationResult:
        """Run a single training iteration.

        This performs:
        1. Sample batch of prompts
        2. Generate responses
        3. Compute rewards
        4. PPO update step

        Args:
            iteration: Current iteration number.

        Returns:
            Metrics from this iteration.
        """
        import statistics

        start_time = time.time()

        # Sample prompts from dataset (may raise StopIteration if exhausted)
        batch = next(self._dataset_loader.iter_batches(batch_size=self.training_config.batch_size))
        prompts = self._dataset_loader.get_prompts(batch)

        # Validate prompts
        if not prompts:
            raise KonicValidationError(
                "No prompts available from dataset. Check dataset configuration.",
                field="prompts",
            )

        # Generate responses
        gen_start = time.time()
        self.callback.on_generation_begin(prompts)
        responses, input_ids, response_ids = self._generate_responses(prompts)
        gen_time = time.time() - gen_start
        self.callback.on_generation_end(prompts, responses)

        # Compute rewards
        reward_start = time.time()
        rewards, reward_breakdown = self._compute_rewards(prompts, responses)
        reward_time = time.time() - reward_start
        self.callback.on_reward_computed(rewards, reward_breakdown)

        # PPO update
        update_start = time.time()
        losses = self._ppo_update(input_ids, response_ids, rewards)
        update_time = time.time() - update_start

        total_time = time.time() - start_time

        # Compute statistics
        rewards_tensor = torch.tensor(rewards)
        response_lengths = [len(r.split()) for r in responses]

        return FinetuningIterationResult(
            iteration=iteration,
            reward_mean=rewards_tensor.mean().item(),
            reward_std=rewards_tensor.std().item() if len(rewards) > 1 else 0.0,
            reward_min=rewards_tensor.min().item(),
            reward_max=rewards_tensor.max().item(),
            kl_divergence=losses.get("kl_divergence", 0.0),
            policy_loss=losses.get("policy_loss", 0.0),
            value_loss=losses.get("value_loss", 0.0),
            entropy_loss=losses.get("entropy_loss", 0.0),
            total_loss=losses.get("total_loss", 0.0),
            response_length_mean=statistics.mean(response_lengths),
            response_length_std=statistics.stdev(response_lengths)
            if len(response_lengths) > 1
            else 0.0,
            learning_rate=self._optimizer.param_groups[0]["lr"],
            clip_fraction=losses.get("clip_fraction", 0.0),
            approx_kl=losses.get("approx_kl", 0.0),
            reward_breakdown={k: statistics.mean(v) for k, v in reward_breakdown.items()},
            generation_time_sec=gen_time,
            reward_compute_time_sec=reward_time,
            update_time_sec=update_time,
            total_time_sec=total_time,
        )

    def _generate_responses(
        self,
        prompts: list[str],
    ) -> tuple[list[str], torch.Tensor, torch.Tensor]:
        """Generate responses for a batch of prompts.

        Args:
            prompts: List of input prompts.

        Returns:
            Tuple of (decoded responses, input token ids, response token ids).
        """
        tokenizer = self._module.tokenizer

        # Tokenize prompts
        inputs = tokenizer(
            prompts,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=self.generation_config.max_length,
        )
        input_ids = inputs["input_ids"].to(self.device)
        attention_mask = inputs["attention_mask"].to(self.device)

        # Generate
        with torch.no_grad():
            output_ids = self._module.generate(
                input_ids=input_ids,
                attention_mask=attention_mask,
            )

        # Extract response tokens (excluding input)
        response_ids = output_ids[:, input_ids.shape[1] :]

        # Decode responses
        responses = tokenizer.batch_decode(
            response_ids,
            skip_special_tokens=True,
        )

        return responses, input_ids, response_ids

    def _compute_rewards(
        self,
        prompts: list[str],
        responses: list[str],
    ) -> tuple[list[float], dict[str, list[float]]]:
        """Compute rewards for prompt-response pairs.

        Args:
            prompts: Input prompts.
            responses: Generated responses.

        Returns:
            Tuple of (total rewards, per-component reward breakdown).
        """
        rewards = []
        breakdowns: dict[str, list[float]] = {}

        for prompt, response in zip(prompts, responses):
            # Get composed reward
            reward = self.reward_composer.compose(prompt, response)
            rewards.append(reward)

            # Get breakdown for logging
            breakdown = self.reward_composer.get_reward_breakdown(prompt, response)
            for key, value in breakdown.items():
                if key not in breakdowns:
                    breakdowns[key] = []
                breakdowns[key].append(value)

        return rewards, breakdowns

    def _ppo_update(
        self,
        input_ids: torch.Tensor,
        response_ids: torch.Tensor,
        rewards: list[float],
    ) -> dict[str, float]:
        """Perform PPO update step.

        Args:
            input_ids: Prompt token IDs.
            response_ids: Response token IDs.
            rewards: Rewards for each sample.

        Returns:
            Dictionary of loss values and metrics.

        Raises:
            KonicValidationError: If inputs are invalid.
        """
        # Validate inputs
        batch_size = input_ids.size(0)
        if batch_size == 0:
            raise KonicValidationError(
                "Empty batch provided to PPO update",
                field="input_ids",
            )

        if len(rewards) != batch_size:
            raise KonicValidationError(
                f"Rewards length ({len(rewards)}) doesn't match batch size ({batch_size})",
                field="rewards",
            )

        # Combine input and response
        full_ids = torch.cat([input_ids, response_ids], dim=1)
        attention_mask = (full_ids != self._module.tokenizer.pad_token_id).long()

        # Get old log probs (before update)
        with torch.no_grad():
            old_log_probs = self._module.get_log_probs(full_ids, attention_mask)
            ref_log_probs = self._module.get_ref_log_probs(full_ids, attention_mask)
            old_values = self._module.compute_values_for_all_tokens(full_ids, attention_mask)

        # Convert rewards to tensor and compute advantages
        rewards_tensor = torch.tensor(rewards, device=self.device, dtype=torch.float32)

        # Expand rewards to sequence length (reward at last token)
        seq_len = full_ids.shape[1]
        reward_seq = torch.zeros(full_ids.shape[0], seq_len, device=self.device)
        reward_seq[:, -1] = rewards_tensor

        # Compute KL penalty
        kl_penalty = self.training_config.kl_penalty_weight * (old_log_probs - ref_log_probs)
        adjusted_rewards = reward_seq[:, :-1] - kl_penalty  # Align with log_probs shape

        # Compute advantages using GAE
        advantages = self._compute_advantages(
            adjusted_rewards,
            old_values[:, :-1],
            self.training_config.gamma,
            self.training_config.gae_lambda,
        )
        # Normalize advantages for stable training
        # When std is very small (all advantages similar), just center them
        advantages_std = advantages.std()
        if advantages_std > ADVANTAGE_STD_THRESHOLD:
            advantages = (advantages - advantages.mean()) / (advantages_std + 1e-8)
        else:
            advantages = advantages - advantages.mean()

        # Compute returns
        returns = advantages + old_values[:, :-1]

        # PPO epochs
        total_policy_loss = 0.0
        total_value_loss = 0.0
        total_entropy_loss = 0.0
        clip_fractions = []

        for _ in range(self.training_config.ppo_epochs):
            # Forward pass
            new_log_probs = self._module.get_log_probs(full_ids, attention_mask)
            new_values = self._module.compute_values_for_all_tokens(full_ids, attention_mask)

            # Policy loss (clipped surrogate)
            ratio = torch.exp(new_log_probs - old_log_probs)
            clip_ratio = torch.clamp(
                ratio,
                1.0 - self.training_config.clip_ratio,
                1.0 + self.training_config.clip_ratio,
            )
            policy_loss = -torch.min(
                ratio * advantages,
                clip_ratio * advantages,
            ).mean()

            # Value loss
            value_loss = 0.5 * ((new_values[:, :-1] - returns) ** 2).mean()

            # Entropy bonus (encourage exploration)
            # Simplified entropy from log_probs
            entropy = -new_log_probs.mean()
            entropy_loss = -self.training_config.entropy_coef * entropy

            # Total loss
            loss = policy_loss + self.training_config.vf_coef * value_loss + entropy_loss

            # Backward pass
            self._optimizer.zero_grad()
            loss.backward()

            # Gradient clipping
            torch.nn.utils.clip_grad_norm_(
                self._module.get_trainable_parameters(),
                self.training_config.max_grad_norm,
            )

            self._optimizer.step()

            # Track metrics
            total_policy_loss += policy_loss.item()
            total_value_loss += value_loss.item()
            total_entropy_loss += entropy_loss.item()
            clip_fractions.append(
                ((ratio - 1.0).abs() > self.training_config.clip_ratio).float().mean().item()
            )

        num_epochs = self.training_config.ppo_epochs

        # Compute final KL for monitoring
        with torch.no_grad():
            final_log_probs = self._module.get_log_probs(full_ids, attention_mask)
            approx_kl = (old_log_probs - final_log_probs).mean().item()
            kl_divergence = (old_log_probs - ref_log_probs).mean().item()

        return {
            "policy_loss": total_policy_loss / num_epochs,
            "value_loss": total_value_loss / num_epochs,
            "entropy_loss": total_entropy_loss / num_epochs,
            "total_loss": (total_policy_loss + total_value_loss + total_entropy_loss) / num_epochs,
            "clip_fraction": sum(clip_fractions) / len(clip_fractions),
            "approx_kl": approx_kl,
            "kl_divergence": kl_divergence,
        }

    def _compute_advantages(
        self,
        rewards: torch.Tensor,
        values: torch.Tensor,
        gamma: float,
        gae_lambda: float,
    ) -> torch.Tensor:
        """Compute GAE advantages.

        Args:
            rewards: Rewards at each timestep.
            values: Value estimates at each timestep.
            gamma: Discount factor.
            gae_lambda: GAE lambda parameter.

        Returns:
            Advantage estimates.
        """
        advantages = torch.zeros_like(rewards)
        last_gae = 0

        for t in reversed(range(rewards.shape[1])):
            if t == rewards.shape[1] - 1:
                next_value = 0
            else:
                next_value = values[:, t + 1]

            delta = rewards[:, t] + gamma * next_value - values[:, t]
            advantages[:, t] = last_gae = delta + gamma * gae_lambda * last_gae

        return advantages

    def _save_checkpoint(self, iteration: int) -> None:
        """Save a training checkpoint.

        Args:
            iteration: Current iteration number.
        """
        if not self.checkpoint_dir:
            return

        checkpoint_path = os.path.join(self.checkpoint_dir, f"checkpoint-{iteration}")
        self._module.save_pretrained(checkpoint_path)

        # Save optimizer state
        optimizer_path = os.path.join(checkpoint_path, "optimizer.pt")
        torch.save(self._optimizer.state_dict(), optimizer_path)

        self.callback.on_checkpoint_saved(checkpoint_path, iteration)

    def evaluate(
        self,
        prompts: list[str],
    ) -> dict[str, Any]:
        """Evaluate the current model on given prompts.

        Args:
            prompts: List of prompts to evaluate.

        Returns:
            Dictionary with generated responses and metrics.
        """
        self.setup()

        responses, _, _ = self._generate_responses(prompts)
        rewards, breakdown = self._compute_rewards(prompts, responses)

        return {
            "prompts": prompts,
            "responses": responses,
            "rewards": rewards,
            "reward_mean": sum(rewards) / len(rewards),
            "reward_breakdown": breakdown,
        }
