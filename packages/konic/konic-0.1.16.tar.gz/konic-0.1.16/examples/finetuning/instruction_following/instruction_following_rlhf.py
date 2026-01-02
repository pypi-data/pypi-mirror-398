"""Advanced RLHF Finetuning Example - Instruction Following with HF Reward Models.

This example demonstrates advanced RLHF finetuning techniques:
- Using HuggingFace pre-trained reward models for instruction quality
- Combining neural reward models with custom rule-based rewards
- Advanced LoRA configuration with more target modules
- Custom callbacks for logging, checkpointing, and early stopping
- WeightedSumReducer for fine-grained reward balancing

Model: LLaMA-2 7B or Mistral 7B (configurable)
Dataset: Alpaca instruction dataset
Reward Model: OpenAssistant DeBERTa reward model

Note: This example requires significant GPU memory (~16GB+ for 7B models).
For testing, you can use smaller models like "gpt2" or "distilgpt2".
"""

import argparse
from typing import Any

from konic.finetuning import (
    BaseKonicFinetuningCallback,
    DatasetConfig,
    DatasetSource,
    FinetuningIterationResult,
    FinetuningResult,
    HuggingFaceRewardModel,
    KonicFinetuningAgent,
    KonicFinetuningEngine,
    KonicLLMRewardComposer,
    LoraConfig,
    TrainingConfig,
    WeightedSumReducer,
    llm_reward,
)

# =============================================================================
# Custom Reward Composer with HuggingFace Reward Model
# =============================================================================


class InstructionFollowingRewardComposer(KonicLLMRewardComposer):
    """Advanced reward composer combining neural and rule-based rewards.

    This composer uses:
    1. A HuggingFace reward model (DeBERTa-based) for instruction quality
    2. Custom @llm_reward functions for formatting and structure checks

    The neural model captures semantic quality and helpfulness, while the
    custom functions enforce specific formatting requirements.
    """

    # Use WeightedSumReducer for fine-grained control
    reducer = WeightedSumReducer

    def __init__(self, use_hf_reward_model: bool = True):
        """Initialize the reward composer.

        Args:
            use_hf_reward_model: Whether to load the HuggingFace reward model.
                Set to False for faster testing without the neural model.
        """
        reward_models = []

        if use_hf_reward_model:
            # OpenAssistant's instruction-tuned reward model
            # This model scores how well a response follows instructions
            reward_models.append(
                HuggingFaceRewardModel(
                    model_id="OpenAssistant/reward-model-deberta-v3-large-v2",
                    device="auto",
                    max_length=512,
                    normalize=True,  # Normalize to stable range
                )
            )

        super().__init__(
            reward_models=reward_models,
            reward_weights={
                # Neural reward model (main signal)
                "hf_OpenAssistant_reward_model_deberta_v3_large_v2": 1.0,
                # Custom format rewards (supplementary signals)
                "format_compliance": 0.3,
                "instruction_acknowledgment": 0.2,
                "response_structure": 0.2,
            },
            kl_penalty_weight=0.05,
        )

    @llm_reward
    def format_compliance(self, prompt: str, response: str) -> float:
        """Check if response follows good formatting practices.

        Rewards responses that:
        - Don't start with "I" (less self-referential)
        - Use proper punctuation
        - Have appropriate length

        Args:
            prompt: The instruction prompt.
            response: The generated response.

        Returns:
            Score between 0.0 and 1.0.
        """
        score = 1.0

        # Penalize starting with "I" (often indicates poor instruction following)
        if response.strip().startswith("I ") or response.strip().startswith("I'm"):
            score -= 0.2

        # Reward proper ending punctuation
        if response.strip() and response.strip()[-1] in ".!?":
            score += 0.1
        else:
            score -= 0.1

        # Penalize very short responses (less than 20 chars)
        if len(response.strip()) < 20:
            score -= 0.3

        # Penalize extremely long responses (more than 500 chars)
        if len(response.strip()) > 500:
            score -= 0.2

        return max(0.0, min(1.0, score))

    @llm_reward
    def instruction_acknowledgment(self, prompt: str, response: str) -> float:
        """Check if response acknowledges key elements from the instruction.

        Looks for evidence that the response is actually addressing the prompt
        rather than generating generic text.

        Args:
            prompt: The instruction prompt.
            response: The generated response.

        Returns:
            Score between 0.0 and 1.0.
        """
        # Extract key nouns/words from prompt (simple heuristic)
        prompt_words = set(prompt.lower().split())
        response_words = set(response.lower().split())

        # Filter to meaningful words (length > 4)
        prompt_keywords = {w for w in prompt_words if len(w) > 4}
        response_keywords = {w for w in response_words if len(w) > 4}

        if not prompt_keywords:
            return 0.5  # Can't evaluate without keywords

        # Calculate overlap
        overlap = prompt_keywords.intersection(response_keywords)
        overlap_ratio = len(overlap) / len(prompt_keywords)

        # At least some overlap is expected
        return min(1.0, overlap_ratio * 2)  # Scale up since we expect ~50%

    @llm_reward
    def response_structure(self, prompt: str, response: str) -> float:
        """Evaluate the structural quality of the response.

        Rewards:
        - Multiple sentences (indicates complete thought)
        - Use of transitional words
        - Logical structure markers

        Args:
            prompt: The instruction prompt.
            response: The generated response.

        Returns:
            Score between 0.0 and 1.0.
        """
        score = 0.5  # Start neutral

        # Count sentences (simple heuristic)
        sentence_enders = response.count(".") + response.count("!") + response.count("?")

        # Reward multiple sentences
        if sentence_enders >= 2:
            score += 0.2
        if sentence_enders >= 3:
            score += 0.1

        # Reward transitional words (indicates logical flow)
        transitions = [
            "first",
            "second",
            "third",
            "finally",
            "however",
            "therefore",
            "additionally",
            "moreover",
            "furthermore",
            "in conclusion",
            "for example",
            "such as",
            "because",
            "since",
            "although",
        ]
        response_lower = response.lower()
        transition_count = sum(1 for t in transitions if t in response_lower)

        if transition_count >= 1:
            score += 0.1
        if transition_count >= 2:
            score += 0.1

        return min(1.0, max(0.0, score))


# =============================================================================
# Custom Training Callback
# =============================================================================


class InstructionTrainingCallback(BaseKonicFinetuningCallback):
    """Custom callback for detailed training monitoring.

    Features:
    - Detailed progress logging with reward breakdown
    - Sample generation logging for quality inspection
    - Early stopping based on KL divergence
    - Best model tracking
    """

    def __init__(
        self,
        log_interval: int = 5,
        log_samples: bool = True,
        max_samples_to_log: int = 2,
        early_stop_kl_threshold: float = 0.15,
        early_stop_patience: int = 10,
    ):
        """Initialize the callback.

        Args:
            log_interval: Log detailed metrics every N iterations.
            log_samples: Whether to log generated samples.
            max_samples_to_log: Number of samples to log.
            early_stop_kl_threshold: KL threshold for early stopping.
            early_stop_patience: Consecutive violations before stopping.
        """
        self.log_interval = log_interval
        self.log_samples = log_samples
        self.max_samples_to_log = max_samples_to_log
        self.early_stop_kl_threshold = early_stop_kl_threshold
        self.early_stop_patience = early_stop_patience

        self._kl_violations = 0
        self._best_reward = float("-inf")
        self._best_iteration = 0
        self._current_prompts: list[str] = []
        self._current_responses: list[str] = []

    def on_train_begin(self, config: dict[str, Any]) -> None:
        """Log training configuration."""
        print("\n" + "=" * 70)
        print("INSTRUCTION FOLLOWING RLHF TRAINING")
        print("=" * 70)
        print(f"Model:              {config.get('model_name', 'unknown')}")
        print(f"LoRA Enabled:       {config.get('use_lora', False)}")
        print(f"Learning Rate:      {config.get('learning_rate', 'N/A')}")
        print(f"Batch Size:         {config.get('batch_size', 'N/A')}")
        print(f"Max Iterations:     {config.get('max_iterations', 'N/A')}")
        print(f"KL Penalty Weight:  {config.get('kl_penalty_weight', 'N/A')}")
        print("-" * 70)
        print(f"Early Stop KL:      {self.early_stop_kl_threshold}")
        print(f"Early Stop Patience: {self.early_stop_patience}")
        print("=" * 70 + "\n")

    def on_train_end(self, result: FinetuningResult) -> None:
        """Log final results."""
        print("\n" + "=" * 70)
        print("TRAINING COMPLETE")
        print("=" * 70)
        print(f"Total Iterations:   {result.total_iterations}")
        print(f"Total Samples:      {result.total_samples}")
        print(f"Total Time:         {result.total_time_sec:.1f}s")
        print("-" * 70)
        print(f"Best Reward:        {result.best_reward:.4f} (iter {result.best_iteration})")
        print(f"Final Reward:       {result.final_reward_mean:.4f}")
        print(f"Final KL:           {result.final_kl_divergence:.4f}")
        if result.model_path:
            print(f"Model Saved:        {result.model_path}")
        print("=" * 70 + "\n")

    def on_iteration_end(self, result: FinetuningIterationResult) -> None:
        """Log iteration metrics."""
        # Track best
        if result.reward_mean > self._best_reward:
            self._best_reward = result.reward_mean
            self._best_iteration = result.iteration
            best_marker = " *BEST*"
        else:
            best_marker = ""

        # Always log basic progress
        print(
            f"[Iter {result.iteration:4d}] "
            f"Reward: {result.reward_mean:7.4f} (+/- {result.reward_std:.3f}) | "
            f"KL: {result.kl_divergence:.4f} | "
            f"Loss: {result.total_loss:.4f}{best_marker}"
        )

        # Detailed logging at intervals
        if result.iteration % self.log_interval == 0:
            self._log_detailed_metrics(result)

            if self.log_samples and self._current_responses:
                self._log_samples(result.iteration)

    def on_generation_end(self, prompts: list[str], responses: list[str]) -> None:
        """Store samples for logging."""
        self._current_prompts = prompts[: self.max_samples_to_log]
        self._current_responses = responses[: self.max_samples_to_log]

    def should_stop_early(self, result: FinetuningIterationResult) -> bool:
        """Check KL-based early stopping."""
        if result.kl_divergence > self.early_stop_kl_threshold:
            self._kl_violations += 1
            print(
                f"  WARNING: KL ({result.kl_divergence:.4f}) > threshold "
                f"({self.early_stop_kl_threshold}). "
                f"Violations: {self._kl_violations}/{self.early_stop_patience}"
            )

            if self._kl_violations >= self.early_stop_patience:
                print("\n  EARLY STOPPING: KL divergence too high for too long.")
                return True
        else:
            self._kl_violations = 0

        return False

    def _log_detailed_metrics(self, result: FinetuningIterationResult) -> None:
        """Log detailed metrics breakdown."""
        print(f"\n  {'─' * 50}")
        print(f"  Detailed Metrics (Iteration {result.iteration})")
        print(f"  {'─' * 50}")
        print(f"  Reward Range:     [{result.reward_min:.3f}, {result.reward_max:.3f}]")
        print(f"  Policy Loss:      {result.policy_loss:.4f}")
        print(f"  Value Loss:       {result.value_loss:.4f}")
        print(f"  Entropy:          {-result.entropy_loss:.4f}")
        print(f"  Clip Fraction:    {result.clip_fraction:.3f}")
        print(
            f"  Response Length:  {result.response_length_mean:.1f} (+/- {result.response_length_std:.1f})"
        )

        # Reward breakdown
        if result.reward_breakdown:
            print("\n  Reward Breakdown:")
            for name, value in sorted(result.reward_breakdown.items()):
                print(f"    {name}: {value:.4f}")

        print(f"  {'─' * 50}\n")

    def _log_samples(self, iteration: int) -> None:
        """Log generated samples."""
        print(f"\n  Sample Generations (Iteration {iteration})")
        print(f"  {'─' * 50}")

        for i, (prompt, response) in enumerate(zip(self._current_prompts, self._current_responses)):
            print(f"\n  [{i + 1}] Prompt: {prompt[:100]}...")
            print(f"      Response: {response[:300]}...")

        print(f"\n  {'─' * 50}\n")

        # Clear stored samples
        self._current_prompts = []
        self._current_responses = []


# =============================================================================
# Configuration Functions
# =============================================================================


def create_agent(
    model_name: str = "meta-llama/Llama-2-7b-hf",
    use_hf_reward_model: bool = True,
) -> KonicFinetuningAgent:
    """Create and configure the finetuning agent.

    Args:
        model_name: HuggingFace model ID for the base model.
        use_hf_reward_model: Whether to use the HF reward model.

    Returns:
        Configured KonicFinetuningAgent.
    """
    # Advanced LoRA configuration with more target modules
    lora_config = LoraConfig(
        r=16,  # Higher rank for more capacity
        lora_alpha=32,  # 2x rank for stable training
        lora_dropout=0.05,
        target_modules=[
            "q_proj",
            "k_proj",
            "v_proj",
            "o_proj",  # Attention projections
            "gate_proj",
            "up_proj",
            "down_proj",  # MLP projections
        ],
        bias="none",
    )

    # Training configuration for larger models
    training_config = TrainingConfig(
        learning_rate=1e-5,  # Conservative LR for stability
        batch_size=2,  # Small batch for memory
        gradient_accumulation_steps=4,
        kl_penalty_weight=0.05,
        clip_ratio=0.2,
        ppo_epochs=4,
        vf_coef=0.5,
        entropy_coef=0.01,
        max_grad_norm=0.5,
    )

    # Alpaca instruction dataset
    dataset_config = DatasetConfig(
        source=DatasetSource.HUGGINGFACE,
        name="tatsu-lab/alpaca",
        prompt_column="instruction",
        split="train",
        max_samples=1000,
        shuffle=True,
        shuffle_seed=42,
    )

    # Create reward composer
    reward_composer = InstructionFollowingRewardComposer(
        use_hf_reward_model=use_hf_reward_model,
    )

    agent = KonicFinetuningAgent(
        base_model=model_name,
        reward_composer=reward_composer,
        lora_config=lora_config,
        dataset_config=dataset_config,
        training_config=training_config,
    )

    return agent


# =============================================================================
# Main Training Script
# =============================================================================


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Advanced RLHF Finetuning for Instruction Following"
    )

    parser.add_argument(
        "--model",
        type=str,
        default="meta-llama/Llama-2-7b-hf",
        help="HuggingFace model ID (default: meta-llama/Llama-2-7b-hf)",
    )

    parser.add_argument(
        "--max-iterations",
        type=int,
        default=100,
        help="Maximum training iterations (default: 100)",
    )

    parser.add_argument(
        "--save-every",
        type=int,
        default=25,
        help="Save checkpoint every N iterations (default: 25)",
    )

    parser.add_argument(
        "--no-hf-reward",
        action="store_true",
        help="Disable HuggingFace reward model (for faster testing)",
    )

    parser.add_argument(
        "--checkpoint-dir",
        type=str,
        default="./checkpoints/instruction_following",
        help="Directory to save checkpoints",
    )

    return parser.parse_args()


def main():
    """Run the advanced RLHF finetuning example."""
    args = parse_args()

    print("=" * 70)
    print("Konic Advanced RLHF - Instruction Following")
    print("=" * 70)
    print(f"Model: {args.model}")
    print(f"HF Reward Model: {'Enabled' if not args.no_hf_reward else 'Disabled'}")
    print(f"Max Iterations: {args.max_iterations}")
    print(f"Checkpoint Directory: {args.checkpoint_dir}")
    print("=" * 70 + "\n")

    # Create agent
    print("Initializing agent...")
    agent = create_agent(
        model_name=args.model,
        use_hf_reward_model=not args.no_hf_reward,
    )

    # Create custom callback
    callback = InstructionTrainingCallback(
        log_interval=10,
        log_samples=True,
        max_samples_to_log=2,
        early_stop_kl_threshold=0.15,
        early_stop_patience=10,
    )

    # Create engine
    print("Creating finetuning engine...")
    engine = KonicFinetuningEngine(
        model_name=agent.get_base_model(),
        reward_composer=agent.get_reward_composer(),
        dataset_config=agent.get_dataset_config(),
        lora_config=agent.get_lora_config(),
        training_config=agent.get_training_config(),
        callback=callback,
        checkpoint_dir=args.checkpoint_dir,
    )

    # Run training
    print("Starting training...\n")
    result = engine.train(
        max_iterations=args.max_iterations,
        save_every=args.save_every,
    )

    # Evaluate on sample prompts
    print("\nEvaluating trained model...")
    print("-" * 70)

    test_prompts = [
        "Explain the concept of machine learning in simple terms.",
        "Write a short poem about the ocean.",
        "What are the main differences between Python and JavaScript?",
    ]

    eval_results = engine.evaluate(test_prompts)

    print("\nSample Generations:")
    print("=" * 70)

    for prompt, response, reward in zip(
        eval_results["prompts"],
        eval_results["responses"],
        eval_results["rewards"],
    ):
        print(f"\nPrompt: {prompt}")
        print(f"Response: {response[:400]}...")
        print(f"Reward: {reward:.4f}")
        print("-" * 70)

    print("\nTraining complete!")
    print(f"Final model saved to: {result.model_path}")


if __name__ == "__main__":
    main()
