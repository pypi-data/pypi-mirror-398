# Langchain LLM Config - Examples

This directory contains comprehensive examples demonstrating all features of the langchain-llm-config package.

## 📚 Example Files

### 1. **basic_usage.py** - Getting Started
Basic examples covering:
- Creating assistants with structured output
- Using embeddings
- V2 configuration with model names
- Kunlun API with bearer token authentication
- Simple streaming example

**Run:** `python examples/basic_usage.py`

---

### 2. **structured_output_example.py** - Structured Output
Comprehensive structured output examples:
- Basic structured output with Pydantic models
- Complex nested models
- Lists and enums in response models
- Validation and error handling
- Different providers with structured output
- Async batch processing

**Run:** `python examples/structured_output_example.py`

---

### 3. **streaming_example.py** - Streaming Chat
Streaming chat examples:
- Basic streaming with async iteration
- Streaming with different providers (OpenAI, Kunlun, VLLM)
- Streaming with thinking mode (Kunlun models)
- Streaming with context
- Error handling for streaming

**Run:** `python examples/streaming_example.py`

---

### 4. **raw_text_mode_example.py** - Raw Text Mode
Raw text mode (no structured output) examples:
- Using `auto_apply_parser=False` for raw text output
- When to use raw text mode vs structured output
- Working with raw responses
- Async raw text processing
- Raw text with context

**Run:** `python examples/raw_text_mode_example.py`

---

### 5. **thinking_mode_example.py** - Thinking Mode
Thinking mode examples (Kunlun models):
- Using models with thinking mode enabled (Qwen3-235B, Qwen3-30B)
- Viewing the model's reasoning process
- Streaming with thinking mode
- Structured output with thinking mode
- Complex problem solving with reasoning

**Run:** `python examples/thinking_mode_example.py`

**Note:** Requires Kunlun API credentials

---

### 6. **dynamic_parser_example.py** - Dynamic Parser
Dynamic parser application examples:
- Creating assistants without parser initially
- Applying parser dynamically
- Switching between raw and structured modes
- Different response models for different queries

**Run:** `python examples/dynamic_parser_example.py`

---

### 7. **embeddings_example.py** - Embeddings
Comprehensive embeddings examples:
- Basic text embeddings
- Batch embedding generation
- Semantic similarity calculation
- Different embedding providers (OpenAI, Kunlun, Infinity)
- Async embedding generation
- Use case: Document search

**Run:** `python examples/embeddings_example.py`

---

## 🚀 Quick Start

### Prerequisites

1. Install the package:
```bash
pip install langchain-llm-config
```

2. Initialize configuration:
```bash
llm-config init
```

3. Set up API credentials:
```bash
# OpenAI
export OPENAI_API_KEY="your-api-key"

# Kunlun (optional)
export KUNLUN_BEARER_TOKEN="your-bearer-token"
export KUNLUN_QWEN3_235B_API_BASE="https://your-endpoint/v1"
# ... other Kunlun endpoints
```

### Run Examples

```bash
# Run all basic examples
python examples/basic_usage.py

# Run specific feature examples
python examples/streaming_example.py
python examples/structured_output_example.py
python examples/embeddings_example.py
```

---

## 📖 Feature Matrix

| Feature | Example File | Description |
|---------|-------------|-------------|
| Structured Output | `structured_output_example.py` | Pydantic models for type-safe responses |
| Raw Text Mode | `raw_text_mode_example.py` | Free-form text responses |
| Streaming | `streaming_example.py` | Real-time response streaming |
| Thinking Mode | `thinking_mode_example.py` | View model's reasoning process |
| Dynamic Parser | `dynamic_parser_example.py` | Apply/change parsers at runtime |
| Embeddings | `embeddings_example.py` | Text embeddings and similarity |
| Async/Await | All examples | Asynchronous processing |
| Multiple Providers | All examples | OpenAI, VLLM, Gemini, Kunlun |
| V2 Config | `basic_usage.py` | Model-centric configuration |

---

## 🔧 Configuration

All examples use the configuration from `api.yaml` in your project root. The configuration supports:

- **V2 Format (Recommended):** Model-centric configuration
- **V1 Format (Legacy):** Provider-centric configuration
- **Environment Variables:** For API keys and endpoints

Example `api.yaml`:
```yaml
default:
  chat_provider: gpt-3.5-turbo
  embedding_provider: text-embedding-ada-002

models:
  gpt-3.5-turbo:
    model_type: chat
    provider_type: openai
    model_config:
      model_name: gpt-3.5-turbo
      temperature: 0.7
```

---

## 💡 Tips

1. **Start with `basic_usage.py`** to understand the fundamentals
2. **Use structured output** for type-safe, validated responses
3. **Use raw text mode** for creative writing, code generation, or streaming
4. **Enable thinking mode** for complex reasoning tasks (Kunlun models)
5. **Use async methods** for better performance with multiple requests
6. **Check error handling** examples for production-ready code

---

## 🐛 Troubleshooting

### Common Issues

**Import Error:**
```bash
pip install langchain-llm-config langchain-openai
```

**API Key Not Found:**
```bash
export OPENAI_API_KEY="your-key"
```

**Kunlun Examples Skipped:**
```bash
export KUNLUN_BEARER_TOKEN="your-token"
export KUNLUN_QWEN3_235B_API_BASE="https://your-endpoint/v1"
```

---

## 📝 License

These examples are part of the langchain-llm-config package and follow the same license.

