"""CLI commands for managing reference context files.

Provides commands to add, remove, list, and configure reference files
stored in ~/.config/vbagent for use as context in LLM prompts.
"""

from pathlib import Path

import click

# Import CATEGORIES at module level since it's used in decorators
# This is a simple list constant, not a heavy import
from vbagent.references.context import CATEGORIES, ContextStore


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


# Lazy-loaded console and imports
console = None
Panel = None
Table = None


def _ensure_imports():
    """Ensure lazy imports are loaded."""
    global console, Panel, Table
    if console is None:
        console = _get_console()
    if Panel is None:
        from rich.panel import Panel as P
        Panel = P
    if Table is None:
        from rich.table import Table as T
        Table = T


CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}


@click.group(context_settings=CONTEXT_SETTINGS)
def ref():
    """Manage reference files for context.
    
    Reference files are stored in ~/.config/vbagent/references/
    and can be used as examples to improve LLM output quality.
    
    \b
    Categories:
        tikz      - TikZ/PGF code examples
        latex     - LaTeX formatting examples
        variants  - Variant generation examples
        problems  - Example physics problems
    
    \b
    Examples:
        vbagent ref add tikz diagram.tex
        vbagent ref add variants example.tex -d "Numerical variant"
        vbagent ref list
        vbagent ref list -c tikz
        vbagent ref remove tikz diagram.tex
        vbagent ref enable
        vbagent ref disable
        vbagent ref status
    """
    pass


@ref.command()
@click.argument("category", type=click.Choice(CATEGORIES))
@click.argument("file", type=click.Path(exists=True))
@click.option("-n", "--name", help="Custom name for the reference (default: filename)")
@click.option("-d", "--description", help="Description of the reference")
def add(category: str, file: str, name: str, description: str):
    """Add a reference file to a category.
    
    \b
    Arguments:
        CATEGORY  Category to add to (tikz, latex, variants, problems)
        FILE      Path to the file to add
    
    \b
    Examples:
        vbagent ref add tikz my_diagram.tex
        vbagent ref add variants example.tex -n "numerical_example.tex"
        vbagent ref add latex formatting.tex -d "Standard formatting template"
    """
    _ensure_imports()
    store = ContextStore.get_instance()
    
    try:
        ref = store.add_reference(
            source_path=file,
            category=category,
            name=name,
            description=description,
        )
        console.print(f"[green]✓[/green] Added '{ref.name}' to {category}")
        console.print(f"  [dim]Stored at: {ref.path}[/dim]")
        
    except FileExistsError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)
    except FileNotFoundError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        raise SystemExit(1)


@ref.command()
@click.argument("category", type=click.Choice(CATEGORIES))
@click.argument("name")
def remove(category: str, name: str):
    """Remove a reference file.
    
    \b
    Arguments:
        CATEGORY  Category of the reference
        NAME      Name of the reference file
    
    \b
    Examples:
        vbagent ref remove tikz diagram.tex
        vbagent ref remove variants example.tex
    """
    _ensure_imports()
    store = ContextStore.get_instance()
    
    if store.remove_reference(category, name):
        console.print(f"[green]✓[/green] Removed '{name}' from {category}")
    else:
        console.print(f"[yellow]Not found:[/yellow] '{name}' in {category}")


@ref.command(name="list")
@click.option("-c", "--category", type=click.Choice(CATEGORIES), help="Filter by category")
def list_refs(category: str):
    """List all reference files.
    
    \b
    Examples:
        vbagent ref list
        vbagent ref list -c tikz
    """
    _ensure_imports()
    store = ContextStore.get_instance()
    refs = store.list_references(category)
    
    if not refs:
        if category:
            console.print(f"[dim]No references in category '{category}'[/dim]")
        else:
            console.print("[dim]No references stored[/dim]")
            console.print("Use 'vbagent ref add <category> <file>' to add references")
        return
    
    # Group by category
    by_category: dict[str, list] = {}
    for ref in refs:
        if ref.category not in by_category:
            by_category[ref.category] = []
        by_category[ref.category].append(ref)
    
    for cat in CATEGORIES:
        if cat not in by_category:
            continue
        
        table = Table(title=f"{cat.title()} References", show_header=True)
        table.add_column("Name", style="cyan")
        table.add_column("Description", style="dim")
        
        for ref in by_category[cat]:
            table.add_row(ref.name, ref.description or "-")
        
        console.print(table)
        console.print()


@ref.command()
@click.argument("category", type=click.Choice(CATEGORIES))
@click.argument("name")
def show(category: str, name: str):
    """Show the content of a reference file.
    
    \b
    Arguments:
        CATEGORY  Category of the reference
        NAME      Name of the reference file
    
    \b
    Examples:
        vbagent ref show tikz diagram.tex
    """
    _ensure_imports()
    store = ContextStore.get_instance()
    
    content = store.get_reference_content(category, name)
    if content:
        console.print(Panel(content, title=f"{category}/{name}", border_style="cyan"))
    else:
        console.print(f"[red]Not found:[/red] '{name}' in {category}")


@ref.command()
def enable():
    """Enable context usage in prompts.
    
    When enabled, reference files will be included as examples
    in LLM prompts to improve output quality.
    """
    _ensure_imports()
    store = ContextStore.get_instance()
    store.enable_context()
    console.print("[green]✓[/green] Context enabled")
    console.print("[dim]Reference files will be included in prompts[/dim]")


@ref.command()
def disable():
    """Disable context usage in prompts.
    
    When disabled, reference files will not be included in prompts.
    """
    _ensure_imports()
    store = ContextStore.get_instance()
    store.disable_context()
    console.print("[yellow]✓[/yellow] Context disabled")
    console.print("[dim]Reference files will not be included in prompts[/dim]")


@ref.command()
def status():
    """Show context configuration and statistics."""
    _ensure_imports()
    store = ContextStore.get_instance()
    stats = store.get_stats()
    
    # Status panel
    status_text = f"Context: [{'green' if stats['enabled'] else 'red'}]{'Enabled' if stats['enabled'] else 'Disabled'}[/]\n"
    status_text += f"Max examples per category: {stats['max_examples']}\n"
    status_text += f"Total references: {stats['total']}"
    
    console.print(Panel(status_text, title="Context Status", border_style="cyan"))
    
    # Category breakdown
    if stats['total'] > 0:
        table = Table(title="References by Category")
        table.add_column("Category", style="cyan")
        table.add_column("Count", justify="right")
        
        for cat in CATEGORIES:
            count = stats['by_category'].get(cat, 0)
            table.add_row(cat, str(count))
        
        console.print(table)
    
    # Show config location
    console.print(f"\n[dim]Config location: {store.config_dir}[/dim]")


@ref.command()
@click.argument("max_examples", type=int)
def set_max(max_examples: int):
    """Set maximum examples per category.
    
    Controls how many reference files from each category
    are included in prompts.
    
    \b
    Arguments:
        MAX_EXAMPLES  Maximum number of examples (1-20)
    
    \b
    Examples:
        vbagent ref set-max 3
        vbagent ref set-max 10
    """
    _ensure_imports()
    if max_examples < 1 or max_examples > 20:
        console.print("[red]Error:[/red] Max examples must be between 1 and 20")
        raise SystemExit(1)
    
    store = ContextStore.get_instance()
    store.set_max_examples(max_examples)
    console.print(f"[green]✓[/green] Max examples set to {max_examples}")


# =============================================================================
# TikZ Reference Commands (with metadata-based context)
# =============================================================================

@ref.group(name="tikz")
def tikz_group():
    """Manage TikZ references with metadata-based context.
    
    TikZ references are stored with classification metadata
    (diagram_type, topic, subtopic) for intelligent context matching.
    
    \b
    Commands:
        import  - Import TikZ from processed problem
        list    - List TikZ references
        remove  - Remove a TikZ reference
        show    - Show TikZ reference content
        status  - Show TikZ reference statistics
    
    \b
    Examples:
        vbagent ref tikz import agentic/scans/Problem_5.tex
        vbagent ref tikz import -d agentic/scans -r 1 10
        vbagent ref tikz list
        vbagent ref tikz list --diagram-type pulley
        vbagent ref tikz status
    """
    pass


@tikz_group.command(name="import")
@click.argument("path", type=click.Path(exists=True))
@click.option("-r", "--range", "item_range", nargs=2, type=int,
              help="Range of problems to import (1-based inclusive)")
@click.option("-t", "--tikz-dir", type=click.Path(exists=True),
              help="Directory containing separate TikZ files")
@click.option("-c", "--class-dir", type=click.Path(exists=True),
              help="Directory containing classification JSON files")
def tikz_import(path: str, item_range: tuple, tikz_dir: str, class_dir: str):
    """Import TikZ references from processed problems.
    
    Extracts TikZ code and loads classification metadata automatically.
    Can import a single file or a range of problems from a directory.
    
    \b
    Arguments:
        PATH  Path to scan file or scans directory
    
    \b
    Examples:
        # Import single problem
        vbagent ref tikz import agentic/scans/Problem_5.tex
        
        # Import range from directory
        vbagent ref tikz import agentic/scans -r 1 10
        
        # Import with custom tikz/classification directories
        vbagent ref tikz import agentic/scans/Problem_5.tex -t agentic/tikz -c agentic/classifications
    """
    _ensure_imports()
    from vbagent.references.tikz_store import TikZReferenceStore
    
    store = TikZReferenceStore.get_instance()
    path_obj = Path(path)
    
    imported = 0
    skipped = 0
    errors = 0
    
    duplicates = 0
    
    if path_obj.is_file():
        # Single file import
        try:
            ref, status = store.add_from_problem(
                scan_path=str(path_obj),
                tikz_path=str(Path(tikz_dir) / path_obj.name) if tikz_dir else None,
                classification_path=str(Path(class_dir) / f"{path_obj.stem}.json") if class_dir else None,
            )
            if ref:
                console.print(f"[green]✓[/green] Imported '{ref.id}'")
                if ref.metadata.diagram_type:
                    console.print(f"  [dim]Diagram type: {ref.metadata.diagram_type}[/dim]")
                if ref.metadata.topic:
                    console.print(f"  [dim]Topic: {ref.metadata.topic}[/dim]")
                imported += 1
            elif status and status.startswith("duplicate:"):
                existing_id = status.split(":")[1]
                console.print(f"[yellow]⚠[/yellow] Duplicate of '{existing_id}', skipping {path_obj.name}")
                duplicates += 1
            else:
                console.print(f"[yellow]⚠[/yellow] No TikZ found in {path_obj.name}")
                skipped += 1
        except Exception as e:
            console.print(f"[red]✗[/red] Error importing {path_obj.name}: {e}")
            errors += 1
    
    elif path_obj.is_dir():
        # Directory import
        tex_files = sorted(path_obj.glob("*.tex"))
        
        if item_range:
            start, end = item_range
            # Filter by range (assuming Problem_N.tex naming)
            import re
            filtered = []
            for f in tex_files:
                match = re.search(r'(\d+)', f.stem)
                if match:
                    num = int(match.group(1))
                    if start <= num <= end:
                        filtered.append(f)
            tex_files = filtered
        
        if not tex_files:
            console.print(f"[yellow]No .tex files found in {path}[/yellow]")
            return
        
        console.print(f"[cyan]Importing {len(tex_files)} file(s)...[/cyan]")
        
        for tex_file in tex_files:
            try:
                # Determine tikz and classification paths
                tikz_path = None
                class_path = None
                
                if tikz_dir:
                    tikz_path = str(Path(tikz_dir) / tex_file.name)
                else:
                    # Try default location
                    default_tikz = path_obj.parent / "tikz" / tex_file.name
                    if default_tikz.exists():
                        tikz_path = str(default_tikz)
                
                if class_dir:
                    class_path = str(Path(class_dir) / f"{tex_file.stem}.json")
                else:
                    # Try default location
                    default_class = path_obj.parent / "classifications" / f"{tex_file.stem}.json"
                    if default_class.exists():
                        class_path = str(default_class)
                
                ref, status = store.add_from_problem(
                    scan_path=str(tex_file),
                    tikz_path=tikz_path,
                    classification_path=class_path,
                )
                if ref:
                    console.print(f"[green]✓[/green] {ref.id}")
                    imported += 1
                elif status and status.startswith("duplicate:"):
                    existing_id = status.split(":")[1]
                    console.print(f"[yellow]~[/yellow] {tex_file.stem} (duplicate of {existing_id})")
                    duplicates += 1
                else:
                    console.print(f"[dim]- {tex_file.stem} (no TikZ)[/dim]")
                    skipped += 1
            except Exception as e:
                console.print(f"[red]✗[/red] {tex_file.stem}: {e}")
                errors += 1
    
    # Summary
    console.print(f"\n[bold]Summary:[/bold]")
    console.print(f"  Imported:   [green]{imported}[/green]")
    if duplicates:
        console.print(f"  Duplicates: [yellow]{duplicates}[/yellow] (skipped)")
    if skipped:
        console.print(f"  No TikZ:    [dim]{skipped}[/dim]")
    if errors:
        console.print(f"  Errors:     [red]{errors}[/red]")


@tikz_group.command(name="list")
@click.option("--diagram-type", "-d", help="Filter by diagram type")
@click.option("--topic", "-t", help="Filter by topic")
def tikz_list(diagram_type: str, topic: str):
    """List TikZ references.
    
    \b
    Examples:
        vbagent ref tikz list
        vbagent ref tikz list --diagram-type pulley
        vbagent ref tikz list -t mechanics
    """
    _ensure_imports()
    from vbagent.references.tikz_store import TikZReferenceStore
    
    store = TikZReferenceStore.get_instance()
    refs = store.list_references(diagram_type=diagram_type, topic=topic)
    
    if not refs:
        console.print("[dim]No TikZ references found[/dim]")
        console.print("Use 'vbagent ref tikz import <path>' to add references")
        return
    
    table = Table(title="TikZ References", show_header=True)
    table.add_column("ID", style="cyan")
    table.add_column("Diagram Type", style="yellow")
    table.add_column("Topic", style="green")
    table.add_column("Subtopic", style="dim")
    table.add_column("Description", style="dim")
    
    for ref in refs:
        table.add_row(
            ref.id,
            ref.metadata.diagram_type or "-",
            ref.metadata.topic or "-",
            ref.metadata.subtopic or "-",
            ref.description or "-",
        )
    
    console.print(table)


@tikz_group.command(name="remove")
@click.argument("ref_id")
def tikz_remove(ref_id: str):
    """Remove a TikZ reference.
    
    \b
    Arguments:
        REF_ID  ID of the reference to remove
    
    \b
    Examples:
        vbagent ref tikz remove Problem_5
    """
    _ensure_imports()
    from vbagent.references.tikz_store import TikZReferenceStore
    
    store = TikZReferenceStore.get_instance()
    
    if store.remove_reference(ref_id):
        console.print(f"[green]✓[/green] Removed '{ref_id}'")
    else:
        console.print(f"[yellow]Not found:[/yellow] '{ref_id}'")


@tikz_group.command(name="show")
@click.argument("ref_id")
def tikz_show(ref_id: str):
    """Show TikZ reference content.
    
    \b
    Arguments:
        REF_ID  ID of the reference to show
    
    \b
    Examples:
        vbagent ref tikz show Problem_5
    """
    _ensure_imports()
    from vbagent.references.tikz_store import TikZReferenceStore
    
    store = TikZReferenceStore.get_instance()
    ref = store.get_reference(ref_id)
    
    if not ref:
        console.print(f"[red]Not found:[/red] '{ref_id}'")
        return
    
    # Show metadata
    meta_text = f"[bold]Metadata:[/bold]\n"
    meta_text += f"  Diagram Type: {ref.metadata.diagram_type or '-'}\n"
    meta_text += f"  Topic: {ref.metadata.topic or '-'}\n"
    meta_text += f"  Subtopic: {ref.metadata.subtopic or '-'}\n"
    meta_text += f"  Question Type: {ref.metadata.question_type or '-'}\n"
    if ref.metadata.key_concepts:
        meta_text += f"  Key Concepts: {', '.join(ref.metadata.key_concepts)}\n"
    if ref.source_file:
        meta_text += f"  Source: {ref.source_file}\n"
    
    console.print(Panel(meta_text, title=f"[cyan]{ref_id}[/cyan]", border_style="cyan"))
    console.print(Panel(ref.tikz_code, title="TikZ Code", border_style="green"))


@tikz_group.command(name="status")
def tikz_status():
    """Show TikZ reference statistics."""
    _ensure_imports()
    from vbagent.references.tikz_store import TikZReferenceStore
    
    store = TikZReferenceStore.get_instance()
    stats = store.get_stats()
    
    # Status panel
    status_text = f"TikZ Context: [{'green' if stats['enabled'] else 'red'}]{'Enabled' if stats['enabled'] else 'Disabled'}[/]\n"
    status_text += f"Max examples: {stats['max_examples']}\n"
    status_text += f"Total references: {stats['total']}"
    
    console.print(Panel(status_text, title="TikZ Reference Status", border_style="cyan"))
    
    # By diagram type
    if stats['by_diagram_type']:
        table = Table(title="By Diagram Type")
        table.add_column("Type", style="yellow")
        table.add_column("Count", justify="right")
        
        for dt, count in sorted(stats['by_diagram_type'].items()):
            table.add_row(dt, str(count))
        
        console.print(table)
    
    # By topic
    if stats['by_topic']:
        table = Table(title="By Topic")
        table.add_column("Topic", style="green")
        table.add_column("Count", justify="right")
        
        for topic, count in sorted(stats['by_topic'].items()):
            table.add_row(topic, str(count))
        
        console.print(table)
