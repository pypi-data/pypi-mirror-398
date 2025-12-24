"""CLI command for extracting physics concepts and ideas.

Analyzes physics problems and solutions to extract core concepts,
formulas, techniques, and difficulty factors.
"""

import re
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


def parse_tex_file(tex_path: str) -> tuple[str, str]:
    """Parse a TeX file to extract problem and solution.
    
    Expects the file to contain \\item for the problem and
    \\begin{solution}...\\end{solution} for the solution.
    
    Args:
        tex_path: Path to the TeX file
        
    Returns:
        Tuple of (problem, solution)
    """
    content = Path(tex_path).read_text()
    
    # Extract problem (everything from \item to \begin{solution})
    problem_match = re.search(
        r'\\item\s*(.*?)(?=\\begin\{solution\})',
        content,
        re.DOTALL
    )
    problem = problem_match.group(1).strip() if problem_match else content
    
    # Extract solution
    solution_match = re.search(
        r'\\begin\{solution\}(.*?)\\end\{solution\}',
        content,
        re.DOTALL
    )
    solution = solution_match.group(1).strip() if solution_match else ""
    
    return problem, solution


def format_result_table(result) -> "Table":
    """Format idea extraction result as a rich table."""
    table = _get_table(title="Extracted Ideas", show_header=True)
    table.add_column("Category", style="cyan", width=20)
    table.add_column("Items", style="green")
    
    if result.concepts:
        table.add_row("Concepts", "\n".join(f"• {c}" for c in result.concepts))
    else:
        table.add_row("Concepts", "[dim]None extracted[/dim]")
    
    if result.formulas:
        table.add_row("Formulas", "\n".join(f"• {f}" for f in result.formulas))
    else:
        table.add_row("Formulas", "[dim]None extracted[/dim]")
    
    if result.techniques:
        table.add_row("Techniques", "\n".join(f"• {t}" for t in result.techniques))
    else:
        table.add_row("Techniques", "[dim]None extracted[/dim]")
    
    if result.difficulty_factors:
        table.add_row("Difficulty Factors", "\n".join(f"• {d}" for d in result.difficulty_factors))
    else:
        table.add_row("Difficulty Factors", "[dim]None extracted[/dim]")
    
    return table


CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}


@click.command(context_settings=CONTEXT_SETTINGS)
@click.option(
    "-t", "--tex",
    required=True,
    type=click.Path(exists=True),
    help="Path to TeX file containing problem and solution"
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
def idea(tex: str, output: str | None, as_json: bool):
    """Extract physics concepts and problem-solving ideas.
    
    Analyzes a physics problem and its solution to identify:
    - Primary physics concepts being tested
    - Key formulas and equations used
    - Problem-solving techniques employed
    - Factors that make the problem challenging
    
    The TeX file should contain the problem (starting with \\item) and
    solution (in a solution environment).
    
    \b
    Examples:
        vbagent idea -t problem.tex
        vbagent idea --tex problem.tex --json
        vbagent idea -t problem.tex -o ideas.json
        vbagent idea -t scans/Problem_1.tex --output ideas/Problem_1.json
    """
    # Lazy imports - only load heavy dependencies when command runs
    from vbagent.agents.idea import extract_ideas
    
    console = _get_console()
    
    try:
        # Parse the TeX file
        problem, solution = parse_tex_file(tex)
        
        if not problem and not solution:
            console.print("[red]Error:[/red] Could not extract problem or solution from TeX file")
            raise SystemExit(1)
        
        # Run idea extraction
        with console.status("[bold green]Extracting ideas..."):
            result = extract_ideas(problem, solution)
        
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
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)
    except Exception as e:
        console.print(f"[red]Idea extraction failed:[/red] {e}")
        raise SystemExit(1)
