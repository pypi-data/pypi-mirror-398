"""CLI command for scanning physics question images to extract LaTeX.

Stage 2: Extract LaTeX from image using type-specific prompts.
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


VALID_QUESTION_TYPES = ["mcq_sc", "mcq_mc", "subjective", "assertion_reason", "passage", "match"]


def display_scan_result(result, console) -> None:
    """Display scan result with syntax highlighting."""
    # Show LaTeX with syntax highlighting
    syntax = _get_syntax(result.latex, "latex", theme="monokai", line_numbers=True)
    console.print(_get_panel(syntax, title="Extracted LaTeX", border_style="green"))
    
    # Show metadata
    if result.has_diagram:
        console.print(f"\n[yellow]Has Diagram:[/yellow] Yes")
        if result.raw_diagram_description:
            console.print(f"[yellow]Diagram Type:[/yellow] {result.raw_diagram_description}")


CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}


@click.command(context_settings=CONTEXT_SETTINGS)
@click.option(
    "-i", "--image",
    type=click.Path(exists=True),
    help="Path to the physics question image file"
)
@click.option(
    "-t", "--tex",
    type=click.Path(exists=True),
    help="Path to existing TeX file (for re-processing)"
)
@click.option(
    "--type", "question_type",
    type=click.Choice(VALID_QUESTION_TYPES),
    help="Override question type (skips classification)"
)
@click.option(
    "-o", "--output",
    type=click.Path(),
    help="Output TeX file path for saving results"
)
def scan(image: str | None, tex: str | None, question_type: str | None, output: str | None):
    """Stage 2: Extract LaTeX from physics question image.
    
    Runs classification first (unless --type provided), then extracts LaTeX
    using the appropriate type-specific prompt.
    
    \b
    Examples:
        vbagent scan -i question.png
        vbagent scan --image images/q1.png --output output.tex
        vbagent scan -i images/q1.png --type mcq_sc
        vbagent scan -i q.png -t existing.tex -o updated.tex
    """
    # Lazy imports - only load heavy dependencies when command runs
    from vbagent.agents.classifier import classify as classify_image
    from vbagent.agents.scanner import scan as scan_image, scan_with_type
    from vbagent.models.scan import ScanResult
    
    console = _get_console()
    
    # Validate input
    if not image and not tex:
        console.print("[red]Error:[/red] Either --image or --tex must be provided")
        raise SystemExit(1)
    
    if tex and not image:
        console.print("[red]Error:[/red] --tex requires --image for scanning")
        raise SystemExit(1)
    
    try:
        result: ScanResult
        
        if question_type:
            # Skip classification, use provided type
            console.print(f"[cyan]Using question type:[/cyan] {question_type}")
            with console.status("[bold green]Scanning image..."):
                result = scan_with_type(image, question_type)
        else:
            # Run classification first
            with console.status("[bold green]Classifying image..."):
                classification = classify_image(image)
            
            console.print(f"[cyan]Detected type:[/cyan] {classification.question_type}")
            console.print(f"[cyan]Confidence:[/cyan] {classification.confidence:.2%}")
            
            # Then scan with classified type
            with console.status("[bold green]Scanning image..."):
                result = scan_image(image, classification)
        
        # Display result
        display_scan_result(result, console)
        
        # Save to file if output path specified
        if output:
            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(result.latex)
            console.print(f"\n[green]LaTeX saved to:[/green] {output}")
            
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)
    except Exception as e:
        console.print(f"[red]Scan failed:[/red] {e}")
        raise SystemExit(1)
