"""Random problem selector for QA Review Agent.

Discovers and selects problems from the processed output directory
for quality review.
"""

import random
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ProblemContext:
    """Context for a problem selected for review.
    
    Contains all the files and content needed for QA review.
    """
    problem_id: str
    base_path: Path
    image_path: str | None
    latex_path: str
    latex_content: str
    variants: dict[str, str] = field(default_factory=dict)  # variant_type -> latex content
    variant_paths: dict[str, str] = field(default_factory=dict)  # variant_type -> file path


def discover_problems(output_dir: str) -> list[str]:
    """Discover all problem IDs in the output directory.
    
    Looks for .tex files in the following locations (in order):
    1. scans/ subdirectory (standard agentic output structure)
    2. Directly in the given directory (flat structure)
    
    Args:
        output_dir: Path to the output directory (e.g., "agentic" or direct tex folder)
        
    Returns:
        List of problem IDs (base names without extension)
    """
    output_path = Path(output_dir)
    
    # First try scans/ subdirectory (standard agentic structure)
    scans_dir = output_path / "scans"
    if scans_dir.exists():
        problem_ids = []
        for tex_file in scans_dir.glob("*.tex"):
            problem_ids.append(tex_file.stem)
        if problem_ids:
            return sorted(problem_ids)
    
    # Fallback: look for .tex files directly in the given directory
    problem_ids = []
    for tex_file in output_path.glob("*.tex"):
        problem_ids.append(tex_file.stem)
    
    return sorted(problem_ids)


def select_random(output_dir: str, count: int) -> list[str]:
    """Randomly select problem IDs for review.
    
    Args:
        output_dir: Path to the output directory
        count: Number of problems to select
        
    Returns:
        List of randomly selected problem IDs.
        Returns min(count, available) problems if fewer are available.
    """
    all_problems = discover_problems(output_dir)
    
    if not all_problems:
        return []
    
    # Select min(count, available) problems
    select_count = min(count, len(all_problems))
    return random.sample(all_problems, select_count)


def load_problem_context(output_dir: str, problem_id: str) -> ProblemContext:
    """Load all files for a problem into a review context.
    
    Args:
        output_dir: Path to the output directory
        problem_id: ID of the problem to load
        
    Returns:
        ProblemContext with all loaded content
        
    Raises:
        FileNotFoundError: If the problem's LaTeX file doesn't exist
    """
    output_path = Path(output_dir)
    
    # Load main LaTeX file - try scans/ first, then direct
    latex_path = output_path / "scans" / f"{problem_id}.tex"
    if not latex_path.exists():
        # Fallback: look directly in the given directory
        latex_path = output_path / f"{problem_id}.tex"
    if not latex_path.exists():
        raise FileNotFoundError(f"Problem LaTeX not found: {problem_id}.tex")
    
    latex_content = latex_path.read_text()
    
    # Try to find associated image
    # Images are typically in a separate images directory with same base name
    image_path = None
    # Check common image locations and extensions
    for ext in [".png", ".jpg", ".jpeg", ".gif", ".webp"]:
        # Check in parent directory's images folder
        candidate = output_path.parent / "images" / f"{problem_id}{ext}"
        if candidate.exists():
            image_path = str(candidate)
            break
        # Check in output directory's images folder
        candidate = output_path / "images" / f"{problem_id}{ext}"
        if candidate.exists():
            image_path = str(candidate)
            break
    
    # Load variants
    variants: dict[str, str] = {}
    variant_paths: dict[str, str] = {}
    variants_dir = output_path / "variants"
    
    if variants_dir.exists():
        for variant_type_dir in variants_dir.iterdir():
            if variant_type_dir.is_dir():
                variant_file = variant_type_dir / f"{problem_id}.tex"
                if variant_file.exists():
                    variant_type = variant_type_dir.name
                    variants[variant_type] = variant_file.read_text()
                    variant_paths[variant_type] = str(variant_file)
    
    return ProblemContext(
        problem_id=problem_id,
        base_path=output_path,
        image_path=image_path,
        latex_path=str(latex_path),
        latex_content=latex_content,
        variants=variants,
        variant_paths=variant_paths,
    )
