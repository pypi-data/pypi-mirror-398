"""
Configuration utilities for handling both v1 and v2 config formats
"""

from typing import Any, Dict, List, Optional


def detect_config_version(config: Dict[str, Any]) -> str:
    """
    Detect configuration version (v1 or v2)

    Args:
        config: Raw configuration dictionary

    Returns:
        "v1" or "v2" indicating the config format version

    Raises:
        ValueError: If config format is unknown
    """
    if "llm" in config:
        # Old format has "llm" key at root
        return "v1"
    elif "models" in config and "default" in config:
        # New format has "models" and "default" at root
        return "v2"
    else:
        raise ValueError(
            "Unknown config format. Expected either 'llm' key (v1) or "
            "'models' and 'default' keys (v2)"
        )


def get_model_config(config: Dict[str, Any], model_name: str) -> Dict[str, Any]:
    """
    Extract model configuration from v2 config

    Args:
        config: Configuration dictionary (v2 format)
        model_name: Name of the model to retrieve

    Returns:
        Model configuration dictionary

    Raises:
        ValueError: If model not found in config
    """
    if "models" not in config:
        raise ValueError("Config is not in v2 format (missing 'models' key)")

    if model_name not in config["models"]:
        available_models = list(config["models"].keys())
        raise ValueError(
            f"Model '{model_name}' not found in configuration. "
            f"Available models: {', '.join(available_models)}"
        )

    model_config: Dict[str, Any] = config["models"][model_name]
    return model_config


def get_model_type(config: Dict[str, Any], model_name: str) -> str:
    """
    Get the model type (chat, embedding, vlm)

    Args:
        config: Configuration dictionary (v2 format)
        model_name: Name of the model

    Returns:
        Model type string
    """
    model_config = get_model_config(config, model_name)
    return str(model_config.get("model_type", "chat"))


def get_provider_type(config: Dict[str, Any], model_name: str) -> str:
    """
    Get the provider type (openai, vllm, gemini, etc.)

    Args:
        config: Configuration dictionary (v2 format)
        model_name: Name of the model

    Returns:
        Provider type string
    """
    model_config = get_model_config(config, model_name)
    return str(model_config.get("provider_type", "openai"))


def list_models_by_type(
    config: Dict[str, Any], model_type: Optional[str] = None
) -> List[str]:
    """
    List all models of a specific type

    Args:
        config: Configuration dictionary (v2 format)
        model_type: Filter by model type (chat, embedding, vlm). If None, return all.

    Returns:
        List of model names
    """
    if "models" not in config:
        return []

    models = []
    for model_name, model_config in config["models"].items():
        if model_type is None or model_config.get("model_type") == model_type:
            models.append(model_name)

    return models


def validate_model_config(model_config: Dict[str, Any]) -> None:
    """
    Validate a model configuration

    Args:
        model_config: Model configuration dictionary

    Raises:
        ValueError: If configuration is invalid
    """
    required_fields = ["model_type", "provider_type", "model_config"]

    for field in required_fields:
        if field not in model_config:
            raise ValueError(f"Model configuration missing required field: {field}")

    # Validate model_type
    valid_types = ["chat", "embedding", "vlm"]
    if model_config["model_type"] not in valid_types:
        raise ValueError(
            f"Invalid model_type: {model_config['model_type']}. "
            f"Must be one of: {', '.join(valid_types)}"
        )

    # Validate provider_type
    valid_providers = ["openai", "vllm", "gemini", "infinity"]
    if model_config["provider_type"] not in valid_providers:
        raise ValueError(
            f"Invalid provider_type: {model_config['provider_type']}. "
            f"Must be one of: {', '.join(valid_providers)}"
        )

    # Validate model_config is a dict
    if not isinstance(model_config["model_config"], dict):
        raise ValueError("model_config must be a dictionary")


def convert_v1_to_v2(v1_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert v1 config format to v2 format

    Args:
        v1_config: Configuration in v1 format (with 'llm' key)

    Returns:
        Configuration in v2 format (with 'models' and 'default' keys)
    """
    if "llm" not in v1_config:
        raise ValueError("Not a valid v1 config (missing 'llm' key)")

    llm_config = v1_config["llm"]
    v2_config: Dict[str, Any] = {"default": {}, "models": {}}

    # Track default provider names from v1
    default_chat_provider = None
    default_embedding_provider = None

    # Extract default providers from v1
    if "default" in llm_config:
        default_config = llm_config["default"]
        default_chat_provider = default_config.get("chat_provider")
        default_embedding_provider = default_config.get("embedding_provider")

    # Convert each provider's models
    for provider_name, provider_config in llm_config.items():
        if provider_name == "default":
            continue

        # Convert chat models
        if "chat" in provider_config:
            chat_config = provider_config["chat"]
            model_name = chat_config.get("model_name", f"{provider_name}-chat")

            # Determine model type based on provider name or config
            model_type = "vlm" if provider_name == "vlm" else "chat"

            v2_config["models"][model_name] = {
                "model_type": model_type,
                "provider_type": provider_name if provider_name != "vlm" else "openai",
                "model_config": chat_config,
            }

            # Update default to use model name if this was the default provider
            if provider_name == default_chat_provider:
                v2_config["default"]["chat_provider"] = model_name

        # Convert embedding models
        if "embeddings" in provider_config:
            embedding_config = provider_config["embeddings"]
            model_name = embedding_config.get(
                "model_name", f"{provider_name}-embedding"
            )

            v2_config["models"][model_name] = {
                "model_type": "embedding",
                "provider_type": provider_name,
                "model_config": embedding_config,
            }

            # Update default to use model name if this was the default provider
            if provider_name == default_embedding_provider:
                v2_config["default"]["embedding_provider"] = model_name

    # Set fallback defaults if not set
    if "chat_provider" not in v2_config["default"] and v2_config["models"]:
        # Find first chat model
        for model_name, model_config in v2_config["models"].items():
            if model_config["model_type"] == "chat":
                v2_config["default"]["chat_provider"] = model_name
                break

    if "embedding_provider" not in v2_config["default"] and v2_config["models"]:
        # Find first embedding model
        for model_name, model_config in v2_config["models"].items():
            if model_config["model_type"] == "embedding":
                v2_config["default"]["embedding_provider"] = model_name
                break

    return v2_config
