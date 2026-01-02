"""Basic RLHF Finetuning Example - Sentiment-Guided Response Generation.

This example demonstrates how to use Konic's RLHF finetuning module to train
a language model to generate more positive and concise responses.

Key concepts demonstrated:
- Custom reward functions using the @llm_reward decorator
- Basic LoRA configuration for parameter-efficient finetuning
- Using HuggingFace datasets for training data
- Simple training loop with console output

Model: GPT-2 (small and fast for demonstration)
Dataset: IMDB movie reviews
Goal: Train the model to generate positive, concise, and coherent responses
"""

import re

from konic.finetuning import (
    DatasetConfig,
    DatasetSource,
    KonicFinetuningAgent,
    KonicFinetuningEngine,
    KonicLLMRewardComposer,
    LoraConfig,
    TrainingConfig,
    llm_reward,
)

# =============================================================================
# Custom Reward Composer
# =============================================================================


class SentimentRewardComposer(KonicLLMRewardComposer):
    """Custom reward composer that encourages positive, concise, and coherent text.

    This composer combines three reward signals:
    1. brevity_bonus: Rewards shorter responses (max 1.0 for very short)
    2. positivity_reward: Rewards positive sentiment words
    3. coherence_penalty: Penalizes repetitive text patterns

    All reward functions are marked with @llm_reward decorator, which allows
    the KonicLLMRewardComposer to automatically discover and apply them.
    """

    # Positive words to reward
    POSITIVE_WORDS = {
        "good",
        "great",
        "excellent",
        "amazing",
        "wonderful",
        "fantastic",
        "love",
        "enjoy",
        "happy",
        "best",
        "perfect",
        "beautiful",
        "brilliant",
        "outstanding",
        "superb",
        "delightful",
        "impressive",
        "positive",
    }

    @llm_reward
    def brevity_bonus(self, prompt: str, response: str) -> float:
        """Reward shorter, more concise responses.

        Encourages the model to be succinct rather than verbose.
        Returns a value between 0 and 1, where shorter responses get higher rewards.

        Args:
            prompt: The input prompt (unused in this reward).
            response: The generated response to evaluate.

        Returns:
            Reward value between 0.0 and 1.0.
        """
        # Target length: around 50-100 characters for a concise response
        # Linearly decrease reward as response gets longer
        max_length = 300  # Responses longer than this get 0 reward
        response_length = len(response)

        if response_length >= max_length:
            return 0.0

        return max(0.0, 1.0 - (response_length / max_length))

    @llm_reward
    def positivity_reward(self, prompt: str, response: str) -> float:
        """Reward responses containing positive sentiment words.

        Encourages the model to generate more positive and uplifting content.

        Args:
            prompt: The input prompt (unused in this reward).
            response: The generated response to evaluate.

        Returns:
            Reward value between 0.0 and 1.0 based on positive word density.
        """
        # Normalize and tokenize
        words = response.lower().split()

        if not words:
            return 0.0

        # Count positive words
        positive_count = sum(1 for word in words if word in self.POSITIVE_WORDS)

        # Calculate positive word density (capped at 0.3 = 30% positive words)
        density = positive_count / len(words)
        normalized_score = min(1.0, density / 0.3)

        return normalized_score

    @llm_reward
    def coherence_penalty(self, prompt: str, response: str) -> float:
        """Penalize repetitive patterns in the response.

        Detects and penalizes:
        - Repeated words (e.g., "the the the")
        - Repeated phrases (e.g., "this is great this is great")
        - Repeated character sequences

        Args:
            prompt: The input prompt (unused in this reward).
            response: The generated response to evaluate.

        Returns:
            Reward value between 0.0 and 1.0, where 1.0 means no repetition.
        """
        if not response:
            return 1.0

        words = response.lower().split()

        if len(words) < 2:
            return 1.0

        # Check for consecutive repeated words
        repeated_words = 0
        for i in range(1, len(words)):
            if words[i] == words[i - 1]:
                repeated_words += 1

        word_repetition_ratio = repeated_words / len(words)

        # Check for repeated bigrams (phrases of 2 words)
        bigrams = [f"{words[i]} {words[i+1]}" for i in range(len(words) - 1)]
        unique_bigrams = set(bigrams)
        bigram_repetition_ratio = 1.0 - (len(unique_bigrams) / len(bigrams)) if bigrams else 0.0

        # Check for repeated character patterns (e.g., "aaaaa")
        char_pattern_penalty = 0.0
        if re.search(r"(.)\1{4,}", response):  # 5+ repeated characters
            char_pattern_penalty = 0.3

        # Combine penalties (lower penalty = higher reward)
        total_penalty = (
            0.4 * word_repetition_ratio + 0.3 * bigram_repetition_ratio + char_pattern_penalty
        )

        return max(0.0, 1.0 - total_penalty)


# =============================================================================
# Training Configuration
# =============================================================================


def create_agent() -> KonicFinetuningAgent:
    """Create and configure the finetuning agent.

    Returns:
        Configured KonicFinetuningAgent ready for training.
    """
    # LoRA configuration for parameter-efficient finetuning
    # Using smaller rank for GPT-2 since it's a smaller model
    lora_config = LoraConfig(
        r=8,  # Low rank for efficiency
        lora_alpha=16,  # Scaling factor (typically 2x r)
        lora_dropout=0.1,
        target_modules=["c_attn", "c_proj"],  # GPT-2 attention modules
        bias="none",
        fan_in_fan_out=True,  # Required for GPT-2 (uses Conv1D layers)
    )

    # Training hyperparameters
    training_config = TrainingConfig(
        learning_rate=5e-5,  # Slightly higher LR for smaller model
        batch_size=4,  # Smaller batch for memory efficiency
        gradient_accumulation_steps=2,
        kl_penalty_weight=0.05,  # Keep policy close to original
        ppo_epochs=2,
    )

    # Dataset configuration - using IMDB for sentiment-based training
    dataset_config = DatasetConfig(
        source=DatasetSource.HUGGINGFACE,
        name="imdb",
        prompt_column="text",  # Use movie review text as prompts
        split="train",
        max_samples=500,  # Limit samples for faster demo
        shuffle=True,
    )

    # Create the agent
    agent = KonicFinetuningAgent(
        base_model="gpt2",  # Small model for demonstration
        reward_composer=SentimentRewardComposer(),
        lora_config=lora_config,
        dataset_config=dataset_config,
        training_config=training_config,
    )

    return agent


# =============================================================================
# Main Training Script
# =============================================================================


def main():
    """Run the RLHF finetuning example."""
    print("=" * 60)
    print("Konic RLHF Finetuning Example - Sentiment-Guided Generation")
    print("=" * 60)
    print()

    # Create agent
    print("Creating finetuning agent...")
    agent = create_agent()

    # Create engine from agent
    print("Initializing finetuning engine...")
    engine = KonicFinetuningEngine.from_agent(agent)

    # Run training
    print("\nStarting RLHF training...")
    print("This will train GPT-2 to generate positive, concise responses.")
    print()

    result = engine.train(
        max_iterations=50,  # Short training for demonstration
        save_every=25,  # Save checkpoint every 25 iterations
    )

    # Print results
    print("\n" + "=" * 60)
    print("Training Complete!")
    print("=" * 60)
    print(result.summary())

    # Test the model with a sample prompt
    print("\nTesting trained model with sample prompts...")
    print("-" * 60)

    test_prompts = [
        "The movie was",
        "I really think that this film",
        "Overall, my experience was",
    ]

    eval_results = engine.evaluate(test_prompts)

    for prompt, response, reward in zip(
        eval_results["prompts"], eval_results["responses"], eval_results["rewards"]
    ):
        print(f"\nPrompt: {prompt}")
        print(f"Response: {response[:200]}...")
        print(f"Reward: {reward:.3f}")

    print("\n" + "=" * 60)
    print("Example complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
