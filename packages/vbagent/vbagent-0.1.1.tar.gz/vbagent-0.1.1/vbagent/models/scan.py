"""Scan result data model."""

from pydantic import BaseModel, Field


class ScanResult(BaseModel):
    """Result from the Scanner Agent.
    
    Contains extracted LaTeX and diagram information.
    """
    latex: str = Field(description="Extracted LaTeX code")
    has_diagram: bool = Field(default=False, description="Whether the question has a diagram")
    raw_diagram_description: str | None = Field(default=None, description="Description of diagram if present")
