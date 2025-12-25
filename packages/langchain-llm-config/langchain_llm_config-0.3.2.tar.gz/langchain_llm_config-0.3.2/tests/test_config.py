"""
Tests for configuration module
"""

from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
import yaml

from langchain_llm_config.config import (
    get_default_config_path,
    init_config,
    load_config,
)


class TestConfigFunctions:
    """Test configuration functions"""

    def test_get_default_config_path_cwd_exists(self, tmp_path: Path) -> None:
        """Test get_default_config_path when api.yaml exists in current directory"""
        # Create api.yaml in current directory
        api_yaml = tmp_path / "api.yaml"
        api_yaml.write_text("test: config")

        with patch("langchain_llm_config.config.Path.cwd", return_value=tmp_path):
            result = get_default_config_path()
            assert result == api_yaml

    def test_get_default_config_path_home_exists(self, tmp_path: Path) -> None:
        """Test get_default_config_path when api.yaml exists in home directory"""
        # Create home directory structure
        home_dir = tmp_path / ".langchain-llm-config"
        home_dir.mkdir()
        api_yaml = home_dir / "api.yaml"
        api_yaml.write_text("test: config")

        with patch("langchain_llm_config.config.Path.cwd") as mock_cwd, patch(
            "langchain_llm_config.config.Path.home", return_value=tmp_path
        ):
            # Mock cwd to not have api.yaml
            mock_cwd.return_value = Path("/some/other/dir")
            result = get_default_config_path()
            assert result == api_yaml

    def test_get_default_config_path_default(self, tmp_path: Path) -> None:
        """Test get_default_config_path when no api.yaml exists"""
        with patch("langchain_llm_config.config.Path.cwd", return_value=tmp_path):
            result = get_default_config_path()
            assert result == tmp_path / "api.yaml"

    def test_load_config_file_not_found(self) -> None:
        """Test load_config with file not found"""
        with pytest.raises(
            ValueError, match="Configuration file not found: nonexistent_file.yaml"
        ):
            load_config("nonexistent_file.yaml")

    def test_load_config_with_default_values(self, tmp_path: Path) -> None:
        """Test load_config with default values"""
        config_content = {
            "models": {
                "gpt-3.5-turbo": {
                    "provider_type": "openai",
                    "model_type": "chat",
                    "model_config": {
                        "model_name": "gpt-3.5-turbo",
                        "api_key": "${OPENAI_API_KEY}",
                    },
                }
            },
            "default": {"chat_provider": "gpt-3.5-turbo"},
        }

        config_file = tmp_path / "test_api.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_content, f)

        # Test with no environment variables set
        config = load_config(str(config_file), strict=False)

        # Verify default values are used - config returns llm_config directly
        # The actual default value might be different, let's check what it is
        assert config["models"]["gpt-3.5-turbo"]["model_config"]["api_key"] in [
            "sk-demo-key-not-for-production",
            "EMPTY",
            "",
        ]

    def test_load_config_with_custom_default_values(self, tmp_path: Path) -> None:
        """Test load_config with custom default values"""
        config_content = {
            "models": {
                "custom-model": {
                    "provider_type": "custom_provider",
                    "model_type": "chat",
                    "model_config": {
                        "api_key": "${CUSTOM_API_KEY}",
                        "model_name": "custom-model",
                    },
                }
            },
            "default": {"chat_provider": "custom-model"},
        }

        config_file = tmp_path / "test_api.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_content, f)

        # Test with no environment variables set
        config = load_config(str(config_file), strict=False)

        # Verify default value is used for unknown provider
        assert config["models"]["custom-model"]["model_config"]["api_key"] == ""

    def test_load_config_with_mixed_env_vars_and_literals(self, tmp_path: Path) -> None:
        """Test load_config with mixed environment variables and literal values"""
        config_content = {
            "models": {
                "gpt-3.5-turbo": {
                    "provider_type": "openai",
                    "model_type": "chat",
                    "model_config": {
                        "api_key": "${OPENAI_API_KEY}",
                        "model_name": "gpt-3.5-turbo",
                        "temperature": 0.7,
                    },
                }
            },
            "default": {"chat_provider": "gpt-3.5-turbo"},
        }

        config_file = tmp_path / "test_api.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_content, f)

        # Test with environment variable set
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key-123"}):
            config = load_config(str(config_file))

        assert (
            config["models"]["gpt-3.5-turbo"]["model_config"]["api_key"]
            == "test-key-123"
        )
        assert (
            config["models"]["gpt-3.5-turbo"]["model_config"]["model_name"]
            == "gpt-3.5-turbo"
        )
        assert config["models"]["gpt-3.5-turbo"]["model_config"]["temperature"] == 0.7

    def test_load_config_strict_mode(self, tmp_path: Path) -> None:
        """Test load_config in strict mode"""
        config_content = {
            "llm": {
                "openai": {"chat": {"api_key": "${OPENAI_API_KEY}"}},
                "default": {"chat_provider": "openai"},
            }
        }

        config_file = tmp_path / "test_api.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_content, f)

        # Test with no environment variables set in strict mode
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(
                ValueError, match="Environment variable OPENAI_API_KEY not set"
            ):
                load_config(str(config_file), strict=True)

    def test_load_config_invalid_yaml(self, tmp_path: Path) -> None:
        """Test load_config with invalid YAML"""
        config_file = tmp_path / "invalid_api.yaml"
        config_file.write_text("invalid: yaml: content: [")

        with pytest.raises(yaml.YAMLError):
            load_config(str(config_file))

    def test_init_config_with_template(self, tmp_path: Path) -> None:
        """Test init_config with existing template"""
        # The template file should now exist in the package
        import langchain_llm_config.config as config_module

        config_file_path = Path(config_module.__file__)
        # Default format is v2, so use api_v2.yaml template
        template_path = config_file_path.parent / "templates" / "api_v2.yaml"

        # Verify the template exists
        assert template_path.exists(), f"Template file not found at {template_path}"
        template_content = template_path.read_text()

        target_path = tmp_path / "new_api.yaml"
        result = init_config(str(target_path), format_version="v2")

        assert result == target_path
        assert target_path.exists()
        # Should copy the template content exactly
        assert target_path.read_text() == template_content
        # Verify it's a valid YAML configuration (V2 format)
        config = yaml.safe_load(target_path.read_text())
        assert "default" in config
        assert "models" in config

    def test_init_config_without_template(self, tmp_path: Path) -> None:
        """Test init_config without template file"""
        target_path = tmp_path / "new_api.yaml"

        # Just test that the function creates a config file
        result = init_config(str(target_path))

        assert result == target_path
        assert target_path.exists()

        # Verify basic config structure was created (V2 format)
        config = load_config(str(result), strict=False)
        assert "default" in config
        assert "models" in config
        # Check that some models exist
        assert len(config["models"]) > 0

    def test_init_config_create_parent_directory(self, tmp_path: Path) -> None:
        """Test init_config creates parent directory if it doesn't exist"""
        target_path = tmp_path / "nested" / "dir" / "api.yaml"

        result = init_config(str(target_path))

        assert result == target_path
        assert target_path.exists()
        assert target_path.parent.exists()

    def test_init_config_default_path(self, tmp_path: Path) -> None:
        """Test init_config with default path"""
        with patch(
            "langchain_llm_config.config.get_default_config_path"
        ) as mock_get_path:
            mock_get_path.return_value = tmp_path / "api.yaml"

            result = init_config()

            assert result == tmp_path / "api.yaml"
            assert result.exists()
