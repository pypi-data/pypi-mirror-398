# Migration Guide: V1 to V2 Configuration Format

This guide helps you migrate from the old provider-centric (v1) configuration format to the new model-centric (v2) format.

## Why Migrate?

The v2 format offers several advantages:

- **More Flexible**: Define multiple models using the same provider with different configurations
- **Clearer**: Reference models by meaningful names instead of provider/type hierarchy
- **Extensible**: Easier to add new models and capabilities (e.g., VLM support)
- **Simpler API**: Use `model="gpt-4"` instead of `provider="openai"`

## Quick Migration

### Automatic Migration (Recommended)

Use the CLI migration tool:

```bash
# Migrate your config (creates backup automatically)
llm-config migrate

# Or migrate to a new file
llm-config migrate -o api_v2.yaml
```

### Manual Migration

If you prefer to migrate manually, follow the structure changes below.

## Configuration Structure Changes

### V1 Format (Old)

```yaml
llm:
  default:
    chat_provider: openai
    embedding_provider: openai
  
  openai:
    chat:
      api_key: ${OPENAI_API_KEY}
      model_name: gpt-3.5-turbo
      temperature: 0.7
    embeddings:
      api_key: ${OPENAI_API_KEY}
      model_name: text-embedding-ada-002
  
  vllm:
    chat:
      api_base: http://localhost:8000/v1
      model_name: llama-2-7b
```

### V2 Format (New)

```yaml
default:
  chat_provider: gpt-3.5-turbo
  embedding_provider: text-embedding-ada-002

models:
  gpt-3.5-turbo:
    model_type: chat
    provider_type: openai
    model_config:
      api_key: ${OPENAI_API_KEY}
      model_name: gpt-3.5-turbo
      temperature: 0.7
  
  text-embedding-ada-002:
    model_type: embedding
    provider_type: openai
    model_config:
      api_key: ${OPENAI_API_KEY}
      model_name: text-embedding-ada-002
  
  llama-2-7b:
    model_type: chat
    provider_type: vllm
    model_config:
      api_base: http://localhost:8000/v1
      model_name: llama-2-7b
```

## Code Changes

### Creating Assistants

**V1 (Old - Still Works):**
```python
from langchain_llm_config import create_assistant

# Using provider name
assistant = create_assistant(
    provider="openai",
    response_model=MyModel
)
```

**V2 (New - Recommended):**
```python
from langchain_llm_config import create_assistant

# Using model name
assistant = create_assistant(
    model="gpt-4",
    response_model=MyModel
)

# Or use default from config
assistant = create_assistant(response_model=MyModel)
```

### Creating Embedding Providers

**V1 (Old - Still Works):**
```python
from langchain_llm_config import create_embedding_provider

embedder = create_embedding_provider(provider="openai")
```

**V2 (New - Recommended):**
```python
from langchain_llm_config import create_embedding_provider

embedder = create_embedding_provider(model="text-embedding-ada-002")

# Or use default from config
embedder = create_embedding_provider()
```

## Backward Compatibility

The package maintains **full backward compatibility**:

- V1 configs are automatically detected and converted at runtime
- Old code using `provider=` parameter continues to work
- You can migrate at your own pace

## Benefits of V2 Format

### 1. Multiple Models per Provider

```yaml
models:
  gpt-3.5-turbo:
    model_type: chat
    provider_type: openai
    model_config:
      model_name: gpt-3.5-turbo
      temperature: 0.7
  
  gpt-4:
    model_type: chat
    provider_type: openai
    model_config:
      model_name: gpt-4
      temperature: 0.5
```

### 2. Meaningful Model Names

```python
# Clear and explicit
assistant = create_assistant(model="gpt-4-turbo")
assistant = create_assistant(model="llama-2-70b-local")
assistant = create_assistant(model="gemini-pro")
```

### 3. Vision-Language Model Support

```yaml
models:
  gpt-4-vision:
    model_type: vlm
    provider_type: openai
    model_config:
      model_name: gpt-4-vision-preview
```

## Troubleshooting

### Issue: "Unknown config format"

Make sure your config has either:
- `llm:` key at root (v1 format)
- `models:` and `default:` keys at root (v2 format)

### Issue: "Model not found"

Check that the model name in `default.chat_provider` exists in the `models:` section.

### Issue: Migration creates wrong provider_type

The automatic migration uses the provider name from v1. If you had custom providers (like "reasoning" or "vlm"), you may need to manually adjust the `provider_type` to the actual provider (e.g., "openai", "vllm").

## Next Steps

1. Run `llm-config migrate` to convert your config
2. Test your application with the new config
3. Update your code to use `model=` parameter (optional but recommended)
4. Enjoy the improved flexibility!

For more examples, see `examples/v2_usage.py`.

