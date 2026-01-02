"""
CLI for MCP Readiness Scanner.

Provides commands for scanning MCP tool definitions and configurations
for operational readiness issues.
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Any

import click

from mcpreadiness import __version__
from mcpreadiness.config import Config, load_config
from mcpreadiness.core.models import ScanResult, Severity
from mcpreadiness.core.orchestrator import ScanOrchestrator, create_default_orchestrator
from mcpreadiness.core.taxonomy import CATEGORY_DESCRIPTIONS, OperationalRiskCategory
from mcpreadiness.providers.base import InspectionProvider
from mcpreadiness.reports.json_report import render_json
from mcpreadiness.reports.markdown_report import render_markdown
from mcpreadiness.reports.sarif import render_sarif

# Output format options
OUTPUT_FORMATS = ["json", "markdown", "sarif"]


def get_orchestrator(config: Config) -> ScanOrchestrator:
    """Create and configure the scan orchestrator."""
    from mcpreadiness.providers import (
        HeuristicProvider,
        LLMJudgeProvider,
        OpaProvider,
        YaraProvider,
    )

    orchestrator = ScanOrchestrator()

    # Register heuristic provider (always available)
    if config.heuristic.enabled:
        orchestrator.register_provider(
            HeuristicProvider(
                max_capabilities=config.heuristic.max_capabilities,
                min_description_length=config.heuristic.min_description_length,
            )
        )

    # Register YARA provider if available
    if config.yara.enabled and YaraProvider is not None:
        yara = YaraProvider(
            rules_dir=config.yara.rules_dir,
            additional_rules=config.yara.additional_rules,
        )
        if yara.is_available():
            orchestrator.register_provider(yara)

    # Register OPA provider if available
    if config.opa.enabled and OpaProvider is not None:
        opa = OpaProvider(
            policies_dir=config.opa.policies_dir,
            opa_binary=config.opa.opa_binary,
        )
        if opa.is_available():
            orchestrator.register_provider(opa)

    # Register LLM provider if explicitly enabled
    if config.llm.enabled:
        llm = LLMJudgeProvider(
            model=config.llm.model,
            api_base=config.llm.api_base,
            temperature=config.llm.temperature,
            max_tokens=config.llm.max_tokens,
        )
        if llm.is_available():
            orchestrator.register_provider(llm)

    return orchestrator


def output_result(
    result: ScanResult,
    format: str,
    output_file: str | None,
    verbose: bool,
) -> None:
    """Output scan result in the specified format."""
    if format == "json":
        content = render_json(result, indent=2 if verbose else None)
    elif format == "markdown":
        content = render_markdown(result, verbose=verbose)
    elif format == "sarif":
        content = render_sarif(result)
    else:
        raise ValueError(f"Unknown format: {format}")

    if output_file:
        Path(output_file).write_text(content, encoding="utf-8")
        if verbose:
            click.echo(f"Output written to: {output_file}", err=True)
    else:
        click.echo(content)


def determine_exit_code(result: ScanResult, config: Config) -> int:
    """Determine CLI exit code based on scan result and config."""
    if config.scan.fail_on_critical and result.has_critical_findings:
        return 2

    if config.scan.fail_on_high and result.has_high_findings:
        return 1

    if config.scan.min_score is not None and result.readiness_score < config.scan.min_score:
        return 1

    return 0


@click.group()
@click.version_option(version=__version__, prog_name="mcp-readiness")
@click.option(
    "--config",
    "-c",
    "config_file",
    type=click.Path(exists=True),
    help="Path to configuration file",
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option("--no-progress", is_flag=True, help="Disable progress indicators")
@click.pass_context
def cli(ctx: click.Context, config_file: str | None, verbose: bool, no_progress: bool) -> None:
    """
    MCP Readiness Scanner - Production readiness scanner for MCP servers and agentic AI tools.

    Scans MCP tool definitions and configurations for operational readiness
    issues like missing timeouts, unsafe retry patterns, and unclear error handling.
    """
    ctx.ensure_object(dict)
    ctx.obj["config"] = load_config(config_file=config_file)
    ctx.obj["config"].output.verbose = verbose or ctx.obj["config"].output.verbose
    ctx.obj["no_progress"] = no_progress


@cli.command("scan-tool")
@click.option(
    "--tool",
    "-t",
    "tool_path",
    type=click.Path(exists=True),
    help="Path to tool definition JSON file (or use stdin)",
)
@click.option(
    "--providers",
    "-p",
    help="Comma-separated list of providers to use",
)
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(OUTPUT_FORMATS),
    default="json",
    help="Output format",
)
@click.option(
    "--output",
    "-o",
    "output_file",
    type=click.Path(),
    help="Output file (default: stdout)",
)
@click.pass_context
def scan_tool(
    ctx: click.Context,
    tool_path: str | None,
    providers: str | None,
    output_format: str,
    output_file: str | None,
) -> None:
    """
    Scan an MCP tool definition for operational readiness issues.

    Example:
        mcp-readiness scan-tool --tool my_tool.json --format markdown
        cat my_tool.json | mcp-readiness scan-tool --format json
    """
    config: Config = ctx.obj["config"]

    # Load tool definition
    if tool_path:
        with open(tool_path, encoding="utf-8") as f:
            tool_definition = json.load(f)
        target_name = tool_path
    else:
        # Read from stdin
        if sys.stdin.isatty():
            raise click.UsageError("No tool definition provided. Use --tool or pipe JSON to stdin.")
        tool_definition = json.load(sys.stdin)
        target_name = "stdin"

    # Parse providers
    provider_list = providers.split(",") if providers else config.scan.providers

    # Create orchestrator and run scan
    orchestrator = get_orchestrator(config)

    # Show progress if in TTY and verbose mode and not disabled
    no_progress = ctx.obj.get("no_progress", False)
    show_progress = sys.stderr.isatty() and config.output.verbose and not no_progress

    async def run_scan() -> ScanResult:
        if show_progress:
            click.echo("🔍 Scanning tool definition...", err=True)
            available_providers = [p.name for p in orchestrator.list_available_providers()]
            click.echo(f"📦 Providers: {', '.join(provider_list or available_providers)}", err=True)

        return await orchestrator.scan_tool(
            tool_definition=tool_definition,
            providers=provider_list,
            target_name=target_name,
        )

    result = asyncio.run(run_scan())

    if show_progress:
        click.echo(f"✅ Scan complete! Score: {result.readiness_score}/100", err=True)

    # Output result
    output_result(result, output_format, output_file, config.output.verbose)

    # Exit with appropriate code
    sys.exit(determine_exit_code(result, config))


@cli.command("scan-config")
@click.option(
    "--config-file",
    "-c",
    "mcp_config_path",
    type=click.Path(exists=True),
    required=True,
    help="Path to MCP configuration file",
)
@click.option(
    "--providers",
    "-p",
    help="Comma-separated list of providers to use",
)
@click.option(
    "--format",
    "-f",
    "output_format",
    type=click.Choice(OUTPUT_FORMATS),
    default="json",
    help="Output format",
)
@click.option(
    "--output",
    "-o",
    "output_file",
    type=click.Path(),
    help="Output file (default: stdout)",
)
@click.pass_context
def scan_config(
    ctx: click.Context,
    mcp_config_path: str,
    providers: str | None,
    output_format: str,
    output_file: str | None,
) -> None:
    """
    Scan an MCP configuration file for operational readiness issues.

    Example:
        mcp-readiness scan-config --config-file ~/.config/mcp/config.json
    """
    config: Config = ctx.obj["config"]

    # Parse providers
    provider_list = providers.split(",") if providers else config.scan.providers

    # Create orchestrator and run scan
    orchestrator = get_orchestrator(config)

    # Show progress if in TTY and verbose mode and not disabled
    no_progress = ctx.obj.get("no_progress", False)
    show_progress = sys.stderr.isatty() and config.output.verbose and not no_progress

    async def run_scan() -> ScanResult:
        if show_progress:
            click.echo("🔍 Scanning MCP configuration...", err=True)
            available_providers = [p.name for p in orchestrator.list_available_providers()]
            click.echo(f"📦 Providers: {', '.join(provider_list or available_providers)}", err=True)

        return await orchestrator.scan_config_file(
            path=mcp_config_path,
            providers=provider_list,
        )

    result = asyncio.run(run_scan())

    if show_progress:
        click.echo(f"✅ Scan complete! Score: {result.readiness_score}/100", err=True)

    # Output result
    output_result(result, output_format, output_file, config.output.verbose)

    # Exit with appropriate code
    sys.exit(determine_exit_code(result, config))


@cli.command("list-providers")
@click.pass_context
def list_providers(ctx: click.Context) -> None:
    """
    List available inspection providers and their status.

    Shows which providers are available (dependencies installed),
    and which are unavailable with reasons.
    """
    ctx.obj["config"]
    create_default_orchestrator()

    from mcpreadiness.providers import LLMJudgeProvider, OpaProvider, YaraProvider
    from mcpreadiness.providers.heuristic_provider import HeuristicProvider

    # Get status for all provider types
    all_providers: list[tuple[str, InspectionProvider | None]] = [
        ("heuristic", HeuristicProvider()),
    ]

    if YaraProvider is not None:
        all_providers.append(("yara", YaraProvider()))
    else:
        all_providers.append(("yara", None))

    if OpaProvider is not None:
        all_providers.append(("opa", OpaProvider()))
    else:
        all_providers.append(("opa", None))

    all_providers.append(("llm-judge", LLMJudgeProvider()))

    click.echo("Available Providers:")
    click.echo("=" * 60)

    for name, provider in all_providers:
        if provider is None:
            status = click.style("UNAVAILABLE", fg="red")
            reason = "Module import failed"
        elif provider.is_available():
            status = click.style("AVAILABLE", fg="green")
            reason = ""
        else:
            status = click.style("UNAVAILABLE", fg="yellow")
            reason = provider.get_unavailable_reason() or "Unknown"

        click.echo(f"\n{name}")
        click.echo(f"  Status: {status}")
        if provider:
            click.echo(f"  Description: {provider.description}")
        if reason:
            click.echo(f"  Reason: {reason}")

    click.echo("\n" + "=" * 60)
    click.echo("\nTo enable unavailable providers, install their dependencies:")
    click.echo("  yara: pip install yara-python")
    click.echo("  opa: Install OPA binary from https://www.openpolicyagent.org/")
    click.echo("  llm-judge: Set MCP_READINESS_LLM_MODEL environment variable")


@cli.command("list-categories")
@click.option("--format", "-f", "output_format", type=click.Choice(["text", "json"]), default="text")
def list_categories(output_format: str) -> None:
    """
    List operational risk categories in the taxonomy.

    Shows all categories that findings can be classified into,
    with descriptions and default severities.
    """
    if output_format == "json":
        categories = []
        for category in OperationalRiskCategory:
            desc = CATEGORY_DESCRIPTIONS.get(category, {})
            categories.append(
                {
                    "id": category.value,
                    "name": desc.get("name", category.value),
                    "short_description": desc.get("short_description", ""),
                    "default_severity": desc.get("default_severity", Severity.MEDIUM).value,
                }
            )
        click.echo(json.dumps(categories, indent=2))
    else:
        click.echo("Operational Risk Categories")
        click.echo("=" * 60)

        for category in OperationalRiskCategory:
            desc = CATEGORY_DESCRIPTIONS.get(category, {})
            name = desc.get("name", category.value)
            short_desc = desc.get("short_description", "No description")
            severity = desc.get("default_severity", Severity.MEDIUM)

            # Color severity
            severity_colors = {
                Severity.CRITICAL: "red",
                Severity.HIGH: "red",
                Severity.MEDIUM: "yellow",
                Severity.LOW: "blue",
                Severity.INFO: "white",
            }
            severity_styled = click.style(
                severity.value.upper(),
                fg=severity_colors.get(severity, "white"),
            )

            click.echo(f"\n{name}")
            click.echo(f"  ID: {category.value}")
            click.echo(f"  Default Severity: {severity_styled}")
            click.echo(f"  {short_desc}")

        click.echo("\n" + "=" * 60)
        click.echo("\nFor detailed descriptions, see: docs/taxonomy.md")


@cli.command("init")
@click.option(
    "--format",
    "-f",
    "config_format",
    type=click.Choice(["toml", "yaml", "json"]),
    default="toml",
    help="Configuration file format",
)
def init(config_format: str) -> None:
    """
    Initialize a configuration file with defaults.

    Creates a .mcp-readiness.{format} file in the current directory
    with default configuration values.
    """
    config = Config()

    filename = f".mcp-readiness.{config_format}"

    if Path(filename).exists():
        if not click.confirm(f"{filename} already exists. Overwrite?"):
            return

    config_dict = config.model_dump(exclude_none=True)

    if config_format == "toml":
        try:
            import tomli_w

            content = tomli_w.dumps(config_dict)
        except ImportError:
            # Fallback to manual TOML generation
            content = _dict_to_toml(config_dict)
    elif config_format == "yaml":
        try:
            import yaml

            content = yaml.dump(config_dict, default_flow_style=False)
        except ImportError:
            raise click.UsageError("PyYAML is required for YAML format. Install with: pip install pyyaml") from None
    else:  # json
        content = json.dumps(config_dict, indent=2)

    Path(filename).write_text(content, encoding="utf-8")
    click.echo(f"Created {filename}")


def _dict_to_toml(d: dict[str, Any], prefix: str = "") -> str:
    """Simple dict to TOML converter for when tomli_w is not available."""
    lines = []

    # First, output simple key-value pairs
    for key, value in d.items():
        if not isinstance(value, dict):
            if isinstance(value, bool):
                lines.append(f"{key} = {str(value).lower()}")
            elif isinstance(value, str):
                lines.append(f'{key} = "{value}"')
            elif isinstance(value, list):
                items = ", ".join(f'"{v}"' if isinstance(v, str) else str(v) for v in value)
                lines.append(f"{key} = [{items}]")
            elif value is None:
                pass  # Skip None values
            else:
                lines.append(f"{key} = {value}")

    # Then, output nested tables
    for key, value in d.items():
        if isinstance(value, dict):
            section = f"{prefix}.{key}" if prefix else key
            lines.append(f"\n[{section}]")
            lines.append(_dict_to_toml(value, section))

    return "\n".join(lines)


def main() -> None:
    """Main entry point for the CLI."""
    cli(obj={})


if __name__ == "__main__":
    main()
