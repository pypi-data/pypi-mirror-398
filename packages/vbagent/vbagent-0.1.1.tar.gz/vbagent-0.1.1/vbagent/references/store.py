"""Reference store for searching PDF, TeX, and STY files.

**Feature: physics-question-pipeline**
**Validates: Requirements 9.1, 9.2, 9.3, 9.5**
"""

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import ClassVar


@dataclass
class SearchResult:
    """Result from a reference search."""
    file_path: str
    content: str
    relevance_score: float


@dataclass
class ReferenceStore:
    """Manages and searches reference files (PDF, TeX, STY).
    
    This class provides functionality to index and search reference files
    for TikZ/PGF syntax examples and other LaTeX-related content.
    
    Attributes:
        directories: List of directory paths to search for reference files.
        index: Dictionary mapping file paths to their indexed content.
    """
    
    directories: list[str] = field(default_factory=list)
    index: dict[str, str] = field(default_factory=dict)
    
    # Singleton instance
    _instance: ClassVar["ReferenceStore | None"] = None
    
    # Supported file extensions
    SUPPORTED_EXTENSIONS: ClassVar[set[str]] = {".pdf", ".tex", ".sty"}
    
    @classmethod
    def get_instance(cls, directories: list[str] | None = None) -> "ReferenceStore":
        """Get or create the singleton instance of ReferenceStore.
        
        Args:
            directories: Optional list of directories to initialize with.
            
        Returns:
            The singleton ReferenceStore instance.
        """
        if cls._instance is None:
            cls._instance = cls(directories=directories or [])
        elif directories:
            # Update directories if provided
            cls._instance.directories = directories
        return cls._instance
    
    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton instance (useful for testing)."""
        cls._instance = None
    
    def index_files(self) -> int:
        """Index all supported files in configured directories.
        
        Scans all configured directories for PDF, TeX, and STY files
        and indexes their content for searching.
        
        Returns:
            Number of files indexed.
        """
        self.index.clear()
        indexed_count = 0
        
        for directory in self.directories:
            dir_path = Path(directory)
            if not dir_path.exists() or not dir_path.is_dir():
                continue
            
            for file_path in dir_path.rglob("*"):
                if file_path.is_file() and file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS:
                    content = self._read_file_content(file_path)
                    if content:
                        self.index[str(file_path)] = content
                        indexed_count += 1
        
        return indexed_count
    
    def _read_file_content(self, file_path: Path) -> str | None:
        """Read content from a file based on its type.
        
        Args:
            file_path: Path to the file to read.
            
        Returns:
            File content as string, or None if reading fails.
        """
        suffix = file_path.suffix.lower()
        
        try:
            if suffix == ".pdf":
                return self._read_pdf_content(file_path)
            elif suffix in {".tex", ".sty"}:
                return self._read_text_content(file_path)
        except Exception:
            # Log warning but continue - as per design doc error handling
            return None
        
        return None
    
    def _read_text_content(self, file_path: Path) -> str | None:
        """Read content from a text file (TeX, STY).
        
        Args:
            file_path: Path to the text file.
            
        Returns:
            File content as string, or None if reading fails.
        """
        try:
            # Try UTF-8 first, then fall back to latin-1
            try:
                return file_path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                return file_path.read_text(encoding="latin-1")
        except Exception:
            return None
    
    def _read_pdf_content(self, file_path: Path) -> str | None:
        """Read content from a PDF file.
        
        Note: PDF text extraction requires additional dependencies.
        For now, we store the file path as a placeholder and return
        basic metadata. Full PDF extraction can be added later.
        
        Args:
            file_path: Path to the PDF file.
            
        Returns:
            Basic file info as string, or None if reading fails.
        """
        # For PDF files, we store basic metadata
        # Full text extraction would require pypdf or similar
        try:
            file_size = file_path.stat().st_size
            return f"[PDF: {file_path.name}, size: {file_size} bytes]"
        except Exception:
            return None
    
    def search(
        self,
        query: str,
        file_types: list[str] | None = None,
        max_results: int = 10
    ) -> list[SearchResult]:
        """Search references for relevant content.
        
        Args:
            query: Search query string.
            file_types: Optional list of file types to search (e.g., ["tex", "sty"]).
                       If None, searches all indexed files.
            max_results: Maximum number of results to return.
            
        Returns:
            List of SearchResult objects sorted by relevance score.
        """
        if not query or not query.strip():
            return []
        
        results: list[SearchResult] = []
        query_lower = query.lower()
        query_terms = self._tokenize_query(query_lower)
        
        for file_path, content in self.index.items():
            # Filter by file type if specified
            if file_types:
                file_ext = Path(file_path).suffix.lower().lstrip(".")
                if file_ext not in file_types:
                    continue
            
            # Calculate relevance score
            score = self._calculate_relevance(query_lower, query_terms, content)
            
            if score > 0:
                # Extract relevant snippet
                snippet = self._extract_snippet(query_terms, content)
                results.append(SearchResult(
                    file_path=file_path,
                    content=snippet,
                    relevance_score=score
                ))
        
        # Sort by relevance score (descending) and limit results
        results.sort(key=lambda r: r.relevance_score, reverse=True)
        return results[:max_results]
    
    def _tokenize_query(self, query: str) -> list[str]:
        """Tokenize a query string into search terms.
        
        Args:
            query: The query string to tokenize.
            
        Returns:
            List of search terms.
        """
        # Split on whitespace and common delimiters
        terms = re.split(r"[\s,;:]+", query)
        # Filter out empty terms and very short terms
        return [t.strip() for t in terms if t.strip() and len(t.strip()) >= 2]
    
    def _calculate_relevance(
        self,
        query: str,
        query_terms: list[str],
        content: str
    ) -> float:
        """Calculate relevance score for content against query.
        
        Uses a simple TF-based scoring with bonuses for exact matches.
        
        Args:
            query: The full query string (lowercase).
            query_terms: Tokenized query terms.
            content: The content to score.
            
        Returns:
            Relevance score (0.0 to 1.0+).
        """
        if not content:
            return 0.0
        
        content_lower = content.lower()
        score = 0.0
        
        # Exact query match bonus
        if query in content_lower:
            score += 0.5
        
        # Term frequency scoring
        for term in query_terms:
            # Count occurrences
            count = content_lower.count(term)
            if count > 0:
                # Logarithmic scaling to prevent very long documents from dominating
                import math
                score += 0.1 * (1 + math.log(count))
        
        # Normalize by number of terms
        if query_terms:
            score /= len(query_terms)
        
        return score
    
    def _extract_snippet(
        self,
        query_terms: list[str],
        content: str,
        snippet_length: int = 500
    ) -> str:
        """Extract a relevant snippet from content.
        
        Args:
            query_terms: Terms to find in content.
            content: The full content.
            snippet_length: Maximum length of snippet.
            
        Returns:
            Relevant snippet from content.
        """
        if not content:
            return ""
        
        if len(content) <= snippet_length:
            return content
        
        content_lower = content.lower()
        
        # Find the first occurrence of any query term
        best_pos = len(content)
        for term in query_terms:
            pos = content_lower.find(term)
            if pos != -1 and pos < best_pos:
                best_pos = pos
        
        if best_pos == len(content):
            # No term found, return start of content
            return content[:snippet_length] + "..."
        
        # Center snippet around the found term
        start = max(0, best_pos - snippet_length // 4)
        end = min(len(content), start + snippet_length)
        
        snippet = content[start:end]
        
        # Add ellipsis if truncated
        if start > 0:
            snippet = "..." + snippet
        if end < len(content):
            snippet = snippet + "..."
        
        return snippet
    
    def get_supported_file_types(self) -> list[str]:
        """Get list of supported file type extensions.
        
        Returns:
            List of supported extensions without dots (e.g., ["pdf", "tex", "sty"]).
        """
        return [ext.lstrip(".") for ext in self.SUPPORTED_EXTENSIONS]
    
    def get_indexed_file_count(self) -> int:
        """Get the number of indexed files.
        
        Returns:
            Number of files in the index.
        """
        return len(self.index)
    
    def get_indexed_files_by_type(self) -> dict[str, int]:
        """Get count of indexed files by type.
        
        Returns:
            Dictionary mapping file extension to count.
        """
        counts: dict[str, int] = {}
        for file_path in self.index:
            ext = Path(file_path).suffix.lower().lstrip(".")
            counts[ext] = counts.get(ext, 0) + 1
        return counts
