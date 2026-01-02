"""Agent classes for LLM finetuning.

This module contains the agent classes for RLHF training:
- BaseKonicFinetuningAgent: Abstract base class
- KonicFinetuningAgent: Concrete implementation with constructor-based configuration
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

from konic.agent.base import BaseKonicAgent
from konic.common.errors import KonicConfigurationError, KonicValidationError
from konic.finetuning.config import (
    GenerationConfig,
    KonicFinetuningMethodType,
    LoraConfig,
    TrainingConfig,
)

if TYPE_CHECKING:
    from konic.finetuning.dataset import DatasetConfig
    from konic.finetuning.environment import BaseKonicLLMEnvironment
    from konic.finetuning.module import BaseKonicLLMModule
    from konic.finetuning.reward import BaseKonicLLMRewardComposer


class BaseKonicFinetuningAgent(BaseKonicAgent, ABC):
    """Abstract base class for LLM finetuning agents.

    This class extends BaseKonicAgent with LLM-specific methods required
    for RLHF training. It defines the interface that all finetuning agents
    must implement.

    Subclasses must implement:
        - get_base_model(): Return the HuggingFace model ID
        - get_finetuning_method(): Return the finetuning method (RLHF)
        - get_lora_config(): Return LoRA configuration (optional)
        - get_reward_composer(): Return the reward composer
        - get_dataset_config(): Return dataset configuration

    In addition to the inherited BaseKonicAgent methods:
        - get_environment(): Return the LLM environment
        - get_environment_config(): Return environment configuration
        - get_algorithm_config(): Return algorithm configuration
        - get_module(): Return the finetuning module class
        - get_training_config(): Return training configuration

    Example:
        >>> class MyFinetuningAgent(BaseKonicFinetuningAgent):
        ...     def get_base_model(self) -> str:
        ...         return "meta-llama/Llama-2-7b-hf"
        ...
        ...     def get_finetuning_method(self):
        ...         return KonicFinetuningMethodType.RLHF
        ...     # ... implement other methods
    """

    @abstractmethod
    def get_base_model(self) -> str:
        """Return the HuggingFace model ID for the base model to finetune.

        Returns:
            A string representing the HuggingFace model ID, e.g.,
            "meta-llama/Llama-2-7b-hf" or "mistralai/Mistral-7B-v0.1".
        """
        pass

    @abstractmethod
    def get_finetuning_method(self) -> KonicFinetuningMethodType:
        """Return the finetuning method to use.

        Returns:
            A KonicFinetuningMethodType enum value. Currently only
            RLHF is supported.
        """
        pass

    @abstractmethod
    def get_lora_config(self) -> LoraConfig | None:
        """Return the LoRA configuration for parameter-efficient finetuning.

        Returns:
            A LoraConfig instance for LoRA finetuning, or None for full
            finetuning (not recommended for large models due to memory).
        """
        pass

    @abstractmethod
    def get_reward_composer(self) -> "BaseKonicLLMRewardComposer":
        """Return the reward composer for computing training rewards.

        The reward composer combines multiple reward signals (from reward
        models and custom functions) into a single scalar reward.

        Returns:
            A KonicLLMRewardComposer instance configured with reward models
            and/or custom reward functions.
        """
        pass

    @abstractmethod
    def get_dataset_config(self) -> "DatasetConfig":
        """Return the dataset configuration for training data.

        Returns:
            A DatasetConfig specifying the data source (HuggingFace Hub
            or Konic Cloud) and dataset parameters.
        """
        pass

    @abstractmethod
    def get_environment(self) -> "BaseKonicLLMEnvironment":
        """Return the LLM environment for training.

        Returns:
            A KonicLLMEnvironment instance configured for text generation.
        """
        pass

    @abstractmethod
    def get_module(self) -> "type[BaseKonicLLMModule]":
        """Return the finetuning module class.

        Returns:
            A class (not instance) that inherits from BaseKonicLLMModule,
            such as KonicTorchRLHF.
        """
        pass


class KonicFinetuningAgent(BaseKonicFinetuningAgent):
    """Concrete finetuning agent with constructor-based configuration.

    This class provides a flexible way to configure LLM finetuning through
    constructor parameters, similar to how KonicAgent works for standard RL.

    Parameters can be provided in the constructor or overridden by subclassing.
    The constructor approach is convenient for simple cases, while subclassing
    allows for more complex logic.

    Attributes:
        base_model: HuggingFace model ID for the base model.
        method: Finetuning method (RLHF).
        environment: LLM environment for training.
        reward_composer: Reward composer for computing rewards.
        module: Module class for the finetuning method.
        lora_config: LoRA configuration (optional).
        dataset_config: Dataset configuration.
        training_config: Training hyperparameters.
        generation_config: Text generation parameters.

    Example:
        >>> from konic.finetuning import (
        ...     KonicFinetuningAgent,
        ...     KonicLLMRewardComposer,
        ...     LoraConfig,
        ...     DatasetConfig,
        ... )
        >>>
        >>> agent = KonicFinetuningAgent(
        ...     base_model="meta-llama/Llama-2-7b-hf",
        ...     reward_composer=MyRewardComposer(),
        ...     lora_config=LoraConfig(r=16, lora_alpha=32),
        ...     dataset_config=DatasetConfig(
        ...         source="huggingface",
        ...         name="Anthropic/hh-rlhf",
        ...     ),
        ... )
    """

    def __init__(
        self,
        base_model: str,
        environment: "BaseKonicLLMEnvironment | None" = None,
        reward_composer: "BaseKonicLLMRewardComposer | None" = None,
        module: "type[BaseKonicLLMModule] | None" = None,
        lora_config: LoraConfig | None = None,
        dataset_config: "DatasetConfig | None" = None,
        training_config: TrainingConfig | dict[str, Any] | None = None,
        generation_config: GenerationConfig | dict[str, Any] | None = None,
        method: KonicFinetuningMethodType = KonicFinetuningMethodType.RLHF,
    ):
        """Initialize the finetuning agent.

        Args:
            base_model: HuggingFace model ID (e.g., "meta-llama/Llama-2-7b-hf").
            environment: LLM environment for training. If None, will be
                created automatically based on other parameters.
            reward_composer: Reward composer for computing rewards. Required
                for RLHF training.
            module: Module class for the finetuning method. If None, defaults
                to the appropriate module for the specified method.
            lora_config: LoRA configuration for parameter-efficient finetuning.
                If None, full finetuning is used (not recommended for large models).
            dataset_config: Dataset configuration specifying training data source.
                Required for training.
            training_config: Training hyperparameters. Can be a TrainingConfig
                instance or a dict. If None, uses default TrainingConfig.
            generation_config: Text generation parameters. Can be a GenerationConfig
                instance or a dict. If None, uses default GenerationConfig.
            method: Finetuning method. Currently only RLHF is supported.
        """
        self._base_model = base_model
        self._method = method
        self._environment = environment
        self._reward_composer = reward_composer
        self._lora_config = lora_config
        self._dataset_config = dataset_config

        # Handle training config
        if training_config is None:
            self._training_config = TrainingConfig()
        elif isinstance(training_config, dict):
            self._training_config = TrainingConfig(**training_config)
        else:
            self._training_config = training_config

        # Handle generation config
        if generation_config is None:
            self._generation_config = GenerationConfig()
        elif isinstance(generation_config, dict):
            self._generation_config = GenerationConfig(**generation_config)
        else:
            self._generation_config = generation_config

        # Set default module based on method
        if module is None:
            self._module = self._get_default_module()
        else:
            self._module = module

        # Track what was explicitly provided
        self._has_environment = environment is not None
        self._has_reward_composer = reward_composer is not None
        self._has_dataset_config = dataset_config is not None

    def _get_default_module(self) -> "type[BaseKonicLLMModule]":
        """Get the default module class for the finetuning method."""
        from konic.finetuning.module import KonicTorchRLHF

        if self._method == KonicFinetuningMethodType.RLHF:
            return KonicTorchRLHF
        else:
            raise KonicValidationError(
                f"Unknown finetuning method: {self._method}. Supported: RLHF",
                field="method",
            )

    def get_base_model(self) -> str:
        """Return the HuggingFace model ID."""
        return self._base_model

    def get_finetuning_method(self) -> KonicFinetuningMethodType:
        """Return the finetuning method."""
        return self._method

    def get_lora_config(self) -> LoraConfig | None:
        """Return the LoRA configuration."""
        return self._lora_config

    def get_reward_composer(self) -> "BaseKonicLLMRewardComposer":
        """Return the reward composer."""
        if self._reward_composer is None:
            raise KonicConfigurationError(
                "Reward composer is required for RLHF training. "
                "Please provide a reward_composer in the constructor.",
                config_key="reward_composer",
            )
        return self._reward_composer

    def get_dataset_config(self) -> "DatasetConfig":
        """Return the dataset configuration."""
        if self._dataset_config is None:
            raise KonicConfigurationError(
                "Dataset configuration is required for training. "
                "Please provide a dataset_config in the constructor.",
                config_key="dataset_config",
            )
        return self._dataset_config

    def get_environment(self) -> "BaseKonicLLMEnvironment":
        """Return the LLM environment."""
        if self._environment is None:
            raise KonicConfigurationError(
                "Environment is required for training. "
                "Please provide an environment in the constructor.",
                config_key="environment",
            )
        return self._environment

    def get_environment_config(self) -> dict[str, Any]:
        """Return environment configuration."""
        return self._generation_config.to_dict()

    def get_algorithm_config(self) -> dict[str, Any]:
        """Return algorithm configuration."""
        return {
            "learning_rate": self._training_config.learning_rate,
            "clip_ratio": self._training_config.clip_ratio,
            "entropy_coef": self._training_config.entropy_coef,
            "vf_coef": self._training_config.vf_coef,
            "max_grad_norm": self._training_config.max_grad_norm,
            "gamma": self._training_config.gamma,
            "gae_lambda": self._training_config.gae_lambda,
        }

    def get_module(self) -> "type[BaseKonicLLMModule]":
        """Return the finetuning module class."""
        return self._module

    def get_training_config(self) -> TrainingConfig:
        """Return the training configuration."""
        return self._training_config

    def get_generation_config(self) -> GenerationConfig:
        """Return the generation configuration."""
        return self._generation_config

    @property
    def training_config(self) -> TrainingConfig:
        """Access the TrainingConfig object directly."""
        return self._training_config

    @property
    def generation_config(self) -> GenerationConfig:
        """Access the GenerationConfig object directly."""
        return self._generation_config
