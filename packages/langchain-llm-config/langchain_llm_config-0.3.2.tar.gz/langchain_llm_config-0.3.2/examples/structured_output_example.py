"""
Structured output examples for langchain-llm-config package

This example demonstrates:
1. Basic structured output with Pydantic models
2. Complex nested models
3. Lists and enums in response models
4. Validation and error handling
5. Different providers with structured output
"""

import asyncio
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field

from langchain_llm_config import create_assistant


# Simple response model
class SimpleResponse(BaseModel):
    """Simple response with a single field"""

    answer: str = Field(..., description="The answer to the question")


# Complex nested model
class Person(BaseModel):
    """Person information"""

    name: str = Field(..., description="Full name")
    age: int = Field(..., description="Age in years")
    occupation: str = Field(..., description="Current occupation")


class Sentiment(str, Enum):
    """Sentiment classification"""

    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class ArticleAnalysis(BaseModel):
    """Detailed article analysis"""

    title: str = Field(..., description="Suggested title for the article")
    summary: str = Field(..., description="Brief summary (2-3 sentences)")
    key_points: List[str] = Field(..., description="Main points (3-5 items)")
    sentiment: Sentiment = Field(..., description="Overall sentiment")
    word_count: int = Field(..., description="Approximate word count")
    tags: List[str] = Field(..., description="Relevant tags/categories")


class CodeReview(BaseModel):
    """Code review response"""

    overall_quality: int = Field(..., description="Quality score from 1-10")
    strengths: List[str] = Field(..., description="Code strengths")
    issues: List[str] = Field(..., description="Issues found")
    suggestions: List[str] = Field(..., description="Improvement suggestions")
    security_concerns: Optional[List[str]] = Field(
        None, description="Security issues if any"
    )


async def basic_structured_output():
    """Basic structured output example"""
    print("📋 Basic Structured Output")
    print("=" * 60)

    assistant = create_assistant(
        provider="openai",
        response_model=SimpleResponse,
        system_prompt="You are a helpful assistant.",
    )

    print("\n💬 Question: What is the capital of France?")
    result = assistant.ask("What is the capital of France?")

    print(f"\nResult type: {type(result)}")
    print(f"Answer: {result['answer']}")


async def complex_nested_model():
    """Complex nested model example"""
    print("\n🏗️  Complex Nested Model")
    print("=" * 60)

    assistant = create_assistant(
        provider="openai",
        response_model=ArticleAnalysis,
        system_prompt="You are a professional content analyzer.",
    )

    article = """
    Artificial Intelligence has revolutionized numerous industries in recent years.
    From healthcare diagnostics to autonomous vehicles, AI systems are becoming
    increasingly sophisticated. Machine learning algorithms can now process vast
    amounts of data to identify patterns and make predictions with remarkable accuracy.
    However, concerns about privacy, bias, and job displacement remain significant
    challenges that society must address as AI continues to evolve.
    """

    print("\n💬 Analyzing article...")
    result = assistant.ask(f"Analyze this article: {article}")

    print(f"\n📊 Analysis Results:")
    print(f"Title: {result['title']}")
    print(f"Summary: {result['summary']}")
    print(f"Sentiment: {result['sentiment']}")
    print(f"Word Count: {result['word_count']}")
    print(f"\nKey Points:")
    for i, point in enumerate(result["key_points"], 1):
        print(f"  {i}. {point}")
    print(f"\nTags: {', '.join(result['tags'])}")


async def list_and_enum_example():
    """Example with lists and enums"""
    print("\n📝 Lists and Enums in Response Models")
    print("=" * 60)

    assistant = create_assistant(
        provider="openai",
        response_model=CodeReview,
        system_prompt="You are an expert code reviewer.",
    )

    code = """
    def calculate_total(items):
        total = 0
        for item in items:
            total = total + item['price']
        return total
    """

    print("\n💬 Reviewing code...")
    result = assistant.ask(f"Review this Python code:\n{code}")

    print(f"\n📊 Code Review:")
    print(f"Overall Quality: {result['overall_quality']}/10")
    print(f"\nStrengths:")
    for strength in result["strengths"]:
        print(f"  ✅ {strength}")
    print(f"\nIssues:")
    for issue in result["issues"]:
        print(f"  ⚠️  {issue}")
    print(f"\nSuggestions:")
    for suggestion in result["suggestions"]:
        print(f"  💡 {suggestion}")

    if result.get("security_concerns"):
        print(f"\nSecurity Concerns:")
        for concern in result["security_concerns"]:
            print(f"  🔒 {concern}")


async def structured_output_with_validation():
    """Structured output with validation"""
    print("\n✅ Structured Output with Validation")
    print("=" * 60)

    class ValidatedResponse(BaseModel):
        """Response with validation"""

        score: int = Field(..., ge=0, le=100, description="Score between 0-100")
        confidence: float = Field(
            ..., ge=0.0, le=1.0, description="Confidence level 0.0-1.0"
        )
        category: str = Field(..., min_length=1, max_length=50, description="Category")

    assistant = create_assistant(
        provider="openai",
        response_model=ValidatedResponse,
        system_prompt="You are an evaluation assistant.",
    )

    print("\n💬 Question: Rate the quality of this essay (score 0-100)")
    result = assistant.ask(
        "Rate this essay: 'AI is changing the world.' Give a score, confidence, and category."
    )

    print(f"\n📊 Evaluation:")
    print(f"Score: {result['score']}/100")
    print(f"Confidence: {result['confidence']:.2f}")
    print(f"Category: {result['category']}")


async def structured_output_different_providers():
    """Structured output with different providers"""
    print("\n🔌 Structured Output with Different Providers")
    print("=" * 60)

    providers = ["openai"]  # Add more if available

    for provider in providers:
        try:
            print(f"\n📍 Provider: {provider}")
            assistant = create_assistant(
                provider=provider,
                response_model=SimpleResponse,
                system_prompt="You are a helpful assistant.",
            )

            result = assistant.ask("What is 2+2?")
            print(f"   Answer: {result['answer']}")

        except Exception as e:
            print(f"   ⚠️  Skipped: {e}")


async def async_batch_processing():
    """Async batch processing with structured output"""
    print("\n⚡ Async Batch Processing")
    print("=" * 60)

    assistant = create_assistant(
        provider="openai",
        response_model=SimpleResponse,
        system_prompt="You are a helpful assistant.",
    )

    questions = [
        "What is Python?",
        "What is JavaScript?",
        "What is Rust?",
        "What is Go?",
    ]

    print("\n💬 Processing 4 questions concurrently...")

    # Process all questions concurrently
    tasks = [assistant.ask_async(q) for q in questions]
    results = await asyncio.gather(*tasks)

    print("\n📊 Results:")
    for question, result in zip(questions, results):
        print(f"\nQ: {question}")
        print(f"A: {result['answer'][:80]}...")


async def main():
    """Run all structured output examples"""
    print("🚀 Langchain LLM Config - Structured Output Examples")
    print("=" * 60)

    await basic_structured_output()
    await complex_nested_model()
    await list_and_enum_example()
    await structured_output_with_validation()
    await structured_output_different_providers()
    await async_batch_processing()

    print("\n✅ All structured output examples completed!")


if __name__ == "__main__":
    asyncio.run(main())
