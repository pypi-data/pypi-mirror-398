"""Idea result data model."""

from pydantic import BaseModel, Field


class IdeaResult(BaseModel):
    """Result from the Idea Agent.
    
    Contains extracted physics concepts and problem-solving ideas.
    Used as output_type for structured outputs with openai-agents SDK.
    """
    concepts: list[str] = Field(default_factory=list, description="Primary physics concepts")
    formulas: list[str] = Field(default_factory=list, description="Key formulas used")
    techniques: list[str] = Field(default_factory=list, description="Problem-solving techniques")
    difficulty_factors: list[str] = Field(default_factory=list, description="What makes this problem difficult")
