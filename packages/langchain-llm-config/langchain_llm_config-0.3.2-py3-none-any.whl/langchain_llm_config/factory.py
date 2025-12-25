from typing import TYPE_CHECKING, Any, Dict, Optional, Type, Union

from pydantic import BaseModel

from .config import load_config
from .config_utils import get_model_config, get_provider_type
from .embeddings.base import BaseEmbeddingProvider


def _safe_import(module_path: str, class_name: str) -> Any:
    """Safely import a class, returning None if import fails."""
    try:
        module = __import__(module_path, fromlist=[class_name])
        return getattr(module, class_name)
    except ImportError:
        return None


def _get_provider_class(provider: str) -> Any:
    """Get the provider class for the given provider name."""
    if provider in _ASSISTANT_PROVIDERS:
        return _ASSISTANT_PROVIDERS[provider]

    # Check for missing providers and raise appropriate errors
    provider_errors = {
        "openai": ("OpenAI", OpenAIAssistant, "openai"),
        "vllm": ("VLLM", VLLMAssistant, "vllm"),
        "gemini": ("Gemini", GeminiAssistant, "gemini"),
        "kunlun": ("Kunlun", KunlunAssistant, "kunlun"),
    }

    if provider in provider_errors:
        name, provider_class, install_name = provider_errors[provider]
        if provider_class is None:
            raise ImportError(
                f"{name} provider is not available. "
                f"Install with: pip install langchain-llm-config[{install_name}]"
            )
        return provider_class

    # For custom providers, use OpenAI-compatible class
    if OpenAIAssistant is None:
        raise ImportError(
            "OpenAI provider is required for custom providers but not available. "
            "Install with: pip install langchain-llm-config[openai]"
        )
    return OpenAIAssistant


def _validate_assistant_config(config: Dict[str, Any], provider: str) -> Any:
    """Validate and extract provider configuration (v1 format)."""
    if provider not in config:
        raise ValueError(f"配置中未找到提供者: {provider}")

    if "chat" not in config[provider]:
        raise ValueError(f"提供者 {provider} 的配置中缺少 'chat' 部分")

    return config[provider]["chat"]


def _resolve_model_config(
    config: Dict[str, Any], model: Optional[str], model_type: str
) -> tuple[str, str, Dict[str, Any]]:
    """
    Resolve model configuration from v2 config format

    Args:
        config: Configuration dictionary (v2 format)
        model: Model name (if None, use default)
        model_type: Type of model ("chat" or "embedding")

    Returns:
        Tuple of (model_name, provider_type, model_config)
    """
    # Get model name from default if not specified
    if model is None:
        default_key = f"{model_type}_provider"
        if "default" not in config or default_key not in config["default"]:
            raise ValueError(
                f"No model specified and no default {model_type}_provider in config"
            )
        model = config["default"][default_key]

    # At this point model is guaranteed to be a string
    assert model is not None

    # Get model configuration
    model_config_obj = get_model_config(config, model)
    provider_type = get_provider_type(config, model)

    # Extract the actual model_config dict
    if "model_config" not in model_config_obj:
        raise ValueError(f"Model '{model}' missing 'model_config' section")

    return model, provider_type, model_config_obj["model_config"]


# Optional imports with proper typing
if TYPE_CHECKING:
    from .assistant.providers.gemini import GeminiAssistant
    from .assistant.providers.kunlun import KunlunAssistant
    from .assistant.providers.openai import OpenAIAssistant
    from .assistant.providers.vllm import VLLMAssistant
    from .embeddings.providers.gemini import GeminiEmbeddingProvider
    from .embeddings.providers.infinity import InfinityEmbeddingProvider
    from .embeddings.providers.kunlun import KunlunEmbeddingProvider
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
    GeminiEmbeddingProvider = _safe_import(
        "langchain_llm_config.embeddings.providers.gemini", "GeminiEmbeddingProvider"
    )
    InfinityEmbeddingProvider = _safe_import(
        "langchain_llm_config.embeddings.providers.infinity",
        "InfinityEmbeddingProvider",
    )
    KunlunAssistant = _safe_import(
        "langchain_llm_config.assistant.providers.kunlun", "KunlunAssistant"
    )
    KunlunEmbeddingProvider = _safe_import(
        "langchain_llm_config.embeddings.providers.kunlun", "KunlunEmbeddingProvider"
    )

# Build provider mappings dynamically based on available imports
_ASSISTANT_PROVIDERS: Dict[str, Any] = {}

if OpenAIAssistant is not None:
    _ASSISTANT_PROVIDERS["openai"] = OpenAIAssistant
if VLLMAssistant is not None:
    _ASSISTANT_PROVIDERS["vllm"] = VLLMAssistant
if GeminiAssistant is not None:
    _ASSISTANT_PROVIDERS["gemini"] = GeminiAssistant
if KunlunAssistant is not None:
    _ASSISTANT_PROVIDERS["kunlun"] = KunlunAssistant

# Build embedding provider mappings
_EMBEDDING_PROVIDERS: Dict[str, Any] = {}

if OpenAIEmbeddingProvider is not None:
    _EMBEDDING_PROVIDERS["openai"] = OpenAIEmbeddingProvider
if VLLMEmbeddingProvider is not None:
    _EMBEDDING_PROVIDERS["vllm"] = VLLMEmbeddingProvider
if InfinityEmbeddingProvider is not None:
    _EMBEDDING_PROVIDERS["infinity"] = InfinityEmbeddingProvider
if GeminiEmbeddingProvider is not None:
    _EMBEDDING_PROVIDERS["gemini"] = GeminiEmbeddingProvider
if KunlunEmbeddingProvider is not None:
    _EMBEDDING_PROVIDERS["kunlun"] = KunlunEmbeddingProvider

# Type alias for concrete embedding providers (build dynamically)
EmbeddingProviderType = Union[
    OpenAIEmbeddingProvider,
    VLLMEmbeddingProvider,
]


def create_assistant(
    response_model: Optional[Type[BaseModel]] = None,
    model: Optional[str] = None,
    provider: Optional[str] = None,
    system_prompt: Optional[str] = None,
    config_path: Optional[str] = None,
    auto_apply_parser: bool = True,
    reasoning: Optional[Dict[str, Any]] = None,
    output_version: str = "responses/v1",
    **kwargs: Any,
) -> Any:
    """
    创建助手实例

    Args:
        response_model: 响应模型类（当auto_apply_parser=False时可选）
        model: 模型名称（v2格式，推荐使用）
        provider: [已弃用] 提供者名称（v1格式，向后兼容）
        system_prompt: 系统提示
        config_path: 配置文件路径
        auto_apply_parser: 是否自动应用解析器（默认True，保持向后兼容）
        reasoning: OpenAI推理参数，用于o系列模型（o1, o3, o4-mini等）
        output_version: 输出版本格式，推荐使用"responses/v1"
        **kwargs: 额外参数

    Returns:
        配置好的助手实例

    Raises:
        ValueError: 当auto_apply_parser=True但未提供response_model时
    """
    # Validate parameters
    if auto_apply_parser and response_model is None:
        raise ValueError(
            "response_model is required when auto_apply_parser=True. "
            "Either provide a response_model or set auto_apply_parser=False "
            "for raw text output."
        )

    config = load_config(config_path)

    # Check if config is v2 format (has 'models' key)
    is_v2_config = "models" in config

    # Determine which parameter to use
    if model is not None and provider is not None:
        raise ValueError(
            "Cannot specify both 'model' and 'provider'. "
            "Use 'model' for v2 configs or 'provider' for v1 configs."
        )

    if is_v2_config:
        # V2 config format - use model name
        model_name, provider_type, provider_config = _resolve_model_config(
            config, model, "chat"
        )
        provider_class = _get_provider_class(provider_type)
    else:
        # V1 config format - use provider name (backward compatibility)
        if provider is None:
            provider = config["default"]["chat_provider"]

        # At this point provider is guaranteed to be a string
        assert provider is not None  # Help type checker
        provider_config = _validate_assistant_config(config, provider)
        provider_class = _get_provider_class(provider)
        provider_type = provider

    # 根据不同的提供者类型，传递不同的参数
    if provider_type == "openai" or (
        provider_class == OpenAIAssistant and OpenAIAssistant is not None
    ):
        # 对于OpenAI和自定义OpenAI兼容提供者，直接传递各个参数
        return provider_class(
            model_name=provider_config["model_name"],
            response_model=response_model,
            temperature=provider_config.get("temperature", 0.7),
            max_tokens=provider_config.get("max_tokens", 2000),
            base_url=provider_config.get("api_base"),
            api_key=provider_config.get("api_key"),
            top_p=provider_config.get("top_p", 1.0),
            read_timeout=provider_config.get("read_timeout"),
            connect_timeout=provider_config.get("connect_timeout"),
            model_kwargs=provider_config.get("model_kwargs", {}),
            extra_body=provider_config.get("extra_body"),
            system_prompt=system_prompt,
            auto_apply_parser=auto_apply_parser,
            reasoning=reasoning,
            output_version=output_version,
            **kwargs,
        )
    elif provider_type == "gemini" and GeminiAssistant is not None:
        # 对于Gemini，传递config对象
        return provider_class(
            config=provider_config,
            response_model=response_model,
            system_prompt=system_prompt,
            auto_apply_parser=auto_apply_parser,
            **kwargs,
        )
    else:
        # 对于其他提供者如VLLM，传递config对象
        return provider_class(
            config=provider_config,
            response_model=response_model,
            system_prompt=system_prompt,
            auto_apply_parser=auto_apply_parser,
            **kwargs,
        )


def create_embedding_provider(
    model: Optional[str] = None,
    provider: Optional[str] = None,
    config_path: Optional[str] = None,
    **kwargs: Any,
) -> BaseEmbeddingProvider:
    """
    创建嵌入提供者实例

    Args:
        model: 模型名称（v2格式，推荐使用）
        provider: [已弃用] 提供者名称（v1格式，向后兼容）
        config_path: 配置文件路径
        **kwargs: 额外参数

    Returns:
        配置好的嵌入提供者实例
    """
    config = load_config(config_path)

    # Check if config is v2 format (has 'models' key)
    is_v2_config = "models" in config

    # Determine which parameter to use
    if model is not None and provider is not None:
        raise ValueError(
            "Cannot specify both 'model' and 'provider'. "
            "Use 'model' for v2 configs or 'provider' for v1 configs."
        )

    if is_v2_config:
        # V2 config format - use model name
        _, provider_type, provider_config = _resolve_model_config(
            config, model, "embedding"
        )
        provider_str = provider_type
    else:
        # V1 config format - use provider name (backward compatibility)
        if provider is None:
            provider = config["default"]["embedding_provider"]
        # At this point provider is guaranteed to be a string
        assert provider is not None
        provider_str = provider
        provider_config = config[provider]["embeddings"]

    if provider_str not in _EMBEDDING_PROVIDERS:
        if provider_str == "openai" and OpenAIEmbeddingProvider is None:
            raise ImportError(
                "OpenAI embedding provider is not available. "
                "Install with: pip install langchain-llm-config[openai]"
            )
        elif provider_str == "vllm" and VLLMEmbeddingProvider is None:
            raise ImportError(
                "VLLM embedding provider is not available. "
                "Install with: pip install langchain-llm-config[vllm]"
            )
        elif provider_str == "infinity" and InfinityEmbeddingProvider is None:
            raise ImportError(
                "Infinity embedding provider is not available. "
                "Install with: pip install langchain-llm-config[infinity]"
            )
        elif provider_str == "kunlun" and KunlunEmbeddingProvider is None:
            raise ImportError(
                "Kunlun embedding provider is not available. "
                "Install with: pip install langchain-llm-config[kunlun]"
            )
        else:
            raise ValueError(f"未知的嵌入提供者: {provider_str}")

    provider_class = _EMBEDDING_PROVIDERS[provider_str]
    if provider_class is None:
        raise ImportError(f"Provider {provider_str} is not available")

    return provider_class(config=provider_config, **kwargs)  # type: ignore[no-any-return]
