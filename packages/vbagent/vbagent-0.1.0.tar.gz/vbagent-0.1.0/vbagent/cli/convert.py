"""CLI command for converting physics questions between formats.

Converts questions between MCQ (single/multiple correct), subjective,
and integer type formats.
"""

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


def _get_syntax(*args, **kwargs):
    """Lazy import of rich Syntax."""
    from rich.syntax import Syntax
    return Syntax(*args, **kwargs)


def _format_latex(content: str) -> str:
    """Format LaTeX content with proper indentation.
    
    Applies consistent indentation to LaTeX environments like:
    - begin/end blocks (solution, align*, tasks, tikzpicture, center, tabular)
    - Nested structures
    
    Args:
        content: Raw LaTeX content
        
    Returns:
        Formatted LaTeX with proper indentation
    """
    if not content:
        return content
    
    lines = content.split('\n')
    formatted_lines = []
    indent_level = 0
    indent_str = "    "  # 4 spaces
    
    # Environments that increase indentation
    begin_pattern = re.compile(r'^\s*\\begin\{(\w+)\}')
    end_pattern = re.compile(r'^\s*\\end\{(\w+)\}')
    
    # Special patterns
    def_pattern = re.compile(r'^\s*\\def\\')
    
    for line in lines:
        stripped = line.strip()
        
        if not stripped:
            formatted_lines.append('')
            continue
        
        # Check for \end{} - decrease indent before this line
        end_match = end_pattern.match(stripped)
        if end_match:
            indent_level = max(0, indent_level - 1)
        
        # Apply current indentation
        if stripped.startswith('\\item') and indent_level == 0:
            # \item at root level stays at root
            formatted_lines.append(stripped)
        elif def_pattern.match(stripped) and indent_level == 0:
            # \def at root level stays at root
            formatted_lines.append(stripped)
        else:
            formatted_lines.append(indent_str * indent_level + stripped)
        
        # Check for \begin{} - increase indent after this line
        begin_match = begin_pattern.match(stripped)
        if begin_match:
            indent_level += 1
    
    return '\n'.join(formatted_lines)


VALID_FORMAT_CHOICES = ["mcq_sc", "mcq_mc", "subjective", "integer"]


def parse_tex_content(tex_path: str) -> str:
    """Read and return the content of a TeX file."""
    return Path(tex_path).read_text()


def detect_format_from_latex(latex: str) -> str:
    """Attempt to detect the format of a LaTeX question."""
    has_tasks = r"\begin{tasks}" in latex or r"\task" in latex
    
    if has_tasks:
        task_count = latex.count(r"\task")
        if re.search(r"more than one|multiple|one or more", latex, re.IGNORECASE):
            return "mcq_mc"
        return "mcq_sc"
    
    if re.search(r"nearest integer|integer value|numerical answer", latex, re.IGNORECASE):
        return "integer"
    
    return "subjective"


def display_conversion_result(result: str, source_format: str, target_format: str, console) -> None:
    """Display conversion result with syntax highlighting."""
    syntax = _get_syntax(result, "latex", theme="monokai", line_numbers=True)
    console.print(_get_panel(
        syntax,
        title=f"Converted: {source_format} → {target_format}",
        border_style="green"
    ))


CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}


@click.command(context_settings=CONTEXT_SETTINGS)
@click.option(
    "-i", "--image",
    type=click.Path(exists=True),
    help="Path to physics question image (will be scanned first)"
)
@click.option(
    "-t", "--tex",
    type=click.Path(exists=True),
    help="Path to TeX file containing the question"
)
@click.option(
    "--from", "source_format",
    type=click.Choice(VALID_FORMAT_CHOICES),
    help="Source format (auto-detected if not specified)"
)
@click.option(
    "--to", "target_format",
    required=True,
    type=click.Choice(VALID_FORMAT_CHOICES),
    help="Target format for conversion"
)
@click.option(
    "-o", "--output",
    type=click.Path(),
    help="Output TeX file path for saving results"
)
def convert(
    image: str | None,
    tex: str | None,
    source_format: str | None,
    target_format: str,
    output: str | None
):
    """Convert physics questions between different formats.
    
    \b
    Supported Formats:
        mcq_sc      - Multiple Choice (Single Correct)
        mcq_mc      - Multiple Choice (Multiple Correct)
        subjective  - Subjective/Descriptive
        integer     - Integer Type
    
    \b
    Examples:
        vbagent convert -t problem.tex --to subjective
        vbagent convert --tex mcq.tex --from mcq_sc --to subjective
        vbagent convert -t mcq.tex --to integer -o integer.tex
        vbagent convert -i image.png --to mcq_sc --output mcq.tex
    """
    # Lazy imports - only load heavy dependencies when command runs
    from vbagent.agents.converter import convert_format
    from vbagent.agents.classifier import classify as classify_image
    from vbagent.agents.scanner import scan as scan_image
    
    console = _get_console()
    
    # Validate input
    if not image and not tex:
        console.print("[red]Error:[/red] Either --image or --tex must be provided")
        raise SystemExit(1)
    
    try:
        source_latex: str
        detected_format: str
        
        if image:
            with console.status("[bold green]Classifying image..."):
                classification = classify_image(image)
            
            console.print(f"[cyan]Detected type:[/cyan] {classification.question_type}")
            
            with console.status("[bold green]Scanning image..."):
                scan_result = scan_image(image, classification)
            
            source_latex = scan_result.latex
            detected_format = classification.question_type
            
            format_mapping = {
                "mcq_sc": "mcq_sc",
                "mcq_mc": "mcq_mc",
                "subjective": "subjective",
                "assertion_reason": "mcq_sc",
                "passage": "subjective",
                "match": "mcq_mc",
            }
            detected_format = format_mapping.get(detected_format, "subjective")
            
        else:
            source_latex = parse_tex_content(tex)
            detected_format = detect_format_from_latex(source_latex)
        
        actual_source_format = source_format or detected_format
        
        console.print(f"[cyan]Source format:[/cyan] {actual_source_format}")
        console.print(f"[cyan]Target format:[/cyan] {target_format}")
        
        if actual_source_format == target_format:
            console.print("[yellow]Warning:[/yellow] Source and target formats are the same")
        
        with console.status("[bold green]Converting format..."):
            result = convert_format(source_latex, actual_source_format, target_format)
        
        # Format the output with proper indentation
        formatted_result = _format_latex(result)
        
        display_conversion_result(formatted_result, actual_source_format, target_format, console)
        
        if output:
            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(formatted_result)
            console.print(f"\n[green]Converted question saved to:[/green] {output}")
            
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)
    except Exception as e:
        console.print(f"[red]Conversion failed:[/red] {e}")
        raise SystemExit(1)
