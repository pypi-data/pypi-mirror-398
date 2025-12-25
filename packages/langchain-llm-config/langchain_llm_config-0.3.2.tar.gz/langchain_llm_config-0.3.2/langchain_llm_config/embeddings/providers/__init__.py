"""
嵌入提供者实现
"""

from typing import TYPE_CHECKING

# Optional imports with proper typing - all providers are now optional
if TYPE_CHECKING:
    from .gemini import GeminiEmbeddingProvider
    from .infinity import InfinityEmbeddingProvider
    from .kunlun import KunlunEmbeddingProvider
    from .openai import OpenAIEmbeddingProvider
    from .vllm import VLLMEmbeddingProvider
else:
    try:
        from .openai import OpenAIEmbeddingProvider
    except ImportError:
        OpenAIEmbeddingProvider = None  # type: ignore[misc,assignment]

    try:
        from .vllm import VLLMEmbeddingProvider
    except ImportError:
        VLLMEmbeddingProvider = None  # type: ignore[misc,assignment]

    try:
        from .gemini import GeminiEmbeddingProvider
    except ImportError:
        GeminiEmbeddingProvider = None  # type: ignore[misc,assignment]

    try:
        from .infinity import InfinityEmbeddingProvider
    except ImportError:
        InfinityEmbeddingProvider = None  # type: ignore[misc,assignment]

    try:
        from .kunlun import KunlunEmbeddingProvider
    except ImportError:
        KunlunEmbeddingProvider = None  # type: ignore[misc,assignment]

# Build __all__ list dynamically
__all__ = []

if OpenAIEmbeddingProvider is not None:
    __all__.append("OpenAIEmbeddingProvider")
if VLLMEmbeddingProvider is not None:
    __all__.append("VLLMEmbeddingProvider")
if GeminiEmbeddingProvider is not None:
    __all__.append("GeminiEmbeddingProvider")
if InfinityEmbeddingProvider is not None:
    __all__.append("InfinityEmbeddingProvider")
if KunlunEmbeddingProvider is not None:
    __all__.append("KunlunEmbeddingProvider")
