"""Advanced LLM Finetuning Agent Template - Code Generation Quality.

This template provides an advanced setup for RLHF finetuning focused on
improving code generation quality. It demonstrates:
- Multiple reward functions for code quality evaluation
- WeightedSumReducer for balancing reward signals
- Custom training callback for monitoring
- Advanced LoRA configuration with more target modules
- Code-focused dataset configuration

Konic Cloud handles the training - this file only defines the agent.
"""

import ast
import re
from typing import Any

from konic.finetuning import (
    BaseKonicFinetuningCallback,
    DatasetConfig,
    DatasetSource,
    FinetuningIterationResult,
    FinetuningResult,
    KonicFinetuningAgent,
    KonicLLMRewardComposer,
    LoraConfig,
    TrainingConfig,
    WeightedSumReducer,
    llm_reward,
)
from konic.runtime import register_agent

# =============================================================================
# Code Quality Reward Composer
# =============================================================================


class CodeQualityRewardComposer(KonicLLMRewardComposer):
    """Reward composer optimized for code generation quality.

    This composer evaluates generated code on multiple dimensions:
    - Syntax validity: Is the code valid Python?
    - Formatting quality: Does it follow good formatting practices?
    - Documentation: Does it include docstrings?
    - Type hints: Does it use type annotations?

    Uses WeightedSumReducer to balance these signals.
    """

    reducer = WeightedSumReducer

    def __init__(self):
        """Initialize with custom reward weights."""
        super().__init__(
            reward_weights={
                "syntax_validity": 1.0,  # Most important
                "formatting_quality": 0.5,
                "docstring_presence": 0.3,
                "type_hint_usage": 0.3,
                "code_structure": 0.4,
            },
            kl_penalty_weight=0.05,
        )

    def _extract_code_block(self, response: str) -> str:
        """Extract code from markdown code blocks if present."""
        # Try to extract from ```python ... ``` blocks
        pattern = r"```(?:python)?\s*\n(.*?)\n```"
        matches = re.findall(pattern, response, re.DOTALL)
        if matches:
            return matches[0].strip()

        # Try to extract from ``` ... ``` blocks
        pattern = r"```\s*\n(.*?)\n```"
        matches = re.findall(pattern, response, re.DOTALL)
        if matches:
            return matches[0].strip()

        # Return raw response if no code blocks found
        return response.strip()

    @llm_reward
    def syntax_validity(self, prompt: str, response: str) -> float:
        """Check if generated code has valid Python syntax.

        Args:
            prompt: The input prompt.
            response: The generated response containing code.

        Returns:
            1.0 if valid Python syntax, 0.0 otherwise.
        """
        code = self._extract_code_block(response)

        if not code:
            return 0.0

        try:
            ast.parse(code)
            return 1.0
        except SyntaxError:
            return 0.0

    @llm_reward
    def formatting_quality(self, prompt: str, response: str) -> float:
        """Evaluate code formatting and style.

        Checks for:
        - Consistent indentation (spaces vs tabs)
        - Reasonable line lengths
        - Proper spacing around operators

        Args:
            prompt: The input prompt.
            response: The generated response containing code.

        Returns:
            Score between 0.0 and 1.0.
        """
        code = self._extract_code_block(response)

        if not code:
            return 0.0

        score = 1.0
        lines = code.split("\n")

        # Check for mixed tabs and spaces
        has_tabs = any("\t" in line for line in lines)
        has_spaces = any(line.startswith("    ") for line in lines)
        if has_tabs and has_spaces:
            score -= 0.3

        # Check for very long lines (>120 chars)
        long_lines = sum(1 for line in lines if len(line) > 120)
        if long_lines > 0:
            score -= min(0.3, long_lines * 0.1)

        # Check for trailing whitespace
        trailing_ws = sum(1 for line in lines if line != line.rstrip())
        if trailing_ws > 0:
            score -= min(0.2, trailing_ws * 0.05)

        return max(0.0, score)

    @llm_reward
    def docstring_presence(self, prompt: str, response: str) -> float:
        """Check if functions and classes have docstrings.

        Args:
            prompt: The input prompt.
            response: The generated response containing code.

        Returns:
            Score between 0.0 and 1.0 based on docstring coverage.
        """
        code = self._extract_code_block(response)

        if not code:
            return 0.0

        try:
            tree = ast.parse(code)
        except SyntaxError:
            return 0.0

        # Count functions and classes
        definitions = [
            node for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef | ast.ClassDef))
        ]

        if not definitions:
            # No functions/classes to document
            return 0.5

        # Count those with docstrings
        documented = 0
        for node in definitions:
            if (
                node.body
                and isinstance(node.body[0], ast.Expr)
                and isinstance(node.body[0].value, ast.Constant)
                and isinstance(node.body[0].value.value, str)
            ):
                documented += 1

        return documented / len(definitions)

    @llm_reward
    def type_hint_usage(self, prompt: str, response: str) -> float:
        """Check if functions use type hints.

        Args:
            prompt: The input prompt.
            response: The generated response containing code.

        Returns:
            Score between 0.0 and 1.0 based on type hint coverage.
        """
        code = self._extract_code_block(response)

        if not code:
            return 0.0

        try:
            tree = ast.parse(code)
        except SyntaxError:
            return 0.0

        functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]

        if not functions:
            return 0.5

        typed_funcs = 0
        for func in functions:
            has_return_type = func.returns is not None
            has_arg_types = any(arg.annotation is not None for arg in func.args.args)

            if has_return_type or has_arg_types:
                typed_funcs += 1

        return typed_funcs / len(functions)

    @llm_reward
    def code_structure(self, prompt: str, response: str) -> float:
        """Evaluate overall code structure and organization.

        Checks for:
        - Reasonable function/method length
        - Not too deeply nested
        - Has meaningful variable names (not single letters)

        Args:
            prompt: The input prompt.
            response: The generated response containing code.

        Returns:
            Score between 0.0 and 1.0.
        """
        code = self._extract_code_block(response)

        if not code:
            return 0.0

        score = 1.0

        try:
            tree = ast.parse(code)
        except SyntaxError:
            return 0.0

        functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]

        # Check function length (penalize very long functions)
        for func in functions:
            func_lines = func.end_lineno - func.lineno if hasattr(func, "end_lineno") else 0
            if func_lines > 50:
                score -= 0.2

        # Check for single-letter variable names (except common ones like i, j, k, x, y)
        allowed_single = {"i", "j", "k", "n", "x", "y", "z", "_"}
        names = [node.id for node in ast.walk(tree) if isinstance(node, ast.Name)]
        single_letter = [n for n in names if len(n) == 1 and n not in allowed_single]
        if len(single_letter) > 3:
            score -= 0.2

        return max(0.0, score)


# =============================================================================
# Custom Training Callback
# =============================================================================


class CodeQualityCallback(BaseKonicFinetuningCallback):
    """Custom callback for monitoring code generation quality metrics.

    Tracks and logs:
    - Reward breakdown by category
    - Best performing iteration
    - Sample generated code snippets
    """

    def __init__(self, log_interval: int = 10, log_samples: bool = True):
        """Initialize the callback.

        Args:
            log_interval: Log detailed metrics every N iterations.
            log_samples: Whether to log sample generations.
        """
        self.log_interval = log_interval
        self.log_samples = log_samples
        self._best_reward = float("-inf")
        self._best_iteration = 0

    def on_train_begin(self, config: dict[str, Any]) -> None:
        """Log training configuration."""
        print("\n" + "=" * 60)
        print("CODE GENERATION QUALITY FINETUNING")
        print("=" * 60)
        print(f"Model: {config.get('model_name', 'unknown')}")
        print(f"LoRA Enabled: {config.get('use_lora', False)}")
        print("=" * 60 + "\n")

    def on_train_end(self, result: FinetuningResult) -> None:
        """Log final training results."""
        print("\n" + "=" * 60)
        print("TRAINING COMPLETE")
        print("=" * 60)
        print(f"Total Iterations: {result.total_iterations}")
        print(f"Best Reward: {result.best_reward:.4f} (iter {result.best_iteration})")
        print(f"Final Reward: {result.final_reward_mean:.4f}")
        print("=" * 60 + "\n")

    def on_iteration_end(self, result: FinetuningIterationResult) -> None:
        """Log iteration metrics."""
        # Track best
        if result.reward_mean > self._best_reward:
            self._best_reward = result.reward_mean
            self._best_iteration = result.iteration
            best_marker = " *BEST*"
        else:
            best_marker = ""

        print(
            f"[Iter {result.iteration:4d}] "
            f"Reward: {result.reward_mean:7.4f} | "
            f"KL: {result.kl_divergence:.4f} | "
            f"Loss: {result.total_loss:.4f}{best_marker}"
        )

        # Detailed logging at intervals
        if result.iteration % self.log_interval == 0 and result.reward_breakdown:
            print("\n  Reward Breakdown:")
            for name, value in sorted(result.reward_breakdown.items()):
                print(f"    {name}: {value:.4f}")
            print()


# =============================================================================
# Configuration
# =============================================================================

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

# Training configuration with PPO parameters
training_config = TrainingConfig(
    learning_rate=1e-5,  # Conservative LR for stability
    batch_size=2,
    gradient_accumulation_steps=4,
    kl_penalty_weight=0.05,
    clip_ratio=0.2,
    ppo_epochs=4,
    vf_coef=0.5,
    entropy_coef=0.01,
    max_grad_norm=0.5,
)

# Code dataset configuration
dataset_config = DatasetConfig(
    source=DatasetSource.HUGGINGFACE,
    name="sahil2801/CodeAlpaca-20k",
    prompt_column="instruction",
    split="train",
    max_samples=1000,
    shuffle=True,
    shuffle_seed=42,
)

# Custom callback for monitoring
callback = CodeQualityCallback(log_interval=10, log_samples=True)


# =============================================================================
# Agent Registration
# =============================================================================

# Create the finetuning agent
agent = KonicFinetuningAgent(
    base_model="codellama/CodeLlama-7b-hf",  # Code-specialized model
    reward_composer=CodeQualityRewardComposer(),
    lora_config=lora_config,
    dataset_config=dataset_config,
    training_config=training_config,
)

# Register for Konic Cloud
register_agent(agent, name="{{cookiecutter.name.replace(' ', '-').lower()}}")
