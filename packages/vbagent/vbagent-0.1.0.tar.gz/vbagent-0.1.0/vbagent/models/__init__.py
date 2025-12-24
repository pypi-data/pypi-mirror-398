"""Data models for vbagent.

Uses lazy imports to avoid loading pydantic until models are actually needed.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .classification import ClassificationResult
    from .scan import ScanResult
    from .idea import IdeaResult
    from .pipeline import PipelineResult
    from .review import ReviewIssueType, Suggestion, ReviewResult, ReviewStats
    from .version_store import SuggestionStatus, StoredSuggestion, VersionStore

__all__ = [
    "ClassificationResult",
    "ScanResult",
    "IdeaResult",
    "PipelineResult",
    "ReviewIssueType",
    "Suggestion",
    "ReviewResult",
    "ReviewStats",
    "SuggestionStatus",
    "StoredSuggestion",
    "VersionStore",
]


def __getattr__(name: str):
    """Lazy import of model classes to speed up CLI startup."""
    if name == "ClassificationResult":
        from .classification import ClassificationResult
        return ClassificationResult
    
    if name == "ScanResult":
        from .scan import ScanResult
        return ScanResult
    
    if name == "IdeaResult":
        from .idea import IdeaResult
        return IdeaResult
    
    if name == "PipelineResult":
        from .pipeline import PipelineResult
        return PipelineResult
    
    if name in ("ReviewIssueType", "Suggestion", "ReviewResult", "ReviewStats"):
        from . import review
        return getattr(review, name)
    
    if name in ("SuggestionStatus", "StoredSuggestion", "VersionStore"):
        from . import version_store
        return getattr(version_store, name)
    
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
