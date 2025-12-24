"""Format converter agent for physics questions.

Uses openai-agents SDK to convert questions between different formats:
- MCQ (single/multiple correct)
- Subjective
- Integer type
"""

import re
from typing import Literal

from vbagent.agents.base import create_agent, run_agent_sync


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
from vbagent.prompts.converter import (
    SYSTEM_PROMPT,
    USER_TEMPLATE,
    get_format_instructions,
)


# Valid format types
FormatType = Literal["mcq_sc", "mcq_mc", "subjective", "integer"]

VALID_FORMATS = {"mcq_sc", "mcq_mc", "subjective", "integer"}


# Create the format converter agent
converter_agent = create_agent(
    name="FormatConverter",
    instructions=SYSTEM_PROMPT,
    agent_type="converter",
)


def convert_format(
    source_latex: str,
    source_format: FormatType,
    target_format: FormatType,
) -> str:
    """Convert a physics question from one format to another.
    
    Converts questions between MCQ (single/multiple correct),
    subjective, and integer type formats while preserving the
    core physics content and difficulty level.
    
    Args:
        source_latex: The source question in LaTeX format
        source_format: The format of the source question
        target_format: The desired target format
        
    Returns:
        Converted question in LaTeX format with solution
        
    Raises:
        ValueError: If source_latex is empty or formats are invalid
    """
    if not source_latex.strip():
        raise ValueError("Source LaTeX cannot be empty")
    
    if source_format not in VALID_FORMATS:
        raise ValueError(
            f"Invalid source format: {source_format}. "
            f"Must be one of: {', '.join(VALID_FORMATS)}"
        )
    
    if target_format not in VALID_FORMATS:
        raise ValueError(
            f"Invalid target format: {target_format}. "
            f"Must be one of: {', '.join(VALID_FORMATS)}"
        )
    
    # Get format-specific instructions for the target
    format_instructions = get_format_instructions(target_format)
    
    # Format the user message
    message = USER_TEMPLATE.format(
        source_format=source_format,
        target_format=target_format,
        source_latex=source_latex,
        format_specific_instructions=format_instructions,
    )
    
    raw_result = run_agent_sync(converter_agent, message)
    
    # Clean up markdown artifacts from LLM output
    return clean_latex_output(raw_result)
