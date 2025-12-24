"""Main CLI entry point for VBAgent.

VBAgent - Physics question processing pipeline.

Uses lazy loading to speed up CLI startup time by deferring
heavy imports (openai, agents, mcp, etc.) until commands are actually invoked.
"""

import click


class LazyGroup(click.Group):
    """A click Group that lazily loads subcommands.
    
    This dramatically improves CLI startup time by deferring imports
    of heavy dependencies (openai, agents, mcp, rich, etc.) until
    a specific command is actually invoked.
    """
    
    def __init__(self, *args, lazy_subcommands: dict[str, str] | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        # Map of command name -> module path
        self._lazy_subcommands = lazy_subcommands or {}
    
    def list_commands(self, ctx: click.Context) -> list[str]:
        base = super().list_commands(ctx)
        lazy = sorted(self._lazy_subcommands.keys())
        return base + lazy
    
    def get_command(self, ctx: click.Context, cmd_name: str) -> click.Command | None:
        if cmd_name in self._lazy_subcommands:
            return self._lazy_load(cmd_name)
        return super().get_command(ctx, cmd_name)
    
    def _lazy_load(self, cmd_name: str) -> click.Command:
        # Import the module and get the command
        import importlib
        module_path = self._lazy_subcommands[cmd_name]
        module = importlib.import_module(module_path)
        return getattr(module, cmd_name)


# Define lazy subcommands: command_name -> module_path
LAZY_SUBCOMMANDS = {
    "classify": "vbagent.cli.classify",
    "scan": "vbagent.cli.scan",
    "tikz": "vbagent.cli.tikz",
    "idea": "vbagent.cli.idea",
    "alternate": "vbagent.cli.alternate",
    "variant": "vbagent.cli.variant",
    "convert": "vbagent.cli.convert",
    "process": "vbagent.cli.process",
    "batch": "vbagent.cli.batch",
    "ref": "vbagent.cli.ref",
    "config": "vbagent.cli.config",
    "check": "vbagent.cli.check",
}


CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}


@click.group(cls=LazyGroup, lazy_subcommands=LAZY_SUBCOMMANDS, context_settings=CONTEXT_SETTINGS)
@click.version_option(version="0.1.0", prog_name="vbagent")
def main():
    """VBAgent - Physics question processing pipeline.
    
    A multi-agent CLI system for processing physics question images.
    Supports classification, scanning, diagram generation, variant creation,
    and format conversion.
    
    \b
    Commands:
        classify  - Stage 1: Classify physics question image
        scan      - Stage 2: Extract LaTeX from image
        tikz      - Generate TikZ code for diagrams
        idea      - Extract physics concepts and ideas
        alternate - Generate alternative solutions
        variant   - Generate problem variants
        convert   - Convert between question formats
        process   - Full pipeline orchestration
        batch     - Batch processing with resume capability
        ref       - Manage reference context files
        config    - Configure models and settings
        check     - QA review with interactive approval
    """
    pass


if __name__ == "__main__":
    main()
