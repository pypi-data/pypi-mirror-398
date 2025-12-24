"""CLI commands for configuring vbagent models.

Provides commands to view and set model configurations for different agents.
"""

import click

from vbagent.config import (
    get_config,
    save_config,
    reset_config,
    AGENT_TYPES,
    MODELS,
    CONFIG_FILE,
)


def _get_console():
    """Lazy import of rich Console."""
    from rich.console import Console
    return Console()


def _get_table(*args, **kwargs):
    """Lazy import of rich Table."""
    from rich.table import Table
    return Table(*args, **kwargs)


CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}


@click.group(context_settings=CONTEXT_SETTINGS)
def config():
    """Configure vbagent models and settings.
    
    View and modify model configurations for different agent types.
    
    \b
    Agent Types:
        classifier  - Image classification
        scanner     - LaTeX extraction from images
        tikz        - TikZ diagram generation
        idea        - Concept extraction
        alternate   - Alternate solution generation
        variant     - Problem variant generation
        converter   - Format conversion
    
    \b
    Examples:
        vbagent config show
        vbagent config models
        vbagent config set scanner --model gpt-4o
        vbagent config set scanner -m gpt-4o
        vbagent config set variant --model o1-mini --reasoning medium
        vbagent config reset
    """
    pass


@config.command()
def show():
    """Show current model configuration for all agents."""
    console = _get_console()
    cfg = get_config()
    
    # Create table
    table = _get_table(title="Agent Model Configuration")
    table.add_column("Agent", style="cyan")
    table.add_column("Model", style="green")
    table.add_column("Reasoning", style="yellow")
    table.add_column("Temperature")
    table.add_column("Max Tokens")
    
    # Add default row
    table.add_row(
        "[bold]default[/bold]",
        cfg.default_model,
        cfg.default_reasoning_effort,
        "-",
        "-",
        style="dim"
    )
    
    # Add each agent
    for agent_type in AGENT_TYPES:
        agent_cfg = getattr(cfg, agent_type)
        table.add_row(
            agent_type,
            agent_cfg.model,
            agent_cfg.reasoning_effort,
            str(agent_cfg.temperature) if agent_cfg.temperature else "-",
            str(agent_cfg.max_tokens) if agent_cfg.max_tokens else "-",
        )
    
    console.print(table)
    
    # Show available models and config location
    console.print("\n[dim]Available models:[/dim]")
    console.print(f"[dim]{', '.join(MODELS.keys())}[/dim]")
    console.print(f"\n[dim]Config file: {CONFIG_FILE}[/dim]")


@config.command()
@click.argument("agent_type", type=click.Choice(AGENT_TYPES + ["default"]))
@click.option("--model", "-m", help="Model to use (e.g., gpt-4o, o1-mini)")
@click.option(
    "--reasoning", "-r",
    type=click.Choice(["low", "medium", "high", "xhigh"]),
    help="Reasoning effort level"
)
@click.option("--temperature", "-t", type=float, help="Temperature (0.0-2.0)")
@click.option("--max-tokens", type=int, help="Maximum tokens")
def set(agent_type: str, model: str, reasoning: str, temperature: float, max_tokens: int):
    """Set model configuration for an agent type.
    
    \b
    Arguments:
        AGENT_TYPE  Agent to configure (classifier, scanner, tikz, etc.)
    
    \b
    Examples:
        vbagent config set scanner --model gpt-4o
        vbagent config set variant --model o1-mini --reasoning medium
        vbagent config set default --model gpt-4.1
    """
    console = _get_console()
    cfg = get_config()
    
    if agent_type == "default":
        if model:
            cfg.default_model = model
        if reasoning:
            cfg.default_reasoning_effort = reasoning
        console.print(f"[green]✓[/green] Updated default configuration")
    else:
        agent_cfg = getattr(cfg, agent_type)
        if model:
            agent_cfg.model = model
        if reasoning:
            agent_cfg.reasoning_effort = reasoning
        if temperature is not None:
            agent_cfg.temperature = temperature
        if max_tokens is not None:
            agent_cfg.max_tokens = max_tokens
        console.print(f"[green]✓[/green] Updated {agent_type} configuration")
    
    # Save to file
    save_config()
    
    # Show updated config
    if agent_type == "default":
        console.print(f"  Model: {cfg.default_model}")
        console.print(f"  Reasoning: {cfg.default_reasoning_effort}")
    else:
        agent_cfg = getattr(cfg, agent_type)
        console.print(f"  Model: {agent_cfg.model}")
        console.print(f"  Reasoning: {agent_cfg.reasoning_effort}")
        if agent_cfg.temperature:
            console.print(f"  Temperature: {agent_cfg.temperature}")
        if agent_cfg.max_tokens:
            console.print(f"  Max Tokens: {agent_cfg.max_tokens}")
    
    console.print(f"\n[dim]Saved to: {CONFIG_FILE}[/dim]")


@config.command()
def reset():
    """Reset all configurations to defaults."""
    console = _get_console()
    reset_config()
    console.print("[green]✓[/green] Configuration reset to defaults")


@config.command()
def models():
    """List available models."""
    console = _get_console()
    console.print("[bold]Available Models:[/bold]\n")
    
    # Group models
    gpt_models = [m for m in MODELS.keys() if m.startswith("gpt")]
    o_models = [m for m in MODELS.keys() if m.startswith("o")]
    
    console.print("[cyan]GPT Models:[/cyan]")
    for m in gpt_models:
        console.print(f"  • {m}")
    
    console.print("\n[cyan]Reasoning Models (o-series):[/cyan]")
    for m in o_models:
        console.print(f"  • {m}")
