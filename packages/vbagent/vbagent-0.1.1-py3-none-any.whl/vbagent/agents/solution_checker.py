"""Solution checker agent for physics problems.

Verifies mathematical correctness, physics principles,
and final answer accuracy in physics solutions.
Also creates solutions when none exists.
"""

import re

from vbagent.agents.base import create_agent, run_agent_sync
from vbagent.prompts.solution_checker import SYSTEM_PROMPT, USER_TEMPLATE


# Create the solution checker agent
solution_checker_agent = create_agent(
    name="SolutionChecker",
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


def check_solution(full_content: str) -> tuple[bool, str, str]:
    """Check a physics solution for correctness, or create one if missing.
    
    Analyzes the solution for:
    - Mathematical calculation errors
    - Physics principle misapplication
    - Final answer correctness
    - Unit consistency
    
    If no solution exists, creates a complete solution.
    
    Args:
        full_content: Full LaTeX file content (problem with or without solution)
        
    Returns:
        Tuple of (passed, summary, corrected_content)
        - passed: True if no errors found (existing solution is correct)
        - summary: Description of what was fixed/created (or "PASSED")
        - corrected_content: The corrected/completed file content (empty if passed)
        
    Raises:
        ValueError: If content is empty
    """
    if not full_content.strip():
        raise ValueError("Content cannot be empty")
    
    # Use string replace instead of .format() to avoid issues with LaTeX curly braces
    message = USER_TEMPLATE.replace('{full_content}', full_content)
    
    raw_result = run_agent_sync(solution_checker_agent, message)
    result = clean_latex_output(raw_result)
    
    return parse_check_result(result, "SOLUTION_CHECK")


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
    
    # Extract summary from comment (handles both "Created new solution" and error fixes)
    summary_pattern = rf'%\s*{check_type}:\s*(.*?)(?:\n|$)'
    summary_match = re.search(summary_pattern, result, re.IGNORECASE)
    summary = summary_match.group(1).strip() if summary_match else "Issues found and corrected"
    
    # Remove the check comment line to get clean content
    corrected_content = re.sub(rf'%\s*{check_type}:.*?\n', '', result, count=1, flags=re.IGNORECASE)
    corrected_content = corrected_content.strip()
    
    return False, summary, corrected_content


def has_solution_passed(result: str) -> bool:
    """Check if solution check passed.
    
    Args:
        result: Raw result from checker
        
    Returns:
        True if solution check passed
    """
    return '% SOLUTION_CHECK: PASSED' in result or 'SOLUTION_CHECK: PASSED' in result.upper()
