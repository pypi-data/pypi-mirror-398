import os
import warnings
from pathlib import Path
from typing import Any, Dict, Optional, Union

import yaml
from dotenv import load_dotenv

from .config_utils import convert_v1_to_v2, detect_config_version


def get_default_config_path() -> Path:
    """
    Get the default configuration file path.

    Returns:
        Path to the default api.yaml file
    """
    # Try to find api.yaml in current working directory first
    cwd_config = Path.cwd() / "api.yaml"
    if cwd_config.exists():
        return cwd_config

    # Try to find api.yaml in user's home directory
    home_config = Path.home() / ".langchain-llm-config" / "api.yaml"
    if home_config.exists():
        return home_config

    # Return the current working directory as default location
    return cwd_config


def _get_default_api_key(env_var: str) -> str:
    """Get default API key for common environment variables."""
    default_values = {
        "OPENAI_API_KEY": "sk-demo-key-not-for-production",
        "GEMINI_API_KEY": "demo-key-not-for-production",
        "ANTHROPIC_API_KEY": "sk-ant-demo-key-not-for-production",
    }
    return default_values.get(env_var, "")


def _process_environment_variable(
    env_var: str,
    env_value: Optional[str],
    strict: bool,
    service_config: Dict[str, Any],
    key: str,
) -> None:
    """Process a single environment variable."""
    if env_value is None:
        if strict:
            raise ValueError(f"Environment variable {env_var} not set")
        else:
            default_value = _get_default_api_key(env_var)
            service_config[key] = default_value
            warnings.warn(
                f"Environment variable {env_var} not set. Using "
                f"default value. Set {env_var} in your environment "
                f"or .env file for production use.",
                UserWarning,
                stacklevel=2,
            )
    else:
        service_config[key] = env_value


def _process_env_vars_recursive(config: Dict[str, Any], strict: bool = False) -> None:
    """
    Recursively process environment variables in configuration

    Args:
        config: Configuration dictionary to process
        strict: If True, raise error for missing env vars
    """
    for key, value in config.items():
        if isinstance(value, dict):
            _process_env_vars_recursive(value, strict)
        elif isinstance(value, str) and value.startswith("${") and value.endswith("}"):
            env_var = value[2:-1]
            env_value = os.getenv(env_var)
            _process_environment_variable(env_var, env_value, strict, config, key)


def load_config(
    config_path: Optional[Union[str, Path]] = None, strict: bool = False
) -> Dict[str, Any]:
    """
    Load LLM configuration (supports both v1 and v2 formats)

    Args:
        config_path: Configuration file path, defaults to api.yaml in current directory
        strict: If True, raise ValueError for missing environment variables.
                If False, use default values and show warnings.

    Returns:
        Processed configuration dictionary in v2 format

    Raises:
        ValueError: Configuration file not found or environment variables not
                   set (if strict=True)
    """
    # Load environment variables from .env file
    dotenv_path = Path.cwd() / ".env"
    if dotenv_path.exists():
        load_dotenv(dotenv_path=dotenv_path)

    if config_path is None:
        config_path = get_default_config_path()
    else:
        config_path = Path(config_path)

    if not config_path.exists():
        raise ValueError(f"Configuration file not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        raw_config: Dict[str, Any] = yaml.safe_load(f)

    # Detect config version and convert if needed
    try:
        version = detect_config_version(raw_config)
    except ValueError:
        # Fallback to v1 if detection fails
        version = "v1"

    if version == "v1":
        # Convert v1 to v2 format
        warnings.warn(
            "Using deprecated v1 config format. Consider migrating to v2 format "
            "using 'llm-config migrate' command for better flexibility.",
            DeprecationWarning,
            stacklevel=2,
        )
        config = convert_v1_to_v2(raw_config)
    else:
        # Already v2 format
        config = raw_config

    # Process environment variables recursively
    _process_env_vars_recursive(config, strict)

    return config


def init_config(
    config_path: Optional[Union[str, Path]] = None, format_version: str = "v2"
) -> Path:
    """
    Initialize a new configuration file with default settings.

    Args:
        config_path: Path where to create the configuration file
        format_version: Config format version ("v1" or "v2", default "v2")

    Returns:
        Path to the created configuration file
    """
    if config_path is None:
        config_path = get_default_config_path()
    else:
        config_path = Path(config_path)

    # Create parent directory if it doesn't exist
    config_path.parent.mkdir(parents=True, exist_ok=True)

    # Get the template configuration based on version
    if format_version == "v2":
        template_name = "api_v2.yaml"
    else:
        template_name = "api.yaml"

    template_path = Path(__file__).parent / "templates" / template_name

    if template_path.exists():
        # Copy template to target location
        import shutil

        shutil.copy2(template_path, config_path)
    else:
        # If template doesn't exist, create a minimal configuration
        if format_version == "v2":
            minimal_config: Dict[str, Any] = {
                "default": {
                    "chat_provider": "gpt-3.5-turbo",
                    "embedding_provider": "text-embedding-ada-002",
                },
                "models": {
                    "gpt-3.5-turbo": {
                        "model_type": "chat",
                        "provider_type": "openai",
                        "model_config": {
                            "api_key": "${OPENAI_API_KEY}",
                            "model_name": "gpt-3.5-turbo",
                        },
                    },
                    "text-embedding-ada-002": {
                        "model_type": "embedding",
                        "provider_type": "openai",
                        "model_config": {
                            "api_key": "${OPENAI_API_KEY}",
                            "model_name": "text-embedding-ada-002",
                        },
                    },
                },
            }
        else:
            # v1 format
            minimal_config = {
                "llm": {
                    "default": {
                        "chat_provider": "openai",
                        "embedding_provider": "openai",
                    },
                    "openai": {
                        "chat": {
                            "api_key": "${OPENAI_API_KEY}",
                            "model_name": "gpt-3.5-turbo",
                        },
                        "embeddings": {
                            "api_key": "${OPENAI_API_KEY}",
                            "model_name": "text-embedding-ada-002",
                        },
                    },
                }
            }

        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(minimal_config, f, default_flow_style=False, allow_unicode=True)

    return config_path
