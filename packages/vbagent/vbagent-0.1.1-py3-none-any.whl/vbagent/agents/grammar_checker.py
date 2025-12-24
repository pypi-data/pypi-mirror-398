"""Grammar checker agent for physics content.

Checks for grammar, spelling, and language errors
in physics problems and solutions.
"""

import re

from vbagent.agents.base import create_agent, run_agent_sync
from vbagent.prompts.grammar_checker import SYSTEM_PROMPT, USER_TEMPLATE


# Create the grammar checker agent
grammar_checker_agent = create_agent(
    name="GrammarChecker",
    instructions=SYSTEM_PROMPT,
    agent_type="reviewer",  # Uses reviewer model config
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


def check_grammar(full_content: str) -> tuple[bool, str, str]:
    """Check physics content for grammar and spelling errors.
    
    Analyzes the content for:
    - Grammar errors
    - Spelling mistakes
    - Awkward phrasing
    - Punctuation issues
    
    Args:
        full_content: Full LaTeX file content
        
    Returns:
        Tuple of (passed, summary, corrected_content)
        - passed: True if no issues found
        - summary: Description of what was fixed (or "PASSED")
        - corrected_content: The corrected file content (empty if passed)
        
    Raises:
        ValueError: If content is empty
    """
    if not full_content.strip():
        raise ValueError("Content cannot be empty")
    
    # Use string replace instead of .format() to avoid issues with LaTeX curly braces
    message = USER_TEMPLATE.replace('{full_content}', full_content)
    
    raw_result = run_agent_sync(grammar_checker_agent, message)
    result = clean_latex_output(raw_result)
    
    return parse_check_result(result, "GRAMMAR_CHECK")


def parse_check_result(result: str, check_type: str) -> tuple[bool, str, str]:
    """Parse the check result to extract pass/fail status and content.
    
    Args:
        result: Raw result from checker
        check_type: Type of check (SOLUTION_CHECK, GRAMMAR_CHECK, CLARITY_CHECK)
        
    Returns:
        Tuple of (passed, summary, corrected_content)
    """
    # Check if passed
    passed_pattern = rf'%\s*{check_type}:\s*PASSED'
    if re.search(passed_pattern, result, re.IGNORECASE):
        # Extract the summary after PASSED
        match = re.search(rf'%\s*{check_type}:\s*PASSED\s*[-–—]?\s*(.*?)(?:\n|$)', result, re.IGNORECASE)
        summary = match.group(1).strip() if match else "No issues found"
        return True, summary, ""
    
    # Extract summary from comment
    summary_pattern = rf'%\s*{check_type}:\s*(.*?)(?:\n|$)'
    summary_match = re.search(summary_pattern, result, re.IGNORECASE)
    summary = summary_match.group(1).strip() if summary_match else "Issues found and corrected"
    
    # Remove the check comment line to get clean content
    corrected_content = re.sub(rf'%\s*{check_type}:.*?\n', '', result, count=1, flags=re.IGNORECASE)
    corrected_content = corrected_content.strip()
    
    return False, summary, corrected_content


def has_grammar_passed(result: str) -> bool:
    """Check if grammar check passed.
    
    Args:
        result: Raw result from checker
        
    Returns:
        True if grammar check passed
    """
    return '% GRAMMAR_CHECK: PASSED' in result or 'GRAMMAR_CHECK: PASSED' in result.upper()
