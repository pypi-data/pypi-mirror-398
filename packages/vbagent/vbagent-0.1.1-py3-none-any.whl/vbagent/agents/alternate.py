"""Alternate solution agent for physics problems.

Uses openai-agents SDK to generate alternative solution methods
while maintaining the same final answer.
"""

import re
from typing import Optional

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


from vbagent.models.idea import IdeaResult
from vbagent.prompts.alternate import (
    SYSTEM_PROMPT,
    USER_TEMPLATE,
    USER_TEMPLATE_WITH_EXISTING,
)


# Create the alternate solution agent
alternate_agent = create_agent(
    name="AlternateSolution",
    instructions=SYSTEM_PROMPT,
    agent_type="alternate",
)


def extract_answer(solution: str) -> str:
    """Extract the final numerical answer from a solution.
    
    Looks for common answer patterns in LaTeX solutions.
    
    Args:
        solution: The solution text in LaTeX format
        
    Returns:
        The extracted answer string, or empty string if not found
    """
    # Common patterns for final answers in physics solutions
    patterns = [
        # Boxed answers: \boxed{...} - handle nested braces
        r'\\boxed\{((?:[^{}]|\{[^{}]*\})*)\}',
        # Answer environment or explicit answer markers
        r'(?:answer|ans|result)\s*[:=]\s*([^\n\\]+)',
        # Final equals in solution: = X (with optional units in \text{})
        r'=\s*([-+]?\d+(?:\.\d+)?(?:\s*\\times\s*10\^?\{?[-+]?\d+\}?)?)\s*(?:\\text\{[^}]*\}|\\[a-zA-Z]+|[a-zA-Z/]+)?(?:\s*$|\s*\\\\|\s*\n)',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, solution, re.IGNORECASE | re.MULTILINE)
        if matches:
            # Return the last match (usually the final answer)
            return matches[-1].strip()
    
    return ""


def extract_existing_alternates(content: str) -> list[str]:
    """Extract existing alternate solutions from LaTeX content.
    
    Args:
        content: Full LaTeX content of the problem file
        
    Returns:
        List of existing alternate solution contents
    """
    pattern = r'\\begin\{alternatesolution\}(.*?)\\end\{alternatesolution\}'
    matches = re.findall(pattern, content, re.DOTALL)
    return [m.strip() for m in matches]


def has_alternate_solution(content: str) -> bool:
    """Check if content already has an alternate solution.
    
    Args:
        content: Full LaTeX content of the problem file
        
    Returns:
        True if alternatesolution environment exists
    """
    return r'\begin{alternatesolution}' in content


def count_alternate_solutions(content: str) -> int:
    """Count the number of alternate solutions in content.
    
    Args:
        content: Full LaTeX content of the problem file
        
    Returns:
        Number of alternatesolution environments
    """
    return content.count(r'\begin{alternatesolution}')


def generate_alternate(
    problem: str,
    solution: str,
    ideas: Optional[IdeaResult] = None,
    existing_alternates: Optional[list[str]] = None,
    full_content: Optional[str] = None,
) -> str:
    """Generate an alternate solution approach for a physics problem.
    
    Creates a different valid solution method that arrives at the same
    final answer as the original solution.
    
    Args:
        problem: The problem statement in LaTeX format (legacy, used if full_content not provided)
        solution: The original solution in LaTeX format (legacy, used if full_content not provided)
        ideas: Optional IdeaResult with extracted concepts and techniques
        existing_alternates: List of existing alternate solutions to avoid repeating
        full_content: Full LaTeX file content (preferred - pass entire file)
        
    Returns:
        Alternative solution in LaTeX format within alternatesolution environment
        
    Raises:
        ValueError: If content is empty
    """
    # Use full_content if provided, otherwise construct from problem/solution
    if full_content:
        content_to_use = full_content.strip()
    else:
        if not problem.strip():
            raise ValueError("Problem cannot be empty")
        if not solution.strip():
            raise ValueError("Solution cannot be empty")
        content_to_use = f"{problem}\n\n\\begin{{solution}}\n{solution}\n\\end{{solution}}"
    
    if not content_to_use:
        raise ValueError("Content cannot be empty")
    
    # Check if there are existing alternates in the content
    has_existing = r'\begin{alternatesolution}' in content_to_use
    
    # Choose template based on whether existing alternates exist
    # Use string replace instead of .format() to avoid issues with LaTeX curly braces
    if has_existing or existing_alternates:
        message = USER_TEMPLATE_WITH_EXISTING.replace('{full_content}', content_to_use)
    else:
        message = USER_TEMPLATE.replace('{full_content}', content_to_use)
    
    raw_result = run_agent_sync(alternate_agent, message)
    
    # Clean up markdown artifacts from LLM output
    return clean_latex_output(raw_result)
