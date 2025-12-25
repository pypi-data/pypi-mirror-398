"""
Command Line Interface for Langchain LLM Config
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Any, Optional, Union

from .config import get_default_config_path, init_config, load_config
from .config_utils import convert_v1_to_v2, detect_config_version


def init_command(args: argparse.Namespace) -> int:
    """Initialize a new configuration file"""
    try:
        format_version = getattr(args, "format", "v2")
        config_path = init_config(args.config_path, format_version=format_version)
        print(f"✅ Configuration file created at: {config_path}")
        print(f"📋 Format version: {format_version}")
        print("\n📝 Next steps:")
        print("1. Edit the configuration file with your API keys and settings")
        print("2. Set up your environment variables (e.g., OPENAI_API_KEY)")
        print("3. Start using the package in your Python code")
        return 0
    except Exception as e:
        print(f"❌ Error creating configuration file: {e}")
        return 1


def validate_command(args: argparse.Namespace) -> int:
    """Validate an existing configuration file"""
    try:
        config_path = args.config_path or get_default_config_path()
        config = load_config(str(config_path))
        print(f"✅ Configuration file is valid: {config_path}")
        print(f"📊 Default chat provider: {config['default']['chat_provider']}")
        print(
            f"📊 Default embedding provider: {config['default']['embedding_provider']}"
        )
        return 0
    except Exception as e:
        print(f"❌ Configuration validation failed: {e}")
        return 1


def migrate_command(args: argparse.Namespace) -> int:
    """Migrate v1 config to v2 format"""
    import yaml

    try:
        config_path = args.config_path or get_default_config_path()

        if not Path(config_path).exists():
            print(f"❌ Configuration file not found: {config_path}")
            return 1

        # Load raw config
        with open(config_path, "r", encoding="utf-8") as f:
            raw_config = yaml.safe_load(f)

        # Detect version
        try:
            version = detect_config_version(raw_config)
        except ValueError as e:
            print(f"❌ {e}")
            return 1

        if version == "v2":
            print(f"ℹ️  Configuration is already in v2 format: {config_path}")
            return 0

        # Convert to v2
        print(f"🔄 Converting configuration from v1 to v2 format...")
        v2_config = convert_v1_to_v2(raw_config)

        # Determine output path
        if args.output:
            output_path = Path(args.output)
        else:
            # Create backup and overwrite
            backup_path = Path(str(config_path) + ".v1.backup")
            import shutil

            shutil.copy2(config_path, backup_path)
            print(f"📦 Backup created: {backup_path}")
            output_path = Path(config_path)

        # Write v2 config
        with open(output_path, "w", encoding="utf-8") as f:
            yaml.dump(
                v2_config,
                f,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
            )

        print(f"✅ Configuration migrated to v2 format: {output_path}")
        print(f"📊 Models defined: {len(v2_config.get('models', {}))}")

        return 0
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback

        traceback.print_exc()
        return 1


def _find_env_vars(obj: Any) -> set[str]:
    """Find all environment variable references in a configuration object."""
    env_vars_needed = set()

    def _find_env_vars_recursive(obj: Any) -> None:
        if isinstance(obj, dict):
            for value in obj.values():
                _find_env_vars_recursive(value)
        elif isinstance(obj, list):
            for item in obj:
                _find_env_vars_recursive(item)
        elif isinstance(obj, str) and obj.startswith("${") and obj.endswith("}"):
            env_vars_needed.add(obj[2:-1])

    _find_env_vars_recursive(obj)
    return env_vars_needed


def _create_env_content(env_vars: set[str]) -> str:
    """Create the content for the .env file."""
    env_content = "# Environment variables for langchain-llm-config\n"
    env_content += "# Copy this file to .env and fill in your actual API keys\n\n"

    for env_var in sorted(env_vars):
        env_content += f"# {env_var} - Get your API key from the provider's website\n"
        env_content += f"{env_var}=your-api-key-here\n\n"

    return env_content


def _print_success_message(env_file_path: Path, env_vars: set[str]) -> None:
    """Print success message and next steps."""
    success_message = (
        f"✅ Created .env file at: {env_file_path}\n"
        "\n📝 Next steps:\n"
        "1. Edit the .env file and replace 'your-api-key-here' "
        "with your actual API keys\n"
        "2. Never commit the .env file to version control "
        "(it should be in .gitignore)\n"
        "3. The package will automatically load these environment variables\n"
        "\n🔑 Environment variables needed:\n"
    )

    # Add environment variables to the message
    for env_var in sorted(env_vars):
        success_message += f"   • {env_var}\n"

    print(success_message)


def setup_env_command(args: argparse.Namespace) -> int:
    """Set up environment variables and create .env file"""
    try:
        # Get the configuration to see what environment variables are needed
        config_path = args.config_path or get_default_config_path()

        if not config_path.exists():
            print(f"❌ Configuration file not found: {config_path}")
            print("💡 Run 'llm-config init' first to create a configuration file")
            return 1

        # Load config in non-strict mode to see what env vars are referenced
        config = load_config(str(config_path), strict=False)

        # Find all environment variable references
        env_vars_needed = _find_env_vars(config)

        if not env_vars_needed:
            print("✅ No environment variables needed in your configuration")
            return 0

        # Create .env file
        env_file_path = Path.cwd() / ".env"

        if env_file_path.exists() and not args.force:
            print(f"⚠️  .env file already exists at {env_file_path}")
            print("💡 Use --force to overwrite it")
            return 1

        # Create .env file with placeholders
        env_content = _create_env_content(env_vars_needed)

        with open(env_file_path, "w") as f:
            f.write(env_content)

        _print_success_message(env_file_path, env_vars_needed)
        return 0

    except Exception as e:
        print(f"❌ Error setting up environment variables: {e}")
        return 1


def info_command(args: argparse.Namespace) -> int:
    """Show information about the package and supported providers"""
    info_prompt = (
        "🤖 Langchain LLM Config\n"
        "==================================================\n"
        "\n📦 Supported Chat Providers:\n"
        "  • OpenAI - GPT models via OpenAI API\n"
        "  • VLLM - Local and remote VLLM servers\n"
        "  • Gemini - Google Gemini models\n"
        "\n🔗 Supported Embedding Providers:\n"
        "  • OpenAI - text-embedding models\n"
        "  • VLLM - Local embedding models\n"
        "  • Infinity - Fast embedding inference\n"
        "\n🚀 Quick Start:\n"
        "  1. llm-config init                     # Initialize config file\n"
        "  2. llm-config setup-env                # Set up environment variables\n"
        "  3. Edit .env with your API keys, api.yaml with your provider settings\n"
        "  4. pip install langchain-llm-config                                    "
        " # Install package\n"
        "  5. Use in your code:\n"
        "     from langchain_llm_config import create_assistant"
    )

    print(info_prompt)
    return 0


def main() -> int:
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        prog="llm-config",
        description="Langchain LLM Config - Manage LLM provider configurations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
        Examples:
            llm-config init                    # Initialize v2 config in current directory
            llm-config init --format v1        # Initialize v1 config (legacy)
            llm-config migrate                 # Migrate v1 config to v2 format
            llm-config migrate -o api_v2.yaml  # Migrate to new file
            llm-config setup-env               # Set up environment variables
            llm-config validate                # Validate current config
            llm-config info                    # Show package information
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Init command
    init_parser = subparsers.add_parser(
        "init", help="Initialize a new configuration file"
    )
    init_parser.add_argument(
        "config_path",
        nargs="?",
        help="Path where to create the configuration file (default: ./api.yaml)",
    )
    init_parser.add_argument(
        "--format",
        choices=["v1", "v2"],
        default="v2",
        help="Configuration format version (default: v2)",
    )
    init_parser.set_defaults(func=init_command)

    # Setup env command
    setup_env_parser = subparsers.add_parser(
        "setup-env", help="Set up environment variables and create .env file"
    )
    setup_env_parser.add_argument(
        "config_path",
        nargs="?",
        help="Path to configuration file (default: ./api.yaml)",
    )
    setup_env_parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing .env file",
    )
    setup_env_parser.set_defaults(func=setup_env_command)

    # Validate command
    validate_parser = subparsers.add_parser(
        "validate", help="Validate configuration file"
    )
    validate_parser.add_argument(
        "config_path",
        nargs="?",
        help="Path to configuration file to validate (default: ./api.yaml)",
    )
    validate_parser.set_defaults(func=validate_command)

    # Migrate command
    migrate_parser = subparsers.add_parser(
        "migrate", help="Migrate v1 config to v2 format"
    )
    migrate_parser.add_argument(
        "config_path",
        nargs="?",
        help="Path to configuration file to migrate (default: ./api.yaml)",
    )
    migrate_parser.add_argument(
        "-o",
        "--output",
        help="Output path for migrated config (default: overwrite with backup)",
    )
    migrate_parser.set_defaults(func=migrate_command)

    # Info command
    info_parser = subparsers.add_parser("info", help="Show package information")
    info_parser.set_defaults(func=info_command)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    result: int = args.func(args)
    return result


if __name__ == "__main__":
    sys.exit(main())
