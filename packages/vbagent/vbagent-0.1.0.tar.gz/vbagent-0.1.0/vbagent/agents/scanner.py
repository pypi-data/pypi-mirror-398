"""Scanner agent for extracting LaTeX from physics question images.

Uses openai-agents SDK to analyze physics question images and extract
LaTeX code using type-specific prompts.
"""

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agents import Agent

from vbagent.agents.base import (
    create_agent,
    create_image_message,
    run_agent_sync,
)
from vbagent.models.classification import ClassificationResult
from vbagent.models.scan import ScanResult
from vbagent.prompts.scanner import get_scanner_prompt, USER_TEMPLATE
from vbagent.references.context import get_context_prompt_section


def clean_latex_output(latex: str) -> str:
    """Clean up LaTeX output by removing markdown code block markers.
    
    Removes patterns like:
    - ```latex ... ```
    - ``` ... ```
    - Leading/trailing whitespace
    
    Args:
        latex: Raw LaTeX output from LLM
        
    Returns:
        Cleaned LaTeX without markdown artifacts
    """
    if not latex:
        return latex
    
    # Remove markdown code block markers with language specifier
    # Matches: ```latex, ```tex, ```LaTeX, etc.
    latex = re.sub(r'^```(?:latex|tex|LaTeX)?\s*\n?', '', latex, flags=re.IGNORECASE)
    
    # Remove closing code block marker
    latex = re.sub(r'\n?```\s*$', '', latex)
    
    # Also handle case where ``` appears at the start without newline
    latex = re.sub(r'^```\s*', '', latex)
    
    return latex.strip()


def create_scanner_agent(question_type: str, use_context: bool = True) -> "Agent":
    """Create a scanner agent with type-specific prompt.
    
    Args:
        question_type: The type of question (mcq_sc, mcq_mc, etc.)
        use_context: Whether to include reference context in prompt
        
    Returns:
        Configured Agent instance for scanning that question type
    """
    prompt = get_scanner_prompt(question_type)
    
    # Add reference context if enabled
    context = get_context_prompt_section("latex", use_context)
    if context:
        prompt = prompt + "\n" + context
    
    return create_agent(
        name=f"Scanner-{question_type}",
        instructions=prompt,
        agent_type="scanner",
    )


def scan(
    image_path: str,
    classification: ClassificationResult,
    use_context: bool = True,
) -> ScanResult:
    """Extract LaTeX from a physics question image.
    
    Uses the classification result to select the appropriate prompt
    for the question type.
    
    Args:
        image_path: Path to the image file to scan
        classification: Classification result with question type info
        use_context: Whether to include reference context in prompt
        
    Returns:
        ScanResult with extracted LaTeX and diagram info
        
    Raises:
        FileNotFoundError: If the image file doesn't exist
    """
    agent = create_scanner_agent(classification.question_type, use_context)
    message = create_image_message(image_path, USER_TEMPLATE)
    raw_latex = run_agent_sync(agent, message)
    
    # Clean up markdown artifacts from LLM output
    latex = clean_latex_output(raw_latex)
    
    return ScanResult(
        latex=latex,
        has_diagram=classification.has_diagram,
        raw_diagram_description=classification.diagram_type,
    )


def scan_with_type(
    image_path: str,
    question_type: str,
    use_context: bool = True,
) -> ScanResult:
    """Extract LaTeX from a physics question image with explicit type.
    
    Bypasses classification and uses the provided question type directly.
    
    Args:
        image_path: Path to the image file to scan
        question_type: The type of question (mcq_sc, mcq_mc, etc.)
        use_context: Whether to include reference context in prompt
        
    Returns:
        ScanResult with extracted LaTeX
        
    Raises:
        FileNotFoundError: If the image file doesn't exist
    """
    agent = create_scanner_agent(question_type, use_context)
    message = create_image_message(image_path, USER_TEMPLATE)
    raw_latex = run_agent_sync(agent, message)
    
    # Clean up markdown artifacts from LLM output
    latex = clean_latex_output(raw_latex)
    
    return ScanResult(
        latex=latex,
        has_diagram=False,  # Unknown without classification
        raw_diagram_description=None,
    )
