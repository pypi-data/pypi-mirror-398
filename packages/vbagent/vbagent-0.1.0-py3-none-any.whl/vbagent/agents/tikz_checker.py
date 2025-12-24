"""TikZ checker agent for LaTeX diagrams.

Checks TikZ/PGF code for syntax errors, best practices,
and physics diagram conventions.
"""

import re

from vbagent.agents.base import create_agent, run_agent_sync
from vbagent.prompts.tikz_checker import SYSTEM_PROMPT, USER_TEMPLATE


# Create the TikZ checker agent
tikz_checker_agent = create_agent(
    name="TikZChecker",
    instructions=SYSTEM_PROMPT,
    agent_type="tikz_checker",  # Uses tikz_checker model config
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


def check_tikz(
    full_content: str,
    image_path: str | None = None,
) -> tuple[bool, str, str]:
    """Check TikZ code for errors and best practices.
    
    Analyzes the content for:
    - TikZ syntax errors
    - Missing libraries or packages
    - Best practice violations
    - Physics diagram convention issues
    
    If an image is provided, the checker can compare the TikZ output
    against the reference image for accuracy.
    
    Args:
        full_content: Full LaTeX file content containing TikZ code
        image_path: Optional path to reference image for comparison
        
    Returns:
        Tuple of (passed, summary, corrected_content)
        - passed: True if no errors found
        - summary: Description of what was fixed (or "PASSED")
        - corrected_content: The corrected file content (empty if passed)
        
    Raises:
        ValueError: If content is empty
    """
    from vbagent.agents.base import create_image_message
    
    if not full_content.strip():
        raise ValueError("Content cannot be empty")
    
    # Use string replace instead of .format() to avoid issues with LaTeX curly braces
    message_text = USER_TEMPLATE.replace('{full_content}', full_content)
    
    # If image provided, create multimodal message
    if image_path:
        message_text += "\n\n[Reference image provided - compare TikZ output against this image for accuracy]"
        message = create_image_message(image_path, message_text)
    else:
        message = message_text
    
    raw_result = run_agent_sync(tikz_checker_agent, message)
    result = clean_latex_output(raw_result)
    
    return parse_check_result(result, "TIKZ_CHECK")


def parse_check_result(result: str, check_type: str) -> tuple[bool, str, str]:
    """Parse the check result to extract pass/fail status and content.
    
    Args:
        result: Raw result from checker
        check_type: Type of check (TIKZ_CHECK)
        
    Returns:
        Tuple of (passed, summary, corrected_content)
    """
    # Check if passed
    passed_pattern = rf'%\s*{check_type}:\s*PASSED'
    if re.search(passed_pattern, result, re.IGNORECASE):
        # Extract the summary after PASSED
        match = re.search(rf'%\s*{check_type}:\s*PASSED\s*[-–—]?\s*(.*?)(?:\n|$)', result, re.IGNORECASE)
        summary = match.group(1).strip() if match else "No TikZ errors found"
        return True, summary, ""
    
    # Extract summary from comment
    summary_pattern = rf'%\s*{check_type}:\s*(.*?)(?:\n|$)'
    summary_match = re.search(summary_pattern, result, re.IGNORECASE)
    summary = summary_match.group(1).strip() if summary_match else "TikZ issues found and corrected"
    
    # Remove the check comment line to get clean content
    corrected_content = re.sub(rf'%\s*{check_type}:.*?\n', '', result, count=1, flags=re.IGNORECASE)
    corrected_content = corrected_content.strip()
    
    return False, summary, corrected_content


def has_tikz_passed(result: str) -> bool:
    """Check if TikZ check passed.
    
    Args:
        result: Raw result from checker
        
    Returns:
        True if TikZ check passed
    """
    return '% TIKZ_CHECK: PASSED' in result or 'TIKZ_CHECK: PASSED' in result.upper()


def has_tikz_environment(content: str) -> bool:
    """Check if content contains TikZ code.
    
    Args:
        content: LaTeX content to check
        
    Returns:
        True if TikZ environment or commands found
    """
    tikz_patterns = [
        r'\\begin\{tikzpicture\}',
        r'\\tikz\s*[{\[]',
        r'\\draw\s*[\[\(]',
        r'\\node\s*[\[\(]',
        r'\\fill\s*[\[\(]',
        r'\\path\s*[\[\(]',
        r'\\begin\{axis\}',
    ]
    for pattern in tikz_patterns:
        if re.search(pattern, content):
            return True
    return False
