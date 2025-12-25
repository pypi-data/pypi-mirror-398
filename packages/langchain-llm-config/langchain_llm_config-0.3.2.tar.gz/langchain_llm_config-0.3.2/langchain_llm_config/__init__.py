"""
Langchain LLM Config - A comprehensive LLM configuration package

This package provides a unified interface for working with multiple LLM providers
including OpenAI, VLLM, Gemini, and Infinity for both chat assistants and embeddings.
"""

import os
from pathlib import Path
from typing import TYPE_CHECKING, Any

# Import base classes for extensibility
from .assistant.base import Assistant
from .assistant.multimodal import create_image_content, create_multimodal_query

# Import configuration functions
from .config import (
    get_default_config_path,
    init_config,
    load_config,
)
from .embeddings.base import BaseEmbeddingProvider


def _safe_import(module_path: str, class_name: str) -> Any:
    """Safely import a class, returning None if import fails."""
    try:
        module = __import__(module_path, fromlist=[class_name])
        return getattr(module, class_name)
    except ImportError:
        return None


# Optional imports - only available if dependencies are installed
if TYPE_CHECKING:
    from .assistant.providers.gemini import GeminiAssistant
    from .assistant.providers.openai import OpenAIAssistant
    from .assistant.providers.vllm import VLLMAssistant
    from .embeddings.providers.infinity import InfinityEmbeddingProvider
    from .embeddings.providers.openai import OpenAIEmbeddingProvider
    from .embeddings.providers.vllm import VLLMEmbeddingProvider
else:
    # Import providers using helper function to reduce complexity
    OpenAIAssistant = _safe_import(
        "langchain_llm_config.assistant.providers.openai", "OpenAIAssistant"
    )
    OpenAIEmbeddingProvider = _safe_import(
        "langchain_llm_config.embeddings.providers.openai", "OpenAIEmbeddingProvider"
    )
    VLLMAssistant = _safe_import(
        "langchain_llm_config.assistant.providers.vllm", "VLLMAssistant"
    )
    VLLMEmbeddingProvider = _safe_import(
        "langchain_llm_config.embeddings.providers.vllm", "VLLMEmbeddingProvider"
    )
    GeminiAssistant = _safe_import(
        "langchain_llm_config.assistant.providers.gemini", "GeminiAssistant"
    )
    InfinityEmbeddingProvider = _safe_import(
        "langchain_llm_config.embeddings.providers.infinity",
        "InfinityEmbeddingProvider",
    )

# Import main factory functions
from .factory import (  # noqa: E402
    create_assistant,
    create_embedding_provider,
)

# Get version from package metadata
try:
    from importlib.metadata import version

    __version__ = version("langchain-llm-config")
except ImportError:
    # Fallback for Python < 3.8
    __version__ = "0.3.2"
__author__ = "Xingbang Liu"
__email__ = "xingbangliu48@gmail.com"

# Define the tiktoken cache directory path
TIKTOKEN_CACHE_DIR = str(Path(__file__).parent / ".tiktoken_cache")

# Build __all__ list dynamically based on available imports
__all__ = [
    # Constants
    "TIKTOKEN_CACHE_DIR",
    # Factory functions
    "create_assistant",
    "create_embedding_provider",
    # Configuration functions
    "load_config",
    "init_config",
    "get_default_config_path",
    # Base classes
    "Assistant",
    "BaseEmbeddingProvider",
    # Multimodal helper functions
    "create_image_content",
    "create_multimodal_query",
]

# Add optional providers if available
if OpenAIAssistant is not None:
    __all__.append("OpenAIAssistant")
if VLLMAssistant is not None:
    __all__.append("VLLMAssistant")
if GeminiAssistant is not None:
    __all__.append("GeminiAssistant")
if OpenAIEmbeddingProvider is not None:
    __all__.append("OpenAIEmbeddingProvider")
if VLLMEmbeddingProvider is not None:
    __all__.append("VLLMEmbeddingProvider")
if InfinityEmbeddingProvider is not None:
    __all__.append("InfinityEmbeddingProvider")
