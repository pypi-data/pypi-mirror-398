"""Agent modules for vbagent using openai-agents SDK.

Uses lazy imports to avoid loading heavy dependencies (openai, agents, mcp, pydantic)
until they are actually needed. This significantly improves CLI startup time.
"""

from typing import TYPE_CHECKING

# Only import for type checking - avoids heavy runtime imports
if TYPE_CHECKING:
    from .base import (
        encode_image,
        create_image_message,
        create_agent,
        run_agent,
        run_agent_sync,
    )
    from .classifier import classifier_agent, classify
    from .idea import idea_agent_json, idea_agent_latex, extract_ideas, generate_idea_latex
    from .alternate import alternate_agent, generate_alternate, extract_answer
    from .selector import (
        ProblemContext,
        discover_problems,
        select_random,
        load_problem_context,
    )
    from .solution_checker import (
        solution_checker_agent,
        check_solution,
        has_solution_passed,
    )
    from .grammar_checker import (
        grammar_checker_agent,
        check_grammar,
        has_grammar_passed,
    )
    from .clarity_checker import (
        clarity_checker_agent,
        check_clarity,
        has_clarity_passed,
    )
    from .tikz_checker import (
        tikz_checker_agent,
        check_tikz,
        has_tikz_passed,
        has_tikz_environment,
    )


__all__ = [
    "encode_image",
    "create_image_message",
    "create_agent",
    "run_agent",
    "run_agent_sync",
    "classifier_agent",
    "classify",
    "idea_agent_json",
    "idea_agent_latex",
    "extract_ideas",
    "generate_idea_latex",
    "alternate_agent",
    "generate_alternate",
    "extract_answer",
    "ProblemContext",
    "discover_problems",
    "select_random",
    "load_problem_context",
    # Solution checker
    "solution_checker_agent",
    "check_solution",
    "has_solution_passed",
    # Grammar checker
    "grammar_checker_agent",
    "check_grammar",
    "has_grammar_passed",
    # Clarity checker
    "clarity_checker_agent",
    "check_clarity",
    "has_clarity_passed",
    # TikZ checker
    "tikz_checker_agent",
    "check_tikz",
    "has_tikz_passed",
    "has_tikz_environment",
]


def __getattr__(name: str):
    """Lazy import of agent modules to speed up CLI startup."""
    if name in ("encode_image", "create_image_message", "create_agent", "run_agent", "run_agent_sync"):
        from . import base
        return getattr(base, name)
    
    if name in ("classifier_agent", "classify"):
        from . import classifier
        return getattr(classifier, name)
    
    if name in ("idea_agent_json", "idea_agent_latex", "extract_ideas", "generate_idea_latex"):
        from . import idea
        return getattr(idea, name)
    
    if name in ("alternate_agent", "generate_alternate", "extract_answer"):
        from . import alternate
        return getattr(alternate, name)
    
    if name in ("ProblemContext", "discover_problems", "select_random", "load_problem_context"):
        from . import selector
        return getattr(selector, name)
    
    if name in ("solution_checker_agent", "check_solution", "has_solution_passed"):
        from . import solution_checker
        return getattr(solution_checker, name)
    
    if name in ("grammar_checker_agent", "check_grammar", "has_grammar_passed"):
        from . import grammar_checker
        return getattr(grammar_checker, name)
    
    if name in ("clarity_checker_agent", "check_clarity", "has_clarity_passed"):
        from . import clarity_checker
        return getattr(clarity_checker, name)
    
    if name in ("tikz_checker_agent", "check_tikz", "has_tikz_passed", "has_tikz_environment"):
        from . import tikz_checker
        return getattr(tikz_checker, name)
    
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
