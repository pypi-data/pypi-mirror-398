"""
Pytest configuration and fixtures for langchain-llm-config tests
"""

import tempfile
from pathlib import Path
from typing import Generator
from unittest.mock import patch

import pytest
import yaml


@pytest.fixture
def test_config_file() -> Generator[str, None, None]:
    """
    Create a temporary test configuration file with mock API keys
    """
    test_config = {
        "llm": {
            "openai": {
                "chat": {
                    "api_base": "https://api.openai.com/v1",
                    "api_key": "sk-test-key-not-for-production",
                    "model_name": "gpt-3.5-turbo",
                    "temperature": 0.7,
                    "max_tokens": 8192,
                    "connect_timeout": 30,
                    "read_timeout": 60,
                },
                "embeddings": {
                    "api_base": "https://api.openai.com/v1",
                    "api_key": "sk-test-key-not-for-production",
                    "model_name": "text-embedding-ada-002",
                    "timeout": 30,
                },
            },
            "vllm": {
                "chat": {
                    "api_base": "http://localhost:8000/v1",
                    "api_key": "sk-test-key-not-for-production",
                    "model_name": "meta-llama/Llama-2-7b-chat-hf",
                    "temperature": 0.6,
                    "top_p": 0.8,
                    "max_tokens": 8192,
                    "connect_timeout": 30,
                    "read_timeout": 60,
                },
                "embeddings": {
                    "api_base": "http://localhost:8000/v1",
                    "api_key": "sk-test-key-not-for-production",
                    "model_name": "bge-m3",
                    "dimensions": 1024,
                    "timeout": 30,
                },
            },
            "gemini": {
                "chat": {
                    "api_key": "test-key-not-for-production",
                    "model_name": "gemini-pro",
                    "temperature": 0.7,
                    "max_tokens": 8192,
                },
                "embeddings": {
                    "api_key": "test-key-not-for-production",
                    "model_name": "embedding-001",
                    "timeout": 30,
                },
            },
            "infinity": {
                "embeddings": {
                    "api_base": "http://localhost:7997/v1",
                    "model_name": "models/bge-m3",
                }
            },
            "default": {"chat_provider": "openai", "embedding_provider": "openai"},
        }
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(test_config, f, default_flow_style=False, allow_unicode=True)
        temp_path = f.name

    yield temp_path

    # Cleanup
    Path(temp_path).unlink(missing_ok=True)


@pytest.fixture
def mock_env_vars() -> Generator[None, None, None]:
    """
    Mock environment variables for testing
    """
    with patch.dict(
        "os.environ",
        {
            "OPENAI_API_KEY": "sk-test-key-not-for-production",
            "GEMINI_API_KEY": "test-key-not-for-production",
            "ANTHROPIC_API_KEY": "sk-ant-test-key-not-for-production",
        },
    ):
        yield


@pytest.fixture(autouse=True)
def suppress_warnings() -> Generator[None, None, None]:
    """
    Suppress warnings during tests to keep output clean
    """
    import warnings

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        yield
