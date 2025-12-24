"""Context store for managing reference files in config directory.

Provides persistent storage for TikZ, LaTeX, and variant examples
that can be used as context for better LLM output.

Config directory location:
- Linux/macOS: ~/.config/vbagent
- Windows: %APPDATA%/vbagent
"""

import json
import os
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


def _get_config_dir() -> Path:
    """Get the platform-specific config directory.
    
    Returns:
        Path to config directory:
        - Windows: %APPDATA%/vbagent
        - macOS/Linux: ~/.config/vbagent
    """
    if sys.platform == "win32":
        # Windows: use APPDATA
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / "vbagent"
        # Fallback to home directory
        return Path.home() / "AppData" / "Roaming" / "vbagent"
    else:
        # Unix-like: use XDG_CONFIG_HOME or ~/.config
        xdg_config = os.environ.get("XDG_CONFIG_HOME")
        if xdg_config:
            return Path(xdg_config) / "vbagent"
        return Path.home() / ".config" / "vbagent"


# Reference categories
CATEGORIES = ["tikz", "latex", "variants", "problems"]


@dataclass
class ContextConfig:
    """Configuration for context usage."""
    enabled: bool = True
    max_examples_per_category: int = 5
    
    def to_dict(self) -> dict:
        return {
            "enabled": self.enabled,
            "max_examples_per_category": self.max_examples_per_category,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "ContextConfig":
        return cls(
            enabled=data.get("enabled", True),
            max_examples_per_category=data.get("max_examples_per_category", 5),
        )


@dataclass
class ReferenceFile:
    """A reference file entry."""
    name: str
    category: str
    path: str
    description: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "category": self.category,
            "path": self.path,
            "description": self.description,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "ReferenceFile":
        return cls(
            name=data["name"],
            category=data["category"],
            path=data["path"],
            description=data.get("description"),
        )


class ContextStore:
    """Manages reference files stored in ~/.config/vbagent.
    
    Structure:
        ~/.config/vbagent/
        ├── config.json          # Settings
        ├── references.json      # Index of reference files
        └── references/
            ├── tikz/            # TikZ code examples
            ├── latex/           # LaTeX formatting examples
            ├── variants/        # Variant examples
            └── problems/        # Example problems
    """
    
    CONFIG_DIR = _get_config_dir()
    CONFIG_FILE = "config.json"
    REFERENCES_FILE = "references.json"
    REFERENCES_DIR = "references"
    
    _instance: Optional["ContextStore"] = None
    
    def __init__(self):
        """Initialize the context store."""
        self.config_dir = self.CONFIG_DIR
        self.config_path = self.config_dir / self.CONFIG_FILE
        self.references_path = self.config_dir / self.REFERENCES_FILE
        self.references_dir = self.config_dir / self.REFERENCES_DIR
        
        self.config = ContextConfig()
        self.references: list[ReferenceFile] = []
        
        self._ensure_directories()
        self._load()
    
    @classmethod
    def get_instance(cls) -> "ContextStore":
        """Get or create the singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton instance (for testing)."""
        cls._instance = None
    
    def _ensure_directories(self):
        """Create necessary directories if they don't exist."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.references_dir.mkdir(parents=True, exist_ok=True)
        
        # Create category subdirectories
        for category in CATEGORIES:
            (self.references_dir / category).mkdir(exist_ok=True)
    
    def _load(self):
        """Load configuration and references from disk."""
        # Load config
        if self.config_path.exists():
            try:
                data = json.loads(self.config_path.read_text())
                self.config = ContextConfig.from_dict(data)
            except (json.JSONDecodeError, KeyError):
                self.config = ContextConfig()
        
        # Load references index
        if self.references_path.exists():
            try:
                data = json.loads(self.references_path.read_text())
                self.references = [
                    ReferenceFile.from_dict(r) for r in data.get("references", [])
                ]
            except (json.JSONDecodeError, KeyError):
                self.references = []
    
    def _save_config(self):
        """Save configuration to disk."""
        self.config_path.write_text(
            json.dumps(self.config.to_dict(), indent=2)
        )
    
    def _save_references(self):
        """Save references index to disk."""
        data = {
            "references": [r.to_dict() for r in self.references]
        }
        self.references_path.write_text(json.dumps(data, indent=2))
    
    def add_reference(
        self,
        source_path: str,
        category: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> ReferenceFile:
        """Add a reference file to the store.
        
        Args:
            source_path: Path to the source file to add
            category: Category (tikz, latex, variants, problems)
            name: Optional name (defaults to filename)
            description: Optional description
            
        Returns:
            The created ReferenceFile entry
            
        Raises:
            ValueError: If category is invalid or file doesn't exist
            FileExistsError: If reference with same name already exists
        """
        if category not in CATEGORIES:
            raise ValueError(f"Invalid category: {category}. Must be one of: {CATEGORIES}")
        
        source = Path(source_path)
        if not source.exists():
            raise FileNotFoundError(f"Source file not found: {source_path}")
        
        # Use filename if name not provided
        if not name:
            name = source.name
        
        # Check for duplicates
        existing = self.get_reference(category, name)
        if existing:
            raise FileExistsError(f"Reference '{name}' already exists in category '{category}'")
        
        # Copy file to references directory
        dest_dir = self.references_dir / category
        dest_path = dest_dir / name
        shutil.copy2(source, dest_path)
        
        # Create reference entry
        ref = ReferenceFile(
            name=name,
            category=category,
            path=str(dest_path),
            description=description,
        )
        
        self.references.append(ref)
        self._save_references()
        
        return ref
    
    def remove_reference(self, category: str, name: str) -> bool:
        """Remove a reference file.
        
        Args:
            category: Category of the reference
            name: Name of the reference
            
        Returns:
            True if removed, False if not found
        """
        ref = self.get_reference(category, name)
        if not ref:
            return False
        
        # Remove file
        ref_path = Path(ref.path)
        if ref_path.exists():
            ref_path.unlink()
        
        # Remove from index
        self.references = [r for r in self.references if not (r.category == category and r.name == name)]
        self._save_references()
        
        return True
    
    def get_reference(self, category: str, name: str) -> Optional[ReferenceFile]:
        """Get a specific reference by category and name."""
        for ref in self.references:
            if ref.category == category and ref.name == name:
                return ref
        return None
    
    def list_references(self, category: Optional[str] = None) -> list[ReferenceFile]:
        """List all references, optionally filtered by category."""
        if category:
            return [r for r in self.references if r.category == category]
        return list(self.references)
    
    def get_reference_content(self, category: str, name: str) -> Optional[str]:
        """Get the content of a reference file."""
        ref = self.get_reference(category, name)
        if not ref:
            return None
        
        ref_path = Path(ref.path)
        if not ref_path.exists():
            return None
        
        try:
            return ref_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return ref_path.read_text(encoding="latin-1")

    
    def get_context_for_category(self, category: str) -> str:
        """Get combined context from all references in a category.
        
        Args:
            category: The category to get context for
            
        Returns:
            Combined content from all references, formatted as examples
        """
        if not self.config.enabled:
            return ""
        
        refs = self.list_references(category)
        if not refs:
            return ""
        
        # Limit to max examples
        refs = refs[:self.config.max_examples_per_category]
        
        parts = []
        for ref in refs:
            content = self.get_reference_content(ref.category, ref.name)
            if content:
                header = f"% === Example: {ref.name} ==="
                if ref.description:
                    header += f"\n% {ref.description}"
                parts.append(f"{header}\n{content}")
        
        if not parts:
            return ""
        
        return "\n\n".join(parts)
    
    def get_tikz_context(self) -> str:
        """Get TikZ reference context."""
        return self.get_context_for_category("tikz")
    
    def get_latex_context(self) -> str:
        """Get LaTeX reference context."""
        return self.get_context_for_category("latex")
    
    def get_variants_context(self) -> str:
        """Get variants reference context."""
        return self.get_context_for_category("variants")
    
    def get_problems_context(self) -> str:
        """Get problems reference context."""
        return self.get_context_for_category("problems")
    
    def enable_context(self):
        """Enable context usage."""
        self.config.enabled = True
        self._save_config()
    
    def disable_context(self):
        """Disable context usage."""
        self.config.enabled = False
        self._save_config()
    
    def is_enabled(self) -> bool:
        """Check if context is enabled."""
        return self.config.enabled
    
    def set_max_examples(self, max_examples: int):
        """Set maximum examples per category."""
        self.config.max_examples_per_category = max_examples
        self._save_config()
    
    def get_stats(self) -> dict:
        """Get statistics about stored references."""
        stats = {
            "enabled": self.config.enabled,
            "max_examples": self.config.max_examples_per_category,
            "total": len(self.references),
            "by_category": {},
        }
        
        for category in CATEGORIES:
            count = len([r for r in self.references if r.category == category])
            stats["by_category"][category] = count
        
        return stats


def get_context_prompt_section(category: str, use_context: bool = True) -> str:
    """Get a formatted context section for prompts.
    
    Args:
        category: The category of context to include
        use_context: Whether to include context (can be overridden by global setting)
        
    Returns:
        Formatted context section for inclusion in prompts, or empty string
    """
    if not use_context:
        return ""
    
    store = ContextStore.get_instance()
    if not store.is_enabled():
        return ""
    
    context = store.get_context_for_category(category)
    if not context:
        return ""
    
    return f"""
## Reference Examples

Use the following examples as style and formatting references:

{context}

---
"""
