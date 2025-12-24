"""Common CLI utilities for interactive sessions.

Provides shared functionality for:
- Diff display with Rich color coding
- Interactive action prompts
- Session summary display
- Signal handling for graceful shutdown
- LaTeX formatting
- Editor integration
"""

from __future__ import annotations

import os
import signal
import subprocess
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Optional

if TYPE_CHECKING:
    from rich.console import Console


# =============================================================================
# Lazy Rich imports
# =============================================================================

def _get_console():
    """Lazy import of rich Console."""
    from rich.console import Console
    return Console()


def _get_panel(*args, **kwargs):
    """Lazy import of rich Panel."""
    from rich.panel import Panel
    return Panel(*args, **kwargs)


def _get_table(*args, **kwargs):
    """Lazy import of rich Table."""
    from rich.table import Table
    return Table(*args, **kwargs)


def _get_syntax(*args, **kwargs):
    """Lazy import of rich Syntax."""
    from rich.syntax import Syntax
    return Syntax(*args, **kwargs)


def _get_prompt():
    """Lazy import of rich Prompt."""
    from rich.prompt import Prompt
    return Prompt


# =============================================================================
# Action Enums
# =============================================================================

class ReviewAction(str, Enum):
    """User action for a review suggestion."""
    APPROVE = "approve"
    REJECT = "reject"
    SKIP = "skip"
    EDIT = "edit"
    QUIT = "quit"


class SimpleAction(str, Enum):
    """Simple approve/skip/quit actions."""
    APPROVE = "approve"
    EDIT = "edit"
    SKIP = "skip"
    QUIT = "quit"


# =============================================================================
# Diff Display
# =============================================================================

def display_diff(diff: str, console: "Console") -> None:
    """Display a diff with color coding using Rich.
    
    Args:
        diff: Unified diff string
        console: Rich console for output
    """
    if not diff or not diff.strip():
        console.print("[dim]No changes[/dim]")
        return
    
    syntax = _get_syntax(diff, "diff", theme="monokai", line_numbers=False)
    console.print(syntax)


def display_content_panel(
    content: str,
    title: str,
    console: "Console",
    language: str = "latex",
    border_style: str = "cyan",
) -> None:
    """Display content in a Rich panel with syntax highlighting.
    
    Args:
        content: Content to display
        title: Panel title
        console: Rich console for output
        language: Syntax highlighting language
        border_style: Panel border style
    """
    syntax = _get_syntax(content, language, theme="monokai", line_numbers=False)
    console.print(_get_panel(syntax, title=title, border_style=border_style))


# =============================================================================
# Action Prompts
# =============================================================================

def prompt_approve_edit_skip_quit(console: "Console") -> SimpleAction:
    """Prompt for approve/edit/skip/quit action.
    
    Standard prompt for content approval workflows.
    
    Args:
        console: Rich console for output
        
    Returns:
        The user's chosen action
    """
    console.print("\n[bold]Actions:[/bold]")
    console.print("  [green]a[/green]pprove - Apply this change")
    console.print("  [blue]e[/blue]dit    - Edit in editor before applying")
    console.print("  [yellow]s[/yellow]kip    - Skip this file")
    console.print("  [dim]q[/dim]uit    - Exit session")
    
    Prompt = _get_prompt()
    
    try:
        choice = Prompt.ask(
            "\nAction",
            choices=["a", "e", "s", "q", "approve", "edit", "skip", "quit"],
            default="a"
        ).lower()
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted[/yellow]")
        return SimpleAction.QUIT
    
    if choice in ["a", "approve"]:
        return SimpleAction.APPROVE
    elif choice in ["e", "edit"]:
        return SimpleAction.EDIT
    elif choice in ["s", "skip"]:
        return SimpleAction.SKIP
    else:
        return SimpleAction.QUIT


def prompt_full_review(console: "Console") -> ReviewAction:
    """Prompt for full review action including reject.
    
    Used for QA review workflows where suggestions can be stored.
    
    Args:
        console: Rich console for output
        
    Returns:
        The user's chosen action
    """
    console.print("\n[bold]Actions:[/bold]")
    console.print("  [green]a[/green]pprove - Apply this change")
    console.print("  [red]r[/red]eject  - Store for later, don't apply")
    console.print("  [yellow]s[/yellow]kip    - Skip without storing")
    console.print("  [blue]e[/blue]dit    - Open file in editor")
    console.print("  [dim]q[/dim]uit    - Exit review session (or Ctrl+C)")
    
    Prompt = _get_prompt()
    
    while True:
        try:
            choice = Prompt.ask(
                "\nAction",
                choices=["a", "r", "s", "e", "q", "approve", "reject", "skip", "edit", "quit"],
                default="s"
            ).lower()
        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted[/yellow]")
            return ReviewAction.QUIT
        
        if choice in ["a", "approve"]:
            return ReviewAction.APPROVE
        elif choice in ["r", "reject"]:
            return ReviewAction.REJECT
        elif choice in ["s", "skip"]:
            return ReviewAction.SKIP
        elif choice in ["e", "edit"]:
            return ReviewAction.EDIT
        elif choice in ["q", "quit"]:
            return ReviewAction.QUIT


def prompt_apply_skip(console: "Console") -> bool:
    """Simple apply/skip prompt after editing.
    
    Args:
        console: Rich console for output
        
    Returns:
        True if apply, False if skip
    """
    console.print("\n[bold]Actions:[/bold]")
    console.print("  [green]a[/green]pply  - Write edited content to file")
    console.print("  [yellow]s[/yellow]kip   - Discard changes")
    
    Prompt = _get_prompt()
    
    try:
        choice = Prompt.ask(
            "Action",
            choices=["a", "s", "apply", "skip"],
            default="a"
        ).lower()
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted[/yellow]")
        return False
    
    return choice in ["a", "apply"]


def prompt_apply_cancel(console: "Console") -> bool:
    """Apply/cancel prompt for confirmation.
    
    Args:
        console: Rich console for output
        
    Returns:
        True if apply, False if cancel
    """
    console.print("\n[bold]Actions:[/bold]")
    console.print("  [green]a[/green]pply  - Write edited content to file")
    console.print("  [yellow]c[/yellow]ancel - Discard changes")
    
    Prompt = _get_prompt()
    
    try:
        choice = Prompt.ask(
            "Action",
            choices=["a", "c", "apply", "cancel"],
            default="a"
        ).lower()
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted[/yellow]")
        return False
    
    return choice in ["a", "apply"]


# =============================================================================
# Session Summary
# =============================================================================

@dataclass
class SessionStats:
    """Statistics for an interactive session."""
    processed: int = 0
    passed: int = 0
    approved: int = 0
    rejected: int = 0
    skipped: int = 0
    generated: int = 0
    failed: int = 0
    
    # Custom fields for specific sessions
    extra: dict = field(default_factory=dict)


def display_session_summary(
    stats: SessionStats | dict,
    console: "Console",
    title: str = "Session Summary",
) -> None:
    """Display summary of an interactive session.
    
    Args:
        stats: Session statistics (SessionStats or dict)
        console: Rich console for output
        title: Summary title
    """
    console.print(f"\n[bold]═══ {title} ═══[/bold]")
    
    table = _get_table(show_header=False, box=None)
    table.add_column("Metric", style="dim")
    table.add_column("Value", justify="right")
    
    # Convert to dict if SessionStats
    if isinstance(stats, SessionStats):
        data = {
            "processed": stats.processed,
            "passed": stats.passed,
            "approved": stats.approved,
            "rejected": stats.rejected,
            "skipped": stats.skipped,
            "generated": stats.generated,
            "failed": stats.failed,
            **stats.extra,
        }
    else:
        data = stats
    
    # Standard metrics with colors
    metric_styles = {
        "processed": ("Files processed", None),
        "problems_reviewed": ("Problems reviewed", None),
        "passed": ("Passed", "green"),
        "approved": ("Approved", "green"),
        "approved_count": ("Approved", "green"),
        "rejected": ("Rejected", "red"),
        "rejected_count": ("Rejected", "red"),
        "skipped": ("Skipped", "yellow"),
        "skipped_count": ("Skipped", "yellow"),
        "generated": ("Generated", None),
        "failed": ("Failed", "yellow"),
        "suggestions_made": ("Suggestions made", None),
    }
    
    for key, value in data.items():
        if value == 0 and key not in ["processed", "problems_reviewed"]:
            continue  # Skip zero values except main counts
        
        if key in metric_styles:
            label, color = metric_styles[key]
            if color:
                table.add_row(label, f"[{color}]{value}[/{color}]")
            else:
                table.add_row(label, str(value))
        elif key not in ["session_id", "interrupted", "extra"]:
            # Custom metrics
            label = key.replace("_", " ").title()
            table.add_row(label, str(value))
    
    console.print(table)


# =============================================================================
# Signal Handling
# =============================================================================

@contextmanager
def graceful_shutdown(console: "Console", message: str = "Shutdown requested."):
    """Context manager for graceful shutdown handling.
    
    Sets up signal handlers for SIGINT and SIGTERM, and provides
    a shutdown flag that can be checked in loops.
    
    Args:
        console: Rich console for output
        message: Message to display on shutdown
        
    Yields:
        A callable that returns True if shutdown was requested
        
    Example:
        with graceful_shutdown(console) as is_shutdown:
            for item in items:
                if is_shutdown():
                    break
                process(item)
    """
    import sys
    
    shutdown_requested = False
    
    def signal_handler(signum, frame):
        nonlocal shutdown_requested
        shutdown_requested = True
        console.print(f"\n[yellow]{message}[/yellow]")
    
    original_sigint = signal.signal(signal.SIGINT, signal_handler)
    # SIGTERM is not available on Windows
    original_sigterm = None
    if sys.platform != "win32":
        original_sigterm = signal.signal(signal.SIGTERM, signal_handler)
    
    def is_shutdown() -> bool:
        return shutdown_requested
    
    def request_shutdown():
        nonlocal shutdown_requested
        shutdown_requested = True
    
    # Attach request_shutdown to the callable for manual triggering
    is_shutdown.request = request_shutdown
    
    try:
        yield is_shutdown
    finally:
        signal.signal(signal.SIGINT, original_sigint)
        if original_sigterm is not None:
            signal.signal(signal.SIGTERM, original_sigterm)


# =============================================================================
# Editor Integration
# =============================================================================

def _get_default_editor() -> str:
    """Get the default editor for the current platform.
    
    Returns:
        Editor command string
    """
    import sys
    
    # Check environment variables first
    editor = os.environ.get("EDITOR") or os.environ.get("VISUAL")
    if editor:
        return editor
    
    # Platform-specific defaults
    if sys.platform == "win32":
        return "notepad"
    else:
        return "vim"


def open_in_editor(file_path: str) -> bool:
    """Open a file in the default editor.
    
    Args:
        file_path: Path to the file to edit
        
    Returns:
        True if editor was opened successfully, False otherwise
    """
    editor = _get_default_editor()
    
    try:
        subprocess.run([editor, file_path], check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def open_content_in_editor(
    original_path: str,
    content: str,
    console: "Console",
) -> tuple[bool, Optional[str]]:
    """Open content in editor for review/modification.
    
    Creates a temp file with the content, opens in editor,
    and returns the (possibly modified) content after editor closes.
    
    Args:
        original_path: Path to the original file (for extension detection)
        content: The content to edit
        console: Rich console for output
        
    Returns:
        Tuple of (success, edited_content). If user saves and exits,
        returns (True, content). If error, returns (False, None).
    """
    editor = _get_default_editor()
    suffix = Path(original_path).suffix or ".txt"
    
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=suffix,
            prefix="vbagent_edit_",
            delete=False
        ) as f:
            f.write(content)
            temp_path = f.name
        
        console.print(f"[dim]Opening editor ({editor})... Save and exit to apply changes.[/dim]")
        result = subprocess.run([editor, temp_path])
        
        if result.returncode != 0:
            console.print(f"[yellow]Editor exited with code {result.returncode}[/yellow]")
        
        with open(temp_path, "r") as f:
            edited_content = f.read()
        
        os.unlink(temp_path)
        return True, edited_content
        
    except (IOError, OSError, FileNotFoundError) as e:
        console.print(f"[red]Error opening editor: {e}[/red]")
        if 'temp_path' in locals() and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except OSError:
                pass
        return False, None


# =============================================================================
# LaTeX Formatting
# =============================================================================

def format_latex(content: str) -> str:
    """Format LaTeX content with proper indentation.
    
    Applies consistent indentation to LaTeX environments like:
    - begin/end blocks (solution, align*, tasks, tikzpicture, center, tabular)
    - Nested structures
    
    Args:
        content: Raw LaTeX content
        
    Returns:
        Formatted LaTeX with proper indentation
    """
    import re
    
    if not content:
        return content
    
    lines = content.split('\n')
    formatted_lines = []
    indent_level = 0
    indent_str = "    "  # 4 spaces
    
    begin_pattern = re.compile(r'^\s*\\begin\{(\w+)\}')
    end_pattern = re.compile(r'^\s*\\end\{(\w+)\}')
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


# =============================================================================
# TeX File Discovery
# =============================================================================

def discover_tex_files(output_path: Path) -> list[Path]:
    """Discover all .tex files in a directory or return single file.
    
    Searches:
    - Direct .tex files in the directory
    - Agentic-style structure (scans/, variants/)
    - Subdirectories one level deep
    
    Args:
        output_path: Path to directory or single file
        
    Returns:
        List of unique .tex file paths
    """
    tex_files: list[Path] = []
    
    # Check if it's a single file
    if output_path.is_file() and output_path.suffix == ".tex":
        return [output_path]
    
    # Check for .tex files directly in the directory
    if output_path.exists():
        tex_files.extend(output_path.glob("*.tex"))
    
    # Also check agentic-style structure (scans/ and variants/)
    scans_dir = output_path / "scans"
    if scans_dir.exists():
        tex_files.extend(scans_dir.glob("*.tex"))
    
    variants_dir = output_path / "variants"
    if variants_dir.exists():
        for variant_type_dir in variants_dir.iterdir():
            if variant_type_dir.is_dir():
                tex_files.extend(variant_type_dir.glob("*.tex"))
    
    # Also check subdirectories one level deep
    for subdir in output_path.iterdir():
        if subdir.is_dir() and not subdir.name.startswith('.'):
            tex_files.extend(subdir.glob("*.tex"))
    
    # Remove duplicates while preserving order
    seen: set[Path] = set()
    unique_tex_files: list[Path] = []
    for f in tex_files:
        if f not in seen:
            seen.add(f)
            unique_tex_files.append(f)
    
    return unique_tex_files


def natural_sort_key(path: Path | str) -> list:
    """Generate a natural sort key for paths with numbers.
    
    Sorts Problem_1, Problem_2, ..., Problem_10 correctly.
    
    Args:
        path: Path or string to generate key for
        
    Returns:
        Sort key list
    """
    import re
    s = str(path)
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r'(\d+)', s)]


# =============================================================================
# Content Extraction
# =============================================================================

def extract_problem_solution(content: str) -> tuple[str, str]:
    """Extract problem statement and solution from LaTeX content.
    
    If no solution environment exists, returns the full content as problem.
    If no \\item marker exists before solution, returns content before solution.
    
    Args:
        content: Full LaTeX content
        
    Returns:
        Tuple of (problem, solution)
    """
    import re
    
    # Extract primary solution (first solution environment)
    solution_match = re.search(
        r'\\begin\{solution\}(.*?)\\end\{solution\}',
        content,
        re.DOTALL
    )
    solution = solution_match.group(1).strip() if solution_match else ""
    
    # Extract problem (everything from \item to \begin{solution})
    if solution_match:
        # There's a solution, extract problem before it
        problem_match = re.search(
            r'\\item\s*(.*?)(?=\\begin\{solution\})',
            content,
            re.DOTALL
        )
        problem = problem_match.group(1).strip() if problem_match else content[:solution_match.start()].strip()
    else:
        # No solution, try to extract from \item or return full content
        item_match = re.search(r'\\item\s*(.*)', content, re.DOTALL)
        problem = item_match.group(1).strip() if item_match else content.strip()
    
    return problem, solution


# =============================================================================
# Image Discovery
# =============================================================================

def find_image_for_problem(
    tex_file: Path,
    images_dir: Optional[str | Path] = None,
    extensions: tuple[str, ...] = (".png", ".jpg", ".jpeg", ".webp", ".gif"),
) -> Optional[Path]:
    """Find the corresponding image file for a tex file.
    
    Searches for an image with the same base name as the tex file
    in the specified images directory.
    
    Args:
        tex_file: Path to the .tex file
        images_dir: Directory to search for images (optional)
        extensions: Image file extensions to search for
        
    Returns:
        Path to the image file if found, None otherwise
        
    Example:
        tex_file = Path("src/src_tex/problem_1.tex")
        images_dir = "src/src_images"
        # Will look for: src/src_images/problem_1.png, problem_1.jpg, etc.
    """
    if images_dir is None:
        return None
    
    images_path = Path(images_dir)
    if not images_path.exists():
        return None
    
    # Get the base name without extension
    base_name = tex_file.stem
    
    # Search for image with matching name
    for ext in extensions:
        image_path = images_path / f"{base_name}{ext}"
        if image_path.exists():
            return image_path
        
        # Also try case-insensitive match
        image_path_upper = images_path / f"{base_name}{ext.upper()}"
        if image_path_upper.exists():
            return image_path_upper
    
    # Try glob pattern for case-insensitive search
    for ext in extensions:
        pattern = f"{base_name}.*"
        matches = list(images_path.glob(pattern))
        for match in matches:
            if match.suffix.lower() in extensions:
                return match
    
    return None


def discover_images_dir(tex_dir: Path) -> Optional[Path]:
    """Auto-discover images directory based on tex directory structure.
    
    Common patterns:
    - src/src_tex/ -> src/src_images/
    - tex/ -> images/
    - problems/ -> images/
    
    Args:
        tex_dir: Directory containing tex files
        
    Returns:
        Path to images directory if found, None otherwise
    """
    # Common sibling directory patterns
    patterns = [
        ("src_tex", "src_images"),
        ("tex", "images"),
        ("problems", "images"),
        ("questions", "images"),
    ]
    
    dir_name = tex_dir.name
    parent = tex_dir.parent
    
    for tex_pattern, img_pattern in patterns:
        if dir_name == tex_pattern:
            candidate = parent / img_pattern
            if candidate.exists():
                return candidate
    
    # Check for images/ sibling
    images_sibling = parent / "images"
    if images_sibling.exists():
        return images_sibling
    
    # Check for images/ in same directory
    images_child = tex_dir / "images"
    if images_child.exists():
        return images_child
    
    return None
