"""CLI commands for batch processing with resume capability.

Provides `init` and `continue` commands for processing multiple images
with SQLite-based state tracking and caffeinate support.
"""

from __future__ import annotations

import signal
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Optional

import click

if TYPE_CHECKING:
    from vbagent.models.batch import BatchDatabase, ImageRecord


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


class SleepInhibitor:
    """Cross-platform sleep prevention during batch processing.
    
    Supports:
    - macOS: caffeinate command
    - Windows: SetThreadExecutionState API
    - Linux: systemd-inhibit or falls back gracefully
    """
    
    def __init__(self, console=None):
        self.process: Optional[subprocess.Popen] = None
        self._console = console
        self._windows_previous_state = None
    
    def _get_console(self):
        """Get console instance, creating one if needed."""
        if self._console is None:
            self._console = _get_console()
        return self._console
    
    def start(self):
        """Start sleep inhibition based on platform."""
        if sys.platform == "darwin":
            self._start_macos()
        elif sys.platform == "win32":
            self._start_windows()
        elif sys.platform.startswith("linux"):
            self._start_linux()
        else:
            self._get_console().print("[dim]Sleep prevention not available on this platform[/dim]")
    
    def _start_macos(self):
        """macOS: Use caffeinate command."""
        try:
            self.process = subprocess.Popen(
                ["caffeinate", "-i", "-s"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            self._get_console().print("[dim]☕ Sleep inhibitor started (caffeinate)[/dim]")
        except FileNotFoundError:
            self._get_console().print("[yellow]Warning:[/yellow] caffeinate not found")
    
    def _start_windows(self):
        """Windows: Use SetThreadExecutionState API."""
        try:
            import ctypes
            # ES_CONTINUOUS | ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED
            ES_CONTINUOUS = 0x80000000
            ES_SYSTEM_REQUIRED = 0x00000001
            self._windows_previous_state = ctypes.windll.kernel32.SetThreadExecutionState(
                ES_CONTINUOUS | ES_SYSTEM_REQUIRED
            )
            self._get_console().print("[dim]☕ Sleep inhibitor started (Windows API)[/dim]")
        except Exception as e:
            self._get_console().print(f"[yellow]Warning:[/yellow] Could not prevent sleep: {e}")
    
    def _start_linux(self):
        """Linux: Try systemd-inhibit, fall back gracefully."""
        try:
            # systemd-inhibit runs a command while inhibiting sleep
            # We use 'sleep infinity' as a placeholder process
            self.process = subprocess.Popen(
                ["systemd-inhibit", "--what=idle:sleep", "--why=Batch processing", 
                 "--mode=block", "sleep", "infinity"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            self._get_console().print("[dim]☕ Sleep inhibitor started (systemd-inhibit)[/dim]")
        except FileNotFoundError:
            self._get_console().print("[dim]Sleep prevention not available (systemd-inhibit not found)[/dim]")
    
    def stop(self):
        """Stop sleep inhibition."""
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.process = None
            self._get_console().print("[dim]☕ Sleep inhibitor stopped[/dim]")
        
        if sys.platform == "win32" and self._windows_previous_state is not None:
            try:
                import ctypes
                ES_CONTINUOUS = 0x80000000
                ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)
                self._windows_previous_state = None
                self._get_console().print("[dim]☕ Sleep inhibitor stopped[/dim]")
            except Exception:
                pass
    
    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
        return False


# Backward compatibility alias
CaffeinateManager = SleepInhibitor


def discover_images(images_dir: str, pattern: str = "*.png") -> list[str]:
    """Discover all images in a directory matching the pattern.
    
    Args:
        images_dir: Directory to search
        pattern: Glob pattern for images (default: *.png)
        
    Returns:
        Sorted list of image paths
    """
    path = Path(images_dir)
    if not path.exists():
        return []
    
    # Support multiple image formats
    patterns = ["*.png", "*.jpg", "*.jpeg", "*.PNG", "*.JPG", "*.JPEG"]
    images = []
    
    for p in patterns:
        images.extend(path.glob(p))
    
    # Sort naturally (Problem_1, Problem_2, ..., Problem_10)
    return sorted([str(img) for img in images], key=lambda x: (
        Path(x).stem.rstrip('0123456789'),
        int(''.join(filter(str.isdigit, Path(x).stem)) or '0')
    ))


def _generate_context_file(output_dir: str, problem_count: int) -> None:
    """Generate CONTEXT.md file for external AI agents.
    
    Creates a documentation file in the output directory that helps
    external AI tools (Codex, Claude Code, Cursor, etc.) understand
    the directory structure and work with physics problems.
    
    Args:
        output_dir: Output directory path
        problem_count: Number of problems being processed
    """
    from vbagent.templates.agentic_context import generate_context_file
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    content = generate_context_file(
        directory_name=output_path.name,
        problem_count=problem_count,
    )
    
    context_file = output_path / "CONTEXT.md"
    context_file.write_text(content)


def process_single_image(
    db: "BatchDatabase",
    record: "ImageRecord",
    variant_types: list[str],
    generate_alternates: bool,
    output_dir: str,
    use_context: bool = True,
) -> bool:
    """Process a single image through the pipeline with state tracking.
    
    Returns True if successful, False if failed.
    """
    # Lazy imports
    from vbagent.agents.classifier import classify as classify_image
    from vbagent.agents.scanner import scan as scan_image
    from vbagent.agents.tikz import generate_tikz
    from vbagent.agents.idea import extract_ideas
    from vbagent.agents.alternate import generate_alternate
    from vbagent.agents.variant import generate_variant
    from vbagent.models.batch import ProcessingStatus
    from vbagent.models.classification import ClassificationResult
    from vbagent.models.idea import IdeaResult
    from vbagent.cli.process import (
        format_latex,
        extract_problem_solution,
        save_pipeline_result_organized,
        get_base_name,
    )
    from vbagent.models.pipeline import PipelineResult
    
    console = _get_console()
    
    image_id = record.id
    image_path = record.image_path
    
    try:
        # Determine which stage to resume from
        status = record.status
        
        # Stage 1: Classification
        if status in [ProcessingStatus.PENDING, ProcessingStatus.CLASSIFYING]:
            db.update_status(image_id, ProcessingStatus.CLASSIFYING, "classifying")
            
            classification = classify_image(image_path)
            db.save_classification(image_id, classification.model_dump_json())
            
            console.print(f"  [cyan]Type:[/cyan] {classification.question_type}")
        else:
            # Load existing classification
            classification = ClassificationResult.model_validate_json(
                record.classification_json
            )
        
        # Stage 2: Scanning
        if status in [ProcessingStatus.PENDING, ProcessingStatus.CLASSIFYING, ProcessingStatus.SCANNING]:
            db.update_status(image_id, ProcessingStatus.SCANNING, "scanning")
            
            scan_result = scan_image(image_path, classification, use_context=use_context)
            latex = scan_result.latex
            db.save_latex(image_id, latex)
        else:
            latex = record.latex
        
        # Stage 3: TikZ (if has diagram)
        tikz_code = record.tikz_code
        if classification.has_diagram:
            if status in [
                ProcessingStatus.PENDING, ProcessingStatus.CLASSIFYING,
                ProcessingStatus.SCANNING, ProcessingStatus.TIKZ
            ]:
                db.update_status(image_id, ProcessingStatus.TIKZ, "tikz")
                
                tikz_code = generate_tikz(
                    description=f"Generate TikZ for {classification.diagram_type or 'diagram'}",
                    image_path=image_path,
                    use_context=use_context,
                )
                db.save_tikz(image_id, tikz_code)
        
        # Stage 4: Ideas
        problem, solution = extract_problem_solution(latex)
        ideas = None
        
        if problem and solution:
            if status in [
                ProcessingStatus.PENDING, ProcessingStatus.CLASSIFYING,
                ProcessingStatus.SCANNING, ProcessingStatus.TIKZ,
                ProcessingStatus.IDEAS
            ]:
                db.update_status(image_id, ProcessingStatus.IDEAS, "ideas")
                
                ideas = extract_ideas(problem, solution)
                db.save_ideas(image_id, ideas.model_dump_json())
            elif record.ideas_json:
                ideas = IdeaResult.model_validate_json(record.ideas_json)
        
        # Stage 5: Alternates
        alternate_solutions = db.get_alternates(image_id)
        if generate_alternates and problem and solution and not alternate_solutions:
            db.update_status(image_id, ProcessingStatus.ALTERNATES, "alternates")
            
            alt = generate_alternate(problem, solution, ideas)
            db.save_alternate(image_id, alt)
            alternate_solutions = [alt]
        
        # Stage 6: Variants
        existing_variants = db.get_variants(image_id)
        variants = dict(existing_variants)
        
        remaining_variants = [v for v in variant_types if v not in existing_variants]
        if remaining_variants:
            db.update_status(image_id, ProcessingStatus.VARIANTS, "variants")
            
            for vtype in remaining_variants:
                variant_latex = generate_variant(latex, vtype, ideas, use_context=use_context)
                db.save_variant(image_id, vtype, variant_latex)
                variants[vtype] = variant_latex
        
        # Save to files
        result = PipelineResult(
            source_path=image_path,
            classification=classification,
            latex=latex,
            tikz_code=tikz_code,
            ideas=ideas,
            alternate_solutions=alternate_solutions,
            variants=variants,
        )
        
        base_name = get_base_name(image_path)
        save_pipeline_result_organized(result, Path(output_dir), base_name)
        
        # Mark as completed
        db.update_status(image_id, ProcessingStatus.COMPLETED)
        return True
        
    except Exception as e:
        db.update_status(
            image_id,
            ProcessingStatus.FAILED,
            error=str(e)
        )
        console.print(f"  [red]Error:[/red] {e}")
        return False


CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}


@click.group(context_settings=CONTEXT_SETTINGS)
def batch():
    """Batch processing commands with resume capability.
    
    Process multiple images through the full pipeline with SQLite-based
    state tracking and automatic resume on interruption.
    
    \b
    Commands:
        init      - Initialize and start batch processing
        continue  - Resume from where you left off
        status    - Show current progress
    
    \b
    Examples:
        vbagent batch init -i ./images
        vbagent batch continue
        vbagent batch status
    """
    pass


@batch.command()
@click.option(
    "-i", "--images-dir",
    type=click.Path(exists=True),
    default="./images",
    help="Directory containing images (default: ./images)"
)
@click.option(
    "-o", "--output",
    type=click.Path(),
    default="agentic",
    help="Output directory (default: agentic)"
)
@click.option(
    "--variants", "variant_types_str",
    type=str,
    default="numerical,context,conceptual,calculus",
    help="Variant types (comma-separated, default: all)"
)
@click.option(
    "--alternate/--no-alternate",
    default=True,
    help="Generate alternate solutions (default: yes)"
)
@click.option(
    "--context/--no-context",
    default=True,
    help="Use reference context from ~/.config/vbagent (default: yes)"
)
def init(
    images_dir: str,
    output: str,
    variant_types_str: str,
    alternate: bool,
    context: bool,
):
    """Initialize batch processing for all images in a directory.
    
    Scans the images directory, creates a SQLite database to track progress,
    and starts processing all images through the full pipeline.
    
    \b
    Examples:
        vbagent batch init
        vbagent batch init -i ./my_images
        vbagent batch init --images-dir ./images --output ./results
        vbagent batch init --variants numerical,context --no-alternate
        vbagent batch init -i ./images -o ./output --no-context
    """
    # Lazy imports
    from vbagent.models.batch import BatchDatabase
    
    console = _get_console()
    
    # Parse variant types
    variant_types = [v.strip() for v in variant_types_str.split(",") if v.strip()]
    
    # Discover images
    images = discover_images(images_dir)
    if not images:
        console.print(f"[red]Error:[/red] No images found in {images_dir}")
        raise SystemExit(1)
    
    console.print(f"[cyan]Found {len(images)} image(s) in {images_dir}[/cyan]")
    
    # Initialize database
    db = BatchDatabase(base_dir=".")
    
    # Save configuration
    db.save_config(
        images_dir=images_dir,
        output_dir=output,
        variant_types=variant_types,
        generate_alternates=alternate,
        use_context=context,
    )
    
    # Add all images to queue
    for img in images:
        db.add_image(img)
    
    stats = db.get_stats()
    console.print(f"[green]Initialized batch with {stats['total']} image(s)[/green]")
    console.print(f"  Variants: {', '.join(variant_types)}")
    console.print(f"  Alternates: {'Yes' if alternate else 'No'}")
    console.print(f"  Context: {'Yes' if context else 'No'}")
    console.print(f"  Output: {output}/")
    
    # Generate CONTEXT.md for external agents
    _generate_context_file(output, stats['total'])
    console.print(f"  [dim]Generated CONTEXT.md for external AI agents[/dim]")
    
    # Start processing
    console.print("\n[bold]Starting batch processing...[/bold]")
    _run_batch(db, variant_types, alternate, output, context)
    
    db.close()


@batch.command(name="continue")
@click.option(
    "--reset-failed/--no-reset-failed",
    default=False,
    help="Reset failed images to pending before continuing"
)
def continue_batch(reset_failed: bool):
    """Continue batch processing from where it left off.
    
    Resumes processing using the existing SQLite database.
    Use --reset-failed to retry previously failed images.
    
    \b
    Examples:
        vbagent batch continue
        vbagent batch continue --reset-failed
    
    \b
    Tip: Run 'vbagent batch status' to see current progress.
    """
    # Lazy imports
    from vbagent.models.batch import BatchDatabase
    
    console = _get_console()
    
    db_path = Path(".") / BatchDatabase.DB_NAME
    if not db_path.exists():
        console.print("[red]Error:[/red] No batch database found. Run 'vbagent batch init' first.")
        raise SystemExit(1)
    
    db = BatchDatabase(base_dir=".")
    
    # Get configuration
    config = db.get_config()
    if not config:
        console.print("[red]Error:[/red] No batch configuration found. Run 'vbagent batch init' first.")
        db.close()
        raise SystemExit(1)
    
    # Reset failed if requested
    if reset_failed:
        count = db.reset_failed()
        if count > 0:
            console.print(f"[yellow]Reset {count} failed image(s) to pending[/yellow]")
    
    # Show current status
    stats = db.get_stats()
    console.print(f"[cyan]Batch status:[/cyan]")
    console.print(f"  Total: {stats['total']}")
    console.print(f"  Completed: {stats['completed']}")
    console.print(f"  Failed: {stats['failed']}")
    console.print(f"  Pending: {stats['pending']}")
    console.print(f"  In Progress: {stats['in_progress']}")
    
    remaining = stats['pending'] + stats['in_progress']
    if remaining == 0:
        console.print("\n[green]All images have been processed![/green]")
        db.close()
        return
    
    console.print(f"\n[bold]Continuing with {remaining} remaining image(s)...[/bold]")
    
    _run_batch(
        db,
        config["variant_types"],
        config["generate_alternates"],
        config["output_dir"],
        config.get("use_context", True),
    )
    
    db.close()


@batch.command()
def status():
    """Show batch processing status.
    
    Displays current progress, configuration, and any failed images.
    
    \b
    Examples:
        vbagent batch status
    """
    # Lazy imports
    from vbagent.models.batch import BatchDatabase, ProcessingStatus
    
    console = _get_console()
    
    db_path = Path(".") / BatchDatabase.DB_NAME
    if not db_path.exists():
        console.print("[yellow]No batch database found.[/yellow]")
        console.print("Run 'vbagent batch init' to start a new batch.")
        return
    
    db = BatchDatabase(base_dir=".")
    
    # Get configuration
    config = db.get_config()
    if config:
        console.print(_get_panel(
            f"Images Dir: {config['images_dir']}\n"
            f"Output Dir: {config['output_dir']}\n"
            f"Variants: {', '.join(config['variant_types'])}\n"
            f"Alternates: {'Yes' if config['generate_alternates'] else 'No'}",
            title="Batch Configuration",
            border_style="cyan"
        ))
    
    # Get stats
    stats = db.get_stats()
    
    # Create progress table
    table = _get_table(title="Processing Status")
    table.add_column("Status", style="cyan")
    table.add_column("Count", justify="right")
    table.add_column("Percentage", justify="right")
    
    total = stats['total'] or 1
    table.add_row("Completed", str(stats['completed']), f"{stats['completed']/total*100:.1f}%")
    table.add_row("Failed", str(stats['failed']), f"{stats['failed']/total*100:.1f}%")
    table.add_row("Pending", str(stats['pending']), f"{stats['pending']/total*100:.1f}%")
    table.add_row("In Progress", str(stats['in_progress']), f"{stats['in_progress']/total*100:.1f}%")
    table.add_row("Total", str(stats['total']), "100%", style="bold")
    
    console.print(table)
    
    # Show failed images if any
    if stats['failed'] > 0:
        console.print("\n[red]Failed Images:[/red]")
        cursor = db.conn.cursor()
        cursor.execute(
            "SELECT image_path, error_message FROM images WHERE status = ?",
            (ProcessingStatus.FAILED.value,)
        )
        for row in cursor.fetchall():
            console.print(f"  • {row['image_path']}: {row['error_message']}")
    
    db.close()


def _run_batch(
    db: "BatchDatabase",
    variant_types: list[str],
    generate_alternates: bool,
    output_dir: str,
    use_context: bool = True,
):
    """Run batch processing with caffeinate and progress tracking."""
    from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn
    
    console = _get_console()
    
    # Set up signal handler for graceful shutdown
    shutdown_requested = False
    
    def signal_handler(signum, frame):
        nonlocal shutdown_requested
        shutdown_requested = True
        console.print("\n[yellow]Shutdown requested. Finishing current image...[/yellow]")
    
    signal.signal(signal.SIGINT, signal_handler)
    # SIGTERM is not available on Windows
    if sys.platform != "win32":
        signal.signal(signal.SIGTERM, signal_handler)
    
    with SleepInhibitor(console=console):
        pending = db.get_pending_images()
        total = len(pending)
        
        if total == 0:
            console.print("[green]No pending images to process.[/green]")
            return
        
        completed = 0
        failed = 0
        
        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TextColumn("({task.completed}/{task.total})"),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            task = progress.add_task("Processing", total=total)
            
            for record in pending:
                if shutdown_requested:
                    console.print("[yellow]Batch interrupted. Run 'vbagent batch continue' to resume.[/yellow]")
                    break
                
                image_name = Path(record.image_path).name
                progress.update(task, description=f"Processing {image_name}")
                
                console.print(f"\n[bold]{image_name}[/bold]")
                
                success = process_single_image(
                    db=db,
                    record=record,
                    variant_types=variant_types,
                    generate_alternates=generate_alternates,
                    output_dir=output_dir,
                    use_context=use_context,
                )
                
                if success:
                    completed += 1
                    console.print(f"  [green]✓ Completed[/green]")
                else:
                    failed += 1
                
                progress.advance(task)
        
        # Final summary
        console.print(f"\n[bold]Batch Summary:[/bold]")
        console.print(f"  Processed: {completed + failed}")
        console.print(f"  Completed: [green]{completed}[/green]")
        console.print(f"  Failed: [red]{failed}[/red]")
        
        stats = db.get_stats()
        remaining = stats['pending'] + stats['in_progress']
        if remaining > 0:
            console.print(f"  Remaining: [yellow]{remaining}[/yellow]")
            console.print("\nRun 'vbagent batch continue' to process remaining images.")
