"""Configuration classes for LLM finetuning.

This module contains all configuration dataclasses for RLHF training:
- LoraConfig: LoRA adapter configuration
- TrainingConfig: PPO/RLHF training hyperparameters
- GenerationConfig: Text generation settings
- KonicFinetuningMethodType: Enum for finetuning methods
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class KonicFinetuningMethodType(str, Enum):
    """Enum representing available LLM finetuning methods.

    Currently supports:
        RLHF: Reinforcement Learning from Human Feedback using PPO.
              Uses a reward model to provide learning signal and
              KL penalty to prevent deviation from reference policy.
    """

    RLHF = "RLHF"


@dataclass
class LoraConfig:
    """Configuration for LoRA (Low-Rank Adaptation) finetuning.

    LoRA enables parameter-efficient finetuning by injecting trainable
    low-rank decomposition matrices into transformer layers.

    Attributes:
        r: The rank of the low-rank matrices. Higher values increase
            capacity but also memory usage. Typical values: 8, 16, 32, 64.
        lora_alpha: Scaling factor for LoRA updates. The effective learning
            rate is scaled by lora_alpha/r. Typically set to 2*r.
        lora_dropout: Dropout probability applied to LoRA layers during
            training. Helps prevent overfitting.
        target_modules: List of module names to apply LoRA to. Common targets
            are attention projection layers like "q_proj", "v_proj", "k_proj",
            "o_proj" for LLaMA-style models.
        bias: Whether to train bias parameters. Options: "none", "all", "lora_only".
        task_type: The task type for PEFT. Defaults to "CAUSAL_LM" for
            autoregressive language models.

    Example:
        >>> config = LoraConfig(
        ...     r=16,
        ...     lora_alpha=32,
        ...     target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],
        ... )
    """

    r: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.05
    target_modules: list[str] = field(default_factory=lambda: ["q_proj", "v_proj"])
    bias: str = "none"
    task_type: str = "CAUSAL_LM"
    fan_in_fan_out: bool = False

    def to_peft_config(self):
        """Convert to a PEFT LoraConfig object.

        Returns:
            A peft.LoraConfig instance configured with this object's parameters.
        """
        from peft import LoraConfig as PeftLoraConfig

        return PeftLoraConfig(
            r=self.r,
            lora_alpha=self.lora_alpha,
            lora_dropout=self.lora_dropout,
            target_modules=self.target_modules,
            bias=self.bias,
            task_type=self.task_type,
            fan_in_fan_out=self.fan_in_fan_out,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation.

        Returns:
            Dictionary with all configuration values.
        """
        return {
            "r": self.r,
            "lora_alpha": self.lora_alpha,
            "lora_dropout": self.lora_dropout,
            "target_modules": self.target_modules,
            "bias": self.bias,
            "task_type": self.task_type,
        }


@dataclass
class TrainingConfig:
    """Configuration for RLHF training hyperparameters.

    This dataclass contains all training-related hyperparameters for
    the RLHF/PPO optimization process.

    Attributes:
        learning_rate: Learning rate for the optimizer. Typical values
            for LLM finetuning are in the range 1e-6 to 5e-5.
        batch_size: Number of samples per training batch. Limited by
            GPU memory when training large models.
        gradient_accumulation_steps: Number of forward passes to accumulate
            gradients before performing an optimizer step. Effective batch
            size = batch_size * gradient_accumulation_steps.
        max_grad_norm: Maximum gradient norm for gradient clipping. Helps
            prevent exploding gradients during training.
        kl_penalty_weight: Weight (beta) for the KL divergence penalty
            against the reference model. Higher values keep the policy
            closer to the reference but may limit learning.
        clip_ratio: PPO clipping parameter (epsilon). Limits how much
            the policy can change in a single update.
        vf_coef: Coefficient for the value function loss in PPO.
        entropy_coef: Coefficient for entropy bonus. Higher values
            encourage exploration.
        gamma: Discount factor for future rewards.
        gae_lambda: Lambda parameter for Generalized Advantage Estimation.
        ppo_epochs: Number of PPO epochs per iteration.
        warmup_steps: Number of warmup steps for learning rate scheduler.
        weight_decay: Weight decay (L2 regularization) coefficient.

    Example:
        >>> config = TrainingConfig(
        ...     learning_rate=1e-5,
        ...     batch_size=8,
        ...     kl_penalty_weight=0.1,
        ... )
    """

    learning_rate: float = 1e-5
    batch_size: int = 8
    gradient_accumulation_steps: int = 4
    max_grad_norm: float = 1.0
    kl_penalty_weight: float = 0.1
    clip_ratio: float = 0.2
    vf_coef: float = 0.5
    entropy_coef: float = 0.01
    gamma: float = 1.0
    gae_lambda: float = 0.95
    ppo_epochs: int = 4
    warmup_steps: int = 100
    weight_decay: float = 0.01

    @property
    def effective_batch_size(self) -> int:
        """Calculate the effective batch size including gradient accumulation."""
        return self.batch_size * self.gradient_accumulation_steps

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation.

        Returns:
            Dictionary with all configuration values.
        """
        return {
            "learning_rate": self.learning_rate,
            "batch_size": self.batch_size,
            "gradient_accumulation_steps": self.gradient_accumulation_steps,
            "max_grad_norm": self.max_grad_norm,
            "kl_penalty_weight": self.kl_penalty_weight,
            "clip_ratio": self.clip_ratio,
            "vf_coef": self.vf_coef,
            "entropy_coef": self.entropy_coef,
            "gamma": self.gamma,
            "gae_lambda": self.gae_lambda,
            "ppo_epochs": self.ppo_epochs,
            "warmup_steps": self.warmup_steps,
            "weight_decay": self.weight_decay,
        }


@dataclass
class GenerationConfig:
    """Configuration for text generation during RLHF training.

    Controls how the language model generates responses during the
    rollout phase of RLHF training.

    Attributes:
        max_new_tokens: Maximum number of new tokens to generate per response.
        min_new_tokens: Minimum number of new tokens to generate. Helps
            prevent very short responses.
        max_length: Maximum total length (prompt + response) for tokenization.
        temperature: Sampling temperature. Higher values (>1) make output
            more random, lower values (<1) make it more deterministic.
        top_p: Nucleus sampling probability threshold. Only tokens with
            cumulative probability up to top_p are considered.
        top_k: Top-k sampling. Only the top k tokens are considered for
            sampling. Set to 0 to disable.
        do_sample: Whether to use sampling. If False, uses greedy decoding.
        repetition_penalty: Penalty for repeating tokens. Values > 1.0
            discourage repetition.
        pad_token_id: Token ID to use for padding. If None, will be set
            from the tokenizer.
        eos_token_id: Token ID(s) that signal end of generation.

    Example:
        >>> config = GenerationConfig(
        ...     max_new_tokens=128,
        ...     temperature=0.7,
        ...     top_p=0.9,
        ... )
    """

    max_new_tokens: int = 128
    min_new_tokens: int = 1
    max_length: int = 512
    temperature: float = 1.0
    top_p: float = 1.0
    top_k: int = 0
    do_sample: bool = True
    repetition_penalty: float = 1.0
    pad_token_id: int | None = None
    eos_token_id: int | list[int] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to a dictionary suitable for HuggingFace generate().

        Returns:
            Dict of generation parameters for model.generate().
        """
        config = {
            "max_new_tokens": self.max_new_tokens,
            "min_new_tokens": self.min_new_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "do_sample": self.do_sample,
            "repetition_penalty": self.repetition_penalty,
        }

        if self.top_k > 0:
            config["top_k"] = self.top_k

        if self.pad_token_id is not None:
            config["pad_token_id"] = self.pad_token_id

        if self.eos_token_id is not None:
            config["eos_token_id"] = self.eos_token_id

        return config
