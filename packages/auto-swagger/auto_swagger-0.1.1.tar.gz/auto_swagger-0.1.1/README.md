# Auto Swagger Documentation Generator

A sophisticated tool that automatically generates Swagger/OpenAPI documentation for Express.js APIs using advanced NLP techniques and LLMs.

## Overview

This project combines Natural Language Processing (NLP) techniques with Large Language Models (LLMs) to automatically generate high-quality API documentation. By preprocessing code with NLP before sending it to LLMs, we achieve:

- Better context understanding
- Reduced token usage
- More specific and higher quality responses
- Fine-grained control over the documentation pipeline
- Automated code base updates

## Features

- Automatic API route detection
- Intelligent parameter inference
- Response schema generation
- Validation rules detection
- Swagger/OpenAPI compliant output
- Support for Express.js routes
- Automated documentation insertion

## Architecture

![Architecture Diagram](attachments/image.png)

## Setup

1. Clone the repository:

```bash
git clone https://github.com/yourusername/auto_swagger.git
cd auto_swagger
```

2. Install UV if you haven't already:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

3. Create a virtual environment and install dependencies:

```bash
uv venv
```

4. Run the auto-swagger tool:

```bash
# Run the main documentation generator
uv run auto-swagger --repo-path path/to/express/app

# Run the fine-tuning tool (if needed)
uv run finetune
```

## CLI Usage

### Basic Usage

```bash
# Generate documentation for the current directory
uv run auto-swagger

# Generate documentation for a specific repository
uv run auto-swagger --repo-path /path/to/express/app
```

### Command Line Arguments

- `--repo-path` (optional): Path to the repository root. Defaults to current working directory.

  ```bash
  uv run auto-swagger --repo-path /Users/username/projects/my-api
  ```

- `--branch` (optional): Branch to check for unmerged changes. Defaults to current branch.

  ```bash
  uv run auto-swagger --repo-path /path/to/repo --branch feature/new-endpoints
  ```

- `--model` (optional): Hugging Face model name to use for generation. Overrides the default model in config.

  ```bash
  # Use Google Gemma model
  uv run auto-swagger --repo-path /path/to/repo --model "google/gemma-2-2b-it"
  
  # Use DeepSeek Coder model
  uv run auto-swagger --repo-path /path/to/repo --model "deepseek-ai/deepseek-coder-1.3b-instruct"
  ```

- `--lora-adapter` (optional): LoRA adapter ID from Hugging Face. Use `none` to disable LoRA adapter and use base model only.

  ```bash
  # Use a custom LoRA adapter
  uv run auto-swagger --repo-path /path/to/repo --lora-adapter "username/my-adapter"
  
  # Disable LoRA adapter (use base model only)
  uv run auto-swagger --repo-path /path/to/repo --lora-adapter none
  ```

### Example Commands

```bash
# Full example with all options
uv run auto-swagger \
  --repo-path "/Users/username/projects/my-api" \
  --branch "main" \
  --model "google/gemma-2-2b-it" \
  --lora-adapter none

# Use default model but disable LoRA adapter
uv run auto-swagger \
  --repo-path "/path/to/repo" \
  --lora-adapter none

# Use a different model with custom LoRA adapter
uv run auto-swagger \
  --repo-path "/path/to/repo" \
  --model "google/gemma-2-2b-it" \
  --lora-adapter "username/custom-adapter"
```

## Project Structure

```text
auto_swagger/
├── src/
│   └── auto_swagger/         # Source code
│       ├── config/          # Configuration management
│       ├── finetune/        # Model fine-tuning utilities
│       ├── parser/          # Code parsing and analysis
│       └── swagger_generator/ # Documentation generation
├── data/                    # Project data
│   ├── jsdocs_finetune.jsonl # Fine-tuning dataset
│   └── swagger_docs/        # Generated documentation
├── pyproject.toml          # Project configuration
└── README.md
```

## Configuration

### Default Model Configuration

The project uses a config with default model settings:

```python
@dataclass
class LLMConfig:
    model_name: str = "deepseek-ai/deepseek-coder-1.3b-instruct"
    lora_adapter_id: Optional[str] = "paulopasso/auto-swagger"  # Default LoRA adapter
    max_new_tokens: int = 8192
    temperature: float = 0.2
    top_k: int = 50
    top_p: float = 0.95
    max_retries: int = 3
```

### Overriding Configuration via CLI

You can override the model and LoRA adapter settings using command-line arguments (see [CLI Usage](#cli-usage) above) without modifying the code:

```bash
# Use a different model
uv run auto-swagger --repo-path /path/to/repo --model "google/gemma-2-2b-it"

# Disable LoRA adapter
uv run auto-swagger --repo-path /path/to/repo --lora-adapter none

# Use custom model and adapter
uv run auto-swagger --repo-path /path/to/repo \
  --model "google/gemma-2-2b-it" \
  --lora-adapter "username/my-adapter"
```

### Advanced Configuration

For advanced configuration (temperature, top_k, top_p, etc.), you can modify `src/auto_swagger/swagger_generator/generator_config.py`.

## Future Improvements

- Support for additional backend frameworks beyond Express.js
- Local CLI version without GitHub app dependency
- Enhanced pattern recognition
- Additional documentation formats
- Real-time documentation updates
