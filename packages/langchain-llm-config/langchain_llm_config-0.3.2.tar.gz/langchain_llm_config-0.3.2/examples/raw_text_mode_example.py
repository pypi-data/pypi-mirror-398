"""
Raw text mode examples for langchain-llm-config package

This example demonstrates:
1. Using auto_apply_parser=False for raw text output
2. When to use raw text mode vs structured output
3. Working with raw responses
4. Converting between raw and structured modes
"""

import asyncio
from typing import List

from pydantic import BaseModel, Field

from langchain_llm_config import create_assistant


class SimpleResponse(BaseModel):
    """Simple response model for structured output"""

    answer: str = Field(..., description="The answer to the question")


async def basic_raw_text_example():
    """Basic raw text mode example"""
    print("📝 Basic Raw Text Mode")
    print("=" * 60)

    # Create assistant without parser
    assistant = create_assistant(
        provider="openai",
        auto_apply_parser=False,  # Disable structured output
        system_prompt="You are a helpful assistant.",
    )

    print("\n💬 Question: What is 2+2?")
    result = assistant.ask("What is 2+2?")

    print(f"Response type: {type(result)}")
    print(f"Response: {result}")


async def raw_vs_structured_comparison():
    """Compare raw text mode vs structured output"""
    print("\n🔄 Raw Text vs Structured Output Comparison")
    print("=" * 60)

    # Raw text mode
    print("\n1️⃣  Raw Text Mode:")
    assistant_raw = create_assistant(
        provider="openai",
        auto_apply_parser=False,
        system_prompt="You are a helpful assistant.",
    )

    raw_result = assistant_raw.ask("What is the capital of France?")
    print(f"   Type: {type(raw_result)}")
    print(f"   Result: {raw_result}")

    # Structured output mode
    print("\n2️⃣  Structured Output Mode:")
    assistant_structured = create_assistant(
        provider="openai",
        response_model=SimpleResponse,
        system_prompt="You are a helpful assistant.",
    )

    structured_result = assistant_structured.ask("What is the capital of France?")
    print(f"   Type: {type(structured_result)}")
    print(f"   Result: {structured_result}")
    print(f"   Answer field: {structured_result['answer']}")


async def when_to_use_raw_text():
    """Examples of when to use raw text mode"""
    print("\n💡 When to Use Raw Text Mode")
    print("=" * 60)

    assistant = create_assistant(
        provider="openai",
        auto_apply_parser=False,
        system_prompt="You are a creative writing assistant.",
    )

    # Use case 1: Creative writing
    print("\n1️⃣  Creative Writing (free-form output):")
    story = assistant.ask("Write a short haiku about programming")
    print(f"   {story}")

    # Use case 2: Code generation
    print("\n2️⃣  Code Generation (preserve formatting):")
    code = assistant.ask("Write a Python function to calculate fibonacci numbers")
    print(f"   {code}")

    # Use case 3: Streaming (covered in streaming_example.py)
    print("\n3️⃣  Streaming: Use raw text mode for streaming responses")
    print("   (See streaming_example.py for details)")


async def raw_text_with_different_providers():
    """Raw text mode with different providers"""
    print("\n🔌 Raw Text Mode with Different Providers")
    print("=" * 60)

    providers = ["openai"]  # Add more if available: "vllm", "gemini"

    for provider in providers:
        try:
            print(f"\n📍 Provider: {provider}")
            assistant = create_assistant(
                provider=provider,
                auto_apply_parser=False,
                system_prompt="You are a helpful assistant.",
            )

            result = assistant.ask("Say hello in 3 different languages")
            print(f"   Response: {result[:100]}...")

        except Exception as e:
            print(f"   ⚠️  Skipped: {e}")


async def raw_text_async_example():
    """Async raw text mode example"""
    print("\n⚡ Async Raw Text Mode")
    print("=" * 60)

    assistant = create_assistant(
        provider="openai",
        auto_apply_parser=False,
        system_prompt="You are a helpful assistant.",
    )

    print("\n💬 Processing multiple questions asynchronously...")

    questions = [
        "What is Python?",
        "What is JavaScript?",
        "What is Rust?",
    ]

    # Process all questions concurrently
    tasks = [assistant.ask_async(q) for q in questions]
    results = await asyncio.gather(*tasks)

    for question, result in zip(questions, results):
        print(f"\nQ: {question}")
        print(f"A: {result[:80]}...")


async def raw_text_with_context():
    """Raw text mode with context"""
    print("\n📚 Raw Text Mode with Context")
    print("=" * 60)

    assistant = create_assistant(
        provider="openai",
        auto_apply_parser=False,
        system_prompt="You are a technical documentation writer.",
    )

    context = """
    Project: FastAPI Todo Application
    Tech Stack: Python 3.11, FastAPI, PostgreSQL, SQLAlchemy
    Current Status: Basic CRUD operations implemented
    """

    print("\n💬 Question: What should I document next?")
    result = assistant.ask(
        "What should I document next for this project?", context=context
    )
    print(f"Response: {result}")


async def main():
    """Run all raw text mode examples"""
    print("🚀 Langchain LLM Config - Raw Text Mode Examples")
    print("=" * 60)

    await basic_raw_text_example()
    await raw_vs_structured_comparison()
    await when_to_use_raw_text()
    await raw_text_with_different_providers()
    await raw_text_async_example()
    await raw_text_with_context()

    print("\n✅ All raw text mode examples completed!")


if __name__ == "__main__":
    asyncio.run(main())
