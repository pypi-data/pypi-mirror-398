"""CLI command for generating TikZ diagram code.

Generates TikZ/PGF code for physics diagrams from images or descriptions.
"""

from pathlib import Path

import click


def _get_console():
    """Lazy import of rich Console."""
    from rich.console import Console
    return Console()


def _get_panel(*args, **kwargs):
    """Lazy import of rich Panel."""
    from rich.panel import Panel
    return Panel(*args, **kwargs)


def _get_syntax(*args, **kwargs):
    """Lazy import of rich Syntax."""
    from rich.syntax import Syntax
    return Syntax(*args, **kwargs)


CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}


@click.command(context_settings=CONTEXT_SETTINGS)
@click.option(
    "-i", "--image",
    type=click.Path(exists=True),
    help="Path to a diagram image file"
)
@click.option(
    "-d", "--description",
    type=str,
    help="Text description of the diagram to generate"
)
@click.option(
    "--ref", "ref_dirs",
    multiple=True,
    type=click.Path(exists=True),
    help="Reference directories containing TikZ/PGF documentation (can be used multiple times)"
)
@click.option(
    "-o", "--output",
    type=click.Path(),
    help="Output TeX file path for saving the generated TikZ code"
)
def tikz(
    image: str | None,
    description: str | None,
    ref_dirs: tuple[str, ...],
    output: str | None
):
    """Generate TikZ code for physics diagrams.
    
    Can generate TikZ code from an image, a text description, or both.
    Optionally searches reference files (STY, TeX, PDF) for syntax examples.
    
    \b
    Examples:
        vbagent tikz -d "Free body diagram with gravity and normal force"
        vbagent tikz --description "Projectile motion" --output motion.tex
        vbagent tikz -i diagram.png -o diagram.tex
        vbagent tikz -i img.png --ref refs/tikz/ --ref refs/pgf/
        vbagent tikz -d "RC circuit" --ref refs/circuitikz/ -o circuit.tex
    """
    # Lazy imports - only load heavy dependencies when command runs
    from vbagent.agents.tikz import generate_tikz, validate_tikz_output
    from vbagent.references.store import ReferenceStore
    
    console = _get_console()
    
    # Validate that at least one input is provided
    if not image and not description:
        console.print("[red]Error:[/red] Either --image or --description must be provided")
        raise SystemExit(1)
    
    try:
        # Initialize reference store if directories provided
        if ref_dirs:
            store = ReferenceStore.get_instance(directories=list(ref_dirs))
            with console.status("[bold blue]Indexing reference files..."):
                indexed_count = store.index_files()
            console.print(f"[dim]Indexed {indexed_count} reference files[/dim]")
        
        # Build description from inputs
        if description:
            desc = description
        else:
            desc = "Generate TikZ code for the diagram shown in the image."
        
        # Generate TikZ code
        with console.status("[bold green]Generating TikZ code..."):
            tikz_code = generate_tikz(
                description=desc,
                image_path=image,
            )
        
        # Validate output
        if not validate_tikz_output(tikz_code):
            console.print("[yellow]Warning:[/yellow] Generated code may not be valid TikZ")
        
        # Display the generated code
        syntax = _get_syntax(tikz_code, "latex", theme="monokai", line_numbers=True)
        console.print(_get_panel(syntax, title="Generated TikZ Code", border_style="green"))
        
        # Save to file if output path specified
        if output:
            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(tikz_code)
            console.print(f"\n[green]TikZ code saved to:[/green] {output}")
            
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)
    except Exception as e:
        console.print(f"[red]TikZ generation failed:[/red] {e}")
        raise SystemExit(1)
