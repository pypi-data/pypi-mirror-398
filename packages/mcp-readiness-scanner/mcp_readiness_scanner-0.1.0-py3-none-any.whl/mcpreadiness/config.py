"""
Configuration loading for MCP Readiness Scanner.

Supports loading configuration from:
- Environment variables
- Configuration files (TOML, YAML, JSON)
- CLI arguments (highest priority)
"""

import os
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

# Default configuration file locations
CONFIG_FILE_NAMES = [
    ".mcp-readiness.toml",
    ".mcp-readiness.yaml",
    ".mcp-readiness.yml",
    ".mcp-readiness.json",
    "mcp-readiness.toml",
    "mcp-readiness.yaml",
    "mcp-readiness.yml",
    "mcp-readiness.json",
]


class ProviderConfig(BaseModel):
    """Configuration for a specific provider."""

    enabled: bool = Field(default=True, description="Whether this provider is enabled")
    options: dict[str, Any] = Field(
        default_factory=dict, description="Provider-specific options"
    )


class HeuristicProviderConfig(ProviderConfig):
    """Configuration for the heuristic provider."""

    max_capabilities: int = Field(
        default=10, description="Maximum capabilities before warning"
    )
    min_description_length: int = Field(
        default=20, description="Minimum description length"
    )


class YaraProviderConfig(ProviderConfig):
    """Configuration for the YARA provider."""

    rules_dir: str | None = Field(
        default=None, description="Directory containing YARA rules"
    )
    additional_rules: list[str] = Field(
        default_factory=list, description="Additional YARA rule strings"
    )


class OpaProviderConfig(ProviderConfig):
    """Configuration for the OPA provider."""

    policies_dir: str | None = Field(
        default=None, description="Directory containing Rego policies"
    )
    opa_binary: str = Field(default="opa", description="Path to OPA binary")


class LLMProviderConfig(ProviderConfig):
    """Configuration for the LLM Judge provider."""

    enabled: bool = Field(
        default=False, description="LLM provider is disabled by default"
    )
    model: str | None = Field(
        default=None, description="LiteLLM model identifier"
    )
    api_base: str | None = Field(
        default=None, description="API base URL for self-hosted models"
    )
    temperature: float = Field(default=0.1, description="LLM temperature")
    max_tokens: int = Field(default=1024, description="Maximum response tokens")


class OutputConfig(BaseModel):
    """Configuration for output formatting."""

    format: str = Field(
        default="json", description="Output format (json, markdown, sarif)"
    )
    output_file: str | None = Field(
        default=None, description="Output file path (default: stdout)"
    )
    verbose: bool = Field(default=False, description="Enable verbose output")
    color: bool = Field(default=True, description="Enable colored output")


class ScanConfig(BaseModel):
    """Configuration for scan behavior."""

    fail_on_critical: bool = Field(
        default=True, description="Exit with error code on critical findings"
    )
    fail_on_high: bool = Field(
        default=False, description="Exit with error code on high findings"
    )
    min_score: int | None = Field(
        default=None, description="Minimum readiness score to pass"
    )
    providers: list[str] | None = Field(
        default=None, description="Providers to use (None = all available)"
    )


class Config(BaseModel):
    """Complete configuration for MCP Readiness Scanner."""

    scan: ScanConfig = Field(default_factory=ScanConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)
    heuristic: HeuristicProviderConfig = Field(default_factory=HeuristicProviderConfig)
    yara: YaraProviderConfig = Field(default_factory=YaraProviderConfig)
    opa: OpaProviderConfig = Field(default_factory=OpaProviderConfig)
    llm: LLMProviderConfig = Field(default_factory=LLMProviderConfig)


def find_config_file(start_dir: Path | None = None) -> Path | None:
    """
    Find configuration file by searching upwards from start_dir.

    Args:
        start_dir: Directory to start searching from (default: cwd)

    Returns:
        Path to config file if found, None otherwise
    """
    if start_dir is None:
        start_dir = Path.cwd()

    current = start_dir.resolve()

    while True:
        for config_name in CONFIG_FILE_NAMES:
            config_path = current / config_name
            if config_path.exists():
                return config_path

        parent = current.parent
        if parent == current:
            # Reached root
            break
        current = parent

    return None


def load_config_file(path: Path) -> dict[str, Any]:
    """
    Load configuration from a file.

    Supports TOML, YAML, and JSON formats.

    Args:
        path: Path to configuration file

    Returns:
        Configuration dictionary
    """
    suffix = path.suffix.lower()

    with open(path, encoding="utf-8") as f:
        content = f.read()

    if suffix == ".toml":
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib  # type: ignore
        return tomllib.loads(content)

    elif suffix in (".yaml", ".yml"):
        try:
            import yaml

            return yaml.safe_load(content) or {}
        except ImportError:
            raise ImportError(
                "PyYAML is required to load YAML config files. "
                "Install with: pip install pyyaml"
            ) from None

    elif suffix == ".json":
        import json

        return json.loads(content)

    else:
        raise ValueError(f"Unsupported config file format: {suffix}")


def load_config(
    config_file: Path | str | None = None,
    search: bool = True,
) -> Config:
    """
    Load configuration from file and environment.

    Priority (highest to lowest):
    1. Explicit config_file parameter
    2. Environment variables
    3. Auto-discovered config file
    4. Defaults

    Args:
        config_file: Explicit path to config file
        search: Whether to search for config file if not specified

    Returns:
        Loaded configuration
    """
    config_data: dict[str, Any] = {}

    # Load from file
    if config_file:
        config_path = Path(config_file)
        if config_path.exists():
            config_data = load_config_file(config_path)
    elif search:
        found_path = find_config_file()
        if found_path:
            config_data = load_config_file(found_path)

    # Apply environment variable overrides
    env_overrides = load_env_config()
    config_data = deep_merge(config_data, env_overrides)

    return Config.model_validate(config_data)


def load_env_config() -> dict[str, Any]:
    """
    Load configuration from environment variables.

    Environment variable naming convention:
    MCP_READINESS_<SECTION>_<KEY> (all uppercase)

    Examples:
    - MCP_READINESS_SCAN_FAIL_ON_CRITICAL=true
    - MCP_READINESS_OUTPUT_FORMAT=markdown
    - MCP_READINESS_LLM_MODEL=gpt-4
    """
    config: dict[str, Any] = {}
    prefix = "MCP_READINESS_"

    for key, value in os.environ.items():
        if not key.startswith(prefix):
            continue

        # Parse key into section and field
        parts = key[len(prefix) :].lower().split("_", 1)
        if len(parts) != 2:
            continue

        section, field = parts

        # Convert value to appropriate type
        parsed_value = parse_env_value(value)

        # Set in config
        if section not in config:
            config[section] = {}
        config[section][field] = parsed_value

    return config


def parse_env_value(value: str) -> Any:
    """Parse an environment variable value to appropriate Python type."""
    # Boolean
    if value.lower() in ("true", "yes", "1", "on"):
        return True
    if value.lower() in ("false", "no", "0", "off"):
        return False

    # None/null
    if value.lower() in ("none", "null", ""):
        return None

    # Integer
    try:
        return int(value)
    except ValueError:
        pass

    # Float
    try:
        return float(value)
    except ValueError:
        pass

    # List (comma-separated)
    if "," in value:
        return [v.strip() for v in value.split(",")]

    # String
    return value


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """
    Deep merge two dictionaries.

    Args:
        base: Base dictionary
        override: Dictionary with values to override

    Returns:
        Merged dictionary
    """
    result = base.copy()

    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value

    return result
