"""Idea extraction agent for physics problems.

Uses openai-agents SDK to analyze physics problems and solutions,
extracting core concepts, formulas, techniques, and difficulty factors.
"""

import re

from vbagent.agents.base import create_agent, run_agent_sync
from vbagent.models.idea import IdeaResult
from vbagent.prompts.idea import (
    SYSTEM_PROMPT,
    SYSTEM_PROMPT_JSON,
    USER_TEMPLATE,
    USER_TEMPLATE_JSON,
)


# Create the idea agent with structured output (for JSON output)
idea_agent_json = create_agent(
    name="IdeaJSON",
    instructions=SYSTEM_PROMPT_JSON,
    output_type=IdeaResult,
    agent_type="idea",
)

# Create the idea agent for LaTeX output
idea_agent_latex = create_agent(
    name="IdeaLaTeX",
    instructions=SYSTEM_PROMPT,
    agent_type="idea",
)


def clean_latex_output(latex: str) -> str:
    """Clean up LaTeX output by removing markdown code block markers.
    
    Args:
        latex: Raw LaTeX output from LLM
        
    Returns:
        Cleaned LaTeX without markdown artifacts
    """
    if not latex:
        return latex
    
    # Remove markdown code block markers
    latex = re.sub(r'^```(?:latex|tex|LaTeX)?\s*\n?', '', latex, flags=re.IGNORECASE)
    latex = re.sub(r'\n?```\s*$', '', latex)
    latex = re.sub(r'^```\s*', '', latex)
    
    return latex.strip()


def extract_ideas(problem_latex: str, solution_latex: str) -> IdeaResult:
    """Extract core concepts and techniques from a physics problem (JSON output).
    
    Analyzes the problem statement and solution to identify:
    - Primary physics concepts being tested
    - Key formulas and equations used
    - Problem-solving techniques employed
    - Factors that make the problem challenging
    
    Args:
        problem_latex: The problem statement in LaTeX format
        solution_latex: The solution in LaTeX format
        
    Returns:
        IdeaResult with extracted concepts, formulas, techniques,
        and difficulty factors
        
    Raises:
        ValueError: If both problem and solution are empty
    """
    if not problem_latex.strip() and not solution_latex.strip():
        raise ValueError("Both problem and solution cannot be empty")
    
    # Format the user message with problem and solution
    message = USER_TEMPLATE_JSON.format(
        problem=problem_latex,
        solution=solution_latex,
    )
    
    result = run_agent_sync(idea_agent_json, message)
    return result


def generate_idea_latex(full_content: str) -> str:
    """Generate idea extraction in LaTeX format for appending to files.
    
    Creates a concise summary of key concepts, formulas, and techniques
    in the `\\begin{idea}...\\end{idea}` environment.
    
    Args:
        full_content: Full LaTeX file content
        
    Returns:
        LaTeX string with idea environment
        
    Raises:
        ValueError: If content is empty
    """
    if not full_content.strip():
        raise ValueError("Content cannot be empty")
    
    # Use string replace instead of .format() to avoid issues with LaTeX curly braces
    message = USER_TEMPLATE.replace('{full_content}', full_content)
    
    raw_result = run_agent_sync(idea_agent_latex, message)
    
    return clean_latex_output(raw_result)


def has_idea_environment(content: str) -> bool:
    """Check if content already has an idea environment.
    
    Args:
        content: Full LaTeX content of the problem file
        
    Returns:
        True if idea environment exists
    """
    return r'\begin{idea}' in content


def count_idea_environments(content: str) -> int:
    """Count the number of idea environments in content.
    
    Args:
        content: Full LaTeX content of the problem file
        
    Returns:
        Number of idea environments
    """
    return content.count(r'\begin{idea}')
