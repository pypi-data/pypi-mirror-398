# LangExtract OpenRouter Provider

A [LangExtract](https://github.com/google/langextract) provider plugin for [OpenRouter](https://openrouter.ai/).

## Installation

```bash
# Using uv (recommended)
uv pip install langextract-provider-openrouter

# Or using pip
pip install langextract-provider-openrouter
```

## Quick Start

1. Set your OpenRouter API key:
   ```bash
   export OPENROUTER_API_KEY=your_key_here
   ```

2. Use it in LangExtract:
   ```python
   import langextract as lx

   # Use the 'openrouter/' prefix followed by the OpenRouter model ID
   result = lx.extract(
       text_or_documents="...",
       prompt_description="...",
       model_id="openrouter/google/gemini-3-flash-preview"
   )
   ```

## Supported Models

This provider supports any model available on OpenRouter by prefixing the model ID with `openrouter/`. Common examples include:

- `openrouter/google/gemini-3-flash-preview`
- `openrouter/google/gemini-3-pro-preview`
- `openrouter/google/gemini-2.5-flash-preview-09-2025`
- `openrouter/Qwen/Qwen2.5-VL-72B-Instruct`
- `openrouter/openai/gpt-5`

## Configuration Options

Customize your requests using the `provider_options` dictionary.

### Reasoning Effort
Control the reasoning effort for models that support it.
- **Key**: `effort`
- **Values**: `"low"`, `"medium"`, `"high"`, `"minimal"` (default)
- **Reference**: [OpenRouter Reasoning Docs](https://openrouter.ai/docs/api/api-reference/responses/create-responses#request.body.reasoning)

```python
# Create a model with high reasoning effort
config = factory.ModelConfig(
    model_id="openrouter/Qwen/Qwen2.5-VL-72B-Instruct",
    provider_kwargs={
        "provider_options": {
            "effort": "high"
        }
    }
)
```

### Routing/Provider Options
These options control how OpenRouter acts as a router:
- `sort`: Strategy for provider selection (`"price"`, `"latency"`, `"throughput"`). Default: `"price"`.
- `ignore`: List of provider names to exclude (e.g., `["Parasail"]`).
- `allow_fallbacks`: Boolean to allow falling back to other providers. Default: `True`.
- `data_collection`: `"allow"` or `"deny"`. Default: `"allow"`.

### Usage Example (Inference Override)

```python
result = lx.extract(
    # ... inputs ...
    # Example: GPT-5
    model_id="openrouter/openai/gpt-5",
    provider_options={
        "effort": "medium",
        "sort": "throughput",
        "ignore": ["SlowProvider"]
    }
)
```

## Development

```bash
cd langextract-openrouter
uv venv --python 3.12
# Install dependencies
uv pip install -e ../langextract
uv pip install -e .
uv pip install pytest requests
# Run tests
uv run pytest
```
