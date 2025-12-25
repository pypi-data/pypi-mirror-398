# Synchronous and Asynchronous Usage

The `langchain-llm-config` package supports both synchronous and asynchronous usage patterns. This document explains how to use each approach.

## Overview

All assistant and embedding provider classes provide both synchronous and asynchronous methods:

- **Synchronous methods**: `ask()`, `embed_texts()`
- **Asynchronous methods**: `ask_async()`, `embed_texts_async()`

## Chat Assistant Usage

### Synchronous Usage

```python
from langchain_llm_config import create_assistant
from pydantic import BaseModel, Field

class ChatResponse(BaseModel):
    message: str = Field(..., description="The assistant's response")
    confidence: float = Field(..., description="Confidence score")

# Create assistant
assistant = create_assistant(
    response_model=ChatResponse,
    provider="openai",
    system_prompt="You are a helpful assistant."
)

# Synchronous call
response = assistant.ask("What is the capital of France?")
print(response['message'])
```

### Asynchronous Usage

```python
import asyncio
from langchain_llm_config import create_assistant
from pydantic import BaseModel, Field

class ChatResponse(BaseModel):
    message: str = Field(..., description="The assistant's response")
    confidence: float = Field(..., description="Confidence score")

async def main():
    # Create assistant
    assistant = create_assistant(
        response_model=ChatResponse,
        provider="openai",
        system_prompt="You are a helpful assistant."
    )
    
    # Asynchronous call
    response = await assistant.ask_async("What is the capital of France?")
    print(response['message'])

# Run the async function
asyncio.run(main())
```

## Embedding Provider Usage

### Synchronous Usage

```python
from langchain_llm_config import create_embedding_provider

# Create embedding provider
provider = create_embedding_provider(provider="openai")

# Synchronous embedding
texts = ["Hello world", "Machine learning is amazing"]
embeddings = provider.embed_texts(texts)
print(f"Generated {len(embeddings)} embeddings")
```

### Asynchronous Usage

```python
import asyncio
from langchain_llm_config import create_embedding_provider

async def main():
    # Create embedding provider
    provider = create_embedding_provider(provider="openai")
    
    # Asynchronous embedding
    texts = ["Hello world", "Machine learning is amazing"]
    embeddings = await provider.embed_texts_async(texts)
    print(f"Generated {len(embeddings)} embeddings")

# Run the async function
asyncio.run(main())
```

## Batch Processing

### Synchronous Batch Processing

```python
from langchain_llm_config import create_assistant, create_embedding_provider

# Batch processing with assistants
assistant = create_assistant(response_model=ChatResponse, provider="openai")
questions = ["What is AI?", "What is ML?", "What is NLP?"]

responses = []
for question in questions:
    response = assistant.ask(question)
    responses.append(response)

# Batch processing with embeddings
provider = create_embedding_provider(provider="openai")
texts = ["Text 1", "Text 2", "Text 3"]
embeddings = provider.embed_texts(texts)
```

### Asynchronous Batch Processing

```python
import asyncio
from langchain_llm_config import create_assistant, create_embedding_provider

async def main():
    # Batch processing with assistants
    assistant = create_assistant(response_model=ChatResponse, provider="openai")
    questions = ["What is AI?", "What is ML?", "What is NLP?"]
    
    # Process all questions concurrently
    tasks = [assistant.ask_async(question) for question in questions]
    responses = await asyncio.gather(*tasks)
    
    # Batch processing with embeddings
    provider = create_embedding_provider(provider="openai")
    texts = ["Text 1", "Text 2", "Text 3"]
    embeddings = await provider.embed_texts_async(texts)

asyncio.run(main())
```

## Error Handling

### Synchronous Error Handling

```python
try:
    response = assistant.ask("Your question here")
    print(response['message'])
except Exception as e:
    print(f"Error: {e}")
```

### Asynchronous Error Handling

```python
async def main():
    try:
        response = await assistant.ask_async("Your question here")
        print(response['message'])
    except Exception as e:
        print(f"Error: {e}")

asyncio.run(main())
```

## Performance Considerations

### When to Use Synchronous

- Simple scripts and utilities
- Sequential processing
- When you don't need to handle multiple requests concurrently
- Easier to understand and debug

### When to Use Asynchronous

- Web applications and APIs
- Batch processing of multiple requests
- When you need to handle multiple requests concurrently
- Better performance for I/O-bound operations

## Example: Mixed Usage

```python
import asyncio
from langchain_llm_config import create_assistant, create_embedding_provider

def sync_function():
    """Synchronous function"""
    assistant = create_assistant(response_model=ChatResponse, provider="openai")
    return assistant.ask("What is Python?")

async def async_function():
    """Asynchronous function"""
    assistant = create_assistant(response_model=ChatResponse, provider="openai")
    return await assistant.ask_async("What is JavaScript?")

async def main():
    # Run synchronous function in thread pool
    sync_result = await asyncio.get_event_loop().run_in_executor(None, sync_function)
    
    # Run asynchronous function
    async_result = await async_function()
    
    print(f"Sync result: {sync_result['message']}")
    print(f"Async result: {async_result['message']}")

# Run the mixed example
asyncio.run(main())
```

## Migration Guide

### From Async to Sync

If you have existing async code and want to use sync:

```python
# Old async code
response = await assistant.ask("question")

# New sync code
response = assistant.ask("question")
```

### From Sync to Async

If you have existing sync code and want to use async:

```python
# Old sync code
response = assistant.ask("question")

# New async code
response = await assistant.ask_async("question")
```

## Best Practices

1. **Choose the right approach**: Use sync for simple scripts, async for concurrent operations
2. **Be consistent**: Stick to one approach within a single function or class
3. **Handle errors**: Always wrap calls in try-catch blocks
4. **Use batch processing**: For multiple requests, consider using async with `asyncio.gather()`
5. **Monitor performance**: Async can be faster for I/O-bound operations but adds complexity

## Troubleshooting

### Common Issues

1. **Forgetting await**: Make sure to use `await` with async methods
2. **Mixing sync/async**: Don't call async methods without await in sync contexts
3. **Event loop issues**: Make sure you're running async code in an event loop

### Debug Tips

1. Use `asyncio.run()` to run async code from sync contexts
2. Use `asyncio.get_event_loop().run_in_executor()` to run sync code from async contexts
3. Check that all async calls are properly awaited
4. Use proper error handling for both sync and async operations 