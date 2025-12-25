# Langchain LLM Config

Yet another redundant Langchain abstraction: comprehensive Python package for managing and using multiple LLM providers (OpenAI, VLLM, Gemini, Infinity) with a unified interface for both chat assistants and embeddings.

[![PyPI version](https://badge.fury.io/py/langchain-llm-config.svg)](https://badge.fury.io/py/langchain-llm-config) [![Python package](https://github.com/liux2/Langchain-LLM-Config/actions/workflows/python-package.yml/badge.svg?branch=main)](https://github.com/liux2/Langchain-LLM-Config/actions/workflows/python-package.yml)

## Features

- 🤖 **Multiple Chat Providers**: Support for OpenAI, VLLM, and Gemini
- 🔗 **Multiple Embedding Providers**: Support for OpenAI, VLLM, and Infinity
- ⚙️ **Unified Configuration**: Single YAML configuration file for all providers
- 🚀 **Easy Setup**: CLI tool for quick configuration initialization
- 🔄 **Easy Context Concatenation**: Simplified process for combining contexts into chat
- 🔒 **Environment Variables**: Secure API key management
- 📦 **Self-Contained**: No need to import specific paths
- ⚡ **Async Support**: Full async/await support for all operations
- 🌊 **Streaming Chat**: Real-time streaming responses for interactive experiences
- 🛠️ **Enhanced CLI**: Environment setup and validation commands
- 🪶 **Lightweight Core**: Minimal dependencies with optional provider-specific packages
- 🎯 **Flexible Installation**: Install only the providers you need

## What's New in V2 Configuration

The V2 configuration format introduces a **model-centric** approach that provides:

### Key Benefits

- ✅ **Simpler API**: Reference models by name instead of provider/type hierarchy
- ✅ **More Flexible**: Define multiple models per provider with different configurations
- ✅ **Better Defaults**: Set default models by name, not provider
- ✅ **VLM Support**: Ready for vision-language models with dedicated `vlm` type
- ✅ **Clearer Structure**: Each model is a first-class entity with its own config
- ✅ **Easy Migration**: One command to migrate from V1 to V2

### Quick Comparison

**V1 (Old):**

```python
# Provider-centric: specify provider name
assistant = create_assistant(provider="openai", ...)
```

**V2 (New):**

```python
# Model-centric: specify model name
assistant = create_assistant(model="gpt-4-turbo", ...)
```

See the [Configuration Reference](#configuration-reference) section for detailed examples.

## Installation

### Basic Installation

The package has a lightweight core with optional dependencies for specific providers.

**Core installation (minimal dependencies):**

```bash
# Using uv (recommended)
uv add langchain-llm-config

# Using pip
pip install langchain-llm-config
```

### Provider-Specific Installation

**With OpenAI support:**

```bash
uv add "langchain-llm-config[openai]"
pip install "langchain-llm-config[openai]"
```

**With VLLM support:**

```bash
uv add "langchain-llm-config[vllm]"
pip install "langchain-llm-config[vllm]"
```

**With Gemini support:**

```bash
uv add "langchain-llm-config[gemini]"
pip install "langchain-llm-config[gemini]"
```

**With Infinity embeddings support:**

```bash
uv add "langchain-llm-config[infinity]"
pip install "langchain-llm-config[infinity]"
```

**With local models support (sentence-transformers):**

```bash
uv add "langchain-llm-config[local-models]"
pip install "langchain-llm-config[local-models]"
```

### Convenience Groups

**All assistant providers (OpenAI, VLLM, Gemini):**

```bash
uv add "langchain-llm-config[assistants]"
pip install "langchain-llm-config[assistants]"
```

**All embedding providers (Infinity, local models):**

```bash
uv add "langchain-llm-config[embeddings]"
pip install "langchain-llm-config[embeddings]"
```

**Everything (all providers and features):**

```bash
uv add "langchain-llm-config[all]"
pip install "langchain-llm-config[all]"
```

### Development Installation

```bash
git clone https://github.com/liux2/Langchain-LLM-Config.git
cd langchain-llm-config
uv sync --dev
uv run pip install -e .
```

## Dependency Optimization

This package is designed with a **lightweight core** approach:

### Core Dependencies (Always Installed)

- `langchain-core` - Core abstractions only (much lighter than full `langchain`)
- `langchain-openai` - OpenAI and VLLM provider support
- `pydantic` - Data validation and parsing
- `pyyaml` - Configuration file parsing
- `python-dotenv` - Environment variable management
- `openai` - OpenAI client library

### Optional Dependencies

- **Gemini**: `langchain-google-genai` - Only installed with `[gemini]` extra
- **Infinity**: `langchain-community` - Only installed with `[infinity]` extra
- **Local Models**: `sentence-transformers` - Only installed with `[local-models]` extra

### Benefits

- ✅ **Smaller installation size** - No heavy ML dependencies unless needed
- ✅ **Faster installation** - Skip unnecessary packages
- ✅ **Cleaner environments** - Only install what you use
- ✅ **Better compatibility** - Avoid conflicts from unused dependencies

## Quick Start

### 1. Initialize Configuration

```bash
# Initialize config in current directory (v2 format by default)
llm-config init

# Or specify a custom location
llm-config init ~/.config/api.yaml

# Use legacy v1 format (deprecated)
llm-config init --format v1
```

This creates an `api.yaml` file with all supported providers configured using the new **v2 model-centric format**.

### 2. Set Up Environment Variables

```bash
# Set up environment variables and create .env file
llm-config setup-env

# Or with custom config path
llm-config setup-env --config-path ~/.config/.env
```

This creates a `.env` file with placeholders for your API keys.

### 3. Configure Your Providers

Edit the generated `api.yaml` file with your API keys and settings.

#### V2 Configuration Format (Recommended)

The new **model-centric** configuration format allows you to define models independently:

```yaml
# Default models to use
default:
  chat_provider: gpt-3.5-turbo
  embedding_provider: text-embedding-ada-002

# Model definitions
models:
  gpt-3.5-turbo:
    model_type: chat
    provider_type: openai
    model_config:
      api_base: https://api.openai.com/v1
      api_key: ${OPENAI_API_KEY}
      model_name: gpt-3.5-turbo
      temperature: 0.7
      max_tokens: 8192

  text-embedding-ada-002:
    model_type: embedding
    provider_type: openai
    model_config:
      api_base: https://api.openai.com/v1
      api_key: ${OPENAI_API_KEY}
      model_name: text-embedding-ada-002

  llama-2-local:
    model_type: chat
    provider_type: vllm
    model_config:
      api_base: http://localhost:8000/v1
      api_key: ${OPENAI_API_KEY}
      model_name: meta-llama/Llama-2-7b-chat-hf
      temperature: 0.6
      extra_body:
        return_reasoning: false  # Set to true for reasoning output
```

#### V1 Configuration Format (Legacy, Auto-Converted)

The old provider-centric format is still supported but deprecated:

```yaml
llm:
  openai:
    chat:
      api_base: "https://api.openai.com/v1"
      api_key: "${OPENAI_API_KEY}"
      model_name: "gpt-3.5-turbo"
  default:
    chat_provider: "openai"
```

**Note:** V1 configs are automatically converted to V2 at runtime with a deprecation warning.

### 4. Set Environment Variables

Edit the `.env` file with your actual API keys:

```bash
OPENAI_API_KEY=your-openai-api-key
GEMINI_API_KEY=your-gemini-api-key
```

### 5. Use in Your Code

#### Basic Usage (Synchronous)

```python
from langchain_llm_config import create_assistant, create_embedding_provider
from pydantic import BaseModel, Field
from typing import List


# Define your response model
class ArticleAnalysis(BaseModel):
    summary: str = Field(..., description="Article summary")
    keywords: List[str] = Field(..., description="Key topics")
    sentiment: str = Field(..., description="Overall sentiment")


# V2 API: Use model names directly (recommended)
assistant = create_assistant(
    model="gpt-3.5-turbo",  # Reference model by name from config
    response_model=ArticleAnalysis,
    system_prompt="You are a helpful article analyzer.",
)

# Use the assistant - returns dict with parsed data
# Note: Structured output returns a dict, not a Pydantic model instance
result = assistant.ask("Analyze this article: ...")
print(result["summary"])  # Access as dict
print(result["keywords"])
print(result["sentiment"])

# Raw text mode (no structured output)
assistant_raw = create_assistant(
    model="gpt-3.5-turbo",
    auto_apply_parser=False,  # Disable parsing
    system_prompt="You are a helpful assistant.",
)
result = assistant_raw.ask("Tell me a joke")
print(result)  # Returns string

# Create an embedding provider
embedding_provider = create_embedding_provider(
    model="text-embedding-ada-002"  # Reference model by name
)

# Get embeddings (synchronous)
texts = ["Hello world", "How are you?"]
embeddings = embedding_provider.embed_texts(texts)

# V1 API: Still supported (deprecated)
assistant_v1 = create_assistant(
    provider="openai",  # Old way - provider name
    response_model=ArticleAnalysis,
)
```

#### Advanced Usage (Asynchronous)

```python
import asyncio

# Use the assistant (asynchronous)
result = await assistant.ask_async("Analyze this article: ...")
print(result["summary"])

# Get embeddings (asynchronous)
embeddings = await embedding_provider.embed_texts_async(texts)
```

#### Streaming Chat

```python
import asyncio
from langchain_llm_config import create_assistant


async def main():
    """Main async function to run the streaming chat example"""
    # Create assistant with auto_apply_parser=False for streaming
    assistant = create_assistant(
        provider="openai",
        system_prompt="You are a helpful assistant.",
        auto_apply_parser=False,  # Required for streaming
    )

    print("🤖 Starting streaming chat...")
    print("Response: ", end="", flush=True)

    try:
        # Simple streaming - just get text chunks
        async for chunk in assistant.chat_async("Tell me a story"):
            print(chunk, end="", flush=True)

        print("\n")

        # Advanced streaming - get chunks with metadata
        async for chunk in assistant.chat_stream("Explain quantum computing"):
            if chunk["type"] == "stream":
                print(chunk["content"], end="", flush=True)
            elif chunk["type"] == "final":
                print(f"\n\nProcessing time: {chunk['processing_time']:.2f}s")
                print(f"Model used: {chunk['model_used']}")
    except Exception as e:
        print(f"\n❌ Error occurred: {e}")


if __name__ == "__main__":
    # Run the async function
    asyncio.run(main())
```

#### Kunlun API (Bearer Token Authentication)

Kunlun APIs are OpenAI-compatible but use bearer token authentication instead of API keys.

```python
from langchain_llm_config import create_assistant, create_embedding_provider
from pydantic import BaseModel, Field

# Define your response model
class Analysis(BaseModel):
    summary: str = Field(description="Brief summary")
    key_points: list[str] = Field(description="Key points")

# Create Kunlun assistant with thinking mode enabled
assistant = create_assistant(
    model="kunlun-qwen3-235b",
    response_model=Analysis,
    system_prompt="You are a helpful AI assistant."
)

# Use the assistant
result = assistant.ask("Analyze the impact of AI on society")
print(result["summary"])
print(result["key_points"])

# Create Kunlun embedding provider
embedding_provider = create_embedding_provider(model="kunlun-bge-m3")
embeddings = embedding_provider.embed_texts(["Hello world", "AI is amazing"])
```

**Configuration:**

```yaml
models:
  kunlun-qwen3-235b:
    model_type: chat
    provider_type: kunlun
    model_config:
      api_base: ${KUNLUN_QWEN3_235B_API_BASE}  # Your Kunlun API endpoint
      bearer_token: ${KUNLUN_BEARER_TOKEN}
      model_name: Qwen3-235B-A22B
      temperature: 0.7
      max_tokens: 8000
      extra_body:
        chat_template_kwargs:
          enable_thinking: true  # Enable reasoning mode

  kunlun-bge-m3:
    model_type: embedding
    provider_type: kunlun
    model_config:
      api_base: ${KUNLUN_BGE_M3_API_BASE}  # Your Kunlun API endpoint
      bearer_token: ${KUNLUN_BEARER_TOKEN}
      model_name: embedding
      dimensions: 1024
```

**Environment Variables:**

```bash
export KUNLUN_BEARER_TOKEN="your_jwt_token_here"
export KUNLUN_QWEN3_235B_API_BASE="https://your-kunlun-endpoint/v1"
export KUNLUN_BGE_M3_API_BASE="https://your-kunlun-endpoint/v1"
```

**Key Features:**

- 🔐 **Bearer Token Authentication**: Uses JWT tokens instead of API keys
- 🧠 **Thinking Mode**: Enable reasoning with `chat_template_kwargs.enable_thinking`
- 🔌 **OpenAI-Compatible**: Works with standard OpenAI API format
- 🚀 **Full Feature Support**: Streaming, structured output, embeddings

## Supported Providers

### Chat Providers

| Provider | Models | Features | Installation |
|----------|--------|----------|-------------|
| **OpenAI** | GPT-3.5, GPT-4, etc. | Streaming, function calling, structured output | ✅ Core (always available) |
| **VLLM** | Any HuggingFace model | Local deployment, high performance | ✅ Core (always available) |
| **Gemini** | Gemini Pro, etc. | Google's latest models | 📦 `[gemini]` extra required |
| **Kunlun** | Qwen3, etc. | Bearer token auth, thinking mode | ✅ Core (always available) |

### Embedding Providers

| Provider | Models | Features | Installation |
|----------|--------|----------|-------------|
| **OpenAI** | text-embedding-ada-002, etc. | High quality, reliable | ✅ Core (always available) |
| **VLLM** | BGE, sentence-transformers | Local deployment | ✅ Core (always available) |
| **Infinity** | Various embedding models | Fast inference | 📦 `[infinity]` extra required |
| **Kunlun** | BGE, Qwen3-Embedding, etc. | Bearer token auth | ✅ Core (always available) |

## CLI Commands

```bash
# Initialize a new configuration file (v2 format by default)
llm-config init [path]
llm-config init --format v2  # Explicit v2 format
llm-config init --format v1  # Legacy v1 format

# Migrate v1 config to v2 format
llm-config migrate [--output path]

# Set up environment variables and create .env file
llm-config setup-env [path] [--force]

# Validate existing configuration
llm-config validate [path]

# Show package information
llm-config info
```

## Advanced Usage

### Custom Configuration Path

```python
from langchain_llm_config import create_assistant

assistant = create_assistant(
    response_model=MyModel,
    config_path="/path/to/custom/api.yaml"
)
```

### Context-Aware Conversations

```python
# Add context to your queries
result = await assistant.ask_async(
    query="What are the main points?",
    context="This is a research paper about machine learning...",
    extra_system_prompt="Focus on technical details."
)
```

### Direct Provider Usage

```python
from langchain_llm_config import VLLMAssistant, OpenAIEmbeddingProvider

# Core providers (always available)
vllm_assistant = VLLMAssistant(
    config={"api_base": "http://localhost:8000/v1", "model_name": "llama-2"},
    response_model=MyModel
)

openai_embeddings = OpenAIEmbeddingProvider(
    config={"api_key": "your-key", "model_name": "text-embedding-ada-002"}
)

# Optional providers (require extras)
# from langchain_llm_config import GeminiAssistant  # requires [gemini]
# from langchain_llm_config import InfinityEmbeddingProvider  # requires [infinity]
```

### Complete Example with Error Handling

```python
import asyncio
from langchain_llm_config import create_assistant, create_embedding_provider
from pydantic import BaseModel, Field
from typing import List

class ChatResponse(BaseModel):
    message: str = Field(..., description="The assistant's response message")
    confidence: float = Field(..., description="Confidence score", ge=0.0, le=1.0)
    suggestions: List[str] = Field(default_factory=list, description="Follow-up questions")

async def main():
    try:
        # Create assistant
        assistant = create_assistant(
            response_model=ChatResponse,
            provider="openai",
            system_prompt="You are a helpful AI assistant."
        )
        
        # Chat conversation
        response = await assistant.ask_async("What is the capital of France?")
        print(f"Assistant: {response['message']}")
        print(f"Confidence: {response['confidence']:.2f}")
        
        # Create embedding provider
        embedding_provider = create_embedding_provider(provider="openai")
        
        # Get embeddings
        texts = ["Hello world", "How are you?"]
        embeddings = await embedding_provider.embed_texts_async(texts)
        print(f"Generated {len(embeddings)} embeddings")
        
    except Exception as e:
        print(f"Error: {e}")

# Run the example
asyncio.run(main())
```

## Configuration Reference

### Environment Variables

The package supports environment variable substitution in configuration:

```yaml
api_key: "${OPENAI_API_KEY}"  # Will be replaced with actual value
```

### V2 Configuration Structure (Recommended)

Model-centric configuration where each model is defined independently:

```yaml
# Default models
default:
  chat_provider: model-name      # Model name for chat
  embedding_provider: model-name # Model name for embeddings

# Model definitions
models:
  model-name:
    model_type: chat | embedding | vlm
    provider_type: openai | vllm | gemini | infinity | reasoning
    model_config:
      api_base: "https://api.example.com/v1"
      api_key: "${API_KEY}"
      model_name: "actual-model-name"
      temperature: 0.7
      max_tokens: 8192
      top_p: 1.0
      connect_timeout: 60
      read_timeout: 60
      extra_body:
        return_reasoning: false  # Enable reasoning output (vLLM)
      # ... other provider-specific parameters
```

### V1 Configuration Structure (Legacy)

Provider-centric configuration (automatically converted to v2 at runtime):

```yaml
llm:
  provider_name:
    chat:
      api_base: "https://api.example.com/v1"
      api_key: "${API_KEY}"
      model_name: "model-name"
      # ... parameters
    embeddings:
      api_base: "https://api.example.com/v1"
      api_key: "${API_KEY}"
      model_name: "embedding-model"
  default:
    chat_provider: "provider_name"
    embedding_provider: "provider_name"
```

### Migration from V1 to V2

Use the CLI migration tool:

```bash
# Migrate and create backup
llm-config migrate

# Specify output path
llm-config migrate --output api_v2.yaml
```

Or manually update your config following the v2 structure above.

## Development

### Testing with Different Provider Combinations

```bash
# Test core functionality only
uv sync --extra test
uv run pytest

# Test with all providers
uv sync --extra test --extra all
uv run pytest

# Test specific provider combinations
uv sync --extra test --extra gemini
uv run pytest tests/test_providers.py -k gemini
```

### Running Tests

```bash
uv run pytest
```

### Code Formatting

```bash
uv run black .
uv run isort .
```

### Type Checking

```bash
uv run mypy .
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Support

- 📖 [Documentation](https://github.com/liux2/Langchain-LLM-Config#readme)
- 🐛 [Issue Tracker](https://github.com/liux2/Langchain-LLM-Config/issues)
- 💬 [Discussions](https://github.com/liux2/Langchain-LLM-Config/discussions)
