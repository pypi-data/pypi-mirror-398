"""CLI command for generating alternate solutions.

Generates alternative solution methods for physics problems
while maintaining the same final answer.
"""

import json
import re
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


def load_ideas(ideas_path: str, idea_result_cls):
    """Load ideas from a JSON file.
    
    Args:
        ideas_path: Path to the ideas JSON file
        idea_result_cls: The IdeaResult class to use
        
    Returns:
        IdeaResult or None if file doesn't exist or is invalid
    """
    try:
        content = Path(ideas_path).read_text()
        data = json.loads(content)
        return idea_result_cls(**data)
    except (FileNotFoundError, json.JSONDecodeError, TypeError):
        return None


CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}


@click.command(context_settings=CONTEXT_SETTINGS)
@click.option(
    "-t", "--tex",
    required=True,
    type=click.Path(exists=True),
    help="Path to TeX file containing problem and solution"
)
@click.option(
    "--ideas",
    type=click.Path(exists=True),
    help="Path to ideas JSON file from idea command"
)
@click.option(
    "-n", "--count",
    default=1,
    type=int,
    help="Number of alternate solutions to generate (default: 1)"
)
@click.option(
    "-o", "--output",
    type=click.Path(),
    help="Output TeX file path for saving results"
)
def alternate(tex: str, ideas: str | None, count: int, output: str | None):
    """Generate alternative solution methods for physics problems.
    
    Creates different valid solution approaches that arrive at the same
    final answer as the original solution.
    
    The TeX file should contain the problem (starting with \\item) and
    solution (in a solution environment).
    
    \b
    Examples:
        vbagent alternate -t problem.tex
        vbagent alternate --tex problem.tex --ideas ideas.json
        vbagent alternate -t problem.tex -n 2 -o alternates.tex
        vbagent alternate -t scans/Problem_1.tex --count 3 --output alt.tex
    """
    # Lazy imports - only load heavy dependencies when command actually runs
    from vbagent.agents.alternate import generate_alternate
    from vbagent.models.idea import IdeaResult
    
    console = _get_console()
    
    try:
        # Parse the TeX file
        problem, solution = parse_tex_file(tex)
        
        if not problem:
            console.print("[red]Error:[/red] Could not extract problem from TeX file")
            raise SystemExit(1)
        
        if not solution:
            console.print("[red]Error:[/red] Could not extract solution from TeX file")
            raise SystemExit(1)
        
        # Load ideas if provided
        ideas_result = load_ideas(ideas, IdeaResult) if ideas else None
        
        if ideas and not ideas_result:
            console.print(f"[yellow]Warning:[/yellow] Could not load ideas from {ideas}")
        
        # Generate alternate solutions
        all_alternates = []
        
        for i in range(count):
            with console.status(f"[bold green]Generating alternate solution {i + 1}/{count}..."):
                alt_solution = generate_alternate(problem, solution, ideas_result)
                all_alternates.append(alt_solution)
            
            # Display the result
            console.print(_get_panel(
                alt_solution,
                title=f"Alternate Solution {i + 1}",
                border_style="green"
            ))
        
        # Save to file if output path specified
        if output:
            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Combine all alternates with separators
            combined = "\n\n% --- Alternate Solution ---\n\n".join(all_alternates)
            output_path.write_text(combined)
            console.print(f"\n[green]Results saved to:[/green] {output}")
            
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)
    except Exception as e:
        console.print(f"[red]Alternate solution generation failed:[/red] {e}")
        raise SystemExit(1)
