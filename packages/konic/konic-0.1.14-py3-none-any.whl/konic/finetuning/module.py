"""LLM finetuning modules for RLHF training.

This module contains all module-related classes for RLHF:
- ValueHead: Neural network for value estimation in PPO
- LoRA utilities: apply_lora, get_lora_state_dict, count_trainable_parameters
- BaseKonicLLMModule: Abstract base class for LLM modules
- KonicTorchRLHF: Concrete PPO-based RLHF implementation
"""

from __future__ import annotations

import threading
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

import torch
import torch.nn as nn
import torch.nn.functional as F  # noqa: N812
from ray.rllib.core.columns import Columns
from ray.rllib.core.rl_module.apis import ValueFunctionAPI
from ray.rllib.core.rl_module.torch import TorchRLModule

from konic.finetuning.config import KonicFinetuningMethodType

if TYPE_CHECKING:
    from peft import PeftModel
    from transformers import PreTrainedModel, PreTrainedTokenizer

    from konic.finetuning.config import GenerationConfig, LoraConfig


# Standard deviation for weight initialization in value head
# Based on GPT-2 initialization strategy for stable training
VALUE_HEAD_INIT_STD = 0.02


class ValueHead(nn.Module):
    """Value head for estimating state values in PPO.

    The value head is a small neural network that takes the last hidden
    state from the language model and produces a scalar value estimate.
    This is used for computing advantages in PPO.

    Attributes:
        hidden_size: Size of the input hidden states.
        dropout: Dropout probability for regularization.

    Example:
        >>> value_head = ValueHead(hidden_size=4096)
        >>> hidden_states = model(input_ids, output_hidden_states=True).hidden_states[-1]
        >>> values = value_head(hidden_states)  # Shape: (batch_size,)
    """

    def __init__(
        self,
        hidden_size: int,
        dropout: float = 0.1,
    ):
        """Initialize the value head.

        Args:
            hidden_size: Size of the input hidden states from the LLM.
            dropout: Dropout probability for the hidden layer.
        """
        super().__init__()

        self.hidden_size = hidden_size
        self.dropout = nn.Dropout(dropout)

        # Two-layer MLP for value estimation
        self.layers = nn.Sequential(
            nn.Linear(hidden_size, hidden_size // 2),
            nn.Tanh(),
            nn.Dropout(dropout),
            nn.Linear(hidden_size // 2, 1),
        )

        # Initialize weights
        self._init_weights()

    def _init_weights(self) -> None:
        """Initialize weights with small values for stable training."""
        for module in self.layers:
            if isinstance(module, nn.Linear):
                nn.init.normal_(module.weight, mean=0.0, std=VALUE_HEAD_INIT_STD)
                if module.bias is not None:
                    nn.init.zeros_(module.bias)

    def forward(
        self,
        hidden_states: torch.Tensor,
        attention_mask: torch.Tensor | None = None,
    ) -> torch.Tensor:
        """Compute value estimates from hidden states.

        Args:
            hidden_states: Hidden states from the LLM.
                Shape: (batch_size, seq_len, hidden_size)
            attention_mask: Optional attention mask to identify the last
                non-padding token. Shape: (batch_size, seq_len)

        Returns:
            Value estimates. Shape: (batch_size,)
        """
        # Get the last token's hidden state (or last non-padding token)
        if attention_mask is not None:
            # Find the last non-padding position for each sequence
            # attention_mask: 1 for real tokens, 0 for padding
            seq_lengths = attention_mask.sum(dim=1) - 1  # 0-indexed
            batch_indices = torch.arange(hidden_states.size(0), device=hidden_states.device)
            last_hidden = hidden_states[batch_indices, seq_lengths]
        else:
            # Use the last token
            last_hidden = hidden_states[:, -1, :]

        # Apply dropout and MLP
        values = self.layers(last_hidden)

        # Squeeze to get (batch_size,) shape
        return values.squeeze(-1)

    def forward_all_tokens(
        self,
        hidden_states: torch.Tensor,
    ) -> torch.Tensor:
        """Compute value estimates for all tokens (for PPO training).

        Args:
            hidden_states: Hidden states from the LLM.
                Shape: (batch_size, seq_len, hidden_size)

        Returns:
            Value estimates for each token. Shape: (batch_size, seq_len)
        """
        batch_size, seq_len, _ = hidden_states.shape

        # Reshape to process all tokens
        flat_hidden = hidden_states.view(-1, self.hidden_size)
        flat_values = self.layers(flat_hidden)

        # Reshape back
        values = flat_values.view(batch_size, seq_len)

        return values


def apply_lora(
    model: PreTrainedModel,
    lora_config: LoraConfig,
) -> PeftModel:
    """Apply LoRA adapters to a HuggingFace model.

    This function wraps the model with PEFT LoRA adapters for
    parameter-efficient finetuning.

    Args:
        model: The base HuggingFace model to wrap.
        lora_config: LoRA configuration specifying rank, alpha, etc.

    Returns:
        A PeftModel with LoRA adapters applied.

    Example:
        >>> from transformers import AutoModelForCausalLM
        >>> from konic.finetuning import LoraConfig
        >>>
        >>> model = AutoModelForCausalLM.from_pretrained("meta-llama/Llama-2-7b-hf")
        >>> lora_config = LoraConfig(r=16, lora_alpha=32)
        >>> peft_model = apply_lora(model, lora_config)
    """
    from peft import get_peft_model

    peft_config = lora_config.to_peft_config()
    peft_model = get_peft_model(model, peft_config)

    return peft_model


def get_lora_state_dict(model: PeftModel) -> dict:
    """Get only the LoRA adapter weights from a PEFT model.

    This is useful for saving just the trained adapters without
    the full base model weights.

    Args:
        model: A PEFT model with LoRA adapters.

    Returns:
        State dict containing only LoRA parameters.

    Example:
        >>> lora_weights = get_lora_state_dict(peft_model)
        >>> torch.save(lora_weights, "lora_adapter.pt")
    """
    state_dict = {}

    for name, param in model.named_parameters():
        # LoRA parameters contain "lora_" in their name
        if "lora_" in name:
            state_dict[name] = param.data.clone()

    return state_dict


def count_trainable_parameters(model: PreTrainedModel) -> tuple[int, int, float]:
    """Count trainable and total parameters in a model.

    Args:
        model: The model to analyze.

    Returns:
        Tuple of (trainable_params, total_params, percentage).
    """
    trainable_params = 0
    total_params = 0

    for param in model.parameters():
        total_params += param.numel()
        if param.requires_grad:
            trainable_params += param.numel()

    percentage = 100 * trainable_params / total_params if total_params > 0 else 0

    return trainable_params, total_params, percentage


def get_target_modules_for_model(model_type: str) -> list[str]:
    """Get recommended LoRA target modules for common model architectures.

    Args:
        model_type: The model type/architecture (e.g., "llama", "mistral").

    Returns:
        List of module names to target with LoRA.
    """
    # Common target module patterns by model architecture
    target_modules_map = {
        "llama": ["q_proj", "v_proj", "k_proj", "o_proj"],
        "mistral": ["q_proj", "v_proj", "k_proj", "o_proj"],
        "falcon": ["query_key_value", "dense"],
        "gpt2": ["c_attn", "c_proj"],
        "gpt_neox": ["query_key_value", "dense"],
        "opt": ["q_proj", "v_proj", "k_proj", "out_proj"],
        "bloom": ["query_key_value", "dense"],
        "phi": ["q_proj", "v_proj", "k_proj", "dense"],
    }

    model_type_lower = model_type.lower()

    for key, modules in target_modules_map.items():
        if key in model_type_lower:
            return modules

    # Default for transformer models
    return ["q_proj", "v_proj"]


class BaseKonicLLMModule(TorchRLModule, ABC):
    """Abstract base class for LLM finetuning modules.

    This class extends Ray RLlib's TorchRLModule to provide a base for
    LLM-specific finetuning methods like RLHF. It defines the interface
    that all LLM finetuning modules must implement.

    Unlike standard RL modules that have separate policy and value networks,
    LLM modules use the language model itself as the policy, with an
    additional value head for PPO-style training.

    Attributes:
        method: The finetuning method (RLHF, etc.)

    Subclasses must implement:
        - base_model: Property returning the base LLM
        - ref_model: Property returning the frozen reference model
        - peft_model: Property returning the PEFT-wrapped model (if using LoRA)
        - generate(): Method for text generation
        - get_log_probs(): Method for computing log probabilities
    """

    method: KonicFinetuningMethodType

    @property
    @abstractmethod
    def base_model(self) -> PreTrainedModel:
        """Get the base language model.

        Returns:
            The HuggingFace model being finetuned.
        """
        pass

    @property
    @abstractmethod
    def ref_model(self) -> PreTrainedModel:
        """Get the frozen reference model.

        The reference model is used for computing KL penalty to prevent
        the policy from deviating too far from the original model.

        Returns:
            The frozen reference model.
        """
        pass

    @property
    def peft_model(self) -> PeftModel | None:
        """Get the PEFT-wrapped model if using LoRA.

        Returns:
            The PEFT model if using LoRA, None otherwise.
        """
        return None

    @abstractmethod
    def generate(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor | None = None,
        **kwargs,
    ) -> torch.Tensor:
        """Generate tokens using the policy model.

        Args:
            input_ids: Input token IDs. Shape: (batch_size, seq_len)
            attention_mask: Attention mask. Shape: (batch_size, seq_len)
            **kwargs: Additional generation arguments.

        Returns:
            Generated token IDs. Shape: (batch_size, new_seq_len)
        """
        pass

    @abstractmethod
    def get_log_probs(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor | None = None,
        labels: torch.Tensor | None = None,
    ) -> torch.Tensor:
        """Compute log probabilities for tokens.

        Args:
            input_ids: Input token IDs. Shape: (batch_size, seq_len)
            attention_mask: Attention mask. Shape: (batch_size, seq_len)
            labels: Token IDs to compute log probs for. If None, uses
                input_ids shifted by one position.

        Returns:
            Log probabilities. Shape: (batch_size, seq_len - 1)
        """
        pass

    @abstractmethod
    def get_ref_log_probs(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor | None = None,
        labels: torch.Tensor | None = None,
    ) -> torch.Tensor:
        """Compute log probabilities from the reference model.

        Used for computing KL divergence penalty.

        Args:
            input_ids: Input token IDs.
            attention_mask: Attention mask.
            labels: Token IDs to compute log probs for.

        Returns:
            Reference log probabilities.
        """
        pass

    def get_hidden_states(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor | None = None,
    ) -> torch.Tensor:
        """Get hidden states from the model.

        Args:
            input_ids: Input token IDs.
            attention_mask: Attention mask.

        Returns:
            Hidden states from the last layer.
        """
        outputs = self.base_model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            output_hidden_states=True,
        )
        return outputs.hidden_states[-1]


class KonicTorchRLHF(BaseKonicLLMModule, ValueFunctionAPI):
    """PPO-based RLHF module for LLM finetuning.

    This module wraps a HuggingFace language model for RLHF training using
    PPO. It maintains both a trainable policy model (optionally with LoRA)
    and a frozen reference model for KL divergence computation.

    The module integrates with Ray RLlib's distributed training infrastructure
    through the TorchRLModule interface.

    Attributes:
        method: The finetuning method (always RLHF for this class).
        model_name: HuggingFace model identifier.
        lora_config: Optional LoRA configuration for parameter-efficient training.
        generation_config: Configuration for text generation.

    Example:
        >>> from konic.finetuning.module import KonicTorchRLHF
        >>> from konic.finetuning.config import LoraConfig, GenerationConfig
        >>>
        >>> module = KonicTorchRLHF(
        ...     model_name="meta-llama/Llama-2-7b-hf",
        ...     lora_config=LoraConfig(r=16, lora_alpha=32),
        ...     generation_config=GenerationConfig(max_new_tokens=128),
        ... )
    """

    method = KonicFinetuningMethodType.RLHF

    def __init__(
        self,
        model_name: str,
        tokenizer: PreTrainedTokenizer | None = None,
        lora_config: LoraConfig | None = None,
        generation_config: GenerationConfig | None = None,
        device: str | torch.device | None = None,
        dtype: torch.dtype = torch.float16,
        trust_remote_code: bool = False,
    ):
        """Initialize the RLHF module.

        Args:
            model_name: HuggingFace model identifier or local path.
            tokenizer: Optional tokenizer. If None, loaded from model_name.
            lora_config: LoRA configuration. If None, full finetuning is used.
            generation_config: Text generation configuration.
            device: Device to load models on. Auto-detected if None.
            dtype: Model dtype for memory efficiency.
            trust_remote_code: Whether to trust remote code from the model
                repository. Defaults to False for security. Set to True only
                for models that require custom code (e.g., some LLaMA variants).
                WARNING: This executes arbitrary code from the model repository.
        """
        super().__init__()

        self.model_name = model_name
        self._lora_config = lora_config
        self._generation_config = generation_config
        self._dtype = dtype
        self._trust_remote_code = trust_remote_code

        # Determine device
        if device is None:
            self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self._device = torch.device(device)

        # Load models and tokenizer
        self._tokenizer = tokenizer
        self._base_model: PreTrainedModel | None = None
        self._ref_model: PreTrainedModel | None = None
        self._peft_model: PeftModel | None = None
        self._value_head: ValueHead | None = None

        # Track if models are loaded (lazy loading support)
        self._models_loaded = False
        self._setup_lock = threading.Lock()

    def setup(self) -> None:
        """Load and configure models.

        This is called by RLlib during module setup. It loads the base model,
        creates a frozen reference copy, applies LoRA if configured, and
        initializes the value head.

        Thread-safe: Uses a lock to prevent concurrent setup from multiple threads.
        """
        import warnings

        # Fast path: already loaded (check before acquiring lock)
        if self._models_loaded:
            return

        with self._setup_lock:
            # Double-check after acquiring lock (another thread may have completed setup)
            if self._models_loaded:
                return

            from transformers import AutoModelForCausalLM, AutoTokenizer

            # Log warning if trust_remote_code is enabled (security risk)
            if self._trust_remote_code:
                warnings.warn(
                    f"Loading model '{self.model_name}' with trust_remote_code=True. "
                    "This executes arbitrary code from the model repository. "
                    "Only use this with models you trust.",
                    UserWarning,
                    stacklevel=2,
                )

            # Load tokenizer if not provided
            if self._tokenizer is None:
                self._tokenizer = AutoTokenizer.from_pretrained(
                    self.model_name,
                    trust_remote_code=self._trust_remote_code,
                )
                # Ensure pad token is set
                if self._tokenizer.pad_token is None:
                    self._tokenizer.pad_token = self._tokenizer.eos_token

            # Load base model (policy model that will be trained)
            self._base_model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=self._dtype,
                trust_remote_code=self._trust_remote_code,
                device_map=self._device,
            )

            # Load reference model separately (frozen, for KL divergence computation)
            # Loading a separate instance avoids the memory overhead of deepcopy
            # and allows for potential memory optimization (e.g., different dtype)
            self._ref_model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=self._dtype,
                trust_remote_code=self._trust_remote_code,
                device_map=self._device,
            )
            self._ref_model.requires_grad_(False)

            # Apply LoRA if configured
            if self._lora_config is not None:
                self._peft_model = apply_lora(self._base_model, self._lora_config)
                # The peft_model wraps base_model, so update reference
                self._base_model = self._peft_model.get_base_model()

            # Initialize value head
            hidden_size = self._base_model.config.hidden_size
            self._value_head = ValueHead(hidden_size=hidden_size)
            self._value_head.to(self._device)

            self._models_loaded = True

    @property
    def base_model(self) -> PreTrainedModel:
        """Get the base language model."""
        if not self._models_loaded:
            self.setup()
        return self._base_model

    @property
    def ref_model(self) -> PreTrainedModel:
        """Get the frozen reference model."""
        if not self._models_loaded:
            self.setup()
        return self._ref_model

    @property
    def peft_model(self) -> PeftModel | None:
        """Get the PEFT-wrapped model if using LoRA."""
        return self._peft_model

    @property
    def tokenizer(self) -> PreTrainedTokenizer:
        """Get the tokenizer."""
        if not self._models_loaded:
            self.setup()
        return self._tokenizer

    @property
    def value_head(self) -> ValueHead:
        """Get the value head for PPO."""
        if not self._models_loaded:
            self.setup()
        return self._value_head

    def generate(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor | None = None,
        **kwargs,
    ) -> torch.Tensor:
        """Generate tokens using the policy model.

        Args:
            input_ids: Input token IDs. Shape: (batch_size, seq_len)
            attention_mask: Attention mask. Shape: (batch_size, seq_len)
            **kwargs: Additional generation arguments (override defaults).

        Returns:
            Generated token IDs including input. Shape: (batch_size, new_seq_len)
        """
        if not self._models_loaded:
            self.setup()

        # Build generation kwargs from config
        gen_kwargs = {}
        if self._generation_config is not None:
            gen_kwargs = {
                "max_new_tokens": self._generation_config.max_new_tokens,
                "temperature": self._generation_config.temperature,
                "top_p": self._generation_config.top_p,
                "top_k": self._generation_config.top_k,
                "do_sample": self._generation_config.do_sample,
                "repetition_penalty": self._generation_config.repetition_penalty,
            }

        # Override with any provided kwargs
        gen_kwargs.update(kwargs)

        # Set pad token id
        gen_kwargs["pad_token_id"] = self._tokenizer.pad_token_id

        # Use the active model (peft or base)
        model = self._peft_model if self._peft_model is not None else self._base_model

        with torch.no_grad():
            outputs = model.generate(
                input_ids=input_ids,
                attention_mask=attention_mask,
                **gen_kwargs,
            )

        return outputs

    def get_log_probs(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor | None = None,
        labels: torch.Tensor | None = None,
    ) -> torch.Tensor:
        """Compute log probabilities for tokens from the policy model.

        Args:
            input_ids: Input token IDs. Shape: (batch_size, seq_len)
            attention_mask: Attention mask. Shape: (batch_size, seq_len)
            labels: Token IDs to compute log probs for. If None, uses
                input_ids shifted by one position.

        Returns:
            Log probabilities. Shape: (batch_size, seq_len - 1)
        """
        if not self._models_loaded:
            self.setup()

        model = self._peft_model if self._peft_model is not None else self._base_model

        outputs = model(
            input_ids=input_ids,
            attention_mask=attention_mask,
            output_hidden_states=False,
        )

        # Get logits and compute log probs
        logits = outputs.logits  # (batch, seq_len, vocab_size)

        # Shift for next-token prediction
        shift_logits = logits[:, :-1, :]  # (batch, seq_len-1, vocab)
        shift_labels = labels[:, 1:] if labels is not None else input_ids[:, 1:]

        # Compute log softmax
        log_probs = F.log_softmax(shift_logits, dim=-1)

        # Gather log probs for actual tokens
        token_log_probs = log_probs.gather(
            dim=-1,
            index=shift_labels.unsqueeze(-1),
        ).squeeze(-1)

        return token_log_probs

    def get_ref_log_probs(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor | None = None,
        labels: torch.Tensor | None = None,
    ) -> torch.Tensor:
        """Compute log probabilities from the reference model.

        Args:
            input_ids: Input token IDs.
            attention_mask: Attention mask.
            labels: Token IDs to compute log probs for.

        Returns:
            Reference log probabilities.
        """
        if not self._models_loaded:
            self.setup()

        with torch.no_grad():
            outputs = self._ref_model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                output_hidden_states=False,
            )

            logits = outputs.logits
            shift_logits = logits[:, :-1, :]
            shift_labels = labels[:, 1:] if labels is not None else input_ids[:, 1:]

            log_probs = F.log_softmax(shift_logits, dim=-1)
            token_log_probs = log_probs.gather(
                dim=-1,
                index=shift_labels.unsqueeze(-1),
            ).squeeze(-1)

        return token_log_probs

    def compute_values(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor | None = None,
    ) -> torch.Tensor:
        """Compute value estimates for PPO.

        Args:
            input_ids: Input token IDs.
            attention_mask: Attention mask.

        Returns:
            Value estimates. Shape: (batch_size,)
        """
        hidden_states = self.get_hidden_states(input_ids, attention_mask)
        return self._value_head(hidden_states, attention_mask)

    def compute_values_for_all_tokens(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor | None = None,
    ) -> torch.Tensor:
        """Compute value estimates for all tokens (for GAE computation).

        Args:
            input_ids: Input token IDs.
            attention_mask: Attention mask.

        Returns:
            Value estimates. Shape: (batch_size, seq_len)
        """
        hidden_states = self.get_hidden_states(input_ids, attention_mask)
        return self._value_head.forward_all_tokens(hidden_states)

    def _forward_inference(self, batch: dict[str, Any]) -> dict[str, Any]:
        """Forward pass for inference (deployment).

        Used when the model is deployed for serving predictions.
        Generates responses without exploration noise.

        Args:
            batch: Dictionary containing input data with keys from Columns.

        Returns:
            Dictionary with generated actions (token IDs).
        """
        input_ids = batch[Columns.OBS]["input_ids"]
        attention_mask = batch[Columns.OBS].get("attention_mask")

        # Generate with greedy decoding for inference
        generated = self.generate(
            input_ids=input_ids,
            attention_mask=attention_mask,
            do_sample=False,  # Greedy for inference
        )

        # Extract only newly generated tokens
        new_tokens = generated[:, input_ids.shape[1] :]

        return {Columns.ACTIONS: new_tokens}

    def _forward_exploration(self, batch: dict[str, Any]) -> dict[str, Any]:
        """Forward pass for exploration (rollout collection).

        Used during training to collect experience. Samples from the
        policy distribution for exploration.

        Args:
            batch: Dictionary containing input data.

        Returns:
            Dictionary with sampled actions and action log probabilities.
        """
        input_ids = batch[Columns.OBS]["input_ids"]
        attention_mask = batch[Columns.OBS].get("attention_mask")

        # Generate with sampling for exploration
        generated = self.generate(
            input_ids=input_ids,
            attention_mask=attention_mask,
            do_sample=True,
        )

        # Compute log probs for the generated sequence
        log_probs = self.get_log_probs(
            input_ids=generated,
            attention_mask=self._create_attention_mask(generated),
        )

        # Extract only newly generated tokens
        new_tokens = generated[:, input_ids.shape[1] :]
        # Extract log probs for new tokens only
        new_log_probs = log_probs[:, input_ids.shape[1] - 1 :]

        return {
            Columns.ACTIONS: new_tokens,
            Columns.ACTION_LOGP: new_log_probs.sum(dim=-1),  # Sum over sequence
        }

    def _forward_train(self, batch: dict[str, Any]) -> dict[str, Any]:
        """Forward pass for training (PPO update).

        Computes all quantities needed for PPO loss:
        - Current policy log probabilities
        - Value function estimates
        - (Reference log probs computed separately for KL)

        Args:
            batch: Dictionary containing observations and actions.

        Returns:
            Dictionary with log probs, values, and other training outputs.
        """
        # Get the full sequence (prompt + response)
        input_ids = batch[Columns.OBS]["input_ids"]
        attention_mask = batch[Columns.OBS].get("attention_mask")
        actions = batch.get(Columns.ACTIONS)

        # If actions provided, concatenate with input for full sequence
        if actions is not None:
            full_ids = torch.cat([input_ids, actions], dim=1)
            if attention_mask is not None:
                action_mask = torch.ones_like(actions)
                full_mask = torch.cat([attention_mask, action_mask], dim=1)
            else:
                full_mask = None
        else:
            full_ids = input_ids
            full_mask = attention_mask

        # Compute policy log probabilities
        log_probs = self.get_log_probs(
            input_ids=full_ids,
            attention_mask=full_mask,
        )

        # Compute value estimates
        values = self.compute_values_for_all_tokens(
            input_ids=full_ids,
            attention_mask=full_mask,
        )

        # Compute reference log probs for KL penalty
        ref_log_probs = self.get_ref_log_probs(
            input_ids=full_ids,
            attention_mask=full_mask,
        )

        return {
            Columns.ACTION_LOGP: log_probs,
            Columns.VF_PREDS: values,
            "ref_log_probs": ref_log_probs,
        }

    # =========================================================================
    # ValueFunctionAPI Implementation
    # =========================================================================

    def compute_values_for_module(
        self,
        batch: dict[str, Any],
        module_id: str | None = None,
    ) -> dict[str, Any]:
        """Compute value function predictions for a batch.

        This method is part of the ValueFunctionAPI interface used by
        PPO for advantage estimation.

        Args:
            batch: Dictionary containing observation data.
            module_id: Optional module identifier (unused for single-agent).

        Returns:
            Dictionary with value function predictions.
        """
        input_ids = batch[Columns.OBS]["input_ids"]
        attention_mask = batch[Columns.OBS].get("attention_mask")

        values = self.compute_values(input_ids, attention_mask)

        return {Columns.VF_PREDS: values}

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def _create_attention_mask(self, input_ids: torch.Tensor) -> torch.Tensor:
        """Create attention mask from input_ids.

        Args:
            input_ids: Input token IDs.

        Returns:
            Attention mask (1 for real tokens, 0 for padding).
        """
        return (input_ids != self._tokenizer.pad_token_id).long()

    def get_trainable_parameters(self) -> list[torch.nn.Parameter]:
        """Get all trainable parameters.

        Returns parameters that require gradients, which will be:
        - LoRA parameters if using PEFT
        - All model parameters if full finetuning
        - Value head parameters (always trainable)
        """
        params = []

        if self._peft_model is not None:
            # Only LoRA parameters are trainable
            for param in self._peft_model.parameters():
                if param.requires_grad:
                    params.append(param)
        else:
            # Full finetuning - all parameters trainable
            for param in self._base_model.parameters():
                if param.requires_grad:
                    params.append(param)

        # Value head is always trainable
        for param in self._value_head.parameters():
            params.append(param)

        return params

    def save_pretrained(self, save_path: str) -> None:
        """Save the finetuned model.

        Saves either LoRA adapters (if using PEFT) or the full model.

        Args:
            save_path: Directory to save the model.
        """
        import os

        os.makedirs(save_path, exist_ok=True)

        if self._peft_model is not None:
            # Save only LoRA adapters
            self._peft_model.save_pretrained(save_path)
        else:
            # Save full model
            self._base_model.save_pretrained(save_path)

        # Save tokenizer
        self._tokenizer.save_pretrained(save_path)

        # Save value head
        value_head_path = os.path.join(save_path, "value_head.pt")
        torch.save(self._value_head.state_dict(), value_head_path)

    def load_pretrained(self, load_path: str) -> None:
        """Load a finetuned model from disk.

        Args:
            load_path: Directory containing saved model.
        """
        import os

        if self._peft_model is not None:
            from peft import PeftModel

            # Load LoRA adapters
            self._peft_model = PeftModel.from_pretrained(
                self._base_model,
                load_path,
            )
        else:
            from transformers import AutoModelForCausalLM

            # Load full model
            self._base_model = AutoModelForCausalLM.from_pretrained(
                load_path,
                torch_dtype=self._dtype,
                device_map=self._device,
            )

        # Load value head
        value_head_path = os.path.join(load_path, "value_head.pt")
        if os.path.exists(value_head_path):
            self._value_head.load_state_dict(torch.load(value_head_path))
