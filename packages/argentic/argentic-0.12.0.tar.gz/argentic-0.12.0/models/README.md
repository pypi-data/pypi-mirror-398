# Model Checkpoints Directory

This directory stores downloaded model checkpoints for local inference.

## Quick Start

```bash
# List available models
python scripts/download_models.py --list

# Check your environment setup
python scripts/download_models.py --check

# Download Gemma 3n 4B model (multimodal)
python scripts/download_models.py --model gemma-3n-4b
```

## Configuration

After downloading a model, update your `.env` file:

```bash
# For Gemma models (using Transformers)
GEMMA_MODEL_ID="google/gemma-3n-E4B-it"
GEMMA_MODEL_PATH="./models/gemma-3n-4b"
```

Or in your config file:

```yaml
llm:
  provider: gemma
  gemma_model_id: "google/gemma-3n-E4B-it"
  gemma_model_path: "./models/gemma-3n-4b"  # Optional, uses HF cache if not set
```

## Available Models

### Gemma 3n E4B (4B parameters)
- **ID:** `gemma-3n-4b`
- **HF Model:** `google/gemma-3n-E4B-it`
- **Capabilities:** Vision + Audio + Text (Multimodal)
- **Size:** ~8-10 GB
- **Framework:** Transformers (PyTorch/Flax)
- **Best for:** Multimodal applications with reasonable hardware

### Gemma 3 12B (text-only)
- **ID:** `gemma-3-12b`
- **HF Model:** `google/gemma-3-12b-it`
- **Capabilities:** Text only
- **Size:** ~24 GB
- **Framework:** Transformers (PyTorch/Flax)
- **Best for:** High-quality text generation

## Prerequisites

### Hugging Face Setup (Optional, for private models)

For public models like Gemma, no authentication needed. For private models:

1. Create account at https://huggingface.co
2. Get token from https://huggingface.co/settings/tokens
3. Login: `huggingface-cli login`

### Install Dependencies

```bash
pip install huggingface-hub transformers torch
```

## Directory Structure

After downloading models, this directory will look like:

```
models/
├── README.md                    # This file
├── gemma-3n-4b/                # Symlink to downloaded model
│   ├── _METADATA
│   ├── checkpoint_00000
│   └── ...
└── gemma-3n-2b/                # Another model
    └── ...
```

## Note

This directory is in `.gitignore` - model files are NOT committed to git due to their large size.

