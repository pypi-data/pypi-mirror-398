"""CLI command for full pipeline processing.

Orchestrates all agents for complete physics question processing:
Classify → Scan → TikZ → Ideas → Variants.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING, Optional

import click

# Import common utilities
from vbagent.cli.common import (
    format_latex,
    extract_problem_solution,
    _get_console,
    _get_panel,
)

if TYPE_CHECKING:
    from vbagent.models.pipeline import PipelineResult


# Module-level console for helper functions (lazy initialized)
_console = None


def _ensure_console():
    """Ensure console is initialized."""
    global _console
    if _console is None:
        _console = _get_console()
    return _console


def parse_tex_file(tex_path: str) -> str:
    """Read and return the content of a TeX file."""
    return Path(tex_path).read_text()


def extract_items_from_tex(content: str) -> list[str]:
    """Extract individual items from a TeX file.
    
    Splits content by \\item markers to get individual problems.
    """
    parts = re.split(r'(?=\\item\b)', content)
    items = [p.strip() for p in parts if p.strip() and '\\item' in p]
    return items


def filter_items_by_range(
    items: list[str],
    item_range: Optional[tuple[int, int]],
) -> list[str]:
    """Filter items by the specified range (1-based, inclusive)."""
    if not item_range:
        return items
    
    start, end = item_range
    start_idx = max(0, start - 1)
    end_idx = min(len(items), end)
    
    return items[start_idx:end_idx]


# extract_problem_solution and format_latex are imported from common module


def get_base_name(source_path: str) -> str:
    """Extract base name from source path (without extension)."""
    return Path(source_path).stem


def insert_tikz_into_latex(latex: str, tikz_code: str) -> str:
    """Replace diagram placeholders with actual TikZ code.
    
    Handles two types of placeholders:
    1. Main diagram: \\begin{center}\\input{diagram}\\end{center}
    2. Option diagrams: \\OptionA, \\OptionB, etc. with \\def definitions
    
    Args:
        latex: The LaTeX content with placeholder(s)
        tikz_code: The generated TikZ code (may include \\def\\OptionX{...})
        
    Returns:
        LaTeX with TikZ code inserted
    """
    result = latex
    
    # Check if tikz_code contains option definitions (\def\OptionA, etc.)
    has_option_defs = r'\def\Option' in tikz_code or r'\\def\\Option' in tikz_code
    
    if has_option_defs:
        # Insert option definitions before \begin{tasks}
        tasks_pattern = r'(% OPTIONS_DIAGRAMS:[^\n]*\n)?(\s*\\begin\{tasks\})'
        
        # Clean up the tikz_code - ensure proper escaping
        tikz_to_insert = tikz_code.strip()
        
        def replace_tasks(match):
            return f"{tikz_to_insert}\n{match.group(2)}"
        
        result = re.sub(tasks_pattern, replace_tasks, result)
        
        # Remove the OPTIONS_DIAGRAMS comment if present
        result = re.sub(r'% OPTIONS_DIAGRAMS:[^\n]*\n', '', result)
    else:
        # Handle main diagram placeholder
        # Pattern to match the placeholder (with flexible whitespace)
        placeholder_pattern = r'\\begin\{center\}\s*\\input\{diagram\}\s*\\end\{center\}'
        
        # Wrap TikZ code in center environment if not already wrapped
        if '\\begin{center}' not in tikz_code:
            tikz_wrapped = f"\\begin{{center}}\n{tikz_code}\n\\end{{center}}"
        else:
            tikz_wrapped = tikz_code
        
        # Replace placeholder with actual TikZ code
        # Use a function to avoid issues with backslash escaping
        def replace_diagram(match):
            return tikz_wrapped
        
        result = re.sub(placeholder_pattern, replace_diagram, result)
        
        # If no placeholder found, check for simpler pattern
        if result == latex:
            simple_pattern = r'\\input\{diagram\}'
            if re.search(simple_pattern, latex):
                result = re.sub(simple_pattern, lambda m: tikz_code, result)
    
    return result


def _generate_context_file(output_path: Path, problem_count: int) -> None:
    """Generate CONTEXT.md file for external AI agents.
    
    Creates a documentation file in the output directory that helps
    external AI tools (Codex, Claude Code, Cursor, etc.) understand
    the directory structure and work with physics problems.
    
    Args:
        output_path: Output directory path
        problem_count: Number of problems processed
    """
    from vbagent.templates.agentic_context import generate_context_file
    
    output_path.mkdir(parents=True, exist_ok=True)
    
    content = generate_context_file(
        directory_name=output_path.name,
        problem_count=problem_count,
    )
    
    context_file = output_path / "CONTEXT.md"
    context_file.write_text(content)


def generate_image_paths_from_range(
    image_path: str,
    item_range: tuple[int, int],
) -> list[str]:
    """Generate image paths from a template and range.
    
    Given an image path like 'images/Problem_3.png' and range (1, 5),
    generates paths: Problem_1.png, Problem_2.png, ..., Problem_5.png
    
    Supports patterns:
    - Problem_3.png -> Problem_1.png, Problem_2.png, ...
    - question3.png -> question1.png, question2.png, ...
    - img_03.png -> img_01.png, img_02.png, ...
    """
    path = Path(image_path)
    parent = path.parent
    stem = path.stem
    suffix = path.suffix
    
    # Find the number pattern in the filename
    # Match trailing number with optional underscore/hyphen prefix
    match = re.search(r'([_\-]?)(\d+)$', stem)
    
    if not match:
        # No number found, can't generate range
        return [image_path]
    
    prefix = stem[:match.start()]
    separator = match.group(1)  # underscore, hyphen, or empty
    num_str = match.group(2)
    num_width = len(num_str)  # preserve zero-padding width
    
    start, end = item_range
    paths = []
    
    for i in range(start, end + 1):
        # Format number with same width (zero-padded if original was)
        new_num = str(i).zfill(num_width)
        new_stem = f"{prefix}{separator}{new_num}"
        new_path = parent / f"{new_stem}{suffix}"
        
        if new_path.exists():
            paths.append(str(new_path))
        else:
            _get_console().print(f"[yellow]Warning:[/yellow] Image not found: {new_path}")
    
    return paths


def save_pipeline_result_organized(
    result: PipelineResult,
    base_dir: Path,
    base_name: str,
) -> dict[str, str]:
    """Save pipeline result to organized directory structure.
    
    Structure:
        agentic/
        ├── scans/{base_name}.tex
        ├── classifications/{base_name}.json
        ├── alternates/{base_name}.tex
        ├── variants/
        │   ├── numerical/{base_name}.tex
        │   ├── context/{base_name}.tex
        │   └── ...
        ├── ideas/{base_name}.json
        └── tikz/{base_name}.tex
    
    Returns dict mapping output type to file path.
    """
    saved_files = {}
    
    # Save scanned LaTeX (with formatting)
    scans_dir = base_dir / "scans"
    scans_dir.mkdir(parents=True, exist_ok=True)
    latex_path = scans_dir / f"{base_name}.tex"
    latex_path.write_text(format_latex(result.latex))
    saved_files["scan"] = str(latex_path)
    
    # Save classification
    class_dir = base_dir / "classifications"
    class_dir.mkdir(parents=True, exist_ok=True)
    class_path = class_dir / f"{base_name}.json"
    class_path.write_text(result.classification.model_dump_json(indent=2))
    saved_files["classification"] = str(class_path)
    
    # Save TikZ if present (with formatting)
    if result.tikz_code:
        tikz_dir = base_dir / "tikz"
        tikz_dir.mkdir(parents=True, exist_ok=True)
        tikz_path = tikz_dir / f"{base_name}.tex"
        tikz_path.write_text(format_latex(result.tikz_code))
        saved_files["tikz"] = str(tikz_path)
    
    # Save ideas if present
    if result.ideas:
        ideas_dir = base_dir / "ideas"
        ideas_dir.mkdir(parents=True, exist_ok=True)
        ideas_path = ideas_dir / f"{base_name}.json"
        ideas_path.write_text(result.ideas.model_dump_json(indent=2))
        saved_files["ideas"] = str(ideas_path)
    
    # Save alternate solutions (with formatting)
    if result.alternate_solutions:
        alt_dir = base_dir / "alternates"
        alt_dir.mkdir(parents=True, exist_ok=True)
        alt_path = alt_dir / f"{base_name}.tex"
        formatted_alts = [format_latex(alt) for alt in result.alternate_solutions]
        combined = "\n\n% --- Alternate Solution ---\n\n".join(formatted_alts)
        alt_path.write_text(combined)
        saved_files["alternates"] = str(alt_path)
    
    # Save variants in subdirectories by type (with formatting)
    for variant_type, variant_latex in result.variants.items():
        variant_dir = base_dir / "variants" / variant_type
        variant_dir.mkdir(parents=True, exist_ok=True)
        variant_path = variant_dir / f"{base_name}.tex"
        variant_path.write_text(format_latex(variant_latex))
        saved_files[f"variant_{variant_type}"] = str(variant_path)
    
    return saved_files


def save_pipeline_result(result: PipelineResult, output_dir: Path) -> dict[str, str]:
    """Save pipeline result to output directory (legacy flat structure).
    
    Returns dict mapping output type to file path.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    saved_files = {}
    
    # Save classification
    class_path = output_dir / "classification.json"
    class_path.write_text(result.classification.model_dump_json(indent=2))
    saved_files["classification"] = str(class_path)
    
    # Save LaTeX (with formatting)
    latex_path = output_dir / "scanned.tex"
    latex_path.write_text(format_latex(result.latex))
    saved_files["latex"] = str(latex_path)
    
    # Save TikZ if present (with formatting)
    if result.tikz_code:
        tikz_path = output_dir / "diagram.tex"
        tikz_path.write_text(format_latex(result.tikz_code))
        saved_files["tikz"] = str(tikz_path)
    
    # Save ideas if present
    if result.ideas:
        ideas_path = output_dir / "ideas.json"
        ideas_path.write_text(result.ideas.model_dump_json(indent=2))
        saved_files["ideas"] = str(ideas_path)
    
    # Save alternate solutions (with formatting)
    if result.alternate_solutions:
        alt_path = output_dir / "alternates.tex"
        formatted_alts = [format_latex(alt) for alt in result.alternate_solutions]
        combined = "\n\n% --- Alternate Solution ---\n\n".join(formatted_alts)
        alt_path.write_text(combined)
        saved_files["alternates"] = str(alt_path)
    
    # Save variants (with formatting)
    for variant_type, variant_latex in result.variants.items():
        variant_path = output_dir / f"variant_{variant_type}.tex"
        variant_path.write_text(format_latex(variant_latex))
        saved_files[f"variant_{variant_type}"] = str(variant_path)
    
    # Save full result as JSON
    result_path = output_dir / "pipeline_result.json"
    result_path.write_text(result.model_dump_json(indent=2))
    saved_files["full_result"] = str(result_path)
    
    return saved_files


def _process_images_parallel(
    image_paths: list[str],
    variant_types: list[str],
    generate_alternate: bool,
    generate_ideas: bool,
    use_context: bool,
    output_dir: str,
    num_workers: int,
    console,
) -> tuple[list, int]:
    """Process multiple images in parallel using ThreadPoolExecutor.
    
    Args:
        image_paths: List of image paths to process
        variant_types: Variant types to generate
        generate_alternate: Whether to generate alternate solutions
        generate_ideas: Whether to extract ideas
        use_context: Whether to use reference context
        output_dir: Output directory for results
        num_workers: Number of parallel workers
        console: Rich console for output
        
    Returns:
        Tuple of (results list, failed count)
    """
    import concurrent.futures
    import threading
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
    
    results = []
    failed_count = 0
    output_path = Path(output_dir)
    
    # Thread-safe counters
    lock = threading.Lock()
    completed = {"success": 0, "failed": 0}
    
    def process_single_image(img_path: str) -> tuple[str, Optional["PipelineResult"], Optional[str]]:
        """Process a single image and return (path, result, error)."""
        try:
            result = process_image(
                image_path=img_path,
                variant_types=variant_types,
                generate_alternate=generate_alternate,
                generate_ideas=generate_ideas,
                use_context=use_context,
            )
            
            # Save immediately (thread-safe - each file is unique)
            base_name = get_base_name(result.source_path)
            save_pipeline_result_organized(result, output_path, base_name)
            
            return (img_path, result, None)
        except Exception as e:
            return (img_path, None, str(e))
    
    # Use progress bar for parallel processing
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        task = progress.add_task(
            f"[cyan]Processing {len(image_paths)} images...",
            total=len(image_paths)
        )
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
            # Submit all tasks
            future_to_path = {
                executor.submit(process_single_image, path): path
                for path in image_paths
            }
            
            # Process results as they complete
            for future in concurrent.futures.as_completed(future_to_path):
                img_path = future_to_path[future]
                img_name = Path(img_path).name
                
                try:
                    path, result, error = future.result()
                    
                    if error:
                        with lock:
                            completed["failed"] += 1
                        console.print(f"[red]✗ {img_name}: {error}[/red]")
                    else:
                        with lock:
                            completed["success"] += 1
                            results.append(result)
                        console.print(f"[green]✓ {img_name}[/green]")
                        
                except Exception as e:
                    with lock:
                        completed["failed"] += 1
                    console.print(f"[red]✗ {img_name}: {e}[/red]")
                
                progress.update(task, advance=1)
    
    return results, completed["failed"]


CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}


@click.command(context_settings=CONTEXT_SETTINGS)
@click.option(
    "-i", "--image",
    type=click.Path(exists=True),
    help="Image file path to process"
)
@click.option(
    "-t", "--tex",
    type=click.Path(exists=True),
    help="TeX file path containing problem(s)"
)
@click.option(
    "-r", "--range", "item_range",
    nargs=2,
    type=int,
    help="Range to process (1-based inclusive). For images: Problem_X.png where X is in range. For TeX: items 1-N."
)
@click.option(
    "--variants", "variant_types_str",
    type=str,
    default=None,
    help="Variant types to generate (comma-separated: numerical,context,conceptual,calculus). Disabled by default."
)
@click.option(
    "--alternate/--no-alternate",
    default=False,
    help="Generate alternate solutions (default: disabled)"
)
@click.option(
    "--ideas/--no-ideas",
    default=False,
    help="Extract physics concepts and ideas (default: disabled)"
)
@click.option(
    "--ref", "ref_dirs",
    multiple=True,
    type=click.Path(exists=True),
    help="Reference directories for TikZ generation"
)
@click.option(
    "-o", "--output",
    type=click.Path(),
    default="agentic",
    help="Output directory for saving results (default: agentic)"
)
@click.option(
    "--context/--no-context",
    default=True,
    help="Use reference context from ~/.config/vbagent (default: yes)"
)
@click.option(
    "-p", "--parallel",
    type=int,
    default=1,
    help="Number of images to process in parallel (default: 1, max recommended: 5)"
)
def process(
    image: Optional[str],
    tex: Optional[str],
    item_range: Optional[tuple[int, int]],
    variant_types_str: Optional[str],
    alternate: bool,
    ideas: bool,
    ref_dirs: tuple[str, ...],
    output: str,
    context: bool,
    parallel: int,
):
    """Full pipeline: Classify → Scan → TikZ → Ideas → Variants.
    
    Orchestrates all agents for complete physics question processing.
    Processes images or TeX files through the full pipeline.
    
    By default, only classification, scanning, and TikZ generation run.
    Use --ideas, --alternate, and --variants to enable additional stages.
    
    \b
    Pipeline Stages:
        1. Classification - Extract metadata from image
        2. Scanning - Extract LaTeX from image
        3. TikZ - Generate diagram code (if has_diagram)
        4. Ideas - Extract physics concepts (--ideas)
        5. Alternates - Generate alternate solutions (--alternate)
        6. Variants - Generate problem variants (--variants)
    
    \b
    Output Structure:
        agentic/
        ├── scans/problem_1.tex
        ├── classifications/problem_1.json
        ├── alternates/problem_1.tex      (if --alternate)
        ├── variants/numerical/problem_1.tex  (if --variants)
        ├── ideas/problem_1.json          (if --ideas)
        └── tikz/problem_1.tex
    
    \b
    Examples:
        vbagent process -i images/Problem_1.png
        vbagent process -i images/Problem_1.png --ideas
        vbagent process -i images/Problem_1.png --ideas --alternate
        vbagent process -i images/Problem_1.png --variants numerical,context
        vbagent process -i images/Problem_1.png -r 1 5
        vbagent process -i images/Problem_1.png -r 1 10 --parallel 3
        vbagent process -t problems.tex --range 1 5 --alternate --ideas
    """
    # Lazy imports - only load heavy dependencies when command runs
    from vbagent.agents.classifier import classify as classify_image
    from vbagent.agents.scanner import scan as scan_image
    from vbagent.agents.tikz import generate_tikz
    from vbagent.agents.idea import extract_ideas
    from vbagent.agents.alternate import generate_alternate as gen_alternate
    from vbagent.agents.variant import generate_variant
    from vbagent.models.pipeline import PipelineResult
    from vbagent.references.store import ReferenceStore
    
    console = _get_console()
    
    # Parse variant types from comma-separated string
    valid_variants = {"numerical", "context", "conceptual", "calculus"}
    variant_types: list[str] = []
    if variant_types_str:
        for v in variant_types_str.replace(" ", "").split(","):
            if v and v in valid_variants:
                variant_types.append(v)
            elif v:
                console.print(f"[yellow]Warning:[/yellow] Unknown variant type '{v}', skipping")
    
    # Validate input
    if not image and not tex:
        console.print("[red]Error:[/red] Either --image or --tex must be provided")
        raise SystemExit(1)
    
    try:
        # Initialize reference store if directories provided
        if ref_dirs:
            store = ReferenceStore.get_instance(directories=list(ref_dirs))
            with console.status("[bold blue]Indexing reference files..."):
                indexed_count = store.index_files()
            console.print(f"[dim]Indexed {indexed_count} reference files[/dim]")
        
        results: list[PipelineResult] = []
        
        if image:
            # Determine which images to process
            if item_range:
                # Generate image paths from range
                image_paths = generate_image_paths_from_range(image, item_range)
                if not image_paths:
                    console.print("[red]Error:[/red] No images found in specified range")
                    raise SystemExit(1)
                console.print(f"[cyan]Processing {len(image_paths)} image(s) in range {item_range[0]}-{item_range[1]}...[/cyan]")
            else:
                image_paths = [image]
            
            # Clamp parallel workers
            num_workers = min(max(1, parallel), len(image_paths), 10)
            
            if num_workers > 1 and len(image_paths) > 1:
                # Parallel processing with progress bar
                console.print(f"[cyan]Using {num_workers} parallel workers[/cyan]")
                results, failed_count = _process_images_parallel(
                    image_paths=image_paths,
                    variant_types=variant_types,
                    generate_alternate=alternate,
                    generate_ideas=ideas,
                    use_context=context,
                    output_dir=output,
                    num_workers=num_workers,
                    console=console,
                )
            else:
                # Sequential processing (single image or parallel=1)
                failed_count = 0
                for idx, img_path in enumerate(image_paths, 1):
                    if len(image_paths) > 1:
                        console.print(f"\n[bold]Image {idx}/{len(image_paths)}: {Path(img_path).name}[/bold]")
                    
                    try:
                        result = process_image(
                            image_path=img_path,
                            variant_types=variant_types,
                            generate_alternate=alternate,
                            generate_ideas=ideas,
                            use_context=context,
                        )
                        results.append(result)
                        
                        # Save immediately after each successful processing
                        output_path = Path(output)
                        base_name = get_base_name(result.source_path)
                        saved = save_pipeline_result_organized(result, output_path, base_name)
                        console.print(f"[green]✓ Saved {base_name}[/green]")
                        
                    except Exception as e:
                        console.print(f"[red]✗ Failed {Path(img_path).name}: {e}[/red]")
                        failed_count += 1
                        continue
        
        elif tex:
            # Process TeX file
            content = parse_tex_file(tex)
            items = extract_items_from_tex(content)
            
            if items:
                items = filter_items_by_range(items, item_range)
                console.print(f"[cyan]Processing {len(items)} item(s)...[/cyan]")
                
                for idx, item in enumerate(items, 1):
                    console.print(f"\n[bold]Item {idx}/{len(items)}[/bold]")
                    result = process_tex_item(
                        tex_content=item,
                        source_path=tex,
                        variant_types=variant_types,
                        generate_alternate=alternate,
                        generate_ideas=ideas,
                        use_context=context,
                    )
                    results.append(result)
            else:
                # Process entire content as single item
                result = process_tex_item(
                    tex_content=content,
                    source_path=tex,
                    variant_types=variant_types,
                    generate_alternate=alternate,
                    generate_ideas=ideas,
                    use_context=context,
                )
                results.append(result)
        
        # For TeX processing, save results (images are saved immediately above)
        output_path = Path(output)
        if tex and results:
            console.print(f"\n[cyan]Saving results to:[/cyan] {output_path}/")
            
            for result in results:
                base_name = get_base_name(result.source_path)
                saved = save_pipeline_result_organized(result, output_path, base_name)
                
                console.print(f"\n[green]Saved {base_name}:[/green]")
                for file_type, file_path in saved.items():
                    console.print(f"  • {file_type}: {file_path}")
        
        # Generate CONTEXT.md for external AI agents
        if results:
            _generate_context_file(output_path, len(results))
            console.print(f"\n[dim]Generated CONTEXT.md for external AI agents[/dim]")
        
        # Summary
        console.print(f"\n[bold green]Pipeline complete![/bold green]")
        if image:
            total = len(image_paths) if item_range else 1
            console.print(f"Processed {len(results)}/{total} image(s) successfully")
            if failed_count > 0:
                console.print(f"[yellow]Failed: {failed_count} image(s)[/yellow]")
        else:
            console.print(f"Processed {len(results)} item(s)")
        
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)
    except Exception as e:
        console.print(f"[red]Pipeline failed:[/red] {e}")
        raise SystemExit(1)


def process_image(
    image_path: str,
    variant_types: list[str],
    generate_alternate: bool,
    generate_ideas: bool = False,
    use_context: bool = True,
) -> PipelineResult:
    """Process an image through the full pipeline.
    
    Pipeline stages:
    1. Classification (sequential - needed for other stages)
    2. Scanning + TikZ (PARALLEL if has_diagram - both use same image)
    3. Ideas, Alternates, Variants (sequential, optional)
    """
    import concurrent.futures
    import threading
    
    # Lazy imports
    from vbagent.agents.classifier import classify as classify_image
    from vbagent.agents.scanner import scan as scan_image
    from vbagent.agents.tikz import generate_tikz
    from vbagent.agents.idea import extract_ideas
    from vbagent.agents.variant import generate_variant
    from vbagent.models.pipeline import PipelineResult
    
    console = _get_console()
    
    # Stage 1: Classification (must be sequential - needed for scanning)
    with console.status("[bold green]Stage 1: Classifying image..."):
        classification = classify_image(image_path)
    
    console.print(f"[cyan]Type:[/cyan] {classification.question_type}")
    console.print(f"[cyan]Difficulty:[/cyan] {classification.difficulty}")
    console.print(f"[cyan]Has Diagram:[/cyan] {'Yes' if classification.has_diagram else 'No'}")
    
    # Stage 2 & 3: Scanning + TikZ (PARALLEL if has_diagram)
    tikz_code = None
    latex = None
    
    if classification.has_diagram:
        # Run scanning and TikZ generation in parallel
        console.print("[bold green]Stage 2+3: Scanning & TikZ (parallel)...[/bold green]")
        
        # Prepare TikZ description based on classification
        tikz_description = f"Generate TikZ for {classification.diagram_type or 'diagram'}"
        
        # Results holders with completion flags
        scan_result_holder = {"result": None, "error": None, "done": False}
        tikz_result_holder = {"result": None, "error": None, "done": False}
        scan_shown = False
        tikz_shown = False
        
        def run_scan():
            try:
                scan_result_holder["result"] = scan_image(
                    image_path, classification, use_context=use_context
                )
            except Exception as e:
                scan_result_holder["error"] = e
            finally:
                scan_result_holder["done"] = True
        
        def run_tikz():
            try:
                tikz_result_holder["result"] = generate_tikz(
                    description=tikz_description,
                    image_path=image_path,
                    use_context=use_context,
                    classification=classification,  # Pass for metadata-based context
                )
            except Exception as e:
                tikz_result_holder["error"] = e
            finally:
                tikz_result_holder["done"] = True
        
        # Start both threads
        scan_thread = threading.Thread(target=run_scan, daemon=True)
        tikz_thread = threading.Thread(target=run_tikz, daemon=True)
        
        console.print("[dim]  → Scanning LaTeX...[/dim]")
        console.print("[dim]  → Generating TikZ...[/dim]")
        
        scan_thread.start()
        tikz_thread.start()
        
        # Wait for both with interrupt handling, show results as they complete
        # Timeout for TikZ generation (5 minutes max) - prevents infinite hangs
        import time
        tikz_timeout = 600  # 5 minutes
        tikz_start_time = time.time()
        tikz_timed_out = False
        
        while scan_thread.is_alive() or tikz_thread.is_alive():
            # Check if scan completed and show result
            if scan_result_holder["done"] and not scan_shown:
                scan_shown = True
                if scan_result_holder["error"]:
                    console.print("[red]  ✗ Scanning failed[/red]")
                else:
                    console.print("[green]  ✓ Scanning complete[/green]")
                    console.print(_get_panel(
                        scan_result_holder["result"].latex,
                        title="Extracted LaTeX",
                        border_style="dim"
                    ))
            
            # Check if tikz completed and show result
            if tikz_result_holder["done"] and not tikz_shown:
                tikz_shown = True
                if tikz_result_holder["error"]:
                    console.print("[red]  ✗ TikZ generation failed[/red]")
                else:
                    console.print("[green]  ✓ TikZ complete[/green]")
                    console.print(_get_panel(
                        tikz_result_holder["result"],
                        title="Generated TikZ",
                        border_style="cyan"
                    ))
            
            # Check for TikZ timeout (only if scan is done but tikz is still running)
            if scan_result_holder["done"] and tikz_thread.is_alive() and not tikz_timed_out:
                elapsed = time.time() - tikz_start_time
                if elapsed > tikz_timeout:
                    tikz_timed_out = True
                    console.print(f"[yellow]  ⚠ TikZ generation timed out after {int(elapsed)}s, continuing without diagram[/yellow]")
                    tikz_result_holder["error"] = TimeoutError(f"TikZ generation timed out after {tikz_timeout}s")
                    tikz_result_holder["done"] = True
                    break
            
            scan_thread.join(timeout=0.1)
            tikz_thread.join(timeout=0.1)
        
        # Show any remaining results that weren't shown in the loop
        if not scan_shown and scan_result_holder["done"]:
            if scan_result_holder["error"]:
                console.print("[red]  ✗ Scanning failed[/red]")
            else:
                console.print("[green]  ✓ Scanning complete[/green]")
                console.print(_get_panel(
                    scan_result_holder["result"].latex,
                    title="Extracted LaTeX",
                    border_style="dim"
                ))
        
        if not tikz_shown and tikz_result_holder["done"]:
            if tikz_result_holder["error"]:
                console.print("[red]  ✗ TikZ generation failed[/red]")
            else:
                console.print("[green]  ✓ TikZ complete[/green]")
                console.print(_get_panel(
                    tikz_result_holder["result"],
                    title="Generated TikZ",
                    border_style="cyan"
                ))
        
        # Check for errors - scan errors are fatal, tikz errors are recoverable
        if scan_result_holder["error"]:
            raise scan_result_holder["error"]
        
        latex = scan_result_holder["result"].latex
        
        # TikZ errors are recoverable - continue without diagram
        if tikz_result_holder["error"]:
            if tikz_timed_out:
                console.print("[yellow]  ⚠ Continuing without TikZ diagram due to timeout[/yellow]")
            else:
                console.print(f"[yellow]  ⚠ TikZ generation failed: {tikz_result_holder['error']}[/yellow]")
            tikz_code = None
        else:
            tikz_code = tikz_result_holder["result"]
        
        # Check if we need to handle option diagrams (detected after scanning)
        has_option_diagrams = r'\OptionA' in latex or r'\OptionB' in latex
        if has_option_diagrams:
            # Need to regenerate TikZ for option diagrams
            import re
            options_match = re.search(r'% OPTIONS_DIAGRAMS:\s*(.+?)(?:\n|$)', latex)
            if options_match:
                tikz_description = f"Generate option diagrams: {options_match.group(1)}"
            else:
                tikz_description = "Generate TikZ diagrams for MCQ options (\\OptionA, \\OptionB, \\OptionC, \\OptionD)"
            
            console.print("[dim]  → Generating option diagrams...[/dim]")
            tikz_code = generate_tikz(
                description=tikz_description,
                image_path=image_path,
                use_context=use_context,
                classification=classification,
            )
            console.print("[green]  ✓ Option diagrams complete[/green]")
            console.print(_get_panel(tikz_code, title="Option Diagrams TikZ", border_style="cyan"))
        
        # Replace placeholders with actual TikZ code and show combined result
        if tikz_code and (r'\input{diagram}' in latex or has_option_diagrams):
            console.print("[dim]  → Combining LaTeX + TikZ...[/dim]")
            latex = insert_tikz_into_latex(latex, tikz_code)
            latex = format_latex(latex)
            console.print("[green]  ✓ Combined[/green]")
            console.print(_get_panel(latex, title="Final Combined LaTeX", border_style="green"))
        elif not tikz_code and r'\input{diagram}' in latex:
            # TikZ failed/timed out - keep placeholder for manual completion
            console.print("[yellow]  ⚠ Diagram placeholder kept - TikZ generation failed[/yellow]")
    else:
        # No diagram - just run scanning
        console.print("[bold green]Stage 2: Scanning image...[/bold green]")
        console.print("[dim]  → Scanning LaTeX...[/dim]")
        scan_result = scan_image(image_path, classification, use_context=use_context)
        
        latex = scan_result.latex
        console.print("[green]  ✓ Scanning complete[/green]")
        console.print(_get_panel(latex, title="Extracted LaTeX", border_style="dim"))
        
        # Check for option diagrams even if has_diagram is False
        has_option_diagrams = r'\OptionA' in latex or r'\OptionB' in latex
        if has_option_diagrams:
            import re
            options_match = re.search(r'% OPTIONS_DIAGRAMS:\s*(.+?)(?:\n|$)', latex)
            if options_match:
                tikz_description = f"Generate option diagrams: {options_match.group(1)}"
            else:
                tikz_description = "Generate TikZ diagrams for MCQ options (\\OptionA, \\OptionB, \\OptionC, \\OptionD)"
            
            console.print("[bold green]Stage 3: Generating option diagrams...[/bold green]")
            console.print("[dim]  → Generating TikZ for options...[/dim]")
            tikz_code = generate_tikz(
                description=tikz_description,
                image_path=image_path,
                use_context=use_context,
                classification=classification,
            )
            console.print("[green]  ✓ Option diagrams complete[/green]")
            console.print(_get_panel(tikz_code, title="Option Diagrams TikZ", border_style="cyan"))
            
            console.print("[dim]  → Combining LaTeX + TikZ...[/dim]")
            latex = insert_tikz_into_latex(latex, tikz_code)
            latex = format_latex(latex)
            console.print("[green]  ✓ Combined[/green]")
            console.print(_get_panel(latex, title="Final Combined LaTeX", border_style="green"))
    
    # Stage 4: Ideas (optional)
    problem, solution = extract_problem_solution(latex)
    ideas = None
    if generate_ideas and problem and solution:
        with console.status("[bold green]Stage 4: Extracting ideas..."):
            ideas = extract_ideas(problem, solution)
        # Display ideas in a formatted panel
        ideas_text = f"[bold]Concepts:[/bold] {', '.join(ideas.concepts)}\n"
        ideas_text += f"[bold]Formulas:[/bold] {', '.join(ideas.formulas)}\n"
        ideas_text += f"[bold]Techniques:[/bold] {', '.join(ideas.techniques)}\n"
        ideas_text += f"[bold]Difficulty Factors:[/bold] {', '.join(ideas.difficulty_factors)}"
        console.print(_get_panel(ideas_text, title="Extracted Ideas", border_style="yellow"))
    
    # Stage 5: Alternates (optional)
    alternate_solutions = []
    if generate_alternate and problem and solution:
        with console.status("[bold green]Stage 5: Generating alternate solution..."):
            alt = generate_alternate_solution(problem, solution, ideas)
            alternate_solutions.append(alt)
        console.print(_get_panel(alt, title="Alternate Solution", border_style="magenta"))
    
    # Stage 6: Variants (optional)
    variants = {}
    for vtype in variant_types:
        with console.status(f"[bold green]Stage 6: Generating {vtype} variant..."):
            variant_latex = generate_variant(latex, vtype, ideas, use_context=use_context)
            variants[vtype] = variant_latex
        console.print(_get_panel(variant_latex, title=f"{vtype.title()} Variant", border_style="green"))
    
    return PipelineResult(
        source_path=image_path,
        classification=classification,
        latex=latex,
        tikz_code=tikz_code,
        ideas=ideas,
        alternate_solutions=alternate_solutions,
        variants=variants,
    )


def process_tex_item(
    tex_content: str,
    source_path: str,
    variant_types: list[str],
    generate_alternate: bool,
    generate_ideas: bool = False,
    use_context: bool = True,
) -> PipelineResult:
    """Process a TeX item through the pipeline (skips classification/scanning)."""
    # Lazy imports
    from vbagent.agents.idea import extract_ideas
    from vbagent.agents.variant import generate_variant
    from vbagent.models.classification import ClassificationResult
    from vbagent.models.pipeline import PipelineResult
    
    console = _get_console()
    
    # Create a minimal classification for TeX input
    classification = ClassificationResult(
        question_type="subjective",
        difficulty="medium",
        topic="physics",
        subtopic="general",
        has_diagram=False,
        diagram_type=None,
        num_options=None,
        estimated_marks=4,
        key_concepts=[],
        requires_calculus=False,
        confidence=1.0,
    )
    
    latex = tex_content
    
    # Extract problem and solution
    problem, solution = extract_problem_solution(latex)
    
    # Stage 4: Ideas (optional)
    ideas = None
    if generate_ideas and problem and solution:
        with console.status("[bold green]Extracting ideas..."):
            ideas = extract_ideas(problem, solution)
        # Display ideas in a formatted panel
        ideas_text = f"[bold]Concepts:[/bold] {', '.join(ideas.concepts)}\n"
        ideas_text += f"[bold]Formulas:[/bold] {', '.join(ideas.formulas)}\n"
        ideas_text += f"[bold]Techniques:[/bold] {', '.join(ideas.techniques)}\n"
        ideas_text += f"[bold]Difficulty Factors:[/bold] {', '.join(ideas.difficulty_factors)}"
        console.print(_get_panel(ideas_text, title="Extracted Ideas", border_style="yellow"))
    
    # Stage 5: Alternates (optional)
    alternate_solutions = []
    if generate_alternate and problem and solution:
        with console.status("[bold green]Generating alternate solution..."):
            alt = generate_alternate_solution(problem, solution, ideas)
            alternate_solutions.append(alt)
        console.print(_get_panel(alt, title="Alternate Solution", border_style="magenta"))
    
    # Stage 6: Variants (optional)
    variants = {}
    for vtype in variant_types:
        with console.status(f"[bold green]Generating {vtype} variant..."):
            variant_latex = generate_variant(latex, vtype, ideas, use_context=use_context)
            variants[vtype] = variant_latex
        console.print(_get_panel(variant_latex, title=f"{vtype.title()} Variant", border_style="green"))
    
    return PipelineResult(
        source_path=source_path,
        classification=classification,
        latex=latex,
        tikz_code=None,
        ideas=ideas,
        alternate_solutions=alternate_solutions,
        variants=variants,
    )


def generate_alternate_solution(problem: str, solution: str, ideas) -> str:
    """Generate an alternate solution using the alternate agent."""
    from vbagent.agents.alternate import generate_alternate
    return generate_alternate(problem, solution, ideas)
