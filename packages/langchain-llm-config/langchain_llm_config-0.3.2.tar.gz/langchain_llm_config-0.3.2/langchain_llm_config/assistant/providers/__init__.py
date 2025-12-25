"""
助手提供者实现
"""

# Optional imports - all providers are now optional
try:
    from .openai import OpenAIAssistant
except ImportError:
    OpenAIAssistant = None  # type: ignore[misc,assignment]

try:
    from .vllm import VLLMAssistant
except ImportError:
    VLLMAssistant = None  # type: ignore[misc,assignment]

try:
    from .gemini import GeminiAssistant
except ImportError:
    GeminiAssistant = None  # type: ignore[misc,assignment]

try:
    from .kunlun import KunlunAssistant
except ImportError:
    KunlunAssistant = None  # type: ignore[misc,assignment]

__all__ = []

if OpenAIAssistant is not None:
    __all__.append("OpenAIAssistant")
if VLLMAssistant is not None:
    __all__.append("VLLMAssistant")
if GeminiAssistant is not None:
    __all__.append("GeminiAssistant")
if KunlunAssistant is not None:
    __all__.append("KunlunAssistant")
