"""Pipeline result data model."""

from pydantic import BaseModel, Field

from .classification import ClassificationResult
from .idea import IdeaResult


class PipelineResult(BaseModel):
    """Result from the full processing pipeline.
    
    Contains all outputs from the pipeline stages.
    """
    source_path: str = Field(description="Path to source file")
    classification: ClassificationResult = Field(description="Classification result")
    latex: str = Field(description="Extracted LaTeX")
    tikz_code: str | None = Field(default=None, description="Generated TikZ code")
    ideas: IdeaResult | None = Field(default=None, description="Extracted ideas")
    alternate_solutions: list[str] = Field(default_factory=list, description="Alternative solutions")
    variants: dict[str, str] = Field(default_factory=dict, description="Generated variants by type")
