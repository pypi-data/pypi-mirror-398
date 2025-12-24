"""Variant agents for physics problem generation.

Uses openai-agents SDK to generate different types of problem variants:
- numerical: Modify only numerical values
- context: Modify only the scenario/context
- conceptual: Modify the core physics concept
- calculus: Add calculus-based modifications
"""

import re
from typing import Optional

from vbagent.agents.base import create_agent, run_agent_sync
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
from vbagent.models.idea import IdeaResult
from vbagent.prompts.variants.numerical import (
    SYSTEM_PROMPT as NUMERICAL_SYSTEM_PROMPT,
    USER_TEMPLATE as NUMERICAL_USER_TEMPLATE,
)
from vbagent.prompts.variants.context import (
    SYSTEM_PROMPT as CONTEXT_SYSTEM_PROMPT,
    USER_TEMPLATE as CONTEXT_USER_TEMPLATE,
)
from vbagent.prompts.variants.conceptual import (
    SYSTEM_PROMPT as CONCEPTUAL_SYSTEM_PROMPT,
    USER_TEMPLATE as CONCEPTUAL_USER_TEMPLATE,
)
from vbagent.prompts.variants.conceptual_calculus import (
    SYSTEM_PROMPT as CALCULUS_SYSTEM_PROMPT,
    USER_TEMPLATE as CALCULUS_USER_TEMPLATE,
)


# Mapping of variant types to their prompts
VARIANT_PROMPTS = {
    "numerical": {
        "system": NUMERICAL_SYSTEM_PROMPT,
        "user": NUMERICAL_USER_TEMPLATE,
    },
    "context": {
        "system": CONTEXT_SYSTEM_PROMPT,
        "user": CONTEXT_USER_TEMPLATE,
    },
    "conceptual": {
        "system": CONCEPTUAL_SYSTEM_PROMPT,
        "user": CONCEPTUAL_USER_TEMPLATE,
    },
    "calculus": {
        "system": CALCULUS_SYSTEM_PROMPT,
        "user": CALCULUS_USER_TEMPLATE,
    },
}

# Valid variant types
VALID_VARIANT_TYPES = list(VARIANT_PROMPTS.keys())


def get_variant_prompt(variant_type: str) -> tuple[str, str]:
    """Get the system and user prompts for a variant type.
    
    Args:
        variant_type: Type of variant (numerical, context, conceptual, calculus)
        
    Returns:
        Tuple of (system_prompt, user_template)
        
    Raises:
        ValueError: If variant_type is not valid
    """
    if variant_type not in VARIANT_PROMPTS:
        raise ValueError(
            f"Invalid variant type: {variant_type}. "
            f"Valid types are: {VALID_VARIANT_TYPES}"
        )
    
    prompts = VARIANT_PROMPTS[variant_type]
    return prompts["system"], prompts["user"]


def create_variant_agent(variant_type: str, use_context: bool = True):
    """Create a variant agent with type-specific prompt.
    
    Args:
        variant_type: Type of variant (numerical, context, conceptual, calculus)
        use_context: Whether to include reference context in prompt
        
    Returns:
        Configured Agent instance for the variant type
        
    Raises:
        ValueError: If variant_type is not valid
    """
    system_prompt, _ = get_variant_prompt(variant_type)
    
    # Add reference context if enabled
    context = get_context_prompt_section("variants", use_context)
    if context:
        system_prompt = system_prompt + "\n" + context
    
    return create_agent(
        name=f"Variant-{variant_type}",
        instructions=system_prompt,
        agent_type="variant",
    )


def generate_variant(
    source_latex: str,
    variant_type: str,
    ideas: Optional[IdeaResult] = None,
    use_context: bool = True,
) -> str:
    """Generate a variant of the source problem.
    
    Creates a new problem variant based on the specified type:
    - numerical: Changes only numerical values
    - context: Changes only the scenario/context
    - conceptual: Changes the core physics concept
    - calculus: Adds calculus-based modifications
    
    Args:
        source_latex: The source problem in LaTeX format
        variant_type: Type of variant to generate
        ideas: Optional IdeaResult with extracted concepts (used for context)
        use_context: Whether to include reference context in prompt
        
    Returns:
        The generated variant in LaTeX format
        
    Raises:
        ValueError: If source_latex is empty or variant_type is invalid
    """
    if not source_latex.strip():
        raise ValueError("Source LaTeX cannot be empty")
    
    # Get prompts for this variant type
    system_prompt, user_template = get_variant_prompt(variant_type)
    
    # Create the agent
    agent = create_variant_agent(variant_type, use_context)
    
    # Format the user message
    message = user_template.format(source_latex=source_latex)
    
    # Add ideas context if provided
    if ideas and ideas.concepts:
        message += f"\n\nKey Concepts: {', '.join(ideas.concepts)}"
    if ideas and ideas.techniques:
        message += f"\nTechniques: {', '.join(ideas.techniques)}"
    
    # Run the agent
    raw_result = run_agent_sync(agent, message)
    
    # Clean up markdown artifacts from LLM output
    return clean_latex_output(raw_result)
