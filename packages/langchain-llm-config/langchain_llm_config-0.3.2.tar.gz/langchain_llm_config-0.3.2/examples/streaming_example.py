"""
Streaming chat examples for langchain-llm-config package

This example demonstrates:
1. Basic streaming with async iteration
2. Streaming with different providers (OpenAI, Kunlun, VLLM)
3. Streaming with thinking mode (Kunlun models)
4. Handling streaming errors
"""

import asyncio
import os

from langchain_llm_config import create_assistant


async def basic_streaming_example():
    """Basic streaming example with OpenAI"""
    print("🌊 Basic Streaming Example")
    print("=" * 60)

    # Create assistant without parser for streaming
    assistant = create_assistant(
        provider="openai",
        auto_apply_parser=False,  # Required for streaming
        system_prompt="You are a helpful assistant that provides clear explanations.",
    )

    print("\n💬 Question: Explain how neural networks work in simple terms")
    print("Response: ", end="", flush=True)

    # Stream the response
    async for chunk in assistant.chat_async(
        "Explain how neural networks work in simple terms"
    ):
        print(chunk, end="", flush=True)

    print("\n")


async def streaming_with_model_name():
    """Streaming with V2 config using model name"""
    print("\n🎯 Streaming with Model Name (V2 Config)")
    print("=" * 60)

    assistant = create_assistant(
        model="gpt-3.5-turbo",  # Use model name from config
        auto_apply_parser=False,
        system_prompt="You are a concise assistant.",
    )

    print("\n💬 Question: What are the benefits of renewable energy?")
    print("Response: ", end="", flush=True)

    async for chunk in assistant.chat_async(
        "What are the benefits of renewable energy? List 3 key points."
    ):
        print(chunk, end="", flush=True)

    print("\n")


async def kunlun_streaming_with_thinking():
    """Streaming with Kunlun model that has thinking mode enabled"""
    print("\n🔐 Kunlun Streaming with Thinking Mode")
    print("=" * 60)

    # Check if Kunlun credentials are available
    if not os.getenv("KUNLUN_BEARER_TOKEN"):
        print("⚠️  Skipped: KUNLUN_BEARER_TOKEN not set")
        return

    try:
        # Use Kunlun model with thinking mode enabled
        assistant = create_assistant(
            model="kunlun-qwen3-235b",  # Has enable_thinking: true in config
            auto_apply_parser=False,
            system_prompt="You are a helpful assistant.",
        )

        print("\n💬 Question: Solve this math problem: What is 127 * 43?")
        print("Response: ", end="", flush=True)

        # The response will include <think> tags showing reasoning
        async for chunk in assistant.chat_async(
            "Solve this math problem: What is 127 * 43?"
        ):
            print(chunk, end="", flush=True)

        print("\n")
        print("ℹ️  Note: The <think> tags show the model's reasoning process")

    except Exception as e:
        print(f"\n⚠️  Error: {e}")


async def streaming_with_context():
    """Streaming with additional context"""
    print("\n📚 Streaming with Context")
    print("=" * 60)

    assistant = create_assistant(
        provider="openai",
        auto_apply_parser=False,
        system_prompt="You are a helpful coding assistant.",
    )

    context = """
    The user is working on a Python project that uses FastAPI.
    They are building a REST API for a todo application.
    """

    print("\n💬 Question: How should I structure my project?")
    print("Response: ", end="", flush=True)

    async for chunk in assistant.chat_async(
        "How should I structure my project?", context=context
    ):
        print(chunk, end="", flush=True)

    print("\n")


async def streaming_error_handling():
    """Example of handling streaming errors"""
    print("\n⚠️  Streaming Error Handling")
    print("=" * 60)

    assistant = create_assistant(
        provider="openai",
        auto_apply_parser=False,
        system_prompt="You are a helpful assistant.",
    )

    try:
        print("\n💬 Streaming with error handling...")
        print("Response: ", end="", flush=True)

        async for chunk in assistant.chat_async("Tell me about Python"):
            print(chunk, end="", flush=True)

        print("\n✅ Streaming completed successfully")

    except Exception as e:
        print(f"\n❌ Error during streaming: {e}")
        print("💡 Tip: Check your API credentials and network connection")


async def main():
    """Run all streaming examples"""
    print("🚀 Langchain LLM Config - Streaming Examples")
    print("=" * 60)

    await basic_streaming_example()
    await streaming_with_model_name()
    await kunlun_streaming_with_thinking()
    await streaming_with_context()
    await streaming_error_handling()

    print("\n✅ All streaming examples completed!")


if __name__ == "__main__":
    asyncio.run(main())
