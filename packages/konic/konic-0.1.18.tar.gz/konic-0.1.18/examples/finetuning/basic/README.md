# Basic RLHF Finetuning Example

This example demonstrates the fundamentals of RLHF (Reinforcement Learning from Human Feedback) using Konic's finetuning module. It trains GPT-2 to generate more positive, concise, and coherent responses.

## What You'll Learn

- How to create custom reward functions using the `@llm_reward` decorator
- Basic LoRA configuration for parameter-efficient finetuning
- Using HuggingFace datasets with Konic
- Running the RLHF training loop with the `KonicFinetuningEngine`

## Prerequisites

- Python 3.10+
- CUDA-compatible GPU (recommended) or CPU
- ~2GB disk space for model and dataset

## Installation

```bash
# Install konic
pip install konic
```

## Quick Start

```bash
python sentiment_rlhf.py
```

## How It Works

### 1. Custom Reward Functions

The example defines three reward functions that guide the model's learning:

```python
class SentimentRewardComposer(KonicLLMRewardComposer):
    @llm_reward
    def brevity_bonus(self, prompt: str, response: str) -> float:
        """Rewards shorter, concise responses."""
        return max(0.0, 1.0 - len(response) / 300)

    @llm_reward
    def positivity_reward(self, prompt: str, response: str) -> float:
        """Rewards positive sentiment words."""
        # ... counts positive words ...

    @llm_reward
    def coherence_penalty(self, prompt: str, response: str) -> float:
        """Penalizes repetitive patterns."""
        # ... detects repetition ...
```

The `@llm_reward` decorator marks methods for automatic discovery. The composer will call all decorated methods and combine their outputs.

### 2. LoRA Configuration

LoRA (Low-Rank Adaptation) enables efficient finetuning by only training small adapter matrices:

```python
lora_config = LoraConfig(
    r=8,              # Rank of adapter matrices
    lora_alpha=16,    # Scaling factor
    target_modules=["c_attn", "c_proj"],  # GPT-2 attention layers
)
```

### 3. Training Loop

The engine handles the complete RLHF pipeline:

```python
agent = KonicFinetuningAgent(
    base_model="gpt2",
    reward_composer=SentimentRewardComposer(),
    lora_config=lora_config,
    dataset_config=dataset_config,
)

engine = KonicFinetuningEngine.from_agent(agent)
result = engine.train(max_iterations=50)
```

## Expected Output

```
============================================================
Starting RLHF Training
============================================================
Model: gpt2
LoRA: True
Learning Rate: 5e-05
Batch Size: 4
Max Iterations: 50
============================================================

[Iter    1] Reward:   0.423 (+/- 0.156) | KL: 0.0012 | Loss: 2.3451 | Time: 1.2s
[Iter    2] Reward:   0.456 (+/- 0.143) | KL: 0.0024 | Loss: 2.1234 | Time: 1.1s
...
[Iter   50] Reward:   0.687 (+/- 0.098) | KL: 0.0156 | Loss: 1.2345 | Time: 1.0s

==================================================
Finetuning Results Summary
==================================================
Model: gpt2
Total Iterations: 50
Best Reward: 0.7234 (iteration 47)
Final Reward: 0.6870
==================================================
```

## Configuration Options

### Adjust Reward Weights

You can weight different reward signals by passing `reward_weights` to the composer:

```python
composer = SentimentRewardComposer(
    reward_weights={
        "brevity_bonus": 1.0,
        "positivity_reward": 2.0,  # Emphasize positivity
        "coherence_penalty": 0.5,
    }
)
```

### Change Training Parameters

```python
training_config = TrainingConfig(
    learning_rate=1e-5,      # Lower for more stable training
    batch_size=8,            # Increase if GPU memory allows
    kl_penalty_weight=0.1,   # Higher to stay closer to base model
    ppo_epochs=4,            # More PPO updates per iteration
)
```

### Use a Different Dataset

```python
dataset_config = DatasetConfig(
    source=DatasetSource.HUGGINGFACE,
    name="yelp_polarity",    # Different sentiment dataset
    prompt_column="text",
    split="train",
    max_samples=1000,
)
```

## Troubleshooting

### Out of Memory

- Reduce `batch_size` in `TrainingConfig`
- Use a smaller model like `distilgpt2`
- Enable gradient checkpointing (if supported)

### Slow Training

- Reduce `max_samples` in `DatasetConfig`
- Lower `ppo_epochs` in `TrainingConfig`
- Use GPU if available

### Poor Results

- Increase `max_iterations`
- Adjust reward weights to balance signals
- Lower `kl_penalty_weight` to allow more learning

## Next Steps

After completing this example, check out:

- **[Advanced Example](../finetuning_instruction_following/)**: Instruction following with HuggingFace reward models
- **Konic Documentation**: Full API reference and advanced features
