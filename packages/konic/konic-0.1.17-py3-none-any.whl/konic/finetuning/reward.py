"""Reward composition for LLM finetuning.

This module contains all reward-related classes for RLHF training:
- llm_reward decorator for custom reward functions
- BaseRewardModel and HuggingFaceRewardModel for reward models
- Reducer strategies (WeightedSumReducer, MeanReducer, MaxReducer)
- BaseKonicLLMRewardComposer and KonicLLMRewardComposer for reward composition
"""

from __future__ import annotations

import functools
import gc
import logging
from abc import ABC, abstractmethod
from collections.abc import Callable
from enum import Enum
from typing import TYPE_CHECKING

from konic.common.errors import KonicValidationError

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    import torch

    from konic.finetuning.environment import BaseKonicLLMEnvironment


class LLMRewardKeys(str, Enum):
    """Keys for LLM reward function attributes."""

    CUSTOM_REWARD_FN_ATTR_KEY = "_is_llm_reward_fn"


def llm_reward(func: Callable) -> Callable:
    """Decorator to mark a method as a custom LLM reward function.

    Use this decorator on methods within a KonicLLMRewardComposer subclass
    to define custom reward logic. The decorated method should accept
    prompt and response arguments and return either a float or a dict
    of named rewards.

    The reward composer will automatically discover and call all
    @llm_reward decorated methods when computing the total reward.

    Args:
        func: The function to decorate. Should have signature:
            def my_reward(self, prompt: str, response: str) -> float | dict[str, float]

    Returns:
        The decorated function with the reward marker attribute.

    Example:
        >>> class MyRewardComposer(KonicLLMRewardComposer):
        ...     @llm_reward
        ...     def brevity_bonus(self, prompt: str, response: str) -> float:
        ...         '''Reward shorter responses.'''
        ...         return max(0, 1.0 - len(response) / 500)
        ...
        ...     @llm_reward
        ...     def multi_reward(self, prompt: str, response: str) -> dict:
        ...         '''Return multiple named rewards.'''
        ...         return {
        ...             "polite": 0.5 if "please" in response.lower() else 0.0,
        ...             "helpful": 0.3 if "help" in response.lower() else 0.0,
        ...         }
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    setattr(wrapper, LLMRewardKeys.CUSTOM_REWARD_FN_ATTR_KEY.value, True)
    return wrapper


def get_llm_reward_fns(obj: object) -> list[Callable]:
    """Get all @llm_reward decorated methods from an object.

    Args:
        obj: The object to inspect for reward functions.

    Returns:
        List of bound methods marked with @llm_reward.
    """
    reward_fns = []

    for name in dir(obj):
        if name.startswith("_"):
            continue

        try:
            attr = getattr(obj, name)
        except AttributeError:
            continue

        if callable(attr) and hasattr(attr, LLMRewardKeys.CUSTOM_REWARD_FN_ATTR_KEY.value):
            if getattr(attr, LLMRewardKeys.CUSTOM_REWARD_FN_ATTR_KEY.value):
                reward_fns.append(attr)

    return reward_fns


class BaseRewardModel(ABC):
    """Abstract base class for reward models.

    Reward models compute scalar rewards for prompt-response pairs.
    They can be pre-trained models loaded from HuggingFace Hub or
    custom implementations.

    Subclasses must implement:
    - name: Property returning the model's unique name
    - compute_reward(): Method to compute reward for a prompt-response pair

    Example:
        >>> class SentimentReward(BaseRewardModel):
        ...     @property
        ...     def name(self) -> str:
        ...         return "sentiment"
        ...
        ...     def compute_reward(self, prompt: str, response: str) -> float:
        ...         # Compute sentiment score
        ...         return sentiment_score
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the unique name of this reward model.

        This name is used as a key when combining multiple reward models
        and for logging/debugging purposes.

        Returns:
            A unique string identifier for this reward model.
        """
        pass

    @abstractmethod
    def compute_reward(
        self,
        prompt: str,
        response: str,
        **kwargs,
    ) -> float:
        """Compute the reward for a prompt-response pair.

        Args:
            prompt: The input prompt that was given to the model.
            response: The model's generated response.
            **kwargs: Additional arguments that specific implementations
                may use (e.g., reference response, metadata).

        Returns:
            A scalar float reward value.
        """
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r})"


class HuggingFaceRewardModel(BaseRewardModel):
    """Reward model loaded from HuggingFace Hub.

    This class wraps a HuggingFace sequence classification model to use
    as a reward model for RLHF training. The model should output a scalar
    reward (or logits that can be converted to a scalar).

    Commonly used with:
    - Sentiment classifiers (reward positive sentiment)
    - Preference models trained on human feedback
    - Quality scoring models

    Attributes:
        model_id: The HuggingFace model ID.
        device: Device for inference.

    Example:
        >>> # Use a sentiment model as reward
        >>> reward_model = HuggingFaceRewardModel(
        ...     model_id="lvwerra/distilbert-imdb",
        ...     label_index=1,  # Index for positive sentiment
        ... )
        >>> reward = reward_model.compute_reward(prompt, response)

        >>> # Use a trained reward model
        >>> reward_model = HuggingFaceRewardModel(
        ...     model_id="OpenAssistant/reward-model-deberta-v3-large-v2",
        ... )
    """

    def __init__(
        self,
        model_id: str,
        device: str | None = "auto",
        dtype: torch.dtype | None = None,
        max_length: int = 512,
        label_index: int | None = None,
        normalize: bool = False,
        normalize_min: float = -1.0,
        normalize_max: float = 1.0,
    ):
        """Initialize the HuggingFace reward model.

        Args:
            model_id: HuggingFace model ID (e.g., "OpenAssistant/reward-model").
            device: Device for inference. "auto" uses model's default.
            dtype: Data type for model weights. Defaults to float16.
            max_length: Maximum sequence length for tokenization.
            label_index: For multi-class models, which class logit to use
                as reward. If None, uses the first logit or mean of logits.
            normalize: Whether to normalize rewards to a fixed range.
            normalize_min: Minimum value for normalization.
            normalize_max: Maximum value for normalization.
        """
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        self._model_id = model_id
        self._dtype = dtype if dtype is not None else torch.float16
        self._max_length = max_length
        self._label_index = label_index
        self._normalize = normalize
        self._normalize_min = normalize_min
        self._normalize_max = normalize_max

        # Load model and tokenizer
        self._model = AutoModelForSequenceClassification.from_pretrained(
            model_id,
            dtype=self._dtype,
            device_map=device if device != "auto" else None,
        )
        self._tokenizer = AutoTokenizer.from_pretrained(model_id)

        # Ensure pad token is set
        if self._tokenizer.pad_token is None:
            self._tokenizer.pad_token = self._tokenizer.eos_token

        # Handle device
        if device == "auto":
            self._device = next(self._model.parameters()).device
        else:
            self._device = torch.device(device) if device else torch.device("cpu")
            self._model = self._model.to(self._device)

        # Set model to inference mode (no gradients)
        self._model.requires_grad_(False)

        # Track running stats for normalization
        self._running_mean = 0.0
        self._running_var = 1.0
        self._n_samples = 0

    @property
    def name(self) -> str:
        """Get the reward model name (derived from model ID)."""
        # Convert model ID to a valid name
        return f"hf_{self._model_id.replace('/', '_').replace('-', '_')}"

    @property
    def model_id(self) -> str:
        """Get the HuggingFace model ID."""
        return self._model_id

    def compute_reward(
        self,
        prompt: str,
        response: str,
        **kwargs,
    ) -> float:
        """Compute reward for a prompt-response pair.

        Args:
            prompt: The input prompt.
            response: The generated response.
            **kwargs: Additional arguments (ignored).

        Returns:
            Scalar reward value.
        """
        import torch

        # Combine prompt and response
        text = self._format_input(prompt, response)

        # Tokenize
        inputs = self._tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=self._max_length,
            padding=True,
        ).to(self._device)

        # Get model output
        with torch.no_grad():
            outputs = self._model(**inputs)

        # Extract reward from logits
        logits = outputs.logits

        if logits.shape[-1] == 1:
            # Single output - use directly
            reward = logits[0, 0].item()
        elif self._label_index is not None:
            # Use specified label index
            reward = logits[0, self._label_index].item()
        else:
            # Default: use first logit or mean
            reward = logits[0, 0].item()

        # Optional normalization
        if self._normalize:
            reward = self._normalize_reward(reward)

        return reward

    def _format_input(self, prompt: str, response: str) -> str:
        """Format prompt and response for the reward model.

        Different reward models expect different input formats.
        This method can be overridden for custom formatting.

        Args:
            prompt: The input prompt.
            response: The generated response.

        Returns:
            Formatted text for the reward model.
        """
        # Default: simple concatenation
        return f"{prompt}\n{response}"

    def _normalize_reward(self, reward: float) -> float:
        """Normalize reward using running statistics.

        Uses Welford's online algorithm for stable running variance.

        Args:
            reward: Raw reward value.

        Returns:
            Normalized reward in [normalize_min, normalize_max].
        """
        # Update running statistics
        self._n_samples += 1
        delta = reward - self._running_mean
        self._running_mean += delta / self._n_samples
        delta2 = reward - self._running_mean
        self._running_var += (delta * delta2 - self._running_var) / self._n_samples

        # Normalize to standard normal
        std = max(self._running_var**0.5, 1e-8)
        normalized = (reward - self._running_mean) / std

        # Scale to target range
        range_size = self._normalize_max - self._normalize_min
        scaled = (normalized + 3) / 6  # Assume ~99.7% within 3 std
        scaled = max(0, min(1, scaled))  # Clamp to [0, 1]
        return self._normalize_min + scaled * range_size

    def batch_compute_reward(
        self,
        prompts: list[str],
        responses: list[str],
    ) -> list[float]:
        """Compute rewards for a batch of prompt-response pairs.

        More efficient than calling compute_reward repeatedly.

        Args:
            prompts: List of prompts.
            responses: List of responses.

        Returns:
            List of scalar rewards.
        """
        import torch

        if len(prompts) != len(responses):
            raise KonicValidationError(
                f"prompts and responses must have same length "
                f"(got {len(prompts)} prompts, {len(responses)} responses)",
                field="prompts/responses",
            )

        # Format all inputs
        texts = [self._format_input(p, r) for p, r in zip(prompts, responses)]

        # Batch tokenize
        inputs = self._tokenizer(
            texts,
            return_tensors="pt",
            truncation=True,
            max_length=self._max_length,
            padding=True,
        ).to(self._device)

        # Get model outputs
        with torch.no_grad():
            outputs = self._model(**inputs)

        logits = outputs.logits

        # Extract rewards
        if logits.shape[-1] == 1:
            rewards = logits[:, 0].tolist()
        elif self._label_index is not None:
            rewards = logits[:, self._label_index].tolist()
        else:
            rewards = logits[:, 0].tolist()

        # Optional normalization
        if self._normalize:
            rewards = [self._normalize_reward(r) for r in rewards]

        return rewards

    def cleanup(self) -> None:
        """Release GPU memory and clean up resources.

        Call this method when the reward model is no longer needed to free
        GPU memory. This is especially important when using multiple reward
        models or in memory-constrained environments.

        Example:
            reward_model = HuggingFaceRewardModel("OpenAssistant/reward-model")
            # ... use the model ...
            reward_model.cleanup()  # Free GPU memory
        """
        import torch

        if hasattr(self, "_model") and self._model is not None:
            # Move model to CPU first to free GPU memory, then delete
            self._model.cpu()
            del self._model
            self._model = None

        if hasattr(self, "_tokenizer") and self._tokenizer is not None:
            del self._tokenizer
            self._tokenizer = None

        # Clear CUDA cache if available
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        gc.collect()

    def __del__(self) -> None:
        """Destructor to ensure cleanup is called when object is garbage collected."""
        try:
            self.cleanup()
        except Exception:
            # Suppress errors during garbage collection to avoid issues
            # during interpreter shutdown
            pass


class BaseRewardReducer(ABC):
    """Abstract base class for reward reduction strategies.

    Reducers combine multiple reward values into a single scalar.
    Different strategies can be used depending on the training objective.

    Example:
        >>> class ProductReducer(BaseRewardReducer):
        ...     def reduce(self, rewards: dict[str, float]) -> float:
        ...         result = 1.0
        ...         for value in rewards.values():
        ...             result *= value
        ...         return result
    """

    @abstractmethod
    def reduce(self, rewards: dict[str, float]) -> float:
        """Reduce multiple rewards to a single scalar.

        Args:
            rewards: Dictionary mapping reward names to values.

        Returns:
            Single scalar reward value.
        """
        pass


class WeightedSumReducer(BaseRewardReducer):
    """Reducer that computes weighted sum of rewards.

    This is the default reducer that combines rewards using weighted
    summation. Weights can be provided per reward name, with a default
    weight for unspecified rewards.

    Attributes:
        weights: Dictionary mapping reward names to weights.
        default_weight: Weight for rewards not in the weights dict.

    Example:
        >>> reducer = WeightedSumReducer(
        ...     weights={"sentiment": 1.0, "brevity": 0.5},
        ...     default_weight=0.1,
        ... )
        >>> total = reducer.reduce({"sentiment": 0.8, "brevity": 0.6, "other": 0.3})
        >>> # = 0.8 * 1.0 + 0.6 * 0.5 + 0.3 * 0.1 = 1.13
    """

    def __init__(
        self,
        weights: dict[str, float] | None = None,
        default_weight: float = 1.0,
    ):
        """Initialize the weighted sum reducer.

        Args:
            weights: Dictionary mapping reward names to weights.
                If None, all rewards use default_weight.
            default_weight: Weight for rewards not in the weights dict.
        """
        self._weights = weights or {}
        self._default_weight = default_weight

    def reduce(self, rewards: dict[str, float]) -> float:
        """Compute weighted sum of rewards.

        Args:
            rewards: Dictionary mapping reward names to values.

        Returns:
            Weighted sum of all reward values.
        """
        total = 0.0
        for name, value in rewards.items():
            weight = self._weights.get(name, self._default_weight)
            total += weight * value
        return total


class MeanReducer(BaseRewardReducer):
    """Reducer that computes the mean of all rewards.

    Simple reducer that averages all reward values regardless of name.

    Example:
        >>> reducer = MeanReducer()
        >>> total = reducer.reduce({"a": 1.0, "b": 2.0, "c": 3.0})
        >>> # = (1.0 + 2.0 + 3.0) / 3 = 2.0
    """

    def reduce(self, rewards: dict[str, float]) -> float:
        """Compute mean of all rewards.

        Args:
            rewards: Dictionary mapping reward names to values.

        Returns:
            Mean of all reward values.
        """
        if not rewards:
            return 0.0
        return sum(rewards.values()) / len(rewards)


class MaxReducer(BaseRewardReducer):
    """Reducer that returns the maximum reward.

    Useful when you want the best-performing reward signal to dominate.

    Example:
        >>> reducer = MaxReducer()
        >>> total = reducer.reduce({"a": 1.0, "b": 2.0, "c": 0.5})
        >>> # = 2.0
    """

    def reduce(self, rewards: dict[str, float]) -> float:
        """Return the maximum reward value.

        Args:
            rewards: Dictionary mapping reward names to values.

        Returns:
            Maximum reward value.
        """
        if not rewards:
            return 0.0
        return max(rewards.values())


class BaseKonicLLMRewardComposer(ABC):
    """Abstract base class for LLM reward composition.

    A reward composer combines multiple reward signals into a single
    scalar reward for RLHF training. It can use:
    - Pre-trained reward models (from HuggingFace or custom)
    - Custom reward functions (decorated with @llm_reward)
    - KL penalty against a reference model

    Subclasses must implement the compose() method which produces
    the final reward given a prompt-response pair.

    Example:
        >>> class MyRewardComposer(BaseKonicLLMRewardComposer):
        ...     def compose(self, prompt: str, response: str) -> float:
        ...         # Custom reward logic
        ...         return reward
    """

    _env: BaseKonicLLMEnvironment | None = None

    def set_env(self, env: BaseKonicLLMEnvironment) -> None:
        """Bind the environment to this reward composer.

        This allows the reward composer to access environment state
        if needed for reward computation.

        Args:
            env: The LLM environment to bind.
        """
        self._env = env

    @property
    def env(self) -> BaseKonicLLMEnvironment | None:
        """Get the bound environment."""
        return self._env

    @abstractmethod
    def compose(self, prompt: str, response: str) -> float:
        """Compose the total reward for a prompt-response pair.

        This method should combine all reward signals (from reward models
        and custom functions) into a single scalar reward.

        Args:
            prompt: The input prompt.
            response: The generated response.

        Returns:
            The total composed reward as a float.
        """
        pass


class KonicLLMRewardComposer(BaseKonicLLMRewardComposer):
    """Concrete reward composer for RLHF training.

    This class combines multiple reward sources:
    1. Registered reward models (HuggingFace or custom models)
    2. Custom reward functions decorated with @llm_reward

    All rewards are combined using a reducer strategy (default: weighted sum).

    Attributes:
        reward_models: List of registered reward models.
        reward_weights: Weights for each reward source.
        kl_penalty_weight: Weight for KL divergence penalty.
        reducer: Strategy for combining rewards.

    Example:
        >>> from konic.finetuning import KonicLLMRewardComposer, HuggingFaceRewardModel, llm_reward
        >>>
        >>> class MyRewardComposer(KonicLLMRewardComposer):
        ...     def __init__(self):
        ...         super().__init__(
        ...             reward_models=[
        ...                 HuggingFaceRewardModel("sentiment-model"),
        ...             ],
        ...             reward_weights={"sentiment": 1.0, "brevity": 0.5},
        ...         )
        ...
        ...     @llm_reward
        ...     def brevity_bonus(self, prompt: str, response: str) -> float:
        ...         '''Reward shorter responses.'''
        ...         return max(0, 1.0 - len(response) / 500)
        ...
        ...     @llm_reward
        ...     def helpfulness(self, prompt: str, response: str) -> float:
        ...         '''Check for helpful content.'''
        ...         helpful_words = ["help", "assist", "guide", "explain"]
        ...         count = sum(1 for w in helpful_words if w in response.lower())
        ...         return min(1.0, count * 0.25)
    """

    reducer: type[BaseRewardReducer] = WeightedSumReducer

    def __init__(
        self,
        reward_models: list[BaseRewardModel] | None = None,
        reward_weights: dict[str, float] | None = None,
        kl_penalty_weight: float = 0.0,
        reducer: type[BaseRewardReducer] | None = None,
    ):
        """Initialize the reward composer.

        Args:
            reward_models: List of reward models to use. Each model's name
                is used as the key in the rewards dict.
            reward_weights: Dictionary mapping reward names to weights.
                Applies to both reward models and @llm_reward functions.
            kl_penalty_weight: Weight (beta) for KL divergence penalty
                against the reference model. Set to 0 to disable.
            reducer: Reducer class for combining rewards. If None, uses
                WeightedSumReducer with the provided weights.
        """
        super().__init__()

        self._reward_models = reward_models or []
        self._reward_weights = reward_weights or {}
        self._kl_penalty_weight = kl_penalty_weight

        if reducer is not None:
            self.reducer = reducer

    def add_reward_model(
        self,
        model: BaseRewardModel,
        weight: float = 1.0,
    ) -> KonicLLMRewardComposer:
        """Add a reward model with optional weight.

        Args:
            model: The reward model to add.
            weight: Weight for this model's reward.

        Returns:
            Self for method chaining.
        """
        self._reward_models.append(model)
        self._reward_weights[model.name] = weight
        return self

    def set_reward_weight(self, name: str, weight: float) -> KonicLLMRewardComposer:
        """Set the weight for a specific reward.

        Args:
            name: Name of the reward (model name or function name).
            weight: Weight value.

        Returns:
            Self for method chaining.
        """
        self._reward_weights[name] = weight
        return self

    @property
    def kl_penalty_weight(self) -> float:
        """Get the KL penalty weight."""
        return self._kl_penalty_weight

    @kl_penalty_weight.setter
    def kl_penalty_weight(self, value: float) -> None:
        """Set the KL penalty weight."""
        self._kl_penalty_weight = value

    def compose(self, prompt: str, response: str) -> float:
        """Compose the total reward from all sources.

        Args:
            prompt: The input prompt.
            response: The generated response.

        Returns:
            Total composed reward.
        """
        rewards: dict[str, float] = {}

        # Get rewards from registered models
        for model in self._reward_models:
            try:
                reward = model.compute_reward(prompt, response)
                rewards[model.name] = reward
            except Exception as e:
                # Log error but continue with other rewards
                logger.warning(f"Reward model {model.name} failed: {e}")
                rewards[model.name] = 0.0

        # Get rewards from @llm_reward decorated methods
        custom_fns = get_llm_reward_fns(self)
        for fn in custom_fns:
            try:
                result = fn(prompt, response)

                if isinstance(result, dict):
                    # Function returned multiple named rewards
                    rewards.update(result)
                elif isinstance(result, (int | float)):
                    # Function returned single reward
                    rewards[fn.__name__] = float(result)
            except Exception as e:
                logger.warning(f"Custom reward function {fn.__name__} failed: {e}")

        # Reduce rewards to single value
        reducer_instance = self.reducer(weights=self._reward_weights)
        total_reward = reducer_instance.reduce(rewards)

        return total_reward

    def compute_kl_penalty(
        self,
        log_probs: torch.Tensor,
        ref_log_probs: torch.Tensor,
    ) -> torch.Tensor:
        """Compute KL divergence penalty between policy and reference.

        The KL penalty encourages the policy to stay close to the reference
        model, preventing reward hacking and maintaining generation quality.

        Args:
            log_probs: Log probabilities from the policy model.
            ref_log_probs: Log probabilities from the reference model.

        Returns:
            KL penalty tensor (can be added to rewards).
        """
        # KL(policy || ref) = sum(policy * log(policy / ref))
        # = sum(policy * (log_policy - log_ref))
        # For per-token KL: log_probs - ref_log_probs
        kl_div = log_probs - ref_log_probs

        return self._kl_penalty_weight * kl_div

    def get_reward_breakdown(
        self,
        prompt: str,
        response: str,
    ) -> dict[str, float]:
        """Get individual reward values without reduction.

        Useful for debugging and analysis.

        Args:
            prompt: The input prompt.
            response: The generated response.

        Returns:
            Dictionary of all reward values before reduction.
        """
        rewards: dict[str, float] = {}

        # Get rewards from registered models
        for model in self._reward_models:
            try:
                reward = model.compute_reward(prompt, response)
                rewards[model.name] = reward
            except Exception:
                rewards[model.name] = 0.0

        # Get rewards from @llm_reward decorated methods
        custom_fns = get_llm_reward_fns(self)
        for fn in custom_fns:
            try:
                result = fn(prompt, response)
                if isinstance(result, dict):
                    rewards.update(result)
                elif isinstance(result, (int | float)):
                    rewards[fn.__name__] = float(result)
            except Exception:
                pass

        return rewards
