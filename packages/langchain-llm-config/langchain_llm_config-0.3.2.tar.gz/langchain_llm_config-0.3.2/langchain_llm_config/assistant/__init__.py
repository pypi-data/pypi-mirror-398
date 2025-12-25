"""
AI 助手模块
"""

from .base import Assistant
from .multimodal import create_image_content, create_multimodal_query

# Optional imports - all providers are now optional
try:
    from .providers.openai import OpenAIAssistant
except ImportError:
    OpenAIAssistant = None  # type: ignore[misc,assignment]

try:
    from .providers.vllm import VLLMAssistant
except ImportError:
    VLLMAssistant = None  # type: ignore[misc,assignment]

try:
    from .providers.gemini import GeminiAssistant
except ImportError:
    GeminiAssistant = None  # type: ignore[misc,assignment]

__all__ = [
    "Assistant",
    "create_image_content",
    "create_multimodal_query",
]

if OpenAIAssistant is not None:
    __all__.append("OpenAIAssistant")
if VLLMAssistant is not None:
    __all__.append("VLLMAssistant")
if GeminiAssistant is not None:
    __all__.append("GeminiAssistant")
