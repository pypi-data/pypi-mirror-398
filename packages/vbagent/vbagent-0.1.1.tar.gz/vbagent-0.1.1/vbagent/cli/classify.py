"""CLI command for classifying physics question images.

Stage 1: Classify physics question image to extract metadata.
"""

from pathlib import Path

import click


def _get_console():
    """Lazy import of rich Console."""
    from rich.console import Console
    return Console()


def _get_table(*args, **kwargs):
    """Lazy import of rich Table."""
    from rich.table import Table
    return Table(*args, **kwargs)


def format_result_table(result) -> "Table":
    """Format classification result as a rich table."""
    table = _get_table(title="Classification Result", show_header=True)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Question Type", result.question_type)
    table.add_row("Difficulty", result.difficulty)
    table.add_row("Topic", result.topic)
    table.add_row("Subtopic", result.subtopic)
    table.add_row("Has Diagram", "Yes" if result.has_diagram else "No")
    
    if result.diagram_type:
        table.add_row("Diagram Type", result.diagram_type)
    
    if result.num_options is not None:
        table.add_row("Number of Options", str(result.num_options))
    
    table.add_row("Estimated Marks", str(result.estimated_marks))
    table.add_row("Requires Calculus", "Yes" if result.requires_calculus else "No")
    table.add_row("Confidence", f"{result.confidence:.2%}")
    
    if result.key_concepts:
        table.add_row("Key Concepts", ", ".join(result.key_concepts))
    
    return table


CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}


@click.command(context_settings=CONTEXT_SETTINGS)
@click.option(
    "-i", "--image",
    required=True,
    type=click.Path(exists=True),
    help="Path to the physics question image file"
)
@click.option(
    "-o", "--output",
    type=click.Path(),
    help="Output JSON file path for saving results"
)
@click.option(
    "--json", "as_json",
    is_flag=True,
    help="Output result as JSON to stdout"
)
def classify(image: str, output: str | None, as_json: bool):
    """Stage 1: Classify physics question image.
    
    Analyzes a physics question image and extracts metadata including:
    question type, difficulty, topic, subtopic, diagram presence, etc.
    
    \b
    Examples:
        vbagent classify -i question.png
        vbagent classify --image images/q1.png --json
        vbagent classify -i images/q1.png -o result.json
    """
    # Lazy imports - only load heavy dependencies when command runs
    from vbagent.agents.classifier import classify as classify_image
    
    console = _get_console()
    
    try:
        # Run classification
        with console.status("[bold green]Classifying image..."):
            result = classify_image(image)
        
        # Output as JSON if requested
        if as_json:
            click.echo(result.model_dump_json(indent=2))
        else:
            # Display rich formatted output
            console.print(format_result_table(result))
        
        # Save to file if output path specified
        if output:
            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(result.model_dump_json(indent=2))
            console.print(f"\n[green]Results saved to:[/green] {output}")
            
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)
    except Exception as e:
        console.print(f"[red]Classification failed:[/red] {e}")
        raise SystemExit(1)
