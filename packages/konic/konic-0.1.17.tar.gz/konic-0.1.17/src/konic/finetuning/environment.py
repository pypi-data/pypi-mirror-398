"""Environment classes for LLM finetuning.

This module contains all environment-related classes for RLHF training:
- TokenizerWrapper: Wrapper around HuggingFace tokenizers
- PromptTemplate: Template for formatting prompts
- BaseKonicLLMEnvironment: Abstract base environment
- KonicLLMEnvironment: Concrete environment implementation
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import gymnasium as gym
import numpy as np
import torch
from transformers import PreTrainedTokenizer, PreTrainedTokenizerFast

if TYPE_CHECKING:
    from transformers import PreTrainedModel

    from konic.finetuning.config import GenerationConfig
    from konic.finetuning.reward import BaseKonicLLMRewardComposer


class TokenizerWrapper:
    """Wrapper around HuggingFace tokenizers with convenience methods.

    This class provides a unified interface for tokenization operations
    commonly needed during RLHF training, including padding, truncation,
    and special token handling.

    Attributes:
        tokenizer: The underlying HuggingFace tokenizer.

    Example:
        >>> from transformers import AutoTokenizer
        >>> hf_tokenizer = AutoTokenizer.from_pretrained("meta-llama/Llama-2-7b-hf")
        >>> wrapper = TokenizerWrapper(hf_tokenizer)
        >>> tokens = wrapper.encode("Hello, world!")
        >>> text = wrapper.decode(tokens)
    """

    def __init__(
        self,
        tokenizer: PreTrainedTokenizer | PreTrainedTokenizerFast,
    ):
        """Initialize the tokenizer wrapper.

        Args:
            tokenizer: A HuggingFace PreTrainedTokenizer or
                PreTrainedTokenizerFast instance.
        """
        self._tokenizer = tokenizer

        # Ensure pad token is set
        if self._tokenizer.pad_token is None:
            self._tokenizer.pad_token = self._tokenizer.eos_token
            self._tokenizer.pad_token_id = self._tokenizer.eos_token_id

    @property
    def tokenizer(self) -> PreTrainedTokenizer | PreTrainedTokenizerFast:
        """Get the underlying HuggingFace tokenizer."""
        return self._tokenizer

    @property
    def vocab_size(self) -> int:
        """Get the vocabulary size."""
        return self._tokenizer.vocab_size

    @property
    def pad_token(self) -> str:
        """Get the padding token."""
        return self._tokenizer.pad_token

    @property
    def pad_token_id(self) -> int:
        """Get the padding token ID."""
        return self._tokenizer.pad_token_id

    @property
    def eos_token(self) -> str:
        """Get the end-of-sequence token."""
        return self._tokenizer.eos_token

    @property
    def eos_token_id(self) -> int:
        """Get the end-of-sequence token ID."""
        return self._tokenizer.eos_token_id

    @property
    def bos_token(self) -> str | None:
        """Get the beginning-of-sequence token."""
        return self._tokenizer.bos_token

    @property
    def bos_token_id(self) -> int | None:
        """Get the beginning-of-sequence token ID."""
        return self._tokenizer.bos_token_id

    def encode(
        self,
        text: str,
        max_length: int | None = None,
        padding: bool | str = False,
        truncation: bool = True,
        return_tensors: str | None = None,
        add_special_tokens: bool = True,
    ) -> list[int] | torch.Tensor:
        """Encode text to token IDs.

        Args:
            text: The text to encode.
            max_length: Maximum sequence length. If None, no limit is applied.
            padding: Padding strategy. Can be True, False, "max_length", or "longest".
            truncation: Whether to truncate sequences longer than max_length.
            return_tensors: If "pt", returns PyTorch tensors. If None, returns lists.
            add_special_tokens: Whether to add special tokens (BOS, EOS).

        Returns:
            Token IDs as a list or tensor.
        """
        result = self._tokenizer.encode(
            text,
            max_length=max_length,
            padding=padding,
            truncation=truncation,
            return_tensors=return_tensors,
            add_special_tokens=add_special_tokens,
        )
        return result

    def decode(
        self,
        token_ids: list[int] | torch.Tensor,
        skip_special_tokens: bool = True,
        clean_up_tokenization_spaces: bool = True,
    ) -> str:
        """Decode token IDs to text.

        Args:
            token_ids: Token IDs to decode.
            skip_special_tokens: Whether to skip special tokens in output.
            clean_up_tokenization_spaces: Whether to clean up extra spaces.

        Returns:
            Decoded text string.
        """
        if isinstance(token_ids, torch.Tensor):
            token_ids = token_ids.tolist()
        return self._tokenizer.decode(
            token_ids,
            skip_special_tokens=skip_special_tokens,
            clean_up_tokenization_spaces=clean_up_tokenization_spaces,
        )

    def batch_encode(
        self,
        texts: list[str],
        max_length: int | None = None,
        padding: bool | str = True,
        truncation: bool = True,
        return_tensors: str = "pt",
        add_special_tokens: bool = True,
    ) -> dict[str, torch.Tensor]:
        """Batch encode multiple texts.

        Args:
            texts: List of texts to encode.
            max_length: Maximum sequence length.
            padding: Padding strategy.
            truncation: Whether to truncate.
            return_tensors: Return type ("pt" for PyTorch).
            add_special_tokens: Whether to add special tokens.

        Returns:
            Dictionary with "input_ids" and "attention_mask" tensors.
        """
        return self._tokenizer(
            texts,
            max_length=max_length,
            padding=padding,
            truncation=truncation,
            return_tensors=return_tensors,
            add_special_tokens=add_special_tokens,
        )

    def batch_decode(
        self,
        token_ids: list[list[int]] | torch.Tensor,
        skip_special_tokens: bool = True,
    ) -> list[str]:
        """Batch decode token IDs to texts.

        Args:
            token_ids: Batch of token ID sequences.
            skip_special_tokens: Whether to skip special tokens.

        Returns:
            List of decoded text strings.
        """
        return self._tokenizer.batch_decode(
            token_ids,
            skip_special_tokens=skip_special_tokens,
        )

    def get_prompt_length(self, prompt: str) -> int:
        """Get the token length of a prompt.

        Args:
            prompt: The prompt text.

        Returns:
            Number of tokens in the prompt.
        """
        return len(self.encode(prompt, add_special_tokens=False))

    def truncate_to_max_length(
        self,
        text: str,
        max_length: int,
        from_end: bool = False,
    ) -> str:
        """Truncate text to a maximum token length.

        Args:
            text: The text to truncate.
            max_length: Maximum number of tokens.
            from_end: If True, keep the last max_length tokens.
                If False, keep the first max_length tokens.

        Returns:
            Truncated text.
        """
        tokens = self.encode(text, add_special_tokens=False)
        if len(tokens) <= max_length:
            return text

        if from_end:
            tokens = tokens[-max_length:]
        else:
            tokens = tokens[:max_length]

        return self.decode(tokens)

    def __call__(
        self,
        text: str | list[str],
        **kwargs: Any,
    ) -> dict[str, torch.Tensor]:
        """Call the tokenizer directly.

        Args:
            text: Text or list of texts to tokenize.
            **kwargs: Additional arguments passed to the tokenizer.

        Returns:
            Tokenizer output dictionary.
        """
        return self._tokenizer(text, **kwargs)


@dataclass
class PromptTemplate:
    """Template for formatting prompts during RLHF training.

    This class handles prompt formatting for different model types and
    training scenarios. It supports both simple prompts and chat-style
    multi-turn conversations.

    Attributes:
        system_prompt: Optional system prompt prepended to all inputs.
        user_prefix: Prefix before user messages (e.g., "User: ", "[INST] ").
        assistant_prefix: Prefix before assistant responses (e.g., "Assistant: ").
        user_suffix: Suffix after user messages (e.g., " [/INST]").
        assistant_suffix: Suffix after assistant responses.
        separator: Separator between turns in multi-turn conversations.

    Example:
        >>> # LLaMA-2 chat template
        >>> template = PromptTemplate(
        ...     system_prompt="You are a helpful assistant.",
        ...     user_prefix="[INST] ",
        ...     assistant_prefix="",
        ...     user_suffix=" [/INST]",
        ...     assistant_suffix="</s>",
        ... )
        >>> formatted = template.format_prompt("Hello!")
    """

    system_prompt: str | None = None
    user_prefix: str = ""
    assistant_prefix: str = ""
    user_suffix: str = ""
    assistant_suffix: str = ""
    separator: str = "\n"

    def format_prompt(
        self,
        user_message: str,
        include_assistant_prefix: bool = True,
    ) -> str:
        """Format a single user message as a prompt.

        Args:
            user_message: The user's input message.
            include_assistant_prefix: Whether to include the assistant
                prefix at the end (for generation to continue from).

        Returns:
            Formatted prompt string ready for the model.
        """
        parts = []

        if self.system_prompt:
            parts.append(self.system_prompt)
            parts.append(self.separator)

        parts.append(self.user_prefix)
        parts.append(user_message)
        parts.append(self.user_suffix)

        if include_assistant_prefix:
            parts.append(self.assistant_prefix)

        return "".join(parts)

    def format_conversation(
        self,
        turns: list[dict[str, str]],
        include_assistant_prefix: bool = True,
    ) -> str:
        """Format a multi-turn conversation.

        Args:
            turns: List of turn dictionaries, each with "role" (user/assistant)
                and "content" keys.
            include_assistant_prefix: Whether to include assistant prefix at end.

        Returns:
            Formatted conversation string.
        """
        parts = []

        if self.system_prompt:
            parts.append(self.system_prompt)
            parts.append(self.separator)

        for i, turn in enumerate(turns):
            role = turn["role"]
            content = turn["content"]

            if role == "user":
                parts.append(self.user_prefix)
                parts.append(content)
                parts.append(self.user_suffix)
            elif role == "assistant":
                parts.append(self.assistant_prefix)
                parts.append(content)
                parts.append(self.assistant_suffix)

            if i < len(turns) - 1:
                parts.append(self.separator)

        # Add assistant prefix for generation if last turn was user
        if include_assistant_prefix and turns and turns[-1]["role"] == "user":
            parts.append(self.assistant_prefix)

        return "".join(parts)

    def extract_response(
        self,
        full_text: str,
        prompt: str,
    ) -> str:
        """Extract the model's response from full generated text.

        Args:
            full_text: The complete text including prompt and response.
            prompt: The original prompt.

        Returns:
            Just the response portion, cleaned up.
        """
        if full_text.startswith(prompt):
            response = full_text[len(prompt) :]
        else:
            response = full_text

        # Remove trailing EOS tokens and whitespace
        response = response.rstrip()
        if response.endswith(self.assistant_suffix):
            response = response[: -len(self.assistant_suffix)]

        return response.strip()

    @classmethod
    def default(cls) -> "PromptTemplate":
        """Create a simple default template with no formatting."""
        return cls()

    @classmethod
    def llama2_chat(cls) -> "PromptTemplate":
        """Create a template for LLaMA-2 chat models."""
        return cls(
            system_prompt="<<SYS>>\nYou are a helpful assistant.\n<</SYS>>\n\n",
            user_prefix="[INST] ",
            assistant_prefix=" ",
            user_suffix=" [/INST]",
            assistant_suffix="</s>",
            separator="",
        )

    @classmethod
    def chatml(cls) -> "PromptTemplate":
        """Create a template for ChatML format (used by many models)."""
        return cls(
            system_prompt="<|im_start|>system\nYou are a helpful assistant.<|im_end|>\n",
            user_prefix="<|im_start|>user\n",
            assistant_prefix="<|im_start|>assistant\n",
            user_suffix="<|im_end|>\n",
            assistant_suffix="<|im_end|>\n",
            separator="",
        )

    @classmethod
    def alpaca(cls) -> "PromptTemplate":
        """Create a template for Alpaca-style instruction format."""
        return cls(
            system_prompt="Below is an instruction that describes a task. "
            "Write a response that appropriately completes the request.\n\n",
            user_prefix="### Instruction:\n",
            assistant_prefix="### Response:\n",
            user_suffix="\n\n",
            assistant_suffix="\n",
            separator="",
        )

    @classmethod
    def simple(cls, system_prompt: str | None = None) -> "PromptTemplate":
        """Create a simple template with optional system prompt."""
        return cls(
            system_prompt=system_prompt + "\n\n" if system_prompt else None,
            user_prefix="Human: ",
            assistant_prefix="Assistant: ",
            user_suffix="\n",
            assistant_suffix="\n",
            separator="",
        )


class BaseKonicLLMEnvironment(gym.Env, ABC):
    """Abstract base class for LLM finetuning environments.

    This class defines the interface for environments used in RLHF training.
    Unlike standard RL environments, LLM environments treat text generation
    as the action space, where each action is a token selection.

    The environment manages:
    - Tokenization of prompts and responses
    - Text generation as action sequences
    - Reward computation at the end of generation

    Subclasses must implement:
    - tokenizer: Returns the tokenizer wrapper
    - prompt_template: Returns the prompt formatting template
    - generation_config: Returns generation parameters
    - reward_composer: Returns the reward composer
    - generate(): Generates text given a prompt
    - compute_reward(): Computes reward for a prompt-response pair
    """

    @property
    @abstractmethod
    def tokenizer(self) -> TokenizerWrapper:
        """Return the tokenizer wrapper."""
        pass

    @property
    @abstractmethod
    def prompt_template(self) -> PromptTemplate:
        """Return the prompt template for formatting."""
        pass

    @property
    @abstractmethod
    def generation_config(self) -> "GenerationConfig":
        """Return generation configuration."""
        pass

    @property
    @abstractmethod
    def reward_composer(self) -> "BaseKonicLLMRewardComposer":
        """Return the reward composer."""
        pass

    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Generate a complete response given a prompt."""
        pass

    @abstractmethod
    def compute_reward(self, prompt: str, response: str) -> float:
        """Compute the reward for a prompt-response pair."""
        pass

    @abstractmethod
    def reset(
        self,
        seed: int | None = None,
        options: dict[str, Any] | None = None,
    ) -> tuple[Any, dict]:
        """Reset the environment with a new prompt."""
        pass

    @abstractmethod
    def step(self, action: int) -> tuple[Any, float, bool, bool, dict]:
        """Take a generation step (add a token to the response)."""
        pass


class KonicLLMEnvironment(BaseKonicLLMEnvironment):
    """Concrete LLM environment for RLHF text generation training.

    This environment wraps a language model and treats text generation as
    a reinforcement learning problem:
    - State: Tokenized prompt + generated tokens so far
    - Action: Next token to generate (from vocabulary)
    - Reward: Computed at end of generation via reward composer

    The environment supports both token-by-token stepping (for RL training)
    and full generation (for rollout collection).

    Example:
        >>> env = KonicLLMEnvironment(
        ...     model=AutoModelForCausalLM.from_pretrained("gpt2"),
        ...     tokenizer=AutoTokenizer.from_pretrained("gpt2"),
        ...     reward_composer=my_reward_composer,
        ... )
        >>> obs, info = env.reset(options={"prompt": "Hello!"})
        >>> response = env.generate(info["formatted_prompt"])
    """

    def __init__(
        self,
        model: "PreTrainedModel",
        tokenizer: "PreTrainedTokenizer | TokenizerWrapper",
        reward_composer: "BaseKonicLLMRewardComposer",
        prompt_template: PromptTemplate | None = None,
        generation_config: "GenerationConfig | None" = None,
        max_sequence_length: int = 512,
        max_new_tokens: int = 128,
        device: str | torch.device = "auto",
    ):
        """Initialize the LLM environment.

        Args:
            model: HuggingFace model for text generation.
            tokenizer: HuggingFace tokenizer or TokenizerWrapper.
            reward_composer: Reward composer for computing rewards.
            prompt_template: Template for formatting prompts.
            generation_config: Generation parameters.
            max_sequence_length: Maximum total sequence length.
            max_new_tokens: Maximum new tokens to generate per episode.
            device: Device for model inference.
        """
        super().__init__()

        from konic.finetuning.config import GenerationConfig as GenConfig

        self._model = model
        self._tokenizer = (
            tokenizer if isinstance(tokenizer, TokenizerWrapper) else TokenizerWrapper(tokenizer)
        )
        self._reward_composer = reward_composer
        self._prompt_template = prompt_template or PromptTemplate.default()
        self._generation_config = generation_config or GenConfig()
        self._max_sequence_length = max_sequence_length
        self._max_new_tokens = max_new_tokens

        # Handle device
        if device == "auto":
            self._device = next(model.parameters()).device
        else:
            self._device = torch.device(device)

        # Bind reward composer to this environment
        if hasattr(self._reward_composer, "set_env"):
            self._reward_composer.set_env(self)

        # Episode state
        self._current_prompt: str = ""
        self._formatted_prompt: str = ""
        self._current_response: str = ""
        self._current_tokens: list[int] = []
        self._prompt_tokens: list[int] = []
        self._response_tokens: list[int] = []
        self._step_count: int = 0
        self._episode_reward: float = 0.0

        # Define observation and action spaces
        self._observation_space = gym.spaces.Box(
            low=0,
            high=self._tokenizer.vocab_size - 1,
            shape=(self._max_sequence_length,),
            dtype=np.int64,
        )
        self._action_space = gym.spaces.Discrete(self._tokenizer.vocab_size)

    @property
    def observation_space(self) -> gym.spaces.Space:
        """Observation space: tokenized sequence."""
        return self._observation_space

    @property
    def action_space(self) -> gym.spaces.Space:
        """Action space: vocabulary tokens."""
        return self._action_space

    @property
    def tokenizer(self) -> TokenizerWrapper:
        """Get the tokenizer wrapper."""
        return self._tokenizer

    @property
    def prompt_template(self) -> PromptTemplate:
        """Get the prompt template."""
        return self._prompt_template

    @property
    def generation_config(self) -> "GenerationConfig":
        """Get generation configuration."""
        return self._generation_config

    @property
    def reward_composer(self) -> "BaseKonicLLMRewardComposer":
        """Get the reward composer."""
        return self._reward_composer

    @property
    def model(self) -> "PreTrainedModel":
        """Get the language model."""
        return self._model

    def reset(
        self,
        seed: int | None = None,
        options: dict[str, Any] | None = None,
    ) -> tuple[np.ndarray, dict]:
        """Reset the environment with a new prompt."""
        super().reset(seed=seed)

        options = options or {}

        # Get prompt from options
        if "formatted_prompt" in options:
            self._formatted_prompt = options["formatted_prompt"]
            self._current_prompt = options.get("prompt", self._formatted_prompt)
        elif "prompt" in options:
            self._current_prompt = options["prompt"]
            self._formatted_prompt = self._prompt_template.format_prompt(self._current_prompt)
        else:
            self._current_prompt = ""
            self._formatted_prompt = ""

        # Tokenize prompt
        if "input_ids" in options:
            self._prompt_tokens = list(options["input_ids"])
        else:
            self._prompt_tokens = self._tokenizer.encode(
                self._formatted_prompt,
                add_special_tokens=True,
            )

        # Reset episode state
        self._current_response = ""
        self._response_tokens = []
        self._current_tokens = self._prompt_tokens.copy()
        self._step_count = 0
        self._episode_reward = 0.0

        obs = self._get_observation()
        info = self._get_info()

        return obs, info

    def step(self, action: int) -> tuple[np.ndarray, float, bool, bool, dict]:
        """Take a generation step by adding a token."""
        # Add token to response
        self._response_tokens.append(action)
        self._current_tokens.append(action)
        self._step_count += 1

        # Decode current response
        self._current_response = self._tokenizer.decode(
            self._response_tokens,
            skip_special_tokens=True,
        )

        # Check termination conditions
        terminated = self._is_terminated(action)
        truncated = self._is_truncated()

        # Compute reward (only at end of generation for efficiency)
        if terminated or truncated:
            reward = self.compute_reward(self._current_prompt, self._current_response)
            self._episode_reward = reward
        else:
            reward = 0.0  # Sparse reward at end

        obs = self._get_observation()
        info = self._get_info()

        return obs, reward, terminated, truncated, info

    def generate(self, prompt: str) -> str:
        """Generate a complete response using the model."""
        # Encode prompt
        input_ids = self._tokenizer.encode(
            prompt,
            return_tensors="pt",
            add_special_tokens=True,
        ).to(self._device)

        # Prepare generation config
        gen_kwargs = self._generation_config.to_dict()
        gen_kwargs["pad_token_id"] = self._tokenizer.pad_token_id
        gen_kwargs["eos_token_id"] = self._tokenizer.eos_token_id

        # Generate
        with torch.no_grad():
            output_ids = self._model.generate(
                input_ids,
                **gen_kwargs,
            )

        # Extract response (remove prompt tokens)
        response_ids = output_ids[0, input_ids.shape[1] :]
        response = self._tokenizer.decode(response_ids, skip_special_tokens=True)

        return response

    def compute_reward(self, prompt: str, response: str) -> float:
        """Compute reward for a prompt-response pair."""
        return self._reward_composer.compose(prompt, response)

    def _get_observation(self) -> np.ndarray:
        """Get padded observation of current token sequence."""
        tokens = self._current_tokens.copy()

        # Truncate if needed
        if len(tokens) > self._max_sequence_length:
            tokens = tokens[-self._max_sequence_length :]

        # Pad to max length
        padding_length = self._max_sequence_length - len(tokens)
        if padding_length > 0:
            tokens = tokens + [self._tokenizer.pad_token_id] * padding_length

        return np.array(tokens, dtype=np.int64)

    def _is_terminated(self, last_token: int) -> bool:
        """Check if generation should terminate (EOS token)."""
        return last_token == self._tokenizer.eos_token_id

    def _is_truncated(self) -> bool:
        """Check if generation is truncated (max tokens reached)."""
        return self._step_count >= self._max_new_tokens

    def _get_info(self) -> dict:
        """Get information dictionary about current state."""
        return {
            "prompt": self._current_prompt,
            "formatted_prompt": self._formatted_prompt,
            "response": self._current_response,
            "step_count": self._step_count,
            "prompt_length": len(self._prompt_tokens),
            "response_length": len(self._response_tokens),
            "total_length": len(self._current_tokens),
            "episode_reward": self._episode_reward,
        }

    def get_obs(self) -> np.ndarray:
        """Get the current observation."""
        return self._get_observation()

    def get_info(self) -> dict:
        """Get current state information."""
        return self._get_info()

    def render(self) -> None:
        """Render the current state (prints prompt and response)."""
        print(f"Prompt: {self._current_prompt}")
        print(f"Response: {self._current_response}")
        print(f"Step: {self._step_count}/{self._max_new_tokens}")
