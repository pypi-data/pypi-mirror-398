"""Classification result data model."""

from typing import Literal
from pydantic import BaseModel, Field


QuestionType = Literal[
    "mcq_sc",
    "mcq_mc",
    "subjective",
    "assertion_reason",
    "passage",
    "match"
]

Difficulty = Literal["easy", "medium", "hard"]

DiagramType = Literal["graph", "circuit", "free_body", "geometry", "none"]


class ClassificationResult(BaseModel):
    """Result from the Classifier Agent.
    
    Contains metadata extracted from a physics question image.
    Used as output_type for structured outputs with openai-agents SDK.
    """
    question_type: QuestionType = Field(description="Type of question")
    difficulty: Difficulty = Field(description="Difficulty level")
    topic: str = Field(description="Physics topic e.g., kinematics, thermodynamics")
    subtopic: str = Field(description="Specific subtopic")
    has_diagram: bool = Field(description="Whether the question contains a diagram")
    diagram_type: DiagramType | None = Field(default=None, description="Type of diagram if present")
    num_options: int | None = Field(default=None, description="Number of options if MCQ")
    estimated_marks: int = Field(default=1, description="Estimated marks")
    key_concepts: list[str] = Field(default_factory=list, description="Key physics concepts")
    requires_calculus: bool = Field(default=False, description="Whether calculus is required")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Classification confidence")
