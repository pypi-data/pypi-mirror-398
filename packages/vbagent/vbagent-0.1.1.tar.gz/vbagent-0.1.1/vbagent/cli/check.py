"""CLI commands for QA review with interactive approval workflow.

Provides `check` command for random spot-checking of processed physics
questions with AI-powered quality review and diff-based suggestions.
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Optional

import click

# Import common utilities
from vbagent.cli.common import (
    ReviewAction,
    SimpleAction,
    display_diff,
    display_content_panel,
    display_session_summary,
    prompt_approve_edit_skip_quit,
    prompt_full_review,
    prompt_apply_skip,
    prompt_apply_cancel,
    graceful_shutdown,
    open_in_editor,
    open_content_in_editor,
    format_latex,
    discover_tex_files,
    natural_sort_key,
    extract_problem_solution,
    find_image_for_problem,
    _get_console,
    _get_panel,
    _get_table,
    _get_syntax,
    _get_prompt,
)

if TYPE_CHECKING:
    from rich.console import Console


def _get_text(*args, **kwargs):
    """Lazy import of rich Text."""
    from rich.text import Text
    return Text(*args, **kwargs)


# Alias for backward compatibility
open_suggested_in_editor = open_content_in_editor


def display_suggestion(suggestion, console: "Console") -> None:
    """Display a suggestion with all details.
    
    Args:
        suggestion: The suggestion to display
        console: Rich console for output
    """
    # Header with issue type and confidence
    confidence_color = "green" if suggestion.confidence >= 0.8 else "yellow" if suggestion.confidence >= 0.5 else "red"
    
    console.print(_get_panel(
        f"[bold]{suggestion.description}[/bold]\n\n"
        f"[dim]File:[/dim] {suggestion.file_path}\n"
        f"[dim]Type:[/dim] {suggestion.issue_type.value}\n"
        f"[dim]Confidence:[/dim] [{confidence_color}]{suggestion.confidence:.0%}[/{confidence_color}]",
        title=f"[cyan]Suggestion[/cyan]",
        border_style="cyan"
    ))
    
    # Reasoning
    console.print(f"\n[bold]Reasoning:[/bold]")
    console.print(suggestion.reasoning)
    
    # Diff
    console.print(f"\n[bold]Proposed Changes:[/bold]")
    display_diff(suggestion.diff, console)


def prompt_review_action(suggestion, console: "Console") -> ReviewAction:
    """Display suggestion and prompt user for action.
    
    Args:
        suggestion: The suggestion to review
        console: Rich console for output
        
    Returns:
        The user's chosen action
    """
    display_suggestion(suggestion, console)
    return prompt_full_review(console)


def apply_suggestion(suggestion, problem_id: str = ""):
    """Apply an approved suggestion to the file.
    
    Args:
        suggestion: The suggestion to apply
        problem_id: Problem ID for path resolution
        
    Returns:
        DiffResult with success status and error details if failed
    """
    from vbagent.models.diff import apply_diff_safe, DiffResult, DiffErrorType
    
    # Try to resolve the file path
    resolved_path = resolve_file_path(suggestion.file_path, problem_id)
    if not resolved_path:
        return DiffResult(
            success=False,
            error_type=DiffErrorType.FILE_NOT_FOUND,
            error_message=f"File not found: {suggestion.file_path}",
            original_preserved=True,
        )
    
    return apply_diff_safe(resolved_path, suggestion.diff)


def format_diff_error(result) -> str:
    """Format a diff error for display.
    
    Args:
        result: DiffResult with error information
        
    Returns:
        Human-readable error message
    """
    from vbagent.models.diff import DiffErrorType
    
    if result.success:
        return ""
    
    error_messages = {
        DiffErrorType.FILE_NOT_FOUND: "File not found",
        DiffErrorType.PERMISSION_DENIED: "Permission denied",
        DiffErrorType.DIFF_CONFLICT: "File has been modified since diff was generated",
        DiffErrorType.IO_ERROR: "I/O error occurred",
        DiffErrorType.INVALID_DIFF: "Invalid diff format",
    }
    
    base_msg = error_messages.get(result.error_type, "Unknown error")
    if result.error_message:
        return f"{base_msg}: {result.error_message}"
    return base_msg


def resolve_file_path(stored_path: str, problem_id: str) -> Optional[str]:
    """Resolve a stored file path to an actual file.
    
    Tries multiple strategies to find the file:
    1. Direct path (if absolute or exists relative to cwd)
    2. Look in common output directories (agentic/, output/)
    3. Search for problem_id directory and find file within
    
    Args:
        stored_path: The path stored in the database
        problem_id: The problem ID associated with this file
        
    Returns:
        Resolved path if found, None otherwise
    """
    # Strategy 1: Direct path
    if os.path.exists(stored_path):
        return stored_path
    
    # Strategy 2: Common output directories
    for base_dir in ["agentic", "output", "."]:
        candidate = os.path.join(base_dir, stored_path)
        if os.path.exists(candidate):
            return candidate
    
    # Strategy 3: Look for problem directory
    file_name = os.path.basename(stored_path)
    for base_dir in ["agentic", "output", "."]:
        problem_dir = os.path.join(base_dir, problem_id)
        if os.path.isdir(problem_dir):
            candidate = os.path.join(problem_dir, file_name)
            if os.path.exists(candidate):
                return candidate
    
    # Strategy 4: Search recursively (limited depth)
    for base_dir in ["agentic", "output"]:
        if not os.path.isdir(base_dir):
            continue
        for root, dirs, files in os.walk(base_dir):
            # Limit depth to 3 levels
            depth = root.replace(base_dir, "").count(os.sep)
            if depth > 3:
                dirs.clear()
                continue
            if file_name in files:
                candidate = os.path.join(root, file_name)
                # Prefer paths containing the problem_id
                if problem_id in root:
                    return candidate
    
    return None



def run_review_session(
    problems: list,
    store,
    console: "Console",
    output_dir: str = "agentic",
    session_id: Optional[str] = None,
) -> dict:
    """Run an interactive review session.
    
    Args:
        problems: List of problem contexts to review
        store: Version store for saving rejected suggestions
        console: Rich console for output
        output_dir: Output directory being reviewed (for resume capability)
        session_id: Optional existing session ID (for resume)
        
    Returns:
        Dictionary with session statistics
    """
    # Lazy imports for this helper function
    from vbagent.agents.reviewer import review_problem_sync, ReviewAgentError
    from vbagent.models.diff import apply_diff_safe, DiffErrorType
    from vbagent.models.version_store import SuggestionStatus
    
    # Create or reuse session
    if session_id is None:
        session_id = store.create_session()
        is_resumed = False
    else:
        is_resumed = True
        console.print(f"[cyan]Resuming session {session_id[:8]}...[/cyan]")
    
    # Statistics
    stats = {
        "problems_reviewed": 0,
        "suggestions_made": 0,
        "approved_count": 0,
        "rejected_count": 0,
        "skipped_count": 0,
        "session_id": session_id,
        "interrupted": False,
    }
    
    # Track remaining problems for resume capability
    remaining_problem_ids = [p.problem_id for p in problems]
    
    # Set up signal handler for graceful shutdown
    shutdown_requested = False
    
    def signal_handler(signum, frame):
        nonlocal shutdown_requested
        shutdown_requested = True
        console.print("\n[yellow]Shutdown requested. Saving session state...[/yellow]")
    
    original_sigint = signal.signal(signal.SIGINT, signal_handler)
    # SIGTERM is not available on Windows
    original_sigterm = None
    if sys.platform != "win32":
        original_sigterm = signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        for idx, problem in enumerate(problems):
            if shutdown_requested:
                # Save remaining problems for resume
                remaining_problem_ids = [p.problem_id for p in problems[idx:]]
                stats["interrupted"] = True
                break
            
            console.print(f"\n[bold cyan]═══ Reviewing: {problem.problem_id} ═══[/bold cyan]")
            
            # Run AI review
            try:
                console.print("[dim]Running AI review... (Ctrl+C to quit)[/dim]")
                result = review_problem_sync(problem)
            except KeyboardInterrupt:
                console.print("\n[yellow]Interrupted during AI review[/yellow]")
                shutdown_requested = True
                stats["interrupted"] = True
                remaining_problem_ids = [p.problem_id for p in problems[idx:]]
                break
            except ReviewAgentError as e:
                # Detailed error from reviewer with retry info
                console.print(f"[red]Error reviewing problem after retries:[/red] {e}")
                if e.last_error:
                    console.print(f"[dim]Error type: {e.last_error.error_type.value}[/dim]")
                    if e.last_error.error_type.value == "rate_limit":
                        console.print("[yellow]Tip: Consider waiting before continuing or reducing batch size.[/yellow]")
                console.print("[dim]Continuing with next problem...[/dim]")
                continue
            except Exception as e:
                # Unexpected error
                console.print(f"[red]Unexpected error reviewing problem:[/red] {e}")
                console.print("[dim]Continuing with next problem...[/dim]")
                continue
            
            stats["problems_reviewed"] += 1
            stats["suggestions_made"] += len(result.suggestions)
            
            if result.passed:
                console.print(f"[green]✓ Problem passed review[/green]")
                console.print(f"[dim]{result.summary}[/dim]")
                # Remove from remaining
                if problem.problem_id in remaining_problem_ids:
                    remaining_problem_ids.remove(problem.problem_id)
                continue
            
            console.print(f"[yellow]Found {len(result.suggestions)} suggestion(s)[/yellow]")
            console.print(f"[dim]{result.summary}[/dim]")
            
            # Process each suggestion
            for i, suggestion in enumerate(result.suggestions, 1):
                if shutdown_requested:
                    stats["interrupted"] = True
                    break
                
                console.print(f"\n[bold]Suggestion {i}/{len(result.suggestions)}[/bold]")
                
                action = prompt_review_action(suggestion, console)
                
                if action == ReviewAction.APPROVE:
                    diff_result = apply_suggestion(suggestion, problem.problem_id)
                    if diff_result.success:
                        console.print("[green]✓ Change applied[/green]")
                        store.save_suggestion(
                            suggestion, problem.problem_id,
                            SuggestionStatus.APPROVED, session_id
                        )
                        stats["approved_count"] += 1
                    else:
                        # Display detailed error information
                        console.print("[red]✗ Failed to apply change[/red]")
                        error_msg = format_diff_error(diff_result)
                        console.print(f"[dim]{error_msg}[/dim]")
                        
                        if diff_result.original_preserved:
                            console.print("[dim]Original file preserved.[/dim]")
                        
                        # Offer options based on error type
                        if diff_result.error_type == DiffErrorType.DIFF_CONFLICT:
                            console.print("[yellow]Tip: The file may have been modified. Consider regenerating the review.[/yellow]")
                        
                        console.print("[dim]Storing as rejected for later reference.[/dim]")
                        store.save_suggestion(
                            suggestion, problem.problem_id,
                            SuggestionStatus.REJECTED, session_id
                        )
                        stats["rejected_count"] += 1
                
                elif action == ReviewAction.REJECT:
                    store.save_suggestion(
                        suggestion, problem.problem_id,
                        SuggestionStatus.REJECTED, session_id
                    )
                    console.print("[yellow]Suggestion stored for later[/yellow]")
                    stats["rejected_count"] += 1
                
                elif action == ReviewAction.SKIP:
                    console.print("[dim]Skipped[/dim]")
                    stats["skipped_count"] += 1
                
                elif action == ReviewAction.EDIT:
                    # Resolve file path
                    resolved_path = resolve_file_path(suggestion.file_path, problem.problem_id)
                    if not resolved_path:
                        console.print(f"[red]File not found: {suggestion.file_path}[/red]")
                        stats["skipped_count"] += 1
                        continue
                    
                    # Open suggested content in editor
                    success, edited_content = open_suggested_in_editor(
                        resolved_path,
                        suggestion.suggested_content,
                        console
                    )
                    
                    if not success:
                        console.print("[red]Could not open editor[/red]")
                        stats["skipped_count"] += 1
                        continue
                    
                    # Ask what to do with edited content
                    Prompt = _get_prompt()
                    console.print("\n[bold]Actions:[/bold]")
                    console.print("  [green]a[/green]pply  - Write edited content to file")
                    console.print("  [yellow]s[/yellow]kip   - Discard changes")
                    
                    edit_choice = Prompt.ask(
                        "Action",
                        choices=["a", "s", "apply", "skip"],
                        default="a"
                    ).lower()
                    
                    if edit_choice in ["a", "apply"]:
                        try:
                            with open(resolved_path, "w") as f:
                                f.write(edited_content)
                            console.print(f"[green]✓ Changes written to {resolved_path}[/green]")
                            store.save_suggestion(
                                suggestion, problem.problem_id,
                                SuggestionStatus.APPROVED, session_id
                            )
                            stats["approved_count"] += 1
                        except (IOError, OSError, PermissionError) as e:
                            console.print(f"[red]✗ Failed to write: {e}[/red]")
                            stats["skipped_count"] += 1
                    else:
                        console.print("[dim]Discarded[/dim]")
                        stats["skipped_count"] += 1
                
                elif action == ReviewAction.QUIT:
                    shutdown_requested = True
                    stats["interrupted"] = True
                    break
            
            # Remove from remaining after processing
            if not shutdown_requested and problem.problem_id in remaining_problem_ids:
                remaining_problem_ids.remove(problem.problem_id)
        
        # Update session with final stats
        if stats["interrupted"]:
            # Save state for resume
            store.save_session_state(session_id, output_dir, remaining_problem_ids)
            store.update_session(
                session_id,
                problems_reviewed=stats["problems_reviewed"],
                suggestions_made=stats["suggestions_made"],
                approved_count=stats["approved_count"],
                rejected_count=stats["rejected_count"],
                skipped_count=stats["skipped_count"],
                completed=False,
            )
            console.print(f"\n[yellow]Session saved. Resume with:[/yellow]")
            console.print(f"[cyan]  vbagent check resume {session_id[:8]}[/cyan]")
        else:
            store.update_session(
                session_id,
                problems_reviewed=stats["problems_reviewed"],
                suggestions_made=stats["suggestions_made"],
                approved_count=stats["approved_count"],
                rejected_count=stats["rejected_count"],
                skipped_count=stats["skipped_count"],
                completed=True,
            )
        
    finally:
        # Restore signal handlers
        signal.signal(signal.SIGINT, original_sigint)
        if original_sigterm is not None:
            signal.signal(signal.SIGTERM, original_sigterm)
    
    return stats


def display_session_summary(stats: dict, console: "Console") -> None:
    """Display summary of a review session.
    
    Args:
        stats: Session statistics dictionary
        console: Rich console for output
    """
    console.print("\n[bold]═══ Session Summary ═══[/bold]")
    
    table = _get_table(show_header=False, box=None)
    table.add_column("Metric", style="dim")
    table.add_column("Value", justify="right")
    
    table.add_row("Problems reviewed", str(stats["problems_reviewed"]))
    table.add_row("Suggestions made", str(stats["suggestions_made"]))
    table.add_row("Approved", f"[green]{stats['approved_count']}[/green]")
    table.add_row("Rejected", f"[red]{stats['rejected_count']}[/red]")
    table.add_row("Skipped", f"[yellow]{stats['skipped_count']}[/yellow]")
    
    console.print(table)



# CLI Commands

CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}


@click.group(context_settings=CONTEXT_SETTINGS)
def check():
    """QA review commands for spot-checking processed problems.
    
    \b
    Commands:
        run       - Start a random QA review session
        init      - Initialize problem tracking database
        continue  - Continue from where you left off
        status    - Show check progress
        recheck   - Reset problems for rechecking
        alternate - Generate alternate solutions
        idea      - Generate idea summaries
        solution  - Check solution correctness
        grammar   - Check grammar and spelling
        clarity   - Check clarity and conciseness
        tikz      - Check TikZ diagram code
        apply     - Apply a stored suggestion
        history   - View suggestion history
        resume    - Resume interrupted session
        stats     - View review statistics
    
    \b
    Examples:
        vbagent check run
        vbagent check init -d ./agentic
        vbagent check continue -c 10
        vbagent check status
        vbagent check alternate -d ./src_tex/
        vbagent check idea -d ./src_tex/
        vbagent check solution -d ./src_tex/
        vbagent check grammar -d ./src_tex/
        vbagent check clarity -d ./src_tex/
        vbagent check tikz -d ./src_tex/
    """
    pass


@check.command(name="run")
@click.option(
    "-c", "--count",
    type=int,
    default=5,
    help="Number of problems to review (default: 5)"
)
@click.option(
    "-p", "--problem-id",
    type=str,
    default=None,
    help="Review a specific problem by ID"
)
@click.option(
    "-d", "--dir",
    "output_dir",
    type=click.Path(exists=True),
    default="agentic",
    help="Output directory to check (default: agentic)"
)
def run_check(count: int, problem_id: Optional[str], output_dir: str):
    """Start a QA review session.
    
    Randomly selects problems from the output directory and runs
    AI-powered quality review with interactive approval.
    
    \b
    Examples:
        vbagent check run
        vbagent check run -c 10
        vbagent check run --count 10 --dir ./output
        vbagent check run -p Problem_42
        vbagent check run --problem-id Problem_42 -d ./my_output
    """
    # Lazy imports
    from vbagent.agents.selector import (
        discover_problems,
        load_problem_context,
        select_random,
    )
    from vbagent.agents.reviewer import review_problem_sync, ReviewAgentError
    from vbagent.models.diff import apply_diff_safe
    from vbagent.models.version_store import VersionStore, SuggestionStatus
    
    console = _get_console()
    
    # Discover available problems
    all_problems = discover_problems(output_dir)
    
    if not all_problems:
        console.print(f"[red]Error:[/red] No problems found in {output_dir}")
        raise SystemExit(1)
    
    console.print(f"[cyan]Found {len(all_problems)} problem(s) in {output_dir}[/cyan]")
    
    # Select problems
    if problem_id:
        if problem_id not in all_problems:
            console.print(f"[red]Error:[/red] Problem '{problem_id}' not found")
            raise SystemExit(1)
        selected_ids = [problem_id]
        console.print(f"[cyan]Reviewing specific problem: {problem_id}[/cyan]")
    else:
        selected_ids = select_random(output_dir, count)
        console.print(f"[cyan]Selected {len(selected_ids)} problem(s) for review[/cyan]")
    
    # Load problem contexts
    problems = []
    for pid in selected_ids:
        try:
            ctx = load_problem_context(output_dir, pid)
            problems.append(ctx)
        except FileNotFoundError as e:
            console.print(f"[yellow]Warning:[/yellow] Could not load {pid}: {e}")
    
    if not problems:
        console.print("[red]Error:[/red] No problems could be loaded")
        raise SystemExit(1)
    
    # Initialize version store
    store = VersionStore(base_dir=".")
    
    try:
        # Run review session
        stats = run_review_session(problems, store, console, output_dir=output_dir)
        
        # Display summary
        display_session_summary(stats, console)
        
    finally:
        store.close()


@check.command()
@click.option(
    "-p", "--problem-id",
    type=str,
    default=None,
    help="Filter by problem ID"
)
@click.option(
    "-f", "--file",
    "file_path",
    type=str,
    default=None,
    help="Filter by file path"
)
@click.option(
    "-n", "--limit",
    type=int,
    default=20,
    help="Maximum number of entries to show (default: 20)"
)
def history(problem_id: Optional[str], file_path: Optional[str], limit: int):
    """Display rejected suggestion history.
    
    Shows previously rejected suggestions that can be applied later.
    
    \b
    Examples:
        vbagent check history
        vbagent check history -p Problem_42
        vbagent check history --problem-id Problem_42 --limit 50
        vbagent check history -f conceptual_variant.tex -n 10
    """
    # Lazy imports
    from vbagent.models.version_store import VersionStore, SuggestionStatus
    
    console = _get_console()
    store = VersionStore(base_dir=".")
    
    try:
        suggestions = store.get_versions(problem_id=problem_id, file_path=file_path)
        
        if not suggestions:
            console.print("[dim]No suggestions found[/dim]")
            return
        
        # Limit results
        suggestions = suggestions[:limit]
        
        table = _get_table(title="Suggestion History")
        table.add_column("ID", style="cyan", justify="right")
        table.add_column("Problem", style="white")
        table.add_column("File", style="dim")
        table.add_column("Type", style="yellow")
        table.add_column("Status", style="white")
        table.add_column("Date", style="dim")
        
        for s in suggestions:
            status_style = {
                SuggestionStatus.APPROVED: "[green]approved[/green]",
                SuggestionStatus.REJECTED: "[red]rejected[/red]",
                SuggestionStatus.PENDING: "[yellow]pending[/yellow]",
            }.get(s.status, str(s.status.value))
            
            table.add_row(
                str(s.id),
                s.problem_id,
                Path(s.file_path).name,
                s.issue_type,
                status_style,
                s.created_at.strftime("%Y-%m-%d %H:%M"),
            )
        
        console.print(table)
        
        if len(suggestions) == limit:
            console.print(f"[dim]Showing first {limit} results. Use --limit to see more.[/dim]")
        
    finally:
        store.close()


@check.command()
@click.argument("version_id", type=int)
@click.option(
    "-e", "--edit",
    is_flag=True,
    help="Open suggested content in editor before applying"
)
def apply(version_id: int, edit: bool):
    """Apply a previously rejected suggestion.
    
    Retrieves a stored suggestion by ID and applies its diff.
    Use --edit to review/modify the suggested content in your editor first.
    
    \b
    Examples:
        vbagent check apply 42
        vbagent check apply 42 -e
        vbagent check apply 42 --edit
    """
    # Lazy imports
    from vbagent.models.version_store import VersionStore, SuggestionStatus
    from vbagent.models.diff import apply_diff_safe, DiffErrorType
    
    console = _get_console()
    store = VersionStore(base_dir=".")
    
    try:
        suggestion = store.get_suggestion(version_id)
        
        if not suggestion:
            console.print(f"[red]Error:[/red] Suggestion {version_id} not found")
            raise SystemExit(1)
        
        # Try to resolve the file path
        resolved_path = resolve_file_path(suggestion.file_path, suggestion.problem_id)
        
        # Display the suggestion
        path_display = suggestion.file_path
        if resolved_path and resolved_path != suggestion.file_path:
            path_display = f"{suggestion.file_path} → [green]{resolved_path}[/green]"
        elif not resolved_path:
            path_display = f"[red]{suggestion.file_path}[/red] (not found)"
        
        console.print(_get_panel(
            f"[bold]{suggestion.description}[/bold]\n\n"
            f"[dim]Problem:[/dim] {suggestion.problem_id}\n"
            f"[dim]File:[/dim] {path_display}\n"
            f"[dim]Type:[/dim] {suggestion.issue_type}\n"
            f"[dim]Status:[/dim] {suggestion.status.value}",
            title=f"[cyan]Suggestion #{version_id}[/cyan]",
            border_style="cyan"
        ))
        
        console.print(f"\n[bold]Reasoning:[/bold]")
        console.print(suggestion.reasoning)
        
        console.print(f"\n[bold]Diff:[/bold]")
        display_diff(suggestion.diff, console)
        
        # Check if file exists
        if not resolved_path:
            console.print(f"\n[red]Error:[/red] File not found: {suggestion.file_path}")
            console.print("[yellow]Tip: The file may have been moved or deleted.[/yellow]")
            console.print("[yellow]You can manually apply the suggested content shown above.[/yellow]")
            raise SystemExit(1)
        
        # Use resolved path for operations
        target_path = resolved_path
        
        if edit:
            # Editor-based workflow
            console.print("\n[bold]Actions:[/bold]")
            console.print("  [blue]e[/blue]dit     - Open suggested content in editor")
            console.print("  [green]a[/green]pply    - Apply suggestion directly")
            console.print("  [yellow]s[/yellow]kip     - Cancel")
            
            Prompt = _get_prompt()
            choice = Prompt.ask(
                "\nAction",
                choices=["e", "a", "s", "edit", "apply", "skip"],
                default="e"
            ).lower()
            
            if choice in ["s", "skip"]:
                console.print("[dim]Cancelled[/dim]")
                return
            
            if choice in ["e", "edit"]:
                # Open suggested content in editor
                success, edited_content = open_suggested_in_editor(
                    target_path,
                    suggestion.suggested_content,
                    console
                )
                
                if not success:
                    console.print("[red]Failed to open editor[/red]")
                    raise SystemExit(1)
                
                # Compare edited content with original suggestion
                if edited_content.strip() == suggestion.suggested_content.strip():
                    console.print("[dim]No changes made in editor[/dim]")
                else:
                    console.print("[cyan]Content was modified in editor[/cyan]")
                
                # Confirm before writing
                console.print("\n[bold]Actions:[/bold]")
                console.print("  [green]a[/green]pply  - Write edited content to file")
                console.print("  [yellow]c[/yellow]ancel - Discard changes")
                
                confirm = Prompt.ask(
                    "\nAction",
                    choices=["a", "c", "apply", "cancel"],
                    default="a"
                ).lower()
                
                if confirm in ["c", "cancel"]:
                    console.print("[dim]Cancelled[/dim]")
                    return
                
                # Write the edited content directly
                try:
                    with open(target_path, "w") as f:
                        f.write(edited_content)
                    store.update_status(version_id, SuggestionStatus.APPROVED)
                    console.print(f"[green]✓ Changes written to {target_path}[/green]")
                except (IOError, OSError, PermissionError) as e:
                    console.print(f"[red]✗ Failed to write file: {e}[/red]")
                    raise SystemExit(1)
                return
            
            # Fall through to direct apply if user chose 'a'
        
        # Direct apply (no editor)
        if not click.confirm("\nApply this change?"):
            console.print("[dim]Cancelled[/dim]")
            return
        
        # Apply the diff with detailed error handling
        result = apply_diff_safe(target_path, suggestion.diff)
        if result.success:
            store.update_status(version_id, SuggestionStatus.APPROVED)
            console.print("[green]✓ Change applied successfully[/green]")
        else:
            console.print("[red]✗ Failed to apply change[/red]")
            error_msg = format_diff_error(result)
            console.print(f"[dim]{error_msg}[/dim]")
            
            if result.original_preserved:
                console.print("[dim]Original file preserved.[/dim]")
            
            if result.error_type == DiffErrorType.DIFF_CONFLICT:
                console.print("[yellow]Tip: The file has been modified since this suggestion was created.[/yellow]")
                console.print("[yellow]Try: vbagent check apply {version_id} --edit[/yellow]")
            elif result.error_type == DiffErrorType.FILE_NOT_FOUND:
                console.print("[yellow]Tip: The file may have been moved or deleted.[/yellow]")
            elif result.error_type == DiffErrorType.PERMISSION_DENIED:
                console.print("[yellow]Tip: Check file permissions and try again.[/yellow]")
            
            raise SystemExit(1)
        
    finally:
        store.close()


@check.command()
@click.argument("session_id", type=str, required=False)
def resume(session_id: Optional[str]):
    """Resume an interrupted review session.
    
    If no session ID is provided, shows a list of incomplete sessions.
    Session IDs can be shortened (prefix match).
    
    \b
    Examples:
        vbagent check resume
        vbagent check resume abc12345
        vbagent check resume abc
    """
    # Lazy imports
    from vbagent.models.version_store import VersionStore
    from vbagent.agents.selector import load_problem_context
    
    console = _get_console()
    store = VersionStore(base_dir=".")
    
    try:
        if session_id is None:
            # Show incomplete sessions
            sessions = store.get_incomplete_sessions()
            
            if not sessions:
                console.print("[dim]No incomplete sessions found[/dim]")
                return
            
            console.print("[bold]Incomplete Sessions:[/bold]\n")
            
            table = _get_table()
            table.add_column("ID", style="cyan")
            table.add_column("Started", style="dim")
            table.add_column("Reviewed", justify="right")
            table.add_column("Remaining", justify="right")
            table.add_column("Directory", style="dim")
            
            for s in sessions:
                remaining = len(s.get("remaining_problems") or [])
                table.add_row(
                    s["id"][:8],
                    s["started_at"][:16] if s["started_at"] else "?",
                    str(s["problems_reviewed"]),
                    str(remaining),
                    s.get("output_dir") or "?",
                )
            
            console.print(table)
            console.print("\n[dim]Resume with: vbagent check resume <session_id>[/dim]")
            return
        
        # Find session by prefix match
        sessions = store.get_incomplete_sessions()
        matching = [s for s in sessions if s["id"].startswith(session_id)]
        
        if not matching:
            console.print(f"[red]Error:[/red] No incomplete session found matching '{session_id}'")
            raise SystemExit(1)
        
        if len(matching) > 1:
            console.print(f"[red]Error:[/red] Multiple sessions match '{session_id}'. Be more specific.")
            for s in matching:
                console.print(f"  {s['id'][:8]}")
            raise SystemExit(1)
        
        session = matching[0]
        full_session_id = session["id"]
        output_dir = session.get("output_dir") or "agentic"
        remaining_problems = session.get("remaining_problems") or []
        
        if not remaining_problems:
            console.print("[yellow]Session has no remaining problems to review[/yellow]")
            # Mark as completed
            store.update_session(full_session_id, completed=True)
            return
        
        console.print(f"[cyan]Resuming session {full_session_id[:8]}[/cyan]")
        console.print(f"[dim]Output directory: {output_dir}[/dim]")
        console.print(f"[dim]Remaining problems: {len(remaining_problems)}[/dim]")
        
        # Load problem contexts
        problems = []
        for pid in remaining_problems:
            try:
                ctx = load_problem_context(output_dir, pid)
                problems.append(ctx)
            except FileNotFoundError as e:
                console.print(f"[yellow]Warning:[/yellow] Could not load {pid}: {e}")
        
        if not problems:
            console.print("[red]Error:[/red] No problems could be loaded")
            raise SystemExit(1)
        
        # Run review session with existing session ID
        stats = run_review_session(
            problems, store, console,
            output_dir=output_dir,
            session_id=full_session_id,
        )
        
        # Display summary
        display_session_summary(stats, console)
        
    finally:
        store.close()


@check.command()
@click.option(
    "-d", "--days",
    type=int,
    default=None,
    help="Filter to last N days"
)
def stats(days: Optional[int]):
    """Display review statistics.
    
    Shows aggregated statistics from review sessions.
    
    \b
    Examples:
        vbagent check stats
        vbagent check stats -d 7
        vbagent check stats --days 30
    """
    # Lazy imports
    from vbagent.models.version_store import VersionStore
    
    console = _get_console()
    store = VersionStore(base_dir=".")
    
    try:
        review_stats = store.get_stats(days=days)
        
        title = "Review Statistics"
        if days:
            title += f" (Last {days} days)"
        
        console.print(_get_panel(title, style="bold cyan"))
        
        # Main stats table
        table = _get_table(show_header=False, box=None)
        table.add_column("Metric", style="dim")
        table.add_column("Value", justify="right")
        
        table.add_row("Problems reviewed", str(review_stats["total_reviewed"]))
        table.add_row("Total suggestions", str(review_stats["total_suggestions"]))
        table.add_row("Approved", f"[green]{review_stats['approved_count']}[/green]")
        table.add_row("Rejected", f"[red]{review_stats['rejected_count']}[/red]")
        table.add_row("Skipped", f"[yellow]{review_stats['skipped_count']}[/yellow]")
        table.add_row("Pending", f"[dim]{review_stats.get('pending_count', 0)}[/dim]")
        table.add_row(
            "Approval rate",
            f"[cyan]{review_stats['approval_rate']:.1%}[/cyan]"
        )
        
        console.print(table)
        
        # Issues by type
        if review_stats["issues_by_type"]:
            console.print("\n[bold]Issues by Type:[/bold]")
            type_table = _get_table(show_header=False, box=None)
            type_table.add_column("Type", style="yellow")
            type_table.add_column("Count", justify="right")
            
            for issue_type, count in sorted(
                review_stats["issues_by_type"].items(),
                key=lambda x: x[1],
                reverse=True
            ):
                type_table.add_row(issue_type, str(count))
            
            console.print(type_table)
        
    finally:
        store.close()


@check.command(name="init")
@click.option(
    "-d", "--dir",
    "output_dir",
    type=click.Path(exists=True),
    default="agentic",
    help="Output directory to check (default: agentic)"
)
@click.option(
    "-r", "--range", "item_range",
    nargs=2,
    type=int,
    help="Range of problems to initialize (1-based inclusive, e.g., -r 1 10)"
)
@click.option(
    "--reset",
    is_flag=True,
    help="Reset existing entries to pending status"
)
def init_check(output_dir: str, item_range: Optional[tuple[int, int]], reset: bool):
    """Initialize problem check tracking.
    
    Discovers all problems in the output directory and adds them
    to the tracking database. Use --range to limit to specific problems.
    
    \b
    Examples:
        vbagent check init
        vbagent check init -d ./my_output
        vbagent check init --dir ./agentic --range 1 50
        vbagent check init -r 1 50
        vbagent check init --reset
    """
    # Lazy imports
    from vbagent.agents.selector import discover_problems
    from vbagent.models.version_store import VersionStore
    
    console = _get_console()
    
    # Discover available problems
    all_problems = discover_problems(output_dir)
    
    if not all_problems:
        console.print(f"[red]Error:[/red] No problems found in {output_dir}")
        raise SystemExit(1)
    
    # Sort problems naturally (Problem_1, Problem_2, ..., Problem_10, ...)
    import re
    def natural_sort_key(s):
        return [int(t) if t.isdigit() else t.lower() for t in re.split(r'(\d+)', s)]
    
    sorted_problems = sorted(all_problems, key=natural_sort_key)
    
    # Apply range filter if specified
    if item_range:
        start, end = item_range
        start_idx = max(0, start - 1)
        end_idx = min(len(sorted_problems), end)
        sorted_problems = sorted_problems[start_idx:end_idx]
        console.print(f"[cyan]Filtering to range {start}-{end}: {len(sorted_problems)} problem(s)[/cyan]")
    
    console.print(f"[cyan]Found {len(sorted_problems)} problem(s) in {output_dir}[/cyan]")
    
    # Initialize tracking
    store = VersionStore(base_dir=".")
    
    try:
        count = store.init_problem_checks(sorted_problems, output_dir, reset=reset)
        
        if reset:
            console.print(f"[green]✓ Reset and initialized {count} problem(s) for checking[/green]")
        else:
            console.print(f"[green]✓ Initialized {count} new problem(s) for checking[/green]")
        
        # Show current stats
        stats = store.get_problem_check_stats(output_dir)
        console.print(f"\n[bold]Check Status:[/bold]")
        console.print(f"  Pending:  {stats.get('pending', 0)}")
        console.print(f"  Checked:  {stats.get('checked', 0)}")
        console.print(f"  Passed:   {stats.get('passed', 0)}")
        console.print(f"  Failed:   {stats.get('failed', 0)}")
        console.print(f"  Skipped:  {stats.get('skipped', 0)}")
        console.print(f"  [dim]Total:    {stats.get('total', 0)}[/dim]")
        
        if stats.get('pending', 0) > 0:
            console.print(f"\n[dim]Run 'vbagent check continue' to start checking[/dim]")
        
    finally:
        store.close()


@check.command(name="continue")
@click.option(
    "-c", "--count",
    type=int,
    default=5,
    help="Number of problems to check in this session (default: 5)"
)
@click.option(
    "-d", "--dir",
    "output_dir",
    type=click.Path(exists=True),
    default="agentic",
    help="Output directory to check (default: agentic)"
)
def continue_check(count: int, output_dir: str):
    """Continue checking from where you left off.
    
    Picks up pending problems from the tracking database and
    runs AI-powered quality review with interactive approval.
    
    \b
    Examples:
        vbagent check continue
        vbagent check continue -c 10
        vbagent check continue --count 10 --dir ./my_output
    """
    # Lazy imports
    from vbagent.agents.selector import load_problem_context
    from vbagent.agents.reviewer import review_problem_sync, ReviewAgentError
    from vbagent.models.version_store import VersionStore, SuggestionStatus, ProblemCheckStatus
    from vbagent.models.diff import DiffErrorType
    
    console = _get_console()
    store = VersionStore(base_dir=".")
    
    try:
        # Get pending problems
        pending = store.get_pending_problems(output_dir, limit=count)
        
        if not pending:
            stats = store.get_problem_check_stats(output_dir)
            if stats.get('total', 0) == 0:
                console.print(f"[yellow]No problems initialized.[/yellow]")
                console.print(f"[dim]Run 'vbagent check init -d {output_dir}' first[/dim]")
            else:
                console.print(f"[green]✓ All problems have been checked![/green]")
                console.print(f"\n[bold]Check Status:[/bold]")
                console.print(f"  Passed:   {stats.get('passed', 0)}")
                console.print(f"  Failed:   {stats.get('failed', 0)}")
                console.print(f"  Skipped:  {stats.get('skipped', 0)}")
                console.print(f"  [dim]Total:    {stats.get('total', 0)}[/dim]")
            return
        
        console.print(f"[cyan]Checking {len(pending)} problem(s) from {output_dir}[/cyan]")
        
        # Show progress
        stats = store.get_problem_check_stats(output_dir)
        total = stats.get('total', 0)
        done = total - stats.get('pending', 0)
        console.print(f"[dim]Progress: {done}/{total} ({done*100//total if total else 0}%)[/dim]")
        
        # Load problem contexts
        problems = []
        for pid in pending:
            try:
                ctx = load_problem_context(output_dir, pid)
                problems.append(ctx)
            except FileNotFoundError as e:
                console.print(f"[yellow]Warning:[/yellow] Could not load {pid}: {e}")
                store.update_problem_check(pid, output_dir, ProblemCheckStatus.SKIPPED)
        
        if not problems:
            console.print("[red]Error:[/red] No problems could be loaded")
            raise SystemExit(1)
        
        # Create session
        session_id = store.create_session()
        
        # Statistics
        session_stats = {
            "problems_reviewed": 0,
            "suggestions_made": 0,
            "approved_count": 0,
            "rejected_count": 0,
            "skipped_count": 0,
            "passed_count": 0,
            "failed_count": 0,
        }
        
        # Set up signal handler for graceful shutdown
        shutdown_requested = False
        
        def signal_handler(signum, frame):
            nonlocal shutdown_requested
            shutdown_requested = True
            console.print("\n[yellow]Shutdown requested. Progress saved.[/yellow]")
        
        original_sigint = signal.signal(signal.SIGINT, signal_handler)
        # SIGTERM is not available on Windows
        original_sigterm = None
        if sys.platform != "win32":
            original_sigterm = signal.signal(signal.SIGTERM, signal_handler)
        
        try:
            for idx, problem in enumerate(problems):
                if shutdown_requested:
                    break
                
                console.print(f"\n[bold cyan]═══ [{idx+1}/{len(problems)}] Checking: {problem.problem_id} ═══[/bold cyan]")
                
                # Run AI review
                try:
                    console.print("[dim]Running AI review... (Ctrl+C to quit)[/dim]")
                    result = review_problem_sync(problem)
                except KeyboardInterrupt:
                    console.print("\n[yellow]Interrupted[/yellow]")
                    shutdown_requested = True
                    break
                except ReviewAgentError as e:
                    console.print(f"[red]Error reviewing problem:[/red] {e}")
                    store.update_problem_check(
                        problem.problem_id, output_dir, 
                        ProblemCheckStatus.SKIPPED
                    )
                    session_stats["skipped_count"] += 1
                    continue
                except Exception as e:
                    console.print(f"[red]Unexpected error:[/red] {e}")
                    store.update_problem_check(
                        problem.problem_id, output_dir,
                        ProblemCheckStatus.SKIPPED
                    )
                    session_stats["skipped_count"] += 1
                    continue
                
                session_stats["problems_reviewed"] += 1
                session_stats["suggestions_made"] += len(result.suggestions)
                
                if result.passed:
                    console.print(f"[green]✓ Problem passed review[/green]")
                    console.print(f"[dim]{result.summary}[/dim]")
                    store.update_problem_check(
                        problem.problem_id, output_dir,
                        ProblemCheckStatus.PASSED, 0
                    )
                    session_stats["passed_count"] += 1
                    continue
                
                console.print(f"[yellow]Found {len(result.suggestions)} suggestion(s)[/yellow]")
                console.print(f"[dim]{result.summary}[/dim]")
                
                # Track if any suggestions were approved
                had_approvals = False
                
                # Process each suggestion
                for i, suggestion in enumerate(result.suggestions, 1):
                    if shutdown_requested:
                        break
                    
                    console.print(f"\n[bold]Suggestion {i}/{len(result.suggestions)}[/bold]")
                    
                    action = prompt_review_action(suggestion, console)
                    
                    if action == ReviewAction.APPROVE:
                        diff_result = apply_suggestion(suggestion, problem.problem_id)
                        if diff_result.success:
                            console.print("[green]✓ Change applied[/green]")
                            store.save_suggestion(
                                suggestion, problem.problem_id,
                                SuggestionStatus.APPROVED, session_id
                            )
                            session_stats["approved_count"] += 1
                            had_approvals = True
                        else:
                            console.print("[red]✗ Failed to apply change[/red]")
                            error_msg = format_diff_error(diff_result)
                            console.print(f"[dim]{error_msg}[/dim]")
                            store.save_suggestion(
                                suggestion, problem.problem_id,
                                SuggestionStatus.REJECTED, session_id
                            )
                            session_stats["rejected_count"] += 1
                    
                    elif action == ReviewAction.REJECT:
                        store.save_suggestion(
                            suggestion, problem.problem_id,
                            SuggestionStatus.REJECTED, session_id
                        )
                        console.print("[yellow]Suggestion stored for later[/yellow]")
                        session_stats["rejected_count"] += 1
                    
                    elif action == ReviewAction.SKIP:
                        console.print("[dim]Skipped[/dim]")
                        session_stats["skipped_count"] += 1
                    
                    elif action == ReviewAction.EDIT:
                        resolved_path = resolve_file_path(suggestion.file_path, problem.problem_id)
                        if not resolved_path:
                            console.print(f"[red]File not found: {suggestion.file_path}[/red]")
                            session_stats["skipped_count"] += 1
                            continue
                        
                        success, edited_content = open_suggested_in_editor(
                            resolved_path, suggestion.suggested_content, console
                        )
                        
                        if success:
                            Prompt = _get_prompt()
                            console.print("\n[bold]Actions:[/bold]")
                            console.print("  [green]a[/green]pply  - Write edited content")
                            console.print("  [yellow]s[/yellow]kip   - Discard changes")
                            
                            edit_choice = Prompt.ask("Action", choices=["a", "s"], default="a").lower()
                            
                            if edit_choice == "a":
                                try:
                                    with open(resolved_path, "w") as f:
                                        f.write(edited_content)
                                    console.print(f"[green]✓ Changes written[/green]")
                                    store.save_suggestion(
                                        suggestion, problem.problem_id,
                                        SuggestionStatus.APPROVED, session_id
                                    )
                                    session_stats["approved_count"] += 1
                                    had_approvals = True
                                except (IOError, OSError) as e:
                                    console.print(f"[red]✗ Failed: {e}[/red]")
                                    session_stats["skipped_count"] += 1
                            else:
                                session_stats["skipped_count"] += 1
                        else:
                            session_stats["skipped_count"] += 1
                    
                    elif action == ReviewAction.QUIT:
                        shutdown_requested = True
                        break
                
                # Update problem status
                if not shutdown_requested:
                    status = ProblemCheckStatus.CHECKED if had_approvals else ProblemCheckStatus.FAILED
                    store.update_problem_check(
                        problem.problem_id, output_dir,
                        status, len(result.suggestions)
                    )
                    if had_approvals:
                        session_stats["failed_count"] += 1  # Had issues that were fixed
                    else:
                        session_stats["failed_count"] += 1  # Had issues
            
            # Update session
            store.update_session(
                session_id,
                problems_reviewed=session_stats["problems_reviewed"],
                suggestions_made=session_stats["suggestions_made"],
                approved_count=session_stats["approved_count"],
                rejected_count=session_stats["rejected_count"],
                skipped_count=session_stats["skipped_count"],
                completed=not shutdown_requested,
            )
            
        finally:
            signal.signal(signal.SIGINT, original_sigint)
            if original_sigterm is not None:
                signal.signal(signal.SIGTERM, original_sigterm)
        
        # Display summary
        console.print("\n[bold]═══ Session Summary ═══[/bold]")
        table = _get_table(show_header=False, box=None)
        table.add_column("Metric", style="dim")
        table.add_column("Value", justify="right")
        
        table.add_row("Problems checked", str(session_stats["problems_reviewed"]))
        table.add_row("Passed", f"[green]{session_stats['passed_count']}[/green]")
        table.add_row("With issues", f"[yellow]{session_stats['failed_count']}[/yellow]")
        table.add_row("Suggestions", str(session_stats["suggestions_made"]))
        table.add_row("Approved", f"[green]{session_stats['approved_count']}[/green]")
        table.add_row("Rejected", f"[red]{session_stats['rejected_count']}[/red]")
        
        console.print(table)
        
        # Show overall progress
        final_stats = store.get_problem_check_stats(output_dir)
        remaining = final_stats.get('pending', 0)
        if remaining > 0:
            console.print(f"\n[dim]{remaining} problem(s) remaining. Run 'vbagent check continue' to continue.[/dim]")
        else:
            console.print(f"\n[green]✓ All problems checked![/green]")
        
    finally:
        store.close()


@check.command(name="status")
@click.option(
    "-d", "--dir",
    "output_dir",
    type=click.Path(exists=True),
    default="agentic",
    help="Output directory to check (default: agentic)"
)
@click.option(
    "-s", "--show", "show_status",
    type=click.Choice(["pending", "passed", "failed", "checked", "skipped", "all"]),
    default=None,
    help="Show problems with specific status"
)
def check_status(output_dir: str, show_status: Optional[str]):
    """Show check progress and status.
    
    Displays statistics for problem checking in the specified directory.
    
    \b
    Examples:
        vbagent check status
        vbagent check status -d ./my_output
        vbagent check status -s pending
        vbagent check status --show failed
        vbagent check status --dir ./agentic --show all
    """
    # Lazy imports
    from vbagent.models.version_store import VersionStore, ProblemCheckStatus
    
    console = _get_console()
    store = VersionStore(base_dir=".")
    
    try:
        stats = store.get_problem_check_stats(output_dir)
        
        if stats.get('total', 0) == 0:
            console.print(f"[yellow]No problems initialized for {output_dir}[/yellow]")
            console.print(f"[dim]Run 'vbagent check init -d {output_dir}' first[/dim]")
            return
        
        # Progress bar
        total = stats.get('total', 0)
        done = total - stats.get('pending', 0)
        pct = done * 100 // total if total else 0
        bar_width = 30
        filled = bar_width * done // total if total else 0
        bar = "█" * filled + "░" * (bar_width - filled)
        
        console.print(f"\n[bold]Check Progress: {output_dir}[/bold]")
        console.print(f"[cyan]{bar}[/cyan] {pct}% ({done}/{total})")
        
        # Stats table
        console.print(f"\n[bold]Status Breakdown:[/bold]")
        table = _get_table(show_header=False, box=None)
        table.add_column("Status", style="dim")
        table.add_column("Count", justify="right")
        
        table.add_row("Pending", f"[yellow]{stats.get('pending', 0)}[/yellow]")
        table.add_row("Passed", f"[green]{stats.get('passed', 0)}[/green]")
        table.add_row("Failed", f"[red]{stats.get('failed', 0)}[/red]")
        table.add_row("Checked", f"[cyan]{stats.get('checked', 0)}[/cyan]")
        table.add_row("Skipped", f"[dim]{stats.get('skipped', 0)}[/dim]")
        
        console.print(table)
        
        # Show specific problems if requested
        if show_status:
            if show_status == "all":
                for status in ProblemCheckStatus:
                    problems = store.get_problems_by_status(output_dir, status)
                    if problems:
                        console.print(f"\n[bold]{status.value.title()} ({len(problems)}):[/bold]")
                        for p in problems[:20]:
                            console.print(f"  {p}")
                        if len(problems) > 20:
                            console.print(f"  [dim]... and {len(problems) - 20} more[/dim]")
            else:
                status_enum = ProblemCheckStatus(show_status)
                problems = store.get_problems_by_status(output_dir, status_enum)
                if problems:
                    console.print(f"\n[bold]{show_status.title()} Problems ({len(problems)}):[/bold]")
                    for p in problems:
                        console.print(f"  {p}")
                else:
                    console.print(f"\n[dim]No {show_status} problems[/dim]")
        
        # Suggestions
        if stats.get('pending', 0) > 0:
            console.print(f"\n[dim]Run 'vbagent check continue' to check pending problems[/dim]")
        
    finally:
        store.close()


@check.command(name="recheck")
@click.option(
    "-d", "--dir",
    "output_dir",
    type=click.Path(exists=True),
    default="agentic",
    help="Output directory (default: agentic)"
)
@click.option(
    "--failed",
    is_flag=True,
    help="Recheck only failed problems"
)
@click.option(
    "-p", "--problem-id",
    type=str,
    multiple=True,
    help="Specific problem IDs to recheck (can be used multiple times)"
)
def recheck(output_dir: str, failed: bool, problem_id: tuple[str, ...]):
    """Reset problems for rechecking.
    
    Resets the status of problems to pending so they can be checked again.
    
    \b
    Examples:
        vbagent check recheck
        vbagent check recheck --failed
        vbagent check recheck -p Problem_1
        vbagent check recheck -p Problem_1 -p Problem_2
        vbagent check recheck --dir ./output --failed
    """
    # Lazy imports
    from vbagent.models.version_store import VersionStore, ProblemCheckStatus
    
    console = _get_console()
    store = VersionStore(base_dir=".")
    
    try:
        if problem_id:
            # Reset specific problems
            count = store.reset_problem_checks(output_dir, list(problem_id))
            console.print(f"[green]✓ Reset {count} problem(s) to pending[/green]")
        elif failed:
            # Reset only failed problems
            failed_problems = store.get_problems_by_status(output_dir, ProblemCheckStatus.FAILED)
            if failed_problems:
                count = store.reset_problem_checks(output_dir, failed_problems)
                console.print(f"[green]✓ Reset {count} failed problem(s) to pending[/green]")
            else:
                console.print("[dim]No failed problems to reset[/dim]")
        else:
            # Reset all
            if not click.confirm("Reset ALL problems to pending?"):
                console.print("[dim]Cancelled[/dim]")
                return
            count = store.reset_problem_checks(output_dir)
            console.print(f"[green]✓ Reset {count} problem(s) to pending[/green]")
        
        # Show updated stats
        stats = store.get_problem_check_stats(output_dir)
        console.print(f"\n[dim]Pending: {stats.get('pending', 0)} | Total: {stats.get('total', 0)}[/dim]")
        
    finally:
        store.close()


@check.command(name="alternate")
@click.option(
    "-d", "--dir",
    "output_dir",
    type=click.Path(exists=True),
    default="agentic",
    help="Directory containing .tex files, or a single .tex file (default: agentic)"
)
@click.option(
    "-c", "--count",
    type=int,
    default=5,
    help="Number of problems to process in this session (default: 5)"
)
@click.option(
    "--min-alternates",
    type=int,
    default=1,
    help="Minimum number of alternate solutions per problem (default: 1)"
)
@click.option(
    "-p", "--problem-id",
    type=str,
    default=None,
    help="Process a specific problem by ID"
)
@click.option(
    "-i", "--images-dir",
    type=click.Path(exists=True),
    default=None,
    help="Directory containing problem images (matched by filename)"
)
@click.option(
    "--prompt",
    type=str,
    default=None,
    help="Additional instructions or context for generating alternates"
)
def check_alternate(
    output_dir: str,
    count: int,
    min_alternates: int,
    problem_id: Optional[str],
    images_dir: Optional[str],
    prompt: Optional[str],
):
    """Check and generate alternate solutions for problems.
    
    Scans all .tex files in the specified directory (or subdirectories),
    checks if they have alternate solutions, and generates new ones with
    interactive approval.
    
    The alternate solution is appended to the problem file using the
    \\begin{alternatesolution}...\\end{alternatesolution} environment.
    
    Images are matched by filename (e.g., problem_1.tex -> problem_1.png).
    Use --prompt to add specific instructions for generating alternates.
    
    \b
    Supports:
        - Direct directory with .tex files (e.g., ./src/src_tex/)
        - Agentic folder structure (scans/, variants/)
        - Single .tex file
    
    \b
    Examples:
        vbagent check alternate
        vbagent check alternate -d ./src/src_tex/
        vbagent check alternate -d ./src/src_tex/ -i ./src/src_images/
        vbagent check alternate --dir ./problem_1.tex
        vbagent check alternate -c 10
        vbagent check alternate --count 10 --min-alternates 2
        vbagent check alternate -p Problem_1
        vbagent check alternate --prompt "Use energy conservation method"
        vbagent check alternate -d ./agentic/scans -p Problem_5
    """
    import re
    from vbagent.agents.alternate import (
        generate_alternate,
        count_alternate_solutions,
    )
    from vbagent.models.version_store import VersionStore, SuggestionStatus
    from vbagent.models.review import Suggestion, ReviewIssueType as IssueType
    
    console = _get_console()
    
    # Discover all tex files
    output_path = Path(output_dir)
    tex_files = []
    
    # Check if it's a single file
    if output_path.is_file() and output_path.suffix == ".tex":
        tex_files = [output_path]
    else:
        # First, check for .tex files directly in the directory
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
        
        # Also check subdirectories one level deep (like src/src_tex/)
        for subdir in output_path.iterdir():
            if subdir.is_dir() and not subdir.name.startswith('.'):
                tex_files.extend(subdir.glob("*.tex"))
    
    # Remove duplicates while preserving order
    seen = set()
    unique_tex_files = []
    for f in tex_files:
        if f not in seen:
            seen.add(f)
            unique_tex_files.append(f)
    tex_files = unique_tex_files
    
    if not tex_files:
        console.print(f"[red]Error:[/red] No .tex files found in {output_dir}")
        console.print("[dim]Tip: Pass a directory containing .tex files or a single .tex file[/dim]")
        raise SystemExit(1)
    
    # Sort naturally
    def natural_sort_key(p):
        return [int(t) if t.isdigit() else t.lower() for t in re.split(r'(\d+)', str(p))]
    
    tex_files = sorted(tex_files, key=natural_sort_key)
    
    # Filter by problem_id if specified
    if problem_id:
        tex_files = [f for f in tex_files if problem_id in f.stem]
        if not tex_files:
            console.print(f"[red]Error:[/red] No files found matching '{problem_id}'")
            raise SystemExit(1)
    
    # Find files needing alternate solutions
    needs_alternate = []
    for tex_file in tex_files:
        content = tex_file.read_text()
        current_count = count_alternate_solutions(content)
        if current_count < min_alternates:
            needs_alternate.append((tex_file, current_count))
    
    if not needs_alternate:
        console.print(f"[green]✓ All problems have at least {min_alternates} alternate solution(s)[/green]")
        return
    
    console.print(f"[cyan]Found {len(needs_alternate)} file(s) needing alternate solutions[/cyan]")
    
    # Limit to count
    to_process = needs_alternate[:count]
    console.print(f"[dim]Processing {len(to_process)} file(s) in this session[/dim]")
    
    # Initialize version store for tracking
    store = VersionStore(base_dir=".")
    session_id = store.create_session()
    
    # Statistics
    stats = {
        "processed": 0,
        "generated": 0,
        "approved": 0,
        "rejected": 0,
        "skipped": 0,
        "session_id": session_id,
    }
    
    # Set up signal handler
    shutdown_requested = False
    
    def signal_handler(signum, frame):
        nonlocal shutdown_requested
        shutdown_requested = True
        console.print("\n[yellow]Shutdown requested. Saving progress...[/yellow]")
    
    original_sigint = signal.signal(signal.SIGINT, signal_handler)
    # SIGTERM is not available on Windows
    original_sigterm = None
    if sys.platform != "win32":
        original_sigterm = signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        for idx, (tex_file, current_count) in enumerate(to_process):
            if shutdown_requested:
                break
            
            rel_path = tex_file.relative_to(output_path)
            console.print(f"\n[bold cyan]═══ [{idx+1}/{len(to_process)}] {rel_path} ═══[/bold cyan]")
            console.print(f"[dim]Current alternate solutions: {current_count}[/dim]")
            
            # Find corresponding image if images_dir is provided
            image_path = find_image_for_problem(tex_file, images_dir) if images_dir else None
            if image_path:
                console.print(f"[dim]Image: {image_path.name}[/dim]")
            
            # Read file content
            content = tex_file.read_text()
            
            # Check if file has a solution (basic validation)
            if r'\begin{solution}' not in content:
                console.print("[yellow]No solution environment found, skipping[/yellow]")
                stats["skipped"] += 1
                continue
            
            # Prepare content with extra prompt if provided
            gen_content = content
            if prompt:
                console.print(f"[dim]Extra instructions: {prompt}[/dim]")
                gen_content = f"% ADDITIONAL INSTRUCTIONS: {prompt}\n\n{content}"
            
            # Generate alternate solution using full file content
            try:
                console.print("[dim]Generating alternate solution... (Ctrl+C to quit)[/dim]")
                alternate_solution = generate_alternate(
                    problem="",  # Not used when full_content is provided
                    solution="",  # Not used when full_content is provided
                    full_content=gen_content,
                )
                stats["generated"] += 1
            except KeyboardInterrupt:
                console.print("\n[yellow]Interrupted[/yellow]")
                shutdown_requested = True
                break
            except Exception as e:
                console.print(f"[red]Error generating alternate:[/red] {e}")
                stats["skipped"] += 1
                continue
            
            # Format the alternate solution
            formatted_alternate = _format_latex(alternate_solution)
            
            # Show the generated solution
            syntax = _get_syntax(formatted_alternate, "latex", theme="monokai", line_numbers=False)
            console.print(_get_panel(
                syntax,
                title="[cyan]Generated Alternate Solution[/cyan]",
                border_style="cyan"
            ))
            
            # Prompt for action
            console.print("\n[bold]Actions:[/bold]")
            console.print("  [green]a[/green]pprove - Append to file")
            console.print("  [red]r[/red]eject  - Store for later, don't apply")
            console.print("  [blue]e[/blue]dit    - Edit in editor before appending")
            console.print("  [yellow]s[/yellow]kip    - Skip without storing")
            console.print("  [dim]q[/dim]uit    - Exit session")
            
            Prompt = _get_prompt()
            try:
                choice = Prompt.ask(
                    "\nAction",
                    choices=["a", "r", "e", "s", "q", "approve", "reject", "edit", "skip", "quit"],
                    default="a"
                ).lower()
            except KeyboardInterrupt:
                console.print("\n[yellow]Interrupted[/yellow]")
                shutdown_requested = True
                break
            
            if choice in ["q", "quit"]:
                shutdown_requested = True
                break
            
            if choice in ["s", "skip"]:
                console.print("[dim]Skipped[/dim]")
                stats["skipped"] += 1
                continue
            
            if choice in ["r", "reject"]:
                # Create suggestion and store for later
                suggestion = Suggestion(
                    file_path=str(tex_file),
                    issue_type=IssueType.OTHER,
                    description=f"Alternate solution for {tex_file.stem}",
                    original_content=content,
                    suggested_content=content + '\n\n' + formatted_alternate + '\n',
                    diff="",
                    reasoning="Generated alternate solution approach.",
                    confidence=0.8,
                )
                store.save_suggestion(
                    suggestion, tex_file.stem,
                    SuggestionStatus.REJECTED, session_id
                )
                console.print("[yellow]Suggestion stored for later[/yellow]")
                stats["rejected"] += 1
                continue
            
            final_content = formatted_alternate
            
            if choice in ["e", "edit"]:
                # Open in editor
                success, edited = open_suggested_in_editor(
                    str(tex_file),
                    formatted_alternate,
                    console
                )
                if success and edited:
                    final_content = edited
                    console.print("[cyan]Content edited[/cyan]")
                else:
                    console.print("[yellow]Edit cancelled, using original[/yellow]")
            
            # Append to file
            try:
                # Ensure proper spacing before appending
                if not content.endswith('\n'):
                    content += '\n'
                new_content = content + '\n' + final_content + '\n'
                
                tex_file.write_text(new_content)
                console.print(f"[green]✓ Alternate solution appended to {rel_path}[/green]")
                
                # Save as approved
                suggestion = Suggestion(
                    file_path=str(tex_file),
                    issue_type=IssueType.OTHER,
                    description=f"Alternate solution for {tex_file.stem}",
                    original_content=content,
                    suggested_content=new_content,
                    diff="",
                    reasoning="Generated alternate solution approach.",
                    confidence=0.8,
                )
                store.save_suggestion(
                    suggestion, tex_file.stem,
                    SuggestionStatus.APPROVED, session_id
                )
                stats["approved"] += 1
            except (IOError, OSError) as e:
                console.print(f"[red]✗ Failed to write: {e}[/red]")
                stats["skipped"] += 1
            
            stats["processed"] += 1
        
        # Update session with final stats
        store.update_session(
            session_id,
            problems_reviewed=stats["processed"],
            suggestions_made=stats["approved"] + stats["rejected"],
            approved_count=stats["approved"],
            rejected_count=stats["rejected"],
            skipped_count=stats["skipped"],
            completed=not shutdown_requested,
        )
    
    finally:
        signal.signal(signal.SIGINT, original_sigint)
        if original_sigterm is not None:
            signal.signal(signal.SIGTERM, original_sigterm)
        store.close()
    
    # Summary
    console.print("\n[bold]═══ Session Summary ═══[/bold]")
    table = _get_table(show_header=False, box=None)
    table.add_column("Metric", style="dim")
    table.add_column("Value", justify="right")
    
    table.add_row("Files processed", str(stats["processed"]))
    table.add_row("Solutions generated", str(stats["generated"]))
    table.add_row("Approved", f"[green]{stats['approved']}[/green]")
    table.add_row("Rejected", f"[red]{stats['rejected']}[/red]")
    table.add_row("Skipped", f"[yellow]{stats['skipped']}[/yellow]")
    
    console.print(table)
    
    remaining = len(needs_alternate) - len(to_process)
    if remaining > 0:
        console.print(f"\n[dim]{remaining} more file(s) need alternate solutions[/dim]")
    
    if shutdown_requested:
        console.print(f"\n[dim]Session {session_id[:8]} saved. View with: vbagent check history[/dim]")


@check.command(name="idea")
@click.option(
    "-d", "--dir",
    "output_dir",
    type=click.Path(exists=True),
    default="agentic",
    help="Directory containing .tex files, or a single .tex file (default: agentic)"
)
@click.option(
    "-c", "--count",
    type=int,
    default=5,
    help="Number of problems to process in this session (default: 5)"
)
@click.option(
    "-p", "--problem-id",
    type=str,
    default=None,
    help="Process a specific problem by ID"
)
def check_idea(
    output_dir: str,
    count: int,
    problem_id: Optional[str],
):
    """Generate and append idea summaries to problems.
    
    Scans .tex files, extracts key concepts/formulas/techniques,
    and appends them in a `\\begin{idea}...\\end{idea}` environment.
    
    \b
    Supports:
        - Direct directory with .tex files
        - Agentic folder structure (scans/, variants/)
        - Single .tex file
    
    \b
    Examples:
        vbagent check idea
        vbagent check idea -d ./src/src_tex/
        vbagent check idea -c 10
        vbagent check idea -p Problem_1
    """
    import re
    from vbagent.agents.idea import (
        generate_idea_latex,
        has_idea_environment,
    )
    from vbagent.models.version_store import VersionStore, SuggestionStatus
    from vbagent.models.review import Suggestion, ReviewIssueType as IssueType
    
    console = _get_console()
    
    # Discover all tex files
    output_path = Path(output_dir)
    tex_files = []
    
    # Check if it's a single file
    if output_path.is_file() and output_path.suffix == ".tex":
        tex_files = [output_path]
    else:
        # First, check for .tex files directly in the directory
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
    seen = set()
    unique_tex_files = []
    for f in tex_files:
        if f not in seen:
            seen.add(f)
            unique_tex_files.append(f)
    tex_files = unique_tex_files
    
    if not tex_files:
        console.print(f"[red]Error:[/red] No .tex files found in {output_dir}")
        raise SystemExit(1)
    
    # Sort naturally
    def natural_sort_key(p):
        return [int(t) if t.isdigit() else t.lower() for t in re.split(r'(\d+)', str(p))]
    
    tex_files = sorted(tex_files, key=natural_sort_key)
    
    # Filter by problem_id if specified
    if problem_id:
        tex_files = [f for f in tex_files if problem_id in f.stem]
        if not tex_files:
            console.print(f"[red]Error:[/red] No files found matching '{problem_id}'")
            raise SystemExit(1)
    
    # Find files needing idea extraction
    needs_idea = []
    for tex_file in tex_files:
        content = tex_file.read_text()
        if not has_idea_environment(content):
            needs_idea.append(tex_file)
    
    if not needs_idea:
        console.print(f"[green]✓ All problems already have idea summaries[/green]")
        return
    
    console.print(f"[cyan]Found {len(needs_idea)} file(s) needing idea extraction[/cyan]")
    
    # Limit to count
    to_process = needs_idea[:count]
    console.print(f"[dim]Processing {len(to_process)} file(s) in this session[/dim]")
    
    # Initialize version store for tracking
    store = VersionStore(base_dir=".")
    session_id = store.create_session()
    
    # Statistics
    stats = {
        "processed": 0,
        "generated": 0,
        "approved": 0,
        "rejected": 0,
        "skipped": 0,
        "session_id": session_id,
    }
    
    # Set up signal handler
    shutdown_requested = False
    
    def signal_handler(signum, frame):
        nonlocal shutdown_requested
        shutdown_requested = True
        console.print("\n[yellow]Shutdown requested. Saving progress...[/yellow]")
    
    original_sigint = signal.signal(signal.SIGINT, signal_handler)
    # SIGTERM is not available on Windows
    original_sigterm = None
    if sys.platform != "win32":
        original_sigterm = signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        for idx, tex_file in enumerate(to_process):
            if shutdown_requested:
                break
            
            rel_path = tex_file.relative_to(output_path) if output_path.is_dir() else tex_file.name
            console.print(f"\n[bold cyan]═══ [{idx+1}/{len(to_process)}] {rel_path} ═══[/bold cyan]")
            
            # Read file content
            content = tex_file.read_text()
            
            # Check if file has a solution (basic validation)
            if r'\begin{solution}' not in content:
                console.print("[yellow]No solution environment found, skipping[/yellow]")
                stats["skipped"] += 1
                continue
            
            # Generate idea using full file content
            try:
                console.print("[dim]Extracting ideas... (Ctrl+C to quit)[/dim]")
                idea_latex = generate_idea_latex(content)
                stats["generated"] += 1
            except KeyboardInterrupt:
                console.print("\n[yellow]Interrupted[/yellow]")
                shutdown_requested = True
                break
            except Exception as e:
                console.print(f"[red]Error generating idea:[/red] {e}")
                stats["skipped"] += 1
                continue
            
            # Format the idea
            formatted_idea = _format_latex(idea_latex)
            
            # Show the generated idea
            syntax = _get_syntax(formatted_idea, "latex", theme="monokai", line_numbers=False)
            console.print(_get_panel(
                syntax,
                title="[cyan]Generated Idea Summary[/cyan]",
                border_style="cyan"
            ))
            
            # Prompt for action
            console.print("\n[bold]Actions:[/bold]")
            console.print("  [green]a[/green]pprove - Append to file")
            console.print("  [red]r[/red]eject  - Store for later, don't apply")
            console.print("  [blue]e[/blue]dit    - Edit in editor before appending")
            console.print("  [yellow]s[/yellow]kip    - Skip without storing")
            console.print("  [dim]q[/dim]uit    - Exit session")
            
            Prompt = _get_prompt()
            try:
                choice = Prompt.ask(
                    "\nAction",
                    choices=["a", "r", "e", "s", "q", "approve", "reject", "edit", "skip", "quit"],
                    default="a"
                ).lower()
            except KeyboardInterrupt:
                console.print("\n[yellow]Interrupted[/yellow]")
                shutdown_requested = True
                break
            
            if choice in ["q", "quit"]:
                shutdown_requested = True
                break
            
            if choice in ["s", "skip"]:
                console.print("[dim]Skipped[/dim]")
                stats["skipped"] += 1
                continue
            
            if choice in ["r", "reject"]:
                # Create suggestion and store for later
                suggestion = Suggestion(
                    file_path=str(tex_file),
                    issue_type=IssueType.OTHER,
                    description=f"Idea summary for {tex_file.stem}",
                    original_content=content,
                    suggested_content=content + '\n\n' + formatted_idea + '\n',
                    diff="",
                    reasoning="Generated idea summary with key concepts.",
                    confidence=0.8,
                )
                store.save_suggestion(
                    suggestion, tex_file.stem,
                    SuggestionStatus.REJECTED, session_id
                )
                console.print("[yellow]Suggestion stored for later[/yellow]")
                stats["rejected"] += 1
                continue
            
            final_content = formatted_idea
            
            if choice in ["e", "edit"]:
                # Open in editor
                success, edited = open_suggested_in_editor(
                    str(tex_file),
                    formatted_idea,
                    console
                )
                if success and edited:
                    final_content = edited
                    console.print("[cyan]Content edited[/cyan]")
                else:
                    console.print("[yellow]Edit cancelled, using original[/yellow]")
            
            # Append to file
            try:
                # Ensure proper spacing before appending
                if not content.endswith('\n'):
                    content += '\n'
                new_content = content + '\n' + final_content + '\n'
                
                tex_file.write_text(new_content)
                console.print(f"[green]✓ Idea summary appended to {rel_path}[/green]")
                
                # Save as approved
                suggestion = Suggestion(
                    file_path=str(tex_file),
                    issue_type=IssueType.OTHER,
                    description=f"Idea summary for {tex_file.stem}",
                    original_content=content,
                    suggested_content=new_content,
                    diff="",
                    reasoning="Generated idea summary with key concepts.",
                    confidence=0.8,
                )
                store.save_suggestion(
                    suggestion, tex_file.stem,
                    SuggestionStatus.APPROVED, session_id
                )
                stats["approved"] += 1
            except (IOError, OSError) as e:
                console.print(f"[red]✗ Failed to write: {e}[/red]")
                stats["skipped"] += 1
            
            stats["processed"] += 1
        
        # Update session with final stats
        store.update_session(
            session_id,
            problems_reviewed=stats["processed"],
            suggestions_made=stats["approved"] + stats["rejected"],
            approved_count=stats["approved"],
            rejected_count=stats["rejected"],
            skipped_count=stats["skipped"],
            completed=not shutdown_requested,
        )
    
    finally:
        signal.signal(signal.SIGINT, original_sigint)
        if original_sigterm is not None:
            signal.signal(signal.SIGTERM, original_sigterm)
        store.close()
    
    # Summary
    console.print("\n[bold]═══ Session Summary ═══[/bold]")
    table = _get_table(show_header=False, box=None)
    table.add_column("Metric", style="dim")
    table.add_column("Value", justify="right")
    
    table.add_row("Files processed", str(stats["processed"]))
    table.add_row("Ideas generated", str(stats["generated"]))
    table.add_row("Approved", f"[green]{stats['approved']}[/green]")
    table.add_row("Rejected", f"[red]{stats['rejected']}[/red]")
    table.add_row("Skipped", f"[yellow]{stats['skipped']}[/yellow]")
    
    console.print(table)
    
    remaining = len(needs_idea) - len(to_process)
    if remaining > 0:
        console.print(f"\n[dim]{remaining} more file(s) need idea extraction[/dim]")
    
    if shutdown_requested:
        console.print(f"\n[dim]Session {session_id[:8]} saved. View with: vbagent check history[/dim]")


@check.command(name="solution")
@click.option(
    "-d", "--dir",
    "output_dir",
    type=click.Path(exists=True),
    default="agentic",
    help="Directory containing .tex files, or a single .tex file (default: agentic)"
)
@click.option(
    "-c", "--count",
    type=int,
    default=5,
    help="Number of problems to check in this session (default: 5)"
)
@click.option(
    "-p", "--problem-id",
    type=str,
    default=None,
    help="Check a specific problem by ID"
)
@click.option(
    "-i", "--images-dir",
    type=click.Path(exists=True),
    default=None,
    help="Directory containing problem images (matched by filename)"
)
@click.option(
    "--prompt",
    type=str,
    default=None,
    help="Additional instructions or context for the checker"
)
@click.option(
    "--reset",
    is_flag=True,
    help="Reset progress and re-check all files"
)
def check_solution_cmd(
    output_dir: str,
    count: int,
    problem_id: Optional[str],
    images_dir: Optional[str],
    prompt: Optional[str],
    reset: bool,
):
    """Check or create solutions for physics problems.
    
    If a solution EXISTS: Verifies calculations, physics principles, and final answers.
    If a solution is MISSING: Creates a complete solution using the problem context.
    
    Prompts for approval before applying corrections or new solutions.
    Images are matched by filename (e.g., problem_1.tex -> problem_1.png).
    Use --prompt to add specific instructions for the checker.
    
    \b
    Examples:
        vbagent check solution
        vbagent check solution -d ./src/src_tex/
        vbagent check solution -d ./src/src_tex/ -i ./src/src_images/
        vbagent check solution -c 10
        vbagent check solution -p Problem_1
        vbagent check solution --prompt "Focus on unit consistency"
        vbagent check solution --reset
    """
    _run_checker_session(
        output_dir=output_dir,
        count=count,
        problem_id=problem_id,
        checker_name="solution",
        check_func_module="vbagent.agents.solution_checker",
        check_func_name="check_solution",
        require_solution=False,  # Solution checker can create solutions if missing
        reset=reset,
        extra_prompt=prompt,
        images_dir=images_dir,
    )


@check.command(name="grammar")
@click.option(
    "-d", "--dir",
    "output_dir",
    type=click.Path(exists=True),
    default="agentic",
    help="Directory containing .tex files, or a single .tex file (default: agentic)"
)
@click.option(
    "-c", "--count",
    type=int,
    default=5,
    help="Number of problems to check in this session (default: 5)"
)
@click.option(
    "-p", "--problem-id",
    type=str,
    default=None,
    help="Check a specific problem by ID"
)
@click.option(
    "--prompt",
    type=str,
    default=None,
    help="Additional instructions or context for the checker"
)
@click.option(
    "--reset",
    is_flag=True,
    help="Reset progress and re-check all files"
)
def check_grammar_cmd(
    output_dir: str,
    count: int,
    problem_id: Optional[str],
    prompt: Optional[str],
    reset: bool,
):
    """Check content for grammar and spelling errors.
    
    Reviews text for grammar, spelling, punctuation, and
    awkward phrasing issues. Prompts for approval to apply fixes.
    
    Use --prompt to add specific instructions for the checker.
    
    \b
    Examples:
        vbagent check grammar
        vbagent check grammar -d ./src/src_tex/
        vbagent check grammar -c 10
        vbagent check grammar -p Problem_1
        vbagent check grammar --prompt "Use British English spelling"
        vbagent check grammar --reset
    """
    _run_checker_session(
        output_dir=output_dir,
        count=count,
        problem_id=problem_id,
        checker_name="grammar",
        check_func_module="vbagent.agents.grammar_checker",
        check_func_name="check_grammar",
        require_solution=False,
        reset=reset,
        extra_prompt=prompt,
    )


@check.command(name="clarity")
@click.option(
    "-d", "--dir",
    "output_dir",
    type=click.Path(exists=True),
    default="agentic",
    help="Directory containing .tex files, or a single .tex file (default: agentic)"
)
@click.option(
    "-c", "--count",
    type=int,
    default=5,
    help="Number of problems to check in this session (default: 5)"
)
@click.option(
    "-p", "--problem-id",
    type=str,
    default=None,
    help="Check a specific problem by ID"
)
@click.option(
    "--prompt",
    type=str,
    default=None,
    help="Additional instructions or context for the checker"
)
@click.option(
    "--reset",
    is_flag=True,
    help="Reset progress and re-check all files"
)
def check_clarity_cmd(
    output_dir: str,
    count: int,
    problem_id: Optional[str],
    prompt: Optional[str],
    reset: bool,
):
    """Check content for clarity and conciseness.
    
    Reviews text for unclear statements, verbose explanations,
    and pedagogical improvements. Prompts for approval to apply changes.
    
    Use --prompt to add specific instructions for the checker.
    
    \b
    Examples:
        vbagent check clarity
        vbagent check clarity -d ./src/src_tex/
        vbagent check clarity -c 10
        vbagent check clarity -p Problem_1
        vbagent check clarity --prompt "Keep explanations brief for JEE level"
        vbagent check clarity --reset
    """
    _run_checker_session(
        output_dir=output_dir,
        count=count,
        problem_id=problem_id,
        checker_name="clarity",
        check_func_module="vbagent.agents.clarity_checker",
        check_func_name="check_clarity",
        require_solution=False,
        reset=reset,
        extra_prompt=prompt,
    )


@check.command(name="tikz")
@click.option(
    "-d", "--dir",
    "output_dir",
    type=click.Path(exists=True),
    default="agentic",
    help="Directory containing .tex files, or a single .tex file (default: agentic)"
)
@click.option(
    "-c", "--count",
    type=int,
    default=5,
    help="Number of problems to check in this session (default: 5)"
)
@click.option(
    "-p", "--problem-id",
    type=str,
    default=None,
    help="Check a specific problem by ID"
)
@click.option(
    "-i", "--images-dir",
    type=click.Path(exists=True),
    default=None,
    help="Directory containing problem images (matched by filename)"
)
@click.option(
    "--prompt",
    type=str,
    default=None,
    help="Additional instructions or context for the checker"
)
@click.option(
    "--only-tikz",
    is_flag=True,
    help="Only check files that contain TikZ code"
)
@click.option(
    "--reset",
    is_flag=True,
    help="Reset progress and re-check all files"
)
def check_tikz_cmd(
    output_dir: str,
    count: int,
    problem_id: Optional[str],
    images_dir: Optional[str],
    prompt: Optional[str],
    only_tikz: bool,
    reset: bool,
):
    """Check TikZ diagram code for errors and best practices.
    
    Reviews TikZ/PGF code for syntax errors, missing libraries,
    and physics diagram conventions. Prompts for approval to apply fixes.
    
    Images are matched by filename (e.g., problem_1.tex -> problem_1.png).
    Use --prompt to add specific instructions for the checker.
    
    \b
    Examples:
        vbagent check tikz
        vbagent check tikz -d ./src/src_tex/
        vbagent check tikz -d ./src/src_tex/ -i ./src/src_images/
        vbagent check tikz -c 10
        vbagent check tikz -p Problem_1
        vbagent check tikz --prompt "Use circuit library for electrical diagrams"
        vbagent check tikz --only-tikz
        vbagent check tikz --reset
    """
    _run_checker_session(
        output_dir=output_dir,
        count=count,
        problem_id=problem_id,
        checker_name="tikz",
        check_func_module="vbagent.agents.tikz_checker",
        check_func_name="check_tikz",
        require_solution=False,
        require_tikz=only_tikz,
        reset=reset,
        images_dir=images_dir,
        extra_prompt=prompt,
    )


def _run_checker_session(
    output_dir: str,
    count: int,
    problem_id: Optional[str],
    checker_name: str,
    check_func_module: str,
    check_func_name: str,
    require_solution: bool = False,
    require_tikz: bool = False,
    reset: bool = False,
    images_dir: Optional[str] = None,
    extra_prompt: Optional[str] = None,
) -> None:
    """Run an interactive checker session with approval workflow.
    
    Saves progress to database for tracking and potential resume.
    Skips already-checked files unless reset=True.
    
    Args:
        output_dir: Directory containing .tex files
        count: Number of files to process
        problem_id: Optional specific problem ID to check
        checker_name: Name of the checker (solution/grammar/clarity/tikz)
        check_func_module: Module containing the check function
        check_func_name: Name of the check function
        require_solution: Whether to require solution environment
        require_tikz: Whether to require TikZ code (for tikz checker)
        reset: Whether to reset progress and re-check all files
        images_dir: Optional directory containing images for problems
        extra_prompt: Optional additional instructions for the checker
    """
    import re
    import importlib
    from vbagent.models.version_store import VersionStore, SuggestionStatus
    from vbagent.models.review import Suggestion, ReviewIssueType as IssueType
    
    # Dynamically import the check function
    module = importlib.import_module(check_func_module)
    check_func = getattr(module, check_func_name)
    
    # Import has_tikz_environment if needed
    has_tikz_environment = None
    if require_tikz:
        from vbagent.agents.tikz_checker import has_tikz_environment
    
    console = _get_console()
    
    output_path = Path(output_dir)
    tex_files = _discover_tex_files(output_path)
    
    if not tex_files:
        console.print(f"[red]Error:[/red] No .tex files found in {output_dir}")
        raise SystemExit(1)
    
    def natural_sort_key(p):
        return [int(t) if t.isdigit() else t.lower() for t in re.split(r'(\d+)', str(p))]
    
    tex_files = sorted(tex_files, key=natural_sort_key)
    
    if problem_id:
        tex_files = [f for f in tex_files if problem_id in f.stem]
        if not tex_files:
            console.print(f"[red]Error:[/red] No files found matching '{problem_id}'")
            raise SystemExit(1)
    
    # Filter for TikZ files if required
    if require_tikz and has_tikz_environment:
        tikz_files = []
        for f in tex_files:
            content = f.read_text()
            if has_tikz_environment(content):
                tikz_files.append(f)
        tex_files = tikz_files
        if not tex_files:
            console.print(f"[yellow]No files with TikZ code found in {output_dir}[/yellow]")
            return
    
    # Initialize version store for tracking
    store = VersionStore(base_dir=".")
    output_dir_normalized = str(output_path.resolve())
    
    # Reset progress if requested
    if reset:
        reset_count = store.reset_checker_progress(checker_name, output_dir_normalized)
        if reset_count > 0:
            console.print(f"[yellow]Reset progress for {reset_count} file(s)[/yellow]")
    
    # Filter out already-checked files
    checked_files = store.get_checked_files(checker_name, output_dir_normalized)
    unchecked_files = [f for f in tex_files if str(f.resolve()) not in checked_files]
    
    if not unchecked_files:
        console.print(f"[green]✓ All {len(tex_files)} file(s) have already been checked for {checker_name} issues[/green]")
        stats = store.get_checker_stats(checker_name, output_dir_normalized)
        console.print(f"[dim]Total: {stats['total']}, Passed: {stats['passed']}, Had issues: {stats['failed']}[/dim]")
        console.print(f"[dim]Use --reset to re-check files[/dim]")
        store.close()
        return
    
    if len(checked_files) > 0:
        console.print(f"[dim]Skipping {len(checked_files)} already-checked file(s)[/dim]")
    
    to_process = unchecked_files[:count]
    console.print(f"[cyan]Checking {len(to_process)} file(s) for {checker_name} issues[/cyan]")
    session_id = store.create_session()
    
    # Map checker names to issue types
    issue_type_map = {
        "solution": IssueType.PHYSICS_ERROR,
        "grammar": IssueType.GRAMMAR,
        "clarity": IssueType.CLARITY,
        "tikz": IssueType.FORMATTING,
    }
    issue_type = issue_type_map.get(checker_name, IssueType.OTHER)
    
    stats = {
        "processed": 0,
        "passed": 0,
        "approved": 0,
        "rejected": 0,
        "skipped": 0,
        "session_id": session_id,
    }
    
    shutdown_requested = False
    
    def signal_handler(signum, frame):
        nonlocal shutdown_requested
        shutdown_requested = True
        console.print("\n[yellow]Shutdown requested. Saving progress...[/yellow]")
    
    original_sigint = signal.signal(signal.SIGINT, signal_handler)
    # SIGTERM is not available on Windows
    original_sigterm = None
    if sys.platform != "win32":
        original_sigterm = signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        for idx, tex_file in enumerate(to_process):
            if shutdown_requested:
                break
            
            rel_path = tex_file.relative_to(output_path) if output_path.is_dir() else tex_file.name
            problem_name = tex_file.stem
            console.print(f"\n[bold cyan]═══ [{idx+1}/{len(to_process)}] {rel_path} ═══[/bold cyan]")
            
            # Find corresponding image if images_dir is provided
            image_path = find_image_for_problem(tex_file, images_dir) if images_dir else None
            if image_path:
                console.print(f"[dim]Image: {image_path.name}[/dim]")
            
            content = tex_file.read_text()
            
            if require_solution and r'\begin{solution}' not in content:
                console.print("[yellow]No solution environment found, skipping[/yellow]")
                stats["skipped"] += 1
                continue
            
            # Prepare content with extra prompt if provided
            check_content = content
            if extra_prompt:
                console.print(f"[dim]Extra instructions: {extra_prompt}[/dim]")
                # Prepend extra instructions as a comment for the checker
                check_content = f"% ADDITIONAL INSTRUCTIONS: {extra_prompt}\n\n{content}"
            
            try:
                console.print(f"[dim]Checking {checker_name}... (Ctrl+C to quit)[/dim]")
                # Pass image to tikz checker if available
                if checker_name == "tikz" and image_path:
                    passed, summary, corrected_content = check_func(check_content, image_path=str(image_path))
                else:
                    passed, summary, corrected_content = check_func(check_content)
                stats["processed"] += 1
            except KeyboardInterrupt:
                console.print("\n[yellow]Interrupted[/yellow]")
                shutdown_requested = True
                break
            except Exception as e:
                console.print(f"[red]Error checking {checker_name}:[/red] {e}")
                stats["skipped"] += 1
                continue
            
            if passed:
                console.print(f"[green]✓ {summary}[/green]")
                stats["passed"] += 1
                # Mark file as checked (passed)
                store.mark_file_checked(str(tex_file.resolve()), checker_name, output_dir_normalized, passed=True)
                continue
            
            # Clean up extra prompt from corrected content if it was added
            if extra_prompt and corrected_content.startswith("% ADDITIONAL INSTRUCTIONS:"):
                # Remove the extra instructions line
                lines = corrected_content.split('\n')
                # Skip the instruction line and any following blank lines
                start_idx = 0
                for i, line in enumerate(lines):
                    if line.startswith("% ADDITIONAL INSTRUCTIONS:"):
                        start_idx = i + 1
                        # Skip blank lines after the instruction
                        while start_idx < len(lines) and not lines[start_idx].strip():
                            start_idx += 1
                        break
                corrected_content = '\n'.join(lines[start_idx:])
            
            # Show the summary
            console.print(f"[yellow]Issues found: {summary}[/yellow]")
            
            # Generate diff
            diff_text = _generate_diff(content, corrected_content, str(rel_path))
            
            # Create suggestion object for database storage
            suggestion = Suggestion(
                file_path=str(tex_file),
                issue_type=issue_type,
                description=f"{checker_name.title()} check: {summary}",
                original_content=content,
                suggested_content=corrected_content,
                diff=diff_text,
                reasoning=f"Automated {checker_name} check found issues.",
                confidence=0.8,
            )
            
            if diff_text:
                console.print(f"\n[bold]Proposed Changes:[/bold]")
                display_diff(diff_text, console)
            else:
                # Fallback to showing corrected content if diff fails
                formatted_content = _format_latex(corrected_content)
                syntax = _get_syntax(formatted_content, "latex", theme="monokai", line_numbers=False)
                console.print(_get_panel(
                    syntax,
                    title=f"[cyan]Corrected Content[/cyan]",
                    border_style="cyan"
                ))
            
            # Prompt for action
            console.print("\n[bold]Actions:[/bold]")
            console.print("  [green]a[/green]pprove - Apply this change")
            console.print("  [red]r[/red]eject  - Store for later, don't apply")
            console.print("  [blue]e[/blue]dit    - Edit in editor before applying")
            console.print("  [yellow]s[/yellow]kip    - Skip without storing")
            console.print("  [dim]q[/dim]uit    - Exit session")
            
            Prompt = _get_prompt()
            try:
                choice = Prompt.ask(
                    "\nAction",
                    choices=["a", "r", "e", "s", "q", "approve", "reject", "edit", "skip", "quit"],
                    default="a"
                ).lower()
            except KeyboardInterrupt:
                console.print("\n[yellow]Interrupted[/yellow]")
                shutdown_requested = True
                break
            
            if choice in ["q", "quit"]:
                shutdown_requested = True
                break
            
            if choice in ["s", "skip"]:
                console.print("[dim]Skipped[/dim]")
                stats["skipped"] += 1
                continue
            
            if choice in ["r", "reject"]:
                # Store for later without applying
                store.save_suggestion(
                    suggestion, problem_name,
                    SuggestionStatus.REJECTED, session_id
                )
                # Mark file as checked (had issues, rejected)
                store.mark_file_checked(str(tex_file.resolve()), checker_name, output_dir_normalized, passed=False)
                console.print("[yellow]Suggestion stored for later[/yellow]")
                stats["rejected"] += 1
                continue
            
            final_content = corrected_content
            
            if choice in ["e", "edit"]:
                success, edited = open_suggested_in_editor(
                    str(tex_file),
                    corrected_content,
                    console
                )
                if success and edited:
                    final_content = edited
                    console.print("[cyan]Content edited[/cyan]")
                else:
                    console.print("[yellow]Edit cancelled, using original correction[/yellow]")
            
            # Write the corrected content
            try:
                tex_file.write_text(final_content)
                console.print(f"[green]✓ Corrections applied to {rel_path}[/green]")
                # Save as approved
                store.save_suggestion(
                    suggestion, problem_name,
                    SuggestionStatus.APPROVED, session_id
                )
                # Mark file as checked (had issues, approved fix)
                store.mark_file_checked(str(tex_file.resolve()), checker_name, output_dir_normalized, passed=False)
                stats["approved"] += 1
            except (IOError, OSError) as e:
                console.print(f"[red]✗ Failed to write: {e}[/red]")
                # Store as rejected since we couldn't apply
                store.save_suggestion(
                    suggestion, problem_name,
                    SuggestionStatus.REJECTED, session_id
                )
                # Mark file as checked (had issues, failed to apply)
                store.mark_file_checked(str(tex_file.resolve()), checker_name, output_dir_normalized, passed=False)
                stats["rejected"] += 1
        
        # Update session with final stats
        store.update_session(
            session_id,
            problems_reviewed=stats["processed"],
            suggestions_made=stats["approved"] + stats["rejected"],
            approved_count=stats["approved"],
            rejected_count=stats["rejected"],
            skipped_count=stats["skipped"],
            completed=not shutdown_requested,
        )
    
    finally:
        signal.signal(signal.SIGINT, original_sigint)
        if original_sigterm is not None:
            signal.signal(signal.SIGTERM, original_sigterm)
        store.close()
    
    # Summary
    console.print("\n[bold]═══ Session Summary ═══[/bold]")
    table = _get_table(show_header=False, box=None)
    table.add_column("Metric", style="dim")
    table.add_column("Value", justify="right")
    
    table.add_row("Files checked", str(stats["processed"]))
    table.add_row("Passed", f"[green]{stats['passed']}[/green]")
    table.add_row("Approved", f"[green]{stats['approved']}[/green]")
    table.add_row("Rejected", f"[red]{stats['rejected']}[/red]")
    table.add_row("Skipped", f"[yellow]{stats['skipped']}[/yellow]")
    
    console.print(table)
    
    if shutdown_requested:
        console.print(f"\n[dim]Session {session_id[:8]} saved. View with: vbagent check history[/dim]")


# Aliases for backward compatibility - use common module functions
def _generate_diff(original: str, corrected: str, filename: str = "file.tex") -> str:
    """Generate a unified diff. Alias for models.diff.generate_diff."""
    from vbagent.models.diff import generate_diff
    return generate_diff(original, corrected, filename)


# Use common module functions directly
_discover_tex_files = discover_tex_files
_extract_problem_solution_from_content = extract_problem_solution
_format_latex = format_latex


# Make 'run' the default command when just 'check' is called
@check.command(name="default", hidden=True)
@click.pass_context
def default_command(ctx):
    """Default command - runs check with default options."""
    ctx.invoke(run_check)
