"""Multi-context variant agent for physics problems.

Uses openai-agents SDK to generate problem variants by combining
elements from multiple source problems into a single coherent problem.
"""

from typing import Optional

from vbagent.agents.base import create_agent, run_agent_sync
from vbagent.prompts.variants.multi_context import SYSTEM_PROMPT, USER_TEMPLATE


# Create the multi-context variant agent
multi_context_agent = create_agent(
    name="MultiContextVariant",
    instructions=SYSTEM_PROMPT,
)


def generate_multi_context_variant(
    source_problems: list[str],
    target_style: Optional[str] = None,
) -> str:
    """Combine elements from multiple problems into a single coherent problem.
    
    Analyzes multiple source problems and creates a new problem that
    synthesizes concepts, techniques, or scenarios from the sources
    into a unified, coherent question.
    
    Args:
        source_problems: List of source problems in LaTeX format
        target_style: Optional style guidance for the output (e.g., "MCQ", "subjective")
        
    Returns:
        A single coherent problem in LaTeX format that combines elements
        from the source problems
        
    Raises:
        ValueError: If source_problems is empty or contains only empty strings
    """
    if not source_problems:
        raise ValueError("At least one source problem is required")
    
    # Filter out empty problems
    valid_problems = [p for p in source_problems if p.strip()]
    
    if not valid_problems:
        raise ValueError("At least one non-empty source problem is required")
    
    # Format the problems text
    problems_text = "\n\n---\n\n".join(
        f"Problem {i + 1}:\n{p}" for i, p in enumerate(valid_problems)
    )
    
    # Format style instruction
    style_instruction = ""
    if target_style:
        style_instruction = f"Target Style: {target_style}"
    
    # Format the user message
    message = USER_TEMPLATE.format(
        problems_text=problems_text,
        style_instruction=style_instruction,
    )
    
    # Run the agent
    result = run_agent_sync(multi_context_agent, message)
    return result
