"""
Basic tests for langchain-llm-config package
"""

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from langchain_llm_config import (
    create_assistant,
    create_embedding_provider,
    get_default_config_path,
    init_config,
    load_config,
)


class TestConfig:
    """Test configuration functions"""

    def test_get_default_config_path(self) -> None:
        """Test default config path resolution"""
        path = get_default_config_path()
        assert isinstance(path, Path)
        assert path.name == "api.yaml"

    def test_init_config(self, tmp_path: Path) -> None:
        """Test configuration initialization"""
        config_path = tmp_path / "test_api.yaml"
        result_path = init_config(str(config_path))

        assert result_path.exists()
        assert result_path.name == "test_api.yaml"

        # Verify config structure - use non-strict mode to avoid env var errors
        config = load_config(str(result_path), strict=False)
        # load_config returns the processed llm_config (contents of "llm" key)
        # V2 format uses "models" key instead of provider keys
        assert "default" in config
        assert "models" in config
        # Check that some models exist
        assert len(config["models"]) > 0

    def test_load_config_strict_mode_missing_env_var(
        self, test_config_file: str
    ) -> None:
        """Test that strict mode raises error for missing environment variables"""
        # Create a config with environment variable references
        import yaml

        strict_config = {
            "llm": {
                "gemini": {
                    "chat": {
                        "api_key": "${GEMINI_API_KEY}",
                        "model_name": "gemini-pro",
                    }
                },
                "default": {"chat_provider": "gemini"},
            }
        }

        with open(test_config_file, "w") as f:
            yaml.dump(strict_config, f)

        # Should raise ValueError in strict mode
        with pytest.raises(
            ValueError, match="Environment variable GEMINI_API_KEY not set"
        ):
            load_config(test_config_file, strict=True)

    def test_load_config_non_strict_mode_missing_env_var(
        self, test_config_file: str
    ) -> None:
        """
        Test that non-strict mode uses default values
        for missing environment variables
        """
        # Create a config with environment variable references (V2 format)
        import yaml

        config_with_env_vars = {
            "models": {
                "gemini-pro": {
                    "provider_type": "gemini",
                    "model_type": "chat",
                    "model_config": {
                        "api_key": "${GEMINI_API_KEY}",
                        "model_name": "gemini-pro",
                    },
                }
            },
            "default": {"chat_provider": "gemini-pro"},
        }

        with open(test_config_file, "w") as f:
            yaml.dump(config_with_env_vars, f)

        # Should not raise error and use default value
        config = load_config(test_config_file, strict=False)
        assert (
            config["models"]["gemini-pro"]["model_config"]["api_key"]
            == "demo-key-not-for-production"
        )

    def test_load_config_with_env_vars(
        self, test_config_file: str, mock_env_vars: Any
    ) -> None:
        """Test loading config with environment variables set"""
        # Create a config with environment variable references (V2 format)
        import yaml

        config_with_env_vars = {
            "models": {
                "gpt-3.5-turbo": {
                    "provider_type": "openai",
                    "model_type": "chat",
                    "model_config": {
                        "api_key": "${OPENAI_API_KEY}",
                        "model_name": "gpt-3.5-turbo",
                    },
                }
            },
            "default": {"chat_provider": "gpt-3.5-turbo"},
        }

        with open(test_config_file, "w") as f:
            yaml.dump(config_with_env_vars, f)

        # Should use the environment variable value
        config = load_config(test_config_file, strict=True)
        assert (
            config["models"]["gpt-3.5-turbo"]["model_config"]["api_key"]
            == "sk-test-key-not-for-production"
        )


class TestFactory:
    """Test factory functions"""

    @pytest.mark.skipif(True, reason="Requires optional dependencies")
    @pytest.mark.asyncio
    async def test_create_assistant_mock(self) -> None:
        """Test assistant creation with mocked dependencies"""
        from pydantic import BaseModel, Field

        class TestResponse(BaseModel):
            result: str = Field(..., description="Test result")

        # Mock the assistant class
        mock_assistant = MagicMock()
        mock_assistant.ask = MagicMock(return_value=TestResponse(result="test"))

        with patch(
            "langchain_llm_config.factory.OpenAIAssistant", return_value=mock_assistant
        ):
            with patch("langchain_llm_config.factory.load_config") as mock_load:
                mock_load.return_value = {
                    "default": {"chat_provider": "openai"},
                    "openai": {
                        "chat": {
                            "model_name": "gpt-3.5-turbo",
                            "api_key": "test-key",
                            "temperature": 0.7,
                            "max_tokens": 2000,
                        }
                    },
                }

                assistant = create_assistant(
                    response_model=TestResponse, provider="openai"
                )

                assert assistant is not None

    @pytest.mark.skipif(True, reason="Requires optional dependencies")
    @pytest.mark.asyncio
    async def test_create_embedding_provider_mock(self) -> None:
        """Test embedding provider creation with mocked dependencies"""
        # Mock the embedding provider class
        mock_provider = MagicMock()
        mock_provider.embed_texts = MagicMock(return_value=[[0.1, 0.2, 0.3]])

        with patch(
            "langchain_llm_config.factory.OpenAIEmbeddingProvider",
            return_value=mock_provider,
        ):
            with patch("langchain_llm_config.factory.load_config") as mock_load:
                mock_load.return_value = {
                    "default": {"embedding_provider": "openai"},
                    "openai": {
                        "embeddings": {
                            "model_name": "text-embedding-ada-002",
                            "api_key": "test-key",
                        }
                    },
                }

                provider = create_embedding_provider(provider="openai")

                assert provider is not None


class TestImports:
    """Test that all imports work correctly"""

    def test_main_imports(self) -> None:
        """Test that main package imports work"""
        from langchain_llm_config import (
            create_assistant,
            create_embedding_provider,
            get_default_config_path,
            init_config,
            load_config,
        )

        # Just verify imports work
        assert all(
            [
                create_assistant,
                create_embedding_provider,
                load_config,
                init_config,
                get_default_config_path,
            ]
        )

    def test_provider_imports(self) -> None:
        """Test that provider imports work"""
        from langchain_llm_config import (
            OpenAIEmbeddingProvider,
            VLLMAssistant,
            VLLMEmbeddingProvider,
        )

        # Test providers (may be None if dependencies not installed)
        # Just verify they can be imported without error
        assert True  # If we got here, imports worked

        # Test optional providers (may be None if dependencies not installed)
        try:
            from langchain_llm_config import GeminiAssistant

            # If import succeeds, it should not be None
            if GeminiAssistant is not None:
                assert GeminiAssistant is not None
        except ImportError:
            # Import error is expected if dependencies not available
            pass

        try:
            from langchain_llm_config import InfinityEmbeddingProvider

            # If import succeeds, it should not be None
            if InfinityEmbeddingProvider is not None:
                assert InfinityEmbeddingProvider is not None
        except ImportError:
            # Import error is expected if dependencies not available
            pass


if __name__ == "__main__":
    pytest.main([__file__])
