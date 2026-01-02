"""Basic LLM Finetuning Agent Template.

This template provides the minimal setup for RLHF finetuning with Konic.
It demonstrates:
- A simple reward composer with basic reward functions
- Minimal LoRA configuration for parameter-efficient training
- Basic dataset configuration using HuggingFace datasets

Konic Cloud handles the training - this file only defines the agent.
"""

from konic.finetuning import (
    DatasetConfig,
    DatasetSource,
    KonicFinetuningAgent,
    KonicLLMRewardComposer,
    LoraConfig,
    TrainingConfig,
    llm_reward,
)
from konic.runtime import register_agent

# =============================================================================
# Reward Composer
# =============================================================================


class SimpleRewardComposer(KonicLLMRewardComposer):
    """A simple reward composer with basic reward signals.

    This composer provides two reward functions:
    - brevity_bonus: Rewards shorter, more concise responses
    - coherence_reward: Penalizes repetitive text patterns
    """

    @llm_reward
    def brevity_bonus(self, prompt: str, response: str) -> float:
        """Reward shorter, more concise responses.

        Args:
            prompt: The input prompt (unused).
            response: The generated response to evaluate.

        Returns:
            Reward between 0.0 and 1.0 (higher for shorter responses).
        """
        max_length = 300
        response_length = len(response)

        if response_length >= max_length:
            return 0.0

        return max(0.0, 1.0 - (response_length / max_length))

    @llm_reward
    def coherence_reward(self, prompt: str, response: str) -> float:
        """Penalize repetitive patterns in the response.

        Args:
            prompt: The input prompt (unused).
            response: The generated response to evaluate.

        Returns:
            Reward between 0.0 and 1.0 (higher for non-repetitive text).
        """
        if not response:
            return 1.0

        words = response.lower().split()

        if len(words) < 2:
            return 1.0

        # Check for consecutive repeated words
        repeated_words = sum(1 for i in range(1, len(words)) if words[i] == words[i - 1])
        repetition_ratio = repeated_words / len(words)

        return max(0.0, 1.0 - repetition_ratio * 2)


# =============================================================================
# Configuration
# =============================================================================

# LoRA configuration for parameter-efficient finetuning
lora_config = LoraConfig(
    r=8,  # Low rank for efficiency
    lora_alpha=16,  # Scaling factor
    lora_dropout=0.1,
    target_modules=["c_attn", "c_proj"],  # GPT-2 attention modules
)

# Training hyperparameters
training_config = TrainingConfig(
    learning_rate=5e-5,
    batch_size=4,
    gradient_accumulation_steps=2,
    kl_penalty_weight=0.05,
)

# Dataset configuration
dataset_config = DatasetConfig(
    source=DatasetSource.HUGGINGFACE,
    name="imdb",
    prompt_column="text",
    split="train",
    max_samples=500,
    shuffle=True,
)


# =============================================================================
# Agent Registration
# =============================================================================

# Create the finetuning agent
agent = KonicFinetuningAgent(
    base_model="gpt2",
    reward_composer=SimpleRewardComposer(),
    lora_config=lora_config,
    dataset_config=dataset_config,
    training_config=training_config,
)

# Register for Konic Cloud
register_agent(agent, name="{{cookiecutter.name.replace(' ', '-').lower()}}")
