#!/usr/bin/env python3
"""
Tests for slim package structure and optional dependencies.

This test file focuses on testing the core functionality of the slim package
without requiring optional dependencies.
"""

from unittest.mock import MagicMock, patch

import pytest

import langchain_llm_config


class TestSlimPackageStructure:
    """Test the slim package structure and optional dependency handling."""

    def test_core_imports_always_work(self) -> None:
        """Test that core imports always work without optional dependencies."""
        # These should always be available
        assert hasattr(langchain_llm_config, "load_config")
        assert hasattr(langchain_llm_config, "init_config")
        assert hasattr(langchain_llm_config, "get_default_config_path")
        assert hasattr(langchain_llm_config, "Assistant")
        assert hasattr(langchain_llm_config, "BaseEmbeddingProvider")
        assert hasattr(langchain_llm_config, "create_image_content")
        assert hasattr(langchain_llm_config, "create_multimodal_query")

    def test_optional_provider_imports(self) -> None:
        """Test that optional provider imports work gracefully."""
        # These may or may not be available depending on installed dependencies
        providers = [
            "OpenAIAssistant",
            "VLLMAssistant",
            "GeminiAssistant",
            "OpenAIEmbeddingProvider",
            "VLLMEmbeddingProvider",
            "InfinityEmbeddingProvider",
        ]

        for provider in providers:
            # Should either be a class or None, never raise an error
            provider_class = getattr(langchain_llm_config, provider, None)
            assert provider_class is None or callable(provider_class)

    def test_factory_error_handling_for_missing_providers(self) -> None:
        """Test that factory functions give helpful errors for missing providers."""
        from langchain_llm_config import create_assistant, create_embedding_provider

        # Test assistant factory with potentially missing providers
        # Note: Only test providers that might be in the config
        providers_to_test = ["openai", "vllm"]

        for provider in providers_to_test:
            try:
                create_assistant(provider=provider, auto_apply_parser=False)
                # If this succeeds, the provider is available
                print(f"✓ {provider} assistant provider is available")
            except ImportError as e:
                # This is expected for missing providers
                error_msg = str(e)
                assert "not available" in error_msg or "not found" in error_msg
                assert "pip install" in error_msg
                print(f"✓ {provider} assistant provider correctly reports as missing")
            except Exception as e:
                pytest.fail(f"Unexpected error for {provider}: {e}")

        # Test embedding factory with potentially missing providers
        embedding_providers = ["openai", "vllm", "infinity"]

        for provider in embedding_providers:
            try:
                create_embedding_provider(provider=provider)
                print(f"✓ {provider} embedding provider is available")
            except ImportError as e:
                error_msg = str(e)
                assert "not available" in error_msg or "not found" in error_msg
                assert "pip install" in error_msg
                print(f"✓ {provider} embedding provider correctly reports as missing")
            except Exception as e:
                pytest.fail(f"Unexpected error for {provider}: {e}")

    def test_configuration_loading_works(self) -> None:
        """Test that configuration loading works without optional dependencies."""
        config = langchain_llm_config.load_config()
        assert isinstance(config, dict)
        assert "default" in config

    def test_package_version_available(self) -> None:
        """Test that package version is available."""
        assert hasattr(langchain_llm_config, "__version__")
        assert isinstance(langchain_llm_config.__version__, str)
        assert len(langchain_llm_config.__version__) > 0

    def test_tiktoken_cache_dir_available(self) -> None:
        """Test that tiktoken cache directory is available."""
        assert hasattr(langchain_llm_config, "TIKTOKEN_CACHE_DIR")
        assert isinstance(langchain_llm_config.TIKTOKEN_CACHE_DIR, str)


class TestAbstractAssistantBase:
    """Test the abstract Assistant base class functionality."""

    def test_assistant_is_abstract(self) -> None:
        """Test that Assistant base class is abstract and cannot be instantiated."""
        from langchain_llm_config import Assistant

        with pytest.raises(TypeError, match="abstract"):
            Assistant()  # type: ignore[abstract]

    def test_assistant_abstract_methods(self) -> None:
        """Test that Assistant has the expected abstract methods."""
        from langchain_llm_config import Assistant

        # Check that abstract methods exist
        assert hasattr(Assistant, "_get_model_name")
        assert hasattr(Assistant, "_setup_prompt_and_chain")

        # Check that they're marked as abstract
        assert getattr(Assistant._get_model_name, "__isabstractmethod__", False)
        assert getattr(Assistant._setup_prompt_and_chain, "__isabstractmethod__", False)


class TestMultimodalHelpers:
    """Test multimodal helper functions."""

    def test_create_image_content(self) -> None:
        """Test create_image_content function."""
        from langchain_llm_config import create_image_content

        # Test with URL (use image_url parameter)
        content = create_image_content(image_url="https://example.com/image.jpg")
        assert isinstance(content, dict)
        assert content["type"] == "image_url"
        assert "image_url" in content

        # Test with base64
        content = create_image_content(
            image_base64="data:image/jpeg;base64,/9j/4AAQ..."
        )
        assert isinstance(content, dict)
        assert content["type"] == "image_url"

    def test_create_multimodal_query(self) -> None:
        """Test create_multimodal_query function."""
        from langchain_llm_config import create_multimodal_query

        text = "What's in this image?"

        # Test with image URL
        query = create_multimodal_query(text, image_url="https://example.com/image.jpg")
        assert isinstance(query, list)
        assert len(query) == 2
        assert query[0]["type"] == "text"
        assert query[0]["text"] == text
        assert query[1]["type"] == "image_url"


if __name__ == "__main__":
    pytest.main([__file__])
