"""
Thinking mode examples for langchain-llm-config package

This example demonstrates:
1. Using models with thinking mode enabled (Kunlun Qwen3-235B, Qwen3-30B)
2. Viewing the model's reasoning process
3. Streaming with thinking mode
4. Structured output with thinking mode
"""

import asyncio
import os

from pydantic import BaseModel, Field

from langchain_llm_config import create_assistant


class MathSolution(BaseModel):
    """Math solution response model"""

    answer: str = Field(..., description="The final answer")
    steps: list[str] = Field(..., description="Step-by-step solution")


class Analysis(BaseModel):
    """Analysis response model"""

    summary: str = Field(..., description="Brief summary")
    key_points: list[str] = Field(..., description="Key points identified")
    conclusion: str = Field(..., description="Final conclusion")


async def basic_thinking_mode_example():
    """Basic thinking mode example with Kunlun"""
    print("🧠 Basic Thinking Mode Example")
    print("=" * 60)

    if not os.getenv("KUNLUN_BEARER_TOKEN"):
        print("⚠️  Skipped: KUNLUN_BEARER_TOKEN not set")
        return

    try:
        # Create assistant with thinking mode enabled
        # Note: enable_thinking is set in the config file for kunlun-qwen3-235b
        assistant = create_assistant(
            model="kunlun-qwen3-235b",
            response_model=MathSolution,
            system_prompt="You are a math tutor. Show your reasoning step by step.",
        )

        print("\n💬 Question: Solve 127 * 43")
        result = assistant.ask("Solve this multiplication: 127 * 43")

        print(f"\n📊 Result:")
        print(f"Answer: {result['answer']}")
        print(f"Steps:")
        for i, step in enumerate(result["steps"], 1):
            print(f"  {i}. {step}")

        print(
            "\nℹ️  Note: The model's internal reasoning (<think> tags) is processed separately"
        )

    except Exception as e:
        print(f"⚠️  Error: {e}")


async def thinking_mode_streaming():
    """Streaming with thinking mode to see reasoning in real-time"""
    print("\n🌊 Thinking Mode with Streaming")
    print("=" * 60)

    if not os.getenv("KUNLUN_BEARER_TOKEN"):
        print("⚠️  Skipped: KUNLUN_BEARER_TOKEN not set")
        return

    try:
        # For streaming, use raw text mode to see the <think> tags
        assistant = create_assistant(
            model="kunlun-qwen3-235b",
            auto_apply_parser=False,
            system_prompt="You are a logical reasoning assistant.",
        )

        print("\n💬 Question: Is it better to exercise in the morning or evening?")
        print("Response (with thinking process):\n")

        async for chunk in assistant.chat_async(
            "Is it better to exercise in the morning or evening? Explain your reasoning."
        ):
            print(chunk, end="", flush=True)

        print("\n")
        print(
            "ℹ️  Note: The <think>...</think> section shows the model's reasoning process"
        )

    except Exception as e:
        print(f"\n⚠️  Error: {e}")


async def thinking_mode_complex_problem():
    """Using thinking mode for complex problem solving"""
    print("\n🎯 Thinking Mode for Complex Problems")
    print("=" * 60)

    if not os.getenv("KUNLUN_BEARER_TOKEN"):
        print("⚠️  Skipped: KUNLUN_BEARER_TOKEN not set")
        return

    try:
        assistant = create_assistant(
            model="kunlun-qwen3-235b",
            response_model=Analysis,
            system_prompt="You are an analytical assistant. Think through problems carefully.",
        )

        problem = """
        A company has 3 options for cloud hosting:
        - Option A: $100/month, unlimited bandwidth, 99.9% uptime
        - Option B: $150/month, unlimited bandwidth, 99.99% uptime, 24/7 support
        - Option C: $80/month, 1TB bandwidth, 99.5% uptime
        
        The company processes critical financial transactions and expects 500GB monthly traffic.
        Which option should they choose?
        """

        print("\n💬 Problem:")
        print(problem)
        print("\n📊 Analysis:")

        result = assistant.ask(f"Analyze this decision: {problem}")

        print(f"\nSummary: {result['summary']}")
        print(f"\nKey Points:")
        for point in result["key_points"]:
            print(f"  • {point}")
        print(f"\nConclusion: {result['conclusion']}")

    except Exception as e:
        print(f"⚠️  Error: {e}")


async def thinking_mode_qwen3_30b():
    """Using thinking mode with Qwen3-30B model"""
    print("\n🔬 Thinking Mode with Qwen3-30B")
    print("=" * 60)

    if not os.getenv("KUNLUN_BEARER_TOKEN"):
        print("⚠️  Skipped: KUNLUN_BEARER_TOKEN not set")
        return

    try:
        # Qwen3-30B also supports thinking mode
        assistant = create_assistant(
            model="kunlun-qwen3-30b",
            auto_apply_parser=False,
            system_prompt="You are a helpful assistant.",
        )

        print("\n💬 Question: Count from 1 to 5")
        print("Response:\n")

        async for chunk in assistant.chat_async("Count from 1 to 5"):
            print(chunk, end="", flush=True)

        print("\n")

    except Exception as e:
        print(f"\n⚠️  Error: {e}")


async def comparing_with_without_thinking():
    """Compare responses with and without thinking mode"""
    print("\n⚖️  Comparing With/Without Thinking Mode")
    print("=" * 60)

    if not os.getenv("KUNLUN_BEARER_TOKEN"):
        print("⚠️  Skipped: KUNLUN_BEARER_TOKEN not set")
        return

    try:
        question = "What is 15 * 23?"

        # With thinking mode (Qwen3-235B)
        print("\n1️⃣  With Thinking Mode (kunlun-qwen3-235b):")
        assistant_thinking = create_assistant(
            model="kunlun-qwen3-235b",
            auto_apply_parser=False,
            system_prompt="You are a helpful assistant.",
        )
        result_thinking = assistant_thinking.ask(question)
        print(f"   {result_thinking[:150]}...")

        # Without thinking mode (Qwen3-32B)
        print("\n2️⃣  Without Thinking Mode (kunlun-qwen3-32b):")
        assistant_no_thinking = create_assistant(
            model="kunlun-qwen3-32b",
            auto_apply_parser=False,
            system_prompt="You are a helpful assistant.",
        )
        result_no_thinking = assistant_no_thinking.ask(question)
        print(f"   {result_no_thinking}")

    except Exception as e:
        print(f"⚠️  Error: {e}")


async def main():
    """Run all thinking mode examples"""
    print("🚀 Langchain LLM Config - Thinking Mode Examples")
    print("=" * 60)
    print("\nℹ️  Thinking mode is available for:")
    print("  • kunlun-qwen3-235b (Qwen3-235B-A22B)")
    print("  • kunlun-qwen3-30b (Qwen3-30B-A3B)")
    print("=" * 60)

    await basic_thinking_mode_example()
    await thinking_mode_streaming()
    await thinking_mode_complex_problem()
    await thinking_mode_qwen3_30b()
    await comparing_with_without_thinking()

    print("\n✅ All thinking mode examples completed!")


if __name__ == "__main__":
    asyncio.run(main())
