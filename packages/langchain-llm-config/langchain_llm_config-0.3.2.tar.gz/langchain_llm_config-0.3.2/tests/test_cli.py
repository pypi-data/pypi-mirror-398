"""
Tests for CLI module
"""

import sys
import tempfile
from io import StringIO
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, mock_open, patch

import pytest
import yaml

from langchain_llm_config.cli import (
    info_command,
    init_command,
    main,
    setup_env_command,
    validate_command,
)


class TestCLICommands:
    """Test CLI command functions"""

    def test_init_command_success(self, tmp_path: Path) -> None:
        """Test successful init command"""
        config_path = tmp_path / "test_api.yaml"

        with patch("langchain_llm_config.cli.init_config") as mock_init:
            mock_init.return_value = config_path

            # Capture stdout
            with patch("sys.stdout", new=StringIO()) as mock_stdout:
                # Mock args with format attribute
                args = MagicMock(config_path=str(config_path), format="v2")
                result = init_command(args)

            assert result == 0
            assert "✅ Configuration file created at:" in mock_stdout.getvalue()
            assert "📝 Next steps:" in mock_stdout.getvalue()
            mock_init.assert_called_once_with(str(config_path), format_version="v2")

    def test_init_command_error(self) -> None:
        """Test init command with error"""
        with patch("langchain_llm_config.cli.init_config") as mock_init:
            mock_init.side_effect = Exception("Test error")

            # Capture stdout
            with patch("sys.stdout", new=StringIO()) as mock_stdout:
                result = init_command(MagicMock(config_path="test.yaml"))

            assert result == 1
            assert "❌ Error creating configuration file:" in mock_stdout.getvalue()
            assert "Test error" in mock_stdout.getvalue()

    def test_validate_command_success(self, tmp_path: Path) -> None:
        """Test successful validate command"""
        config_path = tmp_path / "test_api.yaml"

        with patch(
            "langchain_llm_config.cli.get_default_config_path"
        ) as mock_get_path, patch("langchain_llm_config.cli.load_config") as mock_load:

            mock_get_path.return_value = config_path
            mock_load.return_value = {
                "default": {"chat_provider": "openai", "embedding_provider": "openai"}
            }

            # Capture stdout
            with patch("sys.stdout", new=StringIO()) as mock_stdout:
                result = validate_command(MagicMock(config_path=None))

            assert result == 0
            assert "✅ Configuration file is valid:" in mock_stdout.getvalue()
            assert "📊 Default chat provider: openai" in mock_stdout.getvalue()
            assert "📊 Default embedding provider: openai" in mock_stdout.getvalue()

    def test_validate_command_with_custom_path(self, tmp_path: Path) -> None:
        """Test validate command with custom config path"""
        config_path = tmp_path / "custom_api.yaml"

        with patch("langchain_llm_config.cli.load_config") as mock_load:
            mock_load.return_value = {
                "default": {"chat_provider": "vllm", "embedding_provider": "infinity"}
            }

            # Capture stdout
            with patch("sys.stdout", new=StringIO()) as mock_stdout:
                result = validate_command(MagicMock(config_path=str(config_path)))

            assert result == 0
            assert "✅ Configuration file is valid:" in mock_stdout.getvalue()
            mock_load.assert_called_once_with(str(config_path))

    def test_validate_command_error(self) -> None:
        """Test validate command with error"""
        with patch(
            "langchain_llm_config.cli.get_default_config_path"
        ) as mock_get_path, patch("langchain_llm_config.cli.load_config") as mock_load:

            mock_get_path.return_value = Path("nonexistent.yaml")
            mock_load.side_effect = Exception("Config error")

            # Capture stdout
            with patch("sys.stdout", new=StringIO()) as mock_stdout:
                result = validate_command(MagicMock(config_path=None))

            assert result == 1
            assert "❌ Configuration validation failed:" in mock_stdout.getvalue()
            assert "Config error" in mock_stdout.getvalue()

    def test_setup_env_command_success(self, tmp_path: Path) -> None:
        """Test successful setup_env command"""
        config_path = tmp_path / "test_api.yaml"

        # Create a test config file
        test_config = {
            "llm": {
                "openai": {"chat": {"api_key": "${OPENAI_API_KEY}"}},
                "gemini": {"chat": {"api_key": "${GEMINI_API_KEY}"}},
            }
        }

        with open(config_path, "w") as f:
            yaml.dump(test_config, f)

        with patch(
            "langchain_llm_config.cli.get_default_config_path"
        ) as mock_get_path, patch(
            "langchain_llm_config.cli.load_config"
        ) as mock_load, patch(
            "pathlib.Path.cwd"
        ) as mock_cwd, patch(
            "builtins.open", mock_open()
        ):

            mock_get_path.return_value = config_path
            mock_load.return_value = test_config["llm"]
            mock_cwd.return_value = tmp_path

            # Capture stdout
            with patch("sys.stdout", new=StringIO()) as mock_stdout:
                result = setup_env_command(MagicMock(config_path=None, force=False))

            assert result == 0
            assert "✅ Created .env file at:" in mock_stdout.getvalue()
            assert "🔑 Environment variables needed:" in mock_stdout.getvalue()
            assert "• OPENAI_API_KEY" in mock_stdout.getvalue()
            assert "• GEMINI_API_KEY" in mock_stdout.getvalue()

    def test_setup_env_command_config_not_found(self) -> None:
        """Test setup_env command when config file doesn't exist"""
        with patch("langchain_llm_config.cli.get_default_config_path") as mock_get_path:
            mock_get_path.return_value = Path("nonexistent.yaml")

            # Capture stdout
            with patch("sys.stdout", new=StringIO()) as mock_stdout:
                result = setup_env_command(MagicMock(config_path=None, force=False))

            assert result == 1
            assert "❌ Configuration file not found:" in mock_stdout.getvalue()
            assert "💡 Run 'llm-config init' first" in mock_stdout.getvalue()

    def test_setup_env_command_env_file_exists(self, tmp_path: Path) -> None:
        """Test setup_env command when .env file already exists"""
        config_path = tmp_path / "test_api.yaml"
        env_file = tmp_path / ".env"

        # Create test files
        test_config = {"llm": {"openai": {"chat": {"api_key": "${OPENAI_API_KEY}"}}}}
        with open(config_path, "w") as f:
            yaml.dump(test_config, f)

        with open(env_file, "w") as f:
            f.write("existing content")

        with patch(
            "langchain_llm_config.cli.get_default_config_path"
        ) as mock_get_path, patch(
            "langchain_llm_config.cli.load_config"
        ) as mock_load, patch(
            "pathlib.Path.cwd"
        ) as mock_cwd:

            mock_get_path.return_value = config_path
            mock_load.return_value = test_config["llm"]
            mock_cwd.return_value = tmp_path

            # Capture stdout
            with patch("sys.stdout", new=StringIO()) as mock_stdout:
                result = setup_env_command(MagicMock(config_path=None, force=False))

            assert result == 1
            assert "⚠️  .env file already exists" in mock_stdout.getvalue()
            assert "💡 Use --force to overwrite it" in mock_stdout.getvalue()

    def test_setup_env_command_force_overwrite(self, tmp_path: Path) -> None:
        """Test setup_env command with force flag"""
        config_path = tmp_path / "test_api.yaml"
        env_file = tmp_path / ".env"

        # Create test config
        test_config = {"llm": {"openai": {"chat": {"api_key": "${OPENAI_API_KEY}"}}}}
        with open(config_path, "w") as f:
            yaml.dump(test_config, f)

        # Create existing .env file
        with open(env_file, "w") as f:
            f.write("existing content")

        with patch(
            "langchain_llm_config.cli.get_default_config_path"
        ) as mock_get_path, patch(
            "langchain_llm_config.cli.load_config"
        ) as mock_load, patch(
            "pathlib.Path.cwd"
        ) as mock_cwd, patch(
            "builtins.open", mock_open()
        ):

            mock_get_path.return_value = config_path
            mock_load.return_value = test_config["llm"]
            mock_cwd.return_value = tmp_path

            # Capture stdout
            with patch("sys.stdout", new=StringIO()) as mock_stdout:
                result = setup_env_command(MagicMock(config_path=None, force=True))

            assert result == 0
            assert "✅ Created .env file at:" in mock_stdout.getvalue()

    def test_setup_env_command_no_env_vars_needed(self, tmp_path: Path) -> None:
        """Test setup_env command when no environment variables are needed"""
        config_path = tmp_path / "test_api.yaml"

        # Create test config without env vars
        test_config = {"llm": {"openai": {"chat": {"api_key": "hardcoded-key"}}}}
        with open(config_path, "w") as f:
            yaml.dump(test_config, f)

        with patch(
            "langchain_llm_config.cli.get_default_config_path"
        ) as mock_get_path, patch("langchain_llm_config.cli.load_config") as mock_load:

            mock_get_path.return_value = config_path
            mock_load.return_value = test_config["llm"]

            # Capture stdout
            with patch("sys.stdout", new=StringIO()) as mock_stdout:
                result = setup_env_command(MagicMock(config_path=None, force=False))

            assert result == 0
            assert "✅ No environment variables needed" in mock_stdout.getvalue()

    def test_setup_env_command_error(self) -> None:
        """Test setup_env command with error"""
        with patch("langchain_llm_config.cli.get_default_config_path") as mock_get_path:
            mock_get_path.side_effect = Exception("Setup error")

            # Capture stdout
            with patch("sys.stdout", new=StringIO()) as mock_stdout:
                result = setup_env_command(MagicMock(config_path=None, force=False))

            assert result == 1
            assert (
                "❌ Error setting up environment variables:" in mock_stdout.getvalue()
            )
            assert "Setup error" in mock_stdout.getvalue()

    def test_info_command(self) -> None:
        """Test info command"""
        # Capture stdout
        with patch("sys.stdout", new=StringIO()) as mock_stdout:
            result = info_command(MagicMock())

        assert result == 0
        output = mock_stdout.getvalue()
        assert "🤖 Langchain LLM Config" in output
        assert "📦 Supported Chat Providers:" in output
        assert "🔗 Supported Embedding Providers:" in output
        assert "🚀 Quick Start:" in output
        assert "• OpenAI" in output
        assert "• VLLM" in output
        assert "• Gemini" in output
        assert "• Infinity" in output


class TestCLIMain:
    """Test CLI main function"""

    def test_main_init_command(self) -> None:
        """Test main function with init command"""
        with patch("sys.argv", ["llm-config", "init", "test.yaml"]), patch(
            "langchain_llm_config.cli.init_command"
        ) as mock_init:

            mock_init.return_value = 0
            result = main()

            assert result == 0
            mock_init.assert_called_once()

    def test_main_validate_command(self) -> None:
        """Test main function with validate command"""
        with patch("sys.argv", ["llm-config", "validate"]), patch(
            "langchain_llm_config.cli.validate_command"
        ) as mock_validate:

            mock_validate.return_value = 0
            result = main()

            assert result == 0
            mock_validate.assert_called_once()

    def test_main_setup_env_command(self) -> None:
        """Test main function with setup-env command"""
        with patch("sys.argv", ["llm-config", "setup-env", "--force"]), patch(
            "langchain_llm_config.cli.setup_env_command"
        ) as mock_setup:

            mock_setup.return_value = 0
            result = main()

            assert result == 0
            mock_setup.assert_called_once()

    def test_main_info_command(self) -> None:
        """Test main function with info command"""
        with patch("sys.argv", ["llm-config", "info"]), patch(
            "langchain_llm_config.cli.info_command"
        ) as mock_info:

            mock_info.return_value = 0
            result = main()

            assert result == 0
            mock_info.assert_called_once()

    def test_main_no_command(self) -> None:
        """Test main function with no command"""
        with patch("sys.argv", ["llm-config"]), patch(
            "argparse.ArgumentParser.print_help"
        ) as mock_help:

            result = main()

            assert result == 1
            mock_help.assert_called_once()

    @patch("langchain_llm_config.cli.argparse.ArgumentParser.print_help")
    def test_main_unknown_command(self, mock_print_help: MagicMock) -> None:
        """Test main function with unknown command"""
        with patch("sys.argv", ["llm-config", "unknown"]):
            with pytest.raises(SystemExit):
                main()

        # The print_help method is not called in the actual implementation
        # when an unknown command is provided, so we don't assert it

    def test_main_exit_on_error(self) -> None:
        """Test main function exit on error"""
        with patch("sys.argv", ["llm-config", "init"]), patch(
            "langchain_llm_config.cli.init_command"
        ) as mock_init:

            mock_init.return_value = 1
            result = main()

            assert result == 1
