"""Review data models for QA Review Agent.

Pydantic models for structured review suggestions and results.
"""

from enum import Enum
from pydantic import BaseModel, Field


class ReviewIssueType(str, Enum):
    """Type of issue found during QA review."""
    LATEX_SYNTAX = "latex_syntax"
    PHYSICS_ERROR = "physics_error"
    SOLUTION_ERROR = "solution_error"
    VARIANT_INCONSISTENCY = "variant_inconsistency"
    FORMATTING = "formatting"
    GRAMMAR = "grammar"
    CLARITY = "clarity"
    OTHER = "other"


class Suggestion(BaseModel):
    """A suggested edit from the QA Review Agent.
    
    Contains the issue details, reasoning, and a unified diff
    representing the proposed change.
    """
    issue_type: ReviewIssueType = Field(description="Type of issue found")
    file_path: str = Field(description="Path to the file to modify")
    description: str = Field(description="Brief description of the issue")
    reasoning: str = Field(description="Detailed reasoning for the suggestion")
    confidence: float = Field(
        ge=0.0, le=1.0,
        description="Confidence score between 0.0 and 1.0"
    )
    original_content: str = Field(description="Original content before change")
    suggested_content: str = Field(description="Suggested content after change")
    diff: str = Field(description="Unified diff format of the change")


class ReviewResult(BaseModel):
    """Result from reviewing a problem.
    
    Contains the overall review status and any suggestions.
    """
    problem_id: str = Field(description="ID of the reviewed problem")
    passed: bool = Field(description="Whether the problem passed review")
    suggestions: list[Suggestion] = Field(
        default_factory=list,
        description="List of suggested changes"
    )
    summary: str = Field(description="Summary of the review")


class ReviewStats(BaseModel):
    """Statistics from review sessions.
    
    Aggregated metrics across review sessions.
    """
    total_reviewed: int = Field(default=0, description="Total problems reviewed")
    total_suggestions: int = Field(default=0, description="Total suggestions made")
    approved_count: int = Field(default=0, description="Number of approved suggestions")
    rejected_count: int = Field(default=0, description="Number of rejected suggestions")
    skipped_count: int = Field(default=0, description="Number of skipped suggestions")
    approval_rate: float = Field(default=0.0, description="Approval rate (0.0 to 1.0)")
    issues_by_type: dict[str, int] = Field(
        default_factory=dict,
        description="Count of issues by type"
    )
