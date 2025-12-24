"""Diff utilities for QA Review Agent.

Functions for generating, parsing, and applying unified diffs.
Uses Python's difflib for diff generation.
"""

import difflib
import hashlib
import os
import shutil
import tempfile
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional


class DiffError(Exception):
    """Base exception for diff-related errors."""
    pass


class DiffErrorType(str, Enum):
    """Types of errors that can occur during diff operations."""
    FILE_NOT_FOUND = "file_not_found"
    PERMISSION_DENIED = "permission_denied"
    DIFF_CONFLICT = "diff_conflict"
    IO_ERROR = "io_error"
    INVALID_DIFF = "invalid_diff"


@dataclass
class DiffResult:
    """Result of a diff application operation.
    
    Attributes:
        success: Whether the operation succeeded
        error_type: Type of error if failed, None if successful
        error_message: Human-readable error message if failed
        original_preserved: Whether the original file was preserved on failure
    """
    success: bool
    error_type: Optional[DiffErrorType] = None
    error_message: Optional[str] = None
    original_preserved: bool = True


def generate_unified_diff(
    original: str,
    modified: str,
    file_path: str,
    context_lines: int = 3
) -> str:
    """Generate unified diff between original and modified content.
    
    Args:
        original: Original content
        modified: Modified content
        file_path: Path to the file (used in diff header)
        context_lines: Number of context lines around changes
        
    Returns:
        Unified diff string
    """
    original_lines = original.splitlines(keepends=True)
    modified_lines = modified.splitlines(keepends=True)
    
    # Ensure lines end with newline for proper diff format
    if original_lines and not original_lines[-1].endswith('\n'):
        original_lines[-1] += '\n'
    if modified_lines and not modified_lines[-1].endswith('\n'):
        modified_lines[-1] += '\n'
    
    diff_lines = difflib.unified_diff(
        original_lines,
        modified_lines,
        fromfile=f"a/{file_path}",
        tofile=f"b/{file_path}",
        n=context_lines
    )
    
    return ''.join(diff_lines)


def parse_diff(diff: str) -> tuple[str, str] | None:
    """Parse a unified diff to extract original and modified content.
    
    Args:
        diff: Unified diff string
        
    Returns:
        Tuple of (original_content, modified_content), or None if diff is empty
    """
    # Empty diff means no changes
    if not diff or not diff.strip():
        return None
    
    original_lines: list[str] = []
    modified_lines: list[str] = []
    
    lines = diff.splitlines(keepends=True)
    
    for line in lines:
        # Skip diff headers (must have space after --- or +++ to be a header)
        # e.g., "--- a/file.txt" or "+++ b/file.txt"
        # But NOT "---\n" which is a removed line containing "--"
        if (line.startswith('--- ') or line.startswith('+++ ')):
            continue
        # Skip hunk headers
        if line.startswith('@@'):
            continue
        # Context line (unchanged)
        if line.startswith(' '):
            content = line[1:]  # Remove the leading space
            original_lines.append(content)
            modified_lines.append(content)
        # Removed line (only in original)
        elif line.startswith('-'):
            content = line[1:]  # Remove the leading minus
            original_lines.append(content)
        # Added line (only in modified)
        elif line.startswith('+'):
            content = line[1:]  # Remove the leading plus
            modified_lines.append(content)
    
    original = ''.join(original_lines)
    modified = ''.join(modified_lines)
    
    # Strip trailing newline if present (to match original input)
    if original.endswith('\n'):
        original = original[:-1]
    if modified.endswith('\n'):
        modified = modified[:-1]
    
    return original, modified


def apply_diff(file_path: str, diff: str) -> bool:
    """Apply a unified diff to a file.
    
    Args:
        file_path: Path to the file to modify
        diff: Unified diff string to apply
        
    Returns:
        True if successful, False otherwise
        
    Note:
        For detailed error information, use apply_diff_safe() instead.
    """
    result = apply_diff_safe(file_path, diff)
    return result.success


def apply_diff_safe(file_path: str, diff: str) -> DiffResult:
    """Apply a unified diff to a file with detailed error handling.
    
    This function provides comprehensive error handling and ensures
    the original file is preserved on failure.
    
    Args:
        file_path: Path to the file to modify
        diff: Unified diff string to apply
        
    Returns:
        DiffResult with success status and error details if failed
    """
    path = Path(file_path)
    
    # Check if file exists
    if not path.exists():
        return DiffResult(
            success=False,
            error_type=DiffErrorType.FILE_NOT_FOUND,
            error_message=f"File not found: {file_path}",
            original_preserved=True,
        )
    
    # Empty diff means no changes needed
    if not diff or not diff.strip():
        return DiffResult(success=True)
    
    # Try to read the original content
    try:
        original_content = path.read_text()
    except PermissionError:
        return DiffResult(
            success=False,
            error_type=DiffErrorType.PERMISSION_DENIED,
            error_message=f"Permission denied reading file: {file_path}",
            original_preserved=True,
        )
    except (IOError, OSError) as e:
        return DiffResult(
            success=False,
            error_type=DiffErrorType.IO_ERROR,
            error_message=f"Error reading file: {e}",
            original_preserved=True,
        )
    
    # Parse the diff to get the lines to find and replace
    parsed = parse_diff(diff)
    if parsed is None:
        return DiffResult(success=True)  # Empty diff, no changes
    
    expected_original, replacement = parsed
    
    # The diff contains partial content (the lines being changed).
    # We need to find this content in the file and replace it.
    # Normalize for comparison but preserve original for replacement
    expected_normalized = expected_original.strip()
    
    # Try to find the expected content in the file
    # First try exact match
    if expected_normalized in original_content:
        modified_content = original_content.replace(expected_normalized, replacement.strip(), 1)
    elif expected_normalized in original_content.strip():
        modified_content = original_content.replace(expected_normalized, replacement.strip(), 1)
    else:
        # Try line-by-line matching for more flexibility
        original_lines = original_content.splitlines()
        expected_lines = expected_normalized.splitlines()
        replacement_lines = replacement.strip().splitlines()
        
        # Find where the expected lines appear in the file
        match_start = -1
        for i in range(len(original_lines) - len(expected_lines) + 1):
            match = True
            for j, exp_line in enumerate(expected_lines):
                if original_lines[i + j].strip() != exp_line.strip():
                    match = False
                    break
            if match:
                match_start = i
                break
        
        if match_start == -1:
            return DiffResult(
                success=False,
                error_type=DiffErrorType.DIFF_CONFLICT,
                error_message=(
                    f"File has been modified since diff was generated. "
                    f"Expected content does not match current file content."
                ),
                original_preserved=True,
            )
        
        # Replace the matched lines
        new_lines = (
            original_lines[:match_start] +
            replacement_lines +
            original_lines[match_start + len(expected_lines):]
        )
        modified_content = '\n'.join(new_lines)
        
        # Preserve trailing newline if original had one
        if original_content.endswith('\n'):
            modified_content += '\n'
    
    # Create a backup before modifying
    backup_path = None
    try:
        # Create a temporary backup file
        fd, backup_path = tempfile.mkstemp(
            suffix=".bak",
            prefix=f".{path.name}_",
            dir=path.parent
        )
        os.close(fd)
        shutil.copy2(file_path, backup_path)
    except (IOError, OSError, PermissionError) as e:
        # Clean up backup if it was created
        if backup_path and os.path.exists(backup_path):
            try:
                os.remove(backup_path)
            except OSError:
                pass
        return DiffResult(
            success=False,
            error_type=DiffErrorType.IO_ERROR,
            error_message=f"Failed to create backup: {e}",
            original_preserved=True,
        )
    
    # Try to write the modified content
    try:
        path.write_text(modified_content)
        # Success - remove the backup
        if backup_path and os.path.exists(backup_path):
            os.remove(backup_path)
        return DiffResult(success=True)
    except PermissionError:
        # Restore from backup
        _restore_from_backup(file_path, backup_path)
        return DiffResult(
            success=False,
            error_type=DiffErrorType.PERMISSION_DENIED,
            error_message=f"Permission denied writing to file: {file_path}",
            original_preserved=True,
        )
    except (IOError, OSError) as e:
        # Restore from backup
        _restore_from_backup(file_path, backup_path)
        return DiffResult(
            success=False,
            error_type=DiffErrorType.IO_ERROR,
            error_message=f"Error writing file: {e}",
            original_preserved=True,
        )


def _restore_from_backup(file_path: str, backup_path: str) -> bool:
    """Restore a file from its backup.
    
    Args:
        file_path: Path to the file to restore
        backup_path: Path to the backup file
        
    Returns:
        True if restoration succeeded, False otherwise
    """
    try:
        if backup_path and os.path.exists(backup_path):
            shutil.copy2(backup_path, file_path)
            os.remove(backup_path)
            return True
    except (IOError, OSError):
        pass
    return False


def check_file_modified(file_path: str, expected_hash: str) -> bool:
    """Check if a file has been modified since a hash was computed.
    
    Args:
        file_path: Path to the file to check
        expected_hash: Expected MD5 hash of the file content
        
    Returns:
        True if file has been modified (hash doesn't match), False otherwise
    """
    try:
        content = Path(file_path).read_text()
        current_hash = hashlib.md5(content.encode()).hexdigest()
        return current_hash != expected_hash
    except (IOError, OSError):
        return True  # Assume modified if we can't read


def compute_file_hash(file_path: str) -> Optional[str]:
    """Compute MD5 hash of a file's content.
    
    Args:
        file_path: Path to the file
        
    Returns:
        MD5 hash string, or None if file cannot be read
    """
    try:
        content = Path(file_path).read_text()
        return hashlib.md5(content.encode()).hexdigest()
    except (IOError, OSError):
        return None


def apply_diff_to_content(original: str, diff: str) -> str | None:
    """Apply a unified diff to content string.
    
    This is useful for testing without file I/O.
    
    Args:
        original: Original content string
        diff: Unified diff string to apply
        
    Returns:
        Modified content if successful, None if diff doesn't apply
    """
    # Empty diff means no changes - return original
    if not diff or not diff.strip():
        return original
    
    # Parse the diff to get expected original and modified content
    parsed = parse_diff(diff)
    if parsed is None:
        return original  # Empty diff, return original
    
    expected_original, modified = parsed
    
    # Verify the original content matches what the diff expects
    if original.rstrip() != expected_original.rstrip():
        return None
    
    return modified


def generate_diff(
    original: str,
    modified: str,
    filename: str = "file.tex",
) -> str:
    """Generate a unified diff between original and modified content.
    
    Convenience wrapper around generate_unified_diff with sensible defaults.
    
    Args:
        original: Original file content
        modified: Modified file content
        filename: Filename for diff header (default: file.tex)
        
    Returns:
        Unified diff string, or empty string if no changes
    """
    if original == modified:
        return ""
    
    return generate_unified_diff(original, modified, filename)
