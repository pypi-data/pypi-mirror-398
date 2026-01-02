# Advanced RLHF - Instruction Following with HuggingFace Reward Models

This advanced example demonstrates how to train a large language model to better follow instructions using a combination of neural reward models and custom reward functions.

## What You'll Learn

- Using pre-trained HuggingFace reward models for semantic quality scoring
- Combining neural rewards with rule-based `@llm_reward` functions
- Advanced LoRA configuration targeting multiple transformer layers
- Custom callbacks for detailed training monitoring
- Early stopping based on KL divergence
- Configuring reward weights with `WeightedSumReducer`

## Prerequisites

- Python 3.10+
- CUDA-compatible GPU with 16GB+ VRAM (for 7B models)
- ~20GB disk space for models and checkpoints
- HuggingFace account with model access (for LLaMA)

## Installation

```bash
# Install konic with finetuning dependencies
pip install konic

# Additional dependencies for this example
pip install accelerate bitsandbytes
```

## Quick Start

```bash
# Full training with HF reward model
python instruction_following_rlhf.py

# Faster testing without HF reward model
python instruction_following_rlhf.py --no-hf-reward

# Use a smaller model for testing
python instruction_following_rlhf.py --model gpt2 --no-hf-reward
```

## Command Line Options

| Option | Default | Description |
|--------|---------|-------------|
| `--model` | `meta-llama/Llama-2-7b-hf` | HuggingFace model ID |
| `--max-iterations` | 100 | Training iterations |
| `--save-every` | 25 | Checkpoint frequency |
| `--no-hf-reward` | False | Disable HF reward model |
| `--checkpoint-dir` | `./checkpoints/...` | Checkpoint directory |

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                  Instruction Following RLHF                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   ┌─────────────────┐        ┌──────────────────────────┐   │
│   │  Base Model     │        │  HuggingFace Reward      │   │
│   │  (LLaMA-2 7B)   │        │  Model (DeBERTa)         │   │
│   │                 │        │                          │   │
│   │  + LoRA Adapters│        │  Scores instruction      │   │
│   │   (r=16)        │        │  following quality       │   │
│   └────────┬────────┘        └────────────┬─────────────┘   │
│            │                              │                 │
│            ▼                              │                 │
│   ┌─────────────────┐                     │                 │
│   │  Generate       │                     │                 │
│   │  Responses      │                     │                 │
│   └────────┬────────┘                     │                 │
│            │                              │                 │
│            ▼                              ▼                 │
│   ┌─────────────────────────────────────────────────────┐   │
│   │           Reward Composition                        │   │
│   │                                                     │   │
│   │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │   │
│   │  │ HF Reward   │  │ Format      │  │ Structure   │  │   │
│   │  │ (w=1.0)     │  │ (w=0.3)     │  │ (w=0.2)     │  │   │
│   │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  │   │
│   │         │                │                │         │   │
│   │         └────────────────┴────────────────┘         │   │
│   │                          │                          │   │
│   │                          ▼                          │   │
│   │              WeightedSumReducer                     │   │
│   │              Total Reward = Σ(wi × ri)              │   │
│   └─────────────────────────────────────────────────────┘   │
│                              │                              │
│                              ▼                              │
│   ┌─────────────────────────────────────────────────────┐   │
│   │              PPO Update                             │   │
│   │  - Advantage estimation (GAE)                       │   │
│   │  - Clipped policy gradient                          │   │
│   │  - KL penalty against reference                     │   │
│   └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Key Components

### 1. HuggingFace Reward Model

The example uses OpenAssistant's DeBERTa reward model, which was trained on human preference data:

```python
HuggingFaceRewardModel(
    model_id="OpenAssistant/reward-model-deberta-v3-large-v2",
    device="auto",
    max_length=512,
    normalize=True,  # Normalize to stable range
)
```

### 2. Custom Reward Functions

Three complementary reward functions enforce specific requirements:

```python
@llm_reward
def format_compliance(self, prompt: str, response: str) -> float:
    """Check formatting: punctuation, length, style."""

@llm_reward
def instruction_acknowledgment(self, prompt: str, response: str) -> float:
    """Check if response addresses key prompt elements."""

@llm_reward
def response_structure(self, prompt: str, response: str) -> float:
    """Evaluate logical structure and flow."""
```

### 3. Reward Weighting

Use `WeightedSumReducer` to balance different signals:

```python
reward_weights={
    "hf_OpenAssistant_reward_model_deberta_v3_large_v2": 1.0,  # Primary
    "format_compliance": 0.3,                                   # Secondary
    "instruction_acknowledgment": 0.2,                          # Secondary
    "response_structure": 0.2,                                  # Secondary
}
```

### 4. Custom Callback

The `InstructionTrainingCallback` provides:
- Detailed per-iteration logging with reward breakdown
- Sample generation logging for quality inspection
- KL-based early stopping to prevent mode collapse
- Best model tracking

```python
callback = InstructionTrainingCallback(
    log_interval=10,                    # Detailed logs every 10 iters
    log_samples=True,                   # Show generated samples
    early_stop_kl_threshold=0.15,       # Stop if KL exceeds 0.15
    early_stop_patience=10,             # For 10 consecutive violations
)
```

### 5. Advanced LoRA Configuration

Target more transformer layers for better adaptation:

```python
lora_config = LoraConfig(
    r=16,
    lora_alpha=32,
    target_modules=[
        "q_proj", "k_proj", "v_proj", "o_proj",  # Attention
        "gate_proj", "up_proj", "down_proj",     # MLP
    ],
)
```

## Expected Output

```
======================================================================
INSTRUCTION FOLLOWING RLHF TRAINING
======================================================================
Model:              meta-llama/Llama-2-7b-hf
LoRA Enabled:       True
Learning Rate:      1e-05
Batch Size:         2
Max Iterations:     100
KL Penalty Weight:  0.05
----------------------------------------------------------------------
Early Stop KL:      0.15
Early Stop Patience: 10
======================================================================

[Iter    1] Reward:  0.3421 (+/- 0.156) | KL: 0.0012 | Loss: 3.2451
[Iter    2] Reward:  0.3567 (+/- 0.143) | KL: 0.0024 | Loss: 3.1234
...
[Iter   10] Reward:  0.4523 (+/- 0.098) | KL: 0.0156 | Loss: 2.8765

  ──────────────────────────────────────────────────
  Detailed Metrics (Iteration 10)
  ──────────────────────────────────────────────────
  Reward Range:     [0.312, 0.534]
  Policy Loss:      0.0234
  Value Loss:       0.1567
  Entropy:          0.0234
  Clip Fraction:    0.123
  Response Length:  87.3 (+/- 23.5)

  Reward Breakdown:
    format_compliance: 0.7234
    hf_OpenAssistant...: 0.4123
    instruction_acknowledgment: 0.5678
    response_structure: 0.6234
  ──────────────────────────────────────────────────
```

## Memory Optimization

For systems with limited GPU memory:

```python
# Use 8-bit quantization
from transformers import BitsAndBytesConfig

bnb_config = BitsAndBytesConfig(
    load_in_8bit=True,
)

# Reduce batch size and accumulation
training_config = TrainingConfig(
    batch_size=1,
    gradient_accumulation_steps=8,
)
```

## Troubleshooting

### Model Access Denied

For LLaMA models, you need to:
1. Accept the license at https://huggingface.co/meta-llama/Llama-2-7b-hf
2. Login with `huggingface-cli login`

### Out of Memory

- Use `--model gpt2` for testing
- Add `--no-hf-reward` to skip loading the reward model
- Reduce batch size in the code

### High KL Divergence

- Increase `kl_penalty_weight` in `TrainingConfig`
- Lower the learning rate
- Reduce reward weights to avoid over-optimization

### Reward Hacking

If the model learns to game specific rewards:
- Add more diverse reward functions
- Increase KL penalty
- Reduce training iterations

## Customization

### Using Different Reward Models

```python
# Sentiment-based reward
HuggingFaceRewardModel(
    model_id="lvwerra/distilbert-imdb",
    label_index=1,  # Positive sentiment class
)

# Safety/toxicity reward
HuggingFaceRewardModel(
    model_id="unitary/toxic-bert",
    label_index=0,  # Non-toxic class
)
```

### Using Different Datasets

```python
# OpenAssistant conversations
DatasetConfig(
    name="OpenAssistant/oasst1",
    prompt_column="text",
)

# ShareGPT format
DatasetConfig(
    name="anon8231489123/ShareGPT_Vicuna_unfiltered",
    prompt_column="conversations",
)
```

## Next Steps

- Explore DPO (Direct Preference Optimization) when available
- Add model merging for combining multiple adapters
- Implement multi-turn conversation training
- Add safety guardrails with constitutional AI

## References

- [OpenAssistant Reward Model](https://huggingface.co/OpenAssistant/reward-model-deberta-v3-large-v2)
- [LoRA: Low-Rank Adaptation](https://arxiv.org/abs/2106.09685)
- [PPO for RLHF](https://arxiv.org/abs/2203.02155)
- [Alpaca Dataset](https://huggingface.co/datasets/tatsu-lab/alpaca)
