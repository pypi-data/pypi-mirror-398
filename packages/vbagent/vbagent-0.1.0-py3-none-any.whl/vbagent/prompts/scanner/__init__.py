"""Scanner prompts for different question types.

Each question type has its own prompt file with SYSTEM_PROMPT and USER_TEMPLATE.
Common TikZ guidelines are in common.py and can be imported into individual prompts.
"""

from vbagent.prompts.scanner.mcq_sc import SYSTEM_PROMPT as MCQ_SC_PROMPT
from vbagent.prompts.scanner.mcq_mc import SYSTEM_PROMPT as MCQ_MC_PROMPT
from vbagent.prompts.scanner.subjective import SYSTEM_PROMPT as SUBJECTIVE_PROMPT
from vbagent.prompts.scanner.assertion_reason import SYSTEM_PROMPT as ASSERTION_REASON_PROMPT
from vbagent.prompts.scanner.passage import SYSTEM_PROMPT as PASSAGE_PROMPT
from vbagent.prompts.scanner.match import SYSTEM_PROMPT as MATCH_PROMPT
from vbagent.prompts.scanner.common import (
    TIKZ_GUIDELINES,
    TIKZ_GUIDELINES_SHORT,
    LATEX_FORMATTING_RULES,
    PGFPLOTS_EXAMPLE,
    OPTIONS_WITH_DIAGRAMS,
    DIAGRAM_PLACEHOLDER,
)

# Mapping from question type to prompt
SCANNER_PROMPTS = {
    "mcq_sc": MCQ_SC_PROMPT,
    "mcq_mc": MCQ_MC_PROMPT,
    "subjective": SUBJECTIVE_PROMPT,
    "assertion_reason": ASSERTION_REASON_PROMPT,
    "passage": PASSAGE_PROMPT,
    "match": MATCH_PROMPT,
}

# Default user template for all scanner types
USER_TEMPLATE = "Extract LaTeX from this physics question image."


def get_scanner_prompt(question_type: str) -> str:
    """Get the scanner prompt for a given question type.
    
    Args:
        question_type: The type of question (mcq_sc, mcq_mc, etc.)
        
    Returns:
        The system prompt for that question type
        
    Raises:
        KeyError: If question_type is not recognized
    """
    if question_type not in SCANNER_PROMPTS:
        # Fall back to mcq_sc for unknown types
        return SCANNER_PROMPTS["mcq_sc"]
    return SCANNER_PROMPTS[question_type]


__all__ = [
    "SCANNER_PROMPTS",
    "USER_TEMPLATE",
    "get_scanner_prompt",
    "MCQ_SC_PROMPT",
    "MCQ_MC_PROMPT",
    "SUBJECTIVE_PROMPT",
    "ASSERTION_REASON_PROMPT",
    "PASSAGE_PROMPT",
    "MATCH_PROMPT",
    # Common prompt components
    "TIKZ_GUIDELINES",
    "TIKZ_GUIDELINES_SHORT",
    "LATEX_FORMATTING_RULES",
    "PGFPLOTS_EXAMPLE",
    "OPTIONS_WITH_DIAGRAMS",
    "DIAGRAM_PLACEHOLDER",
]
