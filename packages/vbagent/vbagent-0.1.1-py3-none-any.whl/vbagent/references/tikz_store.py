"""TikZ reference store with metadata-based context selection.

Stores TikZ examples with classification metadata for intelligent
context matching during TikZ generation.
"""

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from vbagent.references.context import _get_config_dir


@dataclass
class TikZMetadata:
    """Metadata for a TikZ reference, derived from classification."""
    
    diagram_type: Optional[str] = None  # graph, circuit, free_body, geometry, pulley, spring, etc.
    topic: Optional[str] = None  # mechanics, waves, optics, thermodynamics, etc.
    subtopic: Optional[str] = None  # shm, kinematics, etc.
    question_type: Optional[str] = None  # mcq_sc, subjective, etc.
    key_concepts: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "diagram_type": self.diagram_type,
            "topic": self.topic,
            "subtopic": self.subtopic,
            "question_type": self.question_type,
            "key_concepts": self.key_concepts,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "TikZMetadata":
        return cls(
            diagram_type=data.get("diagram_type"),
            topic=data.get("topic"),
            subtopic=data.get("subtopic"),
            question_type=data.get("question_type"),
            key_concepts=data.get("key_concepts", []),
        )
    
    @classmethod
    def from_classification(cls, classification) -> "TikZMetadata":
        """Create metadata from a ClassificationResult."""
        return cls(
            diagram_type=classification.diagram_type,
            topic=classification.topic,
            subtopic=classification.subtopic,
            question_type=classification.question_type,
            key_concepts=classification.key_concepts,
        )
    
    def match_score(self, other: "TikZMetadata") -> int:
        """Calculate match score with another metadata (higher = better match)."""
        score = 0
        
        # Exact diagram_type match is most important
        if self.diagram_type and other.diagram_type:
            if self.diagram_type == other.diagram_type:
                score += 10
        
        # Topic match
        if self.topic and other.topic:
            if self.topic.lower() == other.topic.lower():
                score += 5
        
        # Subtopic match
        if self.subtopic and other.subtopic:
            if self.subtopic.lower() == other.subtopic.lower():
                score += 3
        
        # Question type match
        if self.question_type and other.question_type:
            if self.question_type == other.question_type:
                score += 2
        
        # Key concepts overlap
        if self.key_concepts and other.key_concepts:
            self_concepts = set(c.lower() for c in self.key_concepts)
            other_concepts = set(c.lower() for c in other.key_concepts)
            overlap = len(self_concepts & other_concepts)
            score += overlap
        
        return score


@dataclass
class TikZReference:
    """A TikZ reference with metadata."""
    
    id: str  # Unique identifier (e.g., Problem_5)
    name: str  # Display name
    tikz_code: str  # The TikZ code
    metadata: TikZMetadata
    source_file: Optional[str] = None  # Original source file path
    description: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "tikz_code": self.tikz_code,
            "metadata": self.metadata.to_dict(),
            "source_file": self.source_file,
            "description": self.description,
            "created_at": self.created_at,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "TikZReference":
        return cls(
            id=data["id"],
            name=data["name"],
            tikz_code=data["tikz_code"],
            metadata=TikZMetadata.from_dict(data.get("metadata", {})),
            source_file=data.get("source_file"),
            description=data.get("description"),
            created_at=data.get("created_at", datetime.now().isoformat()),
        )


class TikZReferenceStore:
    """Store for TikZ references with metadata-based retrieval.
    
    Structure:
        ~/.config/vbagent/
        └── tikz_references.json  # Index with embedded TikZ code
    """
    
    CONFIG_DIR = _get_config_dir()
    STORE_FILE = "tikz_references.json"
    
    _instance: Optional["TikZReferenceStore"] = None
    
    def __init__(self):
        """Initialize the TikZ reference store."""
        self.config_dir = self.CONFIG_DIR
        self.store_path = self.config_dir / self.STORE_FILE
        self.references: list[TikZReference] = []
        self.enabled: bool = True
        self.max_examples: int = 3
        
        self._ensure_directories()
        self._load()
    
    @classmethod
    def get_instance(cls) -> "TikZReferenceStore":
        """Get or create the singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton instance (for testing)."""
        cls._instance = None
    
    def _ensure_directories(self):
        """Create necessary directories."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
    
    def _load(self):
        """Load references from disk."""
        if self.store_path.exists():
            try:
                data = json.loads(self.store_path.read_text())
                self.references = [
                    TikZReference.from_dict(r) for r in data.get("references", [])
                ]
                self.enabled = data.get("enabled", True)
                self.max_examples = data.get("max_examples", 3)
            except (json.JSONDecodeError, KeyError):
                self.references = []
    
    def _save(self):
        """Save references to disk."""
        data = {
            "enabled": self.enabled,
            "max_examples": self.max_examples,
            "references": [r.to_dict() for r in self.references],
        }
        self.store_path.write_text(json.dumps(data, indent=2))
    
    def add_reference(
        self,
        tikz_code: str,
        metadata: TikZMetadata,
        name: Optional[str] = None,
        source_file: Optional[str] = None,
        description: Optional[str] = None,
    ) -> TikZReference:
        """Add a TikZ reference.
        
        Args:
            tikz_code: The TikZ code
            metadata: Classification metadata
            name: Display name (auto-generated if not provided)
            source_file: Original source file path
            description: Optional description
            
        Returns:
            The created TikZReference
        """
        # Generate ID
        existing_ids = {r.id for r in self.references}
        if source_file:
            base_id = Path(source_file).stem
        else:
            base_id = f"tikz_{len(self.references) + 1}"
        
        # Ensure unique ID
        ref_id = base_id
        counter = 1
        while ref_id in existing_ids:
            ref_id = f"{base_id}_{counter}"
            counter += 1
        
        # Generate name if not provided
        if not name:
            parts = []
            if metadata.diagram_type:
                parts.append(metadata.diagram_type)
            if metadata.topic:
                parts.append(metadata.topic)
            name = "_".join(parts) if parts else ref_id
        
        ref = TikZReference(
            id=ref_id,
            name=name,
            tikz_code=tikz_code,
            metadata=metadata,
            source_file=source_file,
            description=description,
        )
        
        self.references.append(ref)
        self._save()
        
        return ref
    
    def add_from_problem(
        self,
        scan_path: str,
        tikz_path: Optional[str] = None,
        classification_path: Optional[str] = None,
        skip_duplicates: bool = True,
    ) -> tuple[Optional[TikZReference], Optional[str]]:
        """Add a TikZ reference from a processed problem.
        
        Extracts TikZ code from the scan file and loads classification metadata.
        
        Args:
            scan_path: Path to the scanned .tex file (agentic/scans/Problem_X.tex)
            tikz_path: Optional path to separate TikZ file (agentic/tikz/Problem_X.tex)
            classification_path: Optional path to classification JSON
            skip_duplicates: If True, skip if identical TikZ already exists
            
        Returns:
            Tuple of (TikZReference or None, status message or None)
            - (ref, None) = successfully added
            - (None, "no_tikz") = no TikZ found in file
            - (None, "duplicate:ID") = duplicate of existing reference ID
        """
        scan_file = Path(scan_path)
        if not scan_file.exists():
            raise FileNotFoundError(f"Scan file not found: {scan_path}")
        
        problem_id = scan_file.stem
        base_dir = scan_file.parent.parent  # Go up from scans/ to agentic/
        
        # Try to find TikZ code
        tikz_code = None
        
        # Option 1: Separate TikZ file
        if tikz_path:
            tikz_file = Path(tikz_path)
        else:
            tikz_file = base_dir / "tikz" / f"{problem_id}.tex"
        
        if tikz_file.exists():
            tikz_code = tikz_file.read_text()
        else:
            # Option 2: Extract from scan file
            scan_content = scan_file.read_text()
            tikz_code = self._extract_tikz_from_latex(scan_content)
        
        if not tikz_code:
            return None, "no_tikz"
        
        # Check for duplicates
        if skip_duplicates:
            existing = self.find_duplicate(tikz_code)
            if existing:
                return None, f"duplicate:{existing.id}"
        
        # Load classification metadata
        if classification_path:
            class_file = Path(classification_path)
        else:
            class_file = base_dir / "classifications" / f"{problem_id}.json"
        
        metadata = TikZMetadata()
        if class_file.exists():
            try:
                class_data = json.loads(class_file.read_text())
                metadata = TikZMetadata(
                    diagram_type=class_data.get("diagram_type"),
                    topic=class_data.get("topic"),
                    subtopic=class_data.get("subtopic"),
                    question_type=class_data.get("question_type"),
                    key_concepts=class_data.get("key_concepts", []),
                )
            except (json.JSONDecodeError, KeyError):
                pass
        
        # Generate description
        desc_parts = []
        if metadata.diagram_type:
            desc_parts.append(f"Diagram: {metadata.diagram_type}")
        if metadata.topic:
            desc_parts.append(f"Topic: {metadata.topic}")
        description = ", ".join(desc_parts) if desc_parts else None
        
        ref = self.add_reference(
            tikz_code=tikz_code,
            metadata=metadata,
            name=problem_id,
            source_file=str(scan_file),
            description=description,
        )
        return ref, None
    
    def _extract_tikz_from_latex(self, content: str) -> Optional[str]:
        """Extract TikZ code from LaTeX content."""
        # Look for tikzpicture environments
        pattern = r'\\begin\{tikzpicture\}.*?\\end\{tikzpicture\}'
        matches = re.findall(pattern, content, re.DOTALL)
        
        if matches:
            return "\n\n".join(matches)
        
        # Look for \def\OptionA style definitions
        option_pattern = r'\\def\\Option[A-Z]\{.*?\}'
        option_matches = re.findall(option_pattern, content, re.DOTALL)
        
        if option_matches:
            return "\n\n".join(option_matches)
        
        return None
    
    def _normalize_tikz(self, tikz_code: str) -> str:
        """Normalize TikZ code for comparison (remove whitespace variations)."""
        # Remove all whitespace and normalize
        normalized = re.sub(r'\s+', '', tikz_code)
        return normalized.lower()
    
    def find_duplicate(self, tikz_code: str) -> Optional[TikZReference]:
        """Check if TikZ code already exists in store.
        
        Args:
            tikz_code: The TikZ code to check
            
        Returns:
            The existing TikZReference if duplicate found, None otherwise
        """
        normalized_new = self._normalize_tikz(tikz_code)
        
        for ref in self.references:
            normalized_existing = self._normalize_tikz(ref.tikz_code)
            if normalized_new == normalized_existing:
                return ref
        
        return None
    
    def remove_reference(self, ref_id: str) -> bool:
        """Remove a reference by ID."""
        original_len = len(self.references)
        self.references = [r for r in self.references if r.id != ref_id]
        
        if len(self.references) < original_len:
            self._save()
            return True
        return False
    
    def get_reference(self, ref_id: str) -> Optional[TikZReference]:
        """Get a reference by ID."""
        for ref in self.references:
            if ref.id == ref_id:
                return ref
        return None
    
    def list_references(
        self,
        diagram_type: Optional[str] = None,
        topic: Optional[str] = None,
    ) -> list[TikZReference]:
        """List references with optional filtering."""
        results = self.references
        
        if diagram_type:
            results = [r for r in results if r.metadata.diagram_type == diagram_type]
        
        if topic:
            results = [r for r in results if r.metadata.topic and r.metadata.topic.lower() == topic.lower()]
        
        return results
    
    def get_matching_context(
        self,
        metadata: TikZMetadata,
        max_examples: Optional[int] = None,
    ) -> str:
        """Get TikZ context that matches the given metadata.
        
        Args:
            metadata: The metadata to match against
            max_examples: Maximum examples to return (uses store default if None)
            
        Returns:
            Formatted context string with matching TikZ examples
        """
        if not self.enabled or not self.references:
            return ""
        
        if max_examples is None:
            max_examples = self.max_examples
        
        # Score all references
        scored = []
        for ref in self.references:
            score = ref.metadata.match_score(metadata)
            if score > 0:  # Only include if there's some match
                scored.append((score, ref))
        
        # Sort by score (highest first) and take top N
        scored.sort(key=lambda x: x[0], reverse=True)
        top_refs = [ref for _, ref in scored[:max_examples]]
        
        if not top_refs:
            return ""
        
        # Format as context
        parts = []
        for ref in top_refs:
            header = f"% === Example: {ref.name} ==="
            meta_parts = []
            if ref.metadata.diagram_type:
                meta_parts.append(f"diagram_type: {ref.metadata.diagram_type}")
            if ref.metadata.topic:
                meta_parts.append(f"topic: {ref.metadata.topic}")
            if meta_parts:
                header += f"\n% Metadata: {', '.join(meta_parts)}"
            if ref.description:
                header += f"\n% {ref.description}"
            parts.append(f"{header}\n{ref.tikz_code}")
        
        return "\n\n".join(parts)
    
    def get_context_for_classification(self, classification) -> str:
        """Get TikZ context based on a ClassificationResult.
        
        Args:
            classification: A ClassificationResult object
            
        Returns:
            Formatted context string
        """
        metadata = TikZMetadata.from_classification(classification)
        return self.get_matching_context(metadata)
    
    def enable(self):
        """Enable TikZ context."""
        self.enabled = True
        self._save()
    
    def disable(self):
        """Disable TikZ context."""
        self.enabled = False
        self._save()
    
    def set_max_examples(self, max_examples: int):
        """Set maximum examples to include."""
        self.max_examples = max_examples
        self._save()
    
    def get_stats(self) -> dict:
        """Get statistics about stored references."""
        by_diagram_type: dict[str, int] = {}
        by_topic: dict[str, int] = {}
        
        for ref in self.references:
            dt = ref.metadata.diagram_type or "unknown"
            by_diagram_type[dt] = by_diagram_type.get(dt, 0) + 1
            
            topic = ref.metadata.topic or "unknown"
            by_topic[topic] = by_topic.get(topic, 0) + 1
        
        return {
            "enabled": self.enabled,
            "max_examples": self.max_examples,
            "total": len(self.references),
            "by_diagram_type": by_diagram_type,
            "by_topic": by_topic,
        }
