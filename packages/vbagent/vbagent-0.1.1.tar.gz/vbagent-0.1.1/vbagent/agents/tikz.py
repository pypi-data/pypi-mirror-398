"""TikZ agent for diagram generation.

Uses openai-agents SDK to generate TikZ/PGF code for physics diagrams,
with tool access to search reference files for syntax examples.

**Feature: physics-question-pipeline**
**Validates: Requirements 3.1, 3.2, 3.3, 3.4**
"""

import re

from vbagent.agents.base import (
    create_agent,
    create_image_message,
    run_agent_sync,
)
from vbagent.prompts.tikz import SYSTEM_PROMPT, USER_TEMPLATE
from vbagent.references.store import ReferenceStore
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


# Lazy-loaded tool to avoid importing agents SDK at module load
_search_tikz_reference_tool = None


def _get_search_tikz_reference_tool():
    """Get the search_tikz_reference tool, creating it lazily."""
    global _search_tikz_reference_tool
    if _search_tikz_reference_tool is None:
        from agents import function_tool
        
        @function_tool
        def search_tikz_reference(query: str) -> str:
            """Search TikZ/PGF reference files for syntax examples.
            
            Use this tool to find relevant TikZ syntax, package documentation,
            or style definitions from the configured reference files.
            
            Args:
                query: Search query for TikZ/PGF syntax or examples
                
            Returns:
                Relevant content from reference files, or empty string if none found
            """
            store = ReferenceStore.get_instance()
            results = store.search(query, file_types=["sty", "tex", "pdf"])
            
            if not results:
                return "No relevant references found. Using default TikZ knowledge."
            
            # Return top 3 results concatenated
            content_parts = []
            for result in results[:3]:
                content_parts.append(f"--- From {result.file_path} ---\n{result.content}")
            
            return "\n\n".join(content_parts)
        
        _search_tikz_reference_tool = search_tikz_reference
    
    return _search_tikz_reference_tool


# Public accessor for the tool (for testing and direct use)
# This is a property-like accessor that returns the lazy-loaded tool
class _SearchTikzReferenceAccessor:
    """Lazy accessor for search_tikz_reference tool."""
    
    def __getattr__(self, name):
        return getattr(_get_search_tikz_reference_tool(), name)
    
    def __call__(self, *args, **kwargs):
        return _get_search_tikz_reference_tool()(*args, **kwargs)


search_tikz_reference = _SearchTikzReferenceAccessor()


def create_tikz_agent(use_context: bool = True, classification=None):
    """Create a TikZ agent with optional context.
    
    Args:
        use_context: Whether to include reference context in prompt
        classification: Optional ClassificationResult for metadata-based context
        
    Returns:
        Configured Agent instance for TikZ generation
    """
    prompt = SYSTEM_PROMPT
    
    # Add metadata-based TikZ context if classification provided
    if use_context and classification:
        tikz_context = get_tikz_context_for_classification(classification)
        if tikz_context:
            prompt = prompt + "\n" + tikz_context
    
    # Fallback to generic category-based context
    if use_context:
        context = get_context_prompt_section("tikz", use_context)
        if context:
            prompt = prompt + "\n" + context
    
    return create_agent(
        name="TikZ",
        instructions=prompt,
        tools=[_get_search_tikz_reference_tool()],
        agent_type="tikz",
    )


def get_tikz_context_for_classification(classification) -> str:
    """Get TikZ context matched to classification metadata.
    
    Args:
        classification: ClassificationResult with diagram metadata
        
    Returns:
        Formatted context string with matching TikZ examples
    """
    try:
        from vbagent.references.tikz_store import TikZReferenceStore
        
        store = TikZReferenceStore.get_instance()
        context = store.get_context_for_classification(classification)
        
        if not context:
            return ""
        
        return f"""
## Matching TikZ Examples

The following examples match your diagram type and topic. Use them as style references:

{context}

---
"""
    except Exception:
        # If tikz_store not available or errors, return empty
        return ""


# Default TikZ agent (created lazily to allow context configuration)
_tikz_agent = None


def generate_tikz(
    description: str,
    image_path: str | None = None,
    search_references: bool = True,
    use_context: bool = True,
    classification=None,
) -> str:
    """Generate TikZ code for a diagram.
    
    Can generate from a text description, an image, or both.
    The agent can search reference files for relevant syntax.
    
    Args:
        description: Text description of the diagram to generate
        image_path: Optional path to an image of the diagram
        search_references: Whether to enable reference search (default True)
        use_context: Whether to include reference context in prompt
        classification: Optional ClassificationResult for metadata-based context
        
    Returns:
        Generated TikZ code as a string
        
    Raises:
        FileNotFoundError: If image_path is provided but file doesn't exist
    """
    # Create agent with context setting and classification for metadata matching
    agent = create_tikz_agent(use_context, classification)
    
    # Format the user message
    user_message = USER_TEMPLATE.format(description=description)
    
    if image_path:
        # Create message with image and text
        message = create_image_message(image_path, user_message)
    else:
        message = user_message
    
    # Run the agent
    raw_result = run_agent_sync(agent, message)
    
    # Clean up markdown artifacts from LLM output
    return clean_latex_output(raw_result)


def validate_tikz_output(tikz_code: str) -> bool:
    """Validate that TikZ output contains expected structure.
    
    Checks for presence of tikzpicture environment markers.
    
    Args:
        tikz_code: The TikZ code to validate
        
    Returns:
        True if the code appears to be valid TikZ, False otherwise
    """
    if not tikz_code or not tikz_code.strip():
        return False
    
    code_lower = tikz_code.lower()
    
    # Check for tikzpicture environment or common TikZ commands
    has_tikzpicture = "tikzpicture" in code_lower
    has_draw_commands = any(cmd in code_lower for cmd in ["\\draw", "\\node", "\\fill", "\\path"])
    
    return has_tikzpicture or has_draw_commands
