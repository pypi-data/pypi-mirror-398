"""Version Store for QA Review Agent.

SQLite-based storage for suggestions and review history with version tracking.
"""

import json
import sqlite3
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional


class SuggestionStatus(str, Enum):
    """Status of a suggestion in the review workflow."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


@dataclass
class StoredSuggestion:
    """A suggestion stored in the version store.
    
    Contains all data needed to retrieve and apply a stored suggestion.
    """
    id: int
    version: int
    problem_id: str
    file_path: str
    issue_type: str
    description: str
    reasoning: str
    confidence: float
    original_content: str
    suggested_content: str
    diff: str
    status: SuggestionStatus
    created_at: datetime
    session_id: Optional[str]
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "version": self.version,
            "problem_id": self.problem_id,
            "file_path": self.file_path,
            "issue_type": self.issue_type,
            "description": self.description,
            "reasoning": self.reasoning,
            "confidence": self.confidence,
            "original_content": self.original_content,
            "suggested_content": self.suggested_content,
            "diff": self.diff,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "session_id": self.session_id,
        }

    
    @classmethod
    def from_dict(cls, data: dict) -> "StoredSuggestion":
        """Create from dictionary (JSON deserialization)."""
        return cls(
            id=data["id"],
            version=data["version"],
            problem_id=data["problem_id"],
            file_path=data["file_path"],
            issue_type=data["issue_type"],
            description=data["description"],
            reasoning=data["reasoning"],
            confidence=data["confidence"],
            original_content=data["original_content"],
            suggested_content=data["suggested_content"],
            diff=data["diff"],
            status=SuggestionStatus(data["status"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            session_id=data.get("session_id"),
        )


class ProblemCheckStatus(str, Enum):
    """Status of a problem in the check workflow."""
    PENDING = "pending"
    CHECKED = "checked"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


class VersionStore:
    """SQLite-based storage for suggestions and review history.
    
    Provides version tracking for rejected suggestions and
    statistics tracking for review sessions.
    """
    
    DB_NAME = ".vbagent_versions.db"
    
    def __init__(self, base_dir: str = "."):
        """Initialize database connection.
        
        Args:
            base_dir: Directory to store the database file
        """
        self.db_path = Path(base_dir) / self.DB_NAME
        self.conn: Optional[sqlite3.Connection] = None
        self._connect()
        self._create_tables()
    
    def _connect(self):
        """Establish database connection."""
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
    
    def _create_tables(self):
        """Create database tables if they don't exist."""
        cursor = self.conn.cursor()
        
        # Suggestions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS suggestions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version INTEGER NOT NULL,
                problem_id TEXT NOT NULL,
                file_path TEXT NOT NULL,
                issue_type TEXT NOT NULL,
                description TEXT NOT NULL,
                reasoning TEXT NOT NULL,
                confidence REAL NOT NULL,
                original_content TEXT NOT NULL,
                suggested_content TEXT NOT NULL,
                diff TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                session_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(problem_id, file_path, version)
            )
        """)
        
        # Review sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS review_sessions (
                id TEXT PRIMARY KEY,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                problems_reviewed INTEGER DEFAULT 0,
                suggestions_made INTEGER DEFAULT 0,
                approved_count INTEGER DEFAULT 0,
                rejected_count INTEGER DEFAULT 0,
                skipped_count INTEGER DEFAULT 0
            )
        """)
        
        # Problem check tracking table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS problem_checks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                problem_id TEXT NOT NULL,
                output_dir TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                suggestion_count INTEGER DEFAULT 0,
                checked_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(problem_id, output_dir)
            )
        """)
        
        # Checker progress tracking table - tracks which files have been checked by which checker
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS checker_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT NOT NULL,
                checker_type TEXT NOT NULL,
                output_dir TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'checked',
                passed INTEGER DEFAULT 0,
                checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(file_path, checker_type, output_dir)
            )
        """)
        
        # Indexes for efficient queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_suggestions_problem 
            ON suggestions(problem_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_suggestions_status 
            ON suggestions(status)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_suggestions_created 
            ON suggestions(created_at)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_problem_checks_status 
            ON problem_checks(status)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_problem_checks_dir 
            ON problem_checks(output_dir)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_checker_progress_type 
            ON checker_progress(checker_type, output_dir)
        """)
        
        self.conn.commit()
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    
    def _get_next_version(self, problem_id: str, file_path: str) -> int:
        """Get the next version number for a problem-file combination."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT MAX(version) as max_version 
            FROM suggestions 
            WHERE problem_id = ? AND file_path = ?
        """, (problem_id, file_path))
        row = cursor.fetchone()
        max_version = row["max_version"] if row["max_version"] is not None else 0
        return max_version + 1
    
    def save_suggestion(
        self,
        suggestion,  # Suggestion from review.py
        problem_id: str,
        status: SuggestionStatus,
        session_id: Optional[str] = None
    ) -> int:
        """Save a suggestion and return its ID.
        
        Args:
            suggestion: Suggestion object from review.py
            problem_id: ID of the problem being reviewed
            status: Status to set for the suggestion
            session_id: Optional session ID for tracking
            
        Returns:
            The ID of the saved suggestion
        """
        version = self._get_next_version(problem_id, suggestion.file_path)
        
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO suggestions (
                version, problem_id, file_path, issue_type, description,
                reasoning, confidence, original_content, suggested_content,
                diff, status, session_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            version,
            problem_id,
            suggestion.file_path,
            suggestion.issue_type.value if hasattr(suggestion.issue_type, 'value') else suggestion.issue_type,
            suggestion.description,
            suggestion.reasoning,
            suggestion.confidence,
            suggestion.original_content,
            suggestion.suggested_content,
            suggestion.diff,
            status.value,
            session_id,
        ))
        self.conn.commit()
        return cursor.lastrowid
    
    def get_versions(
        self,
        problem_id: Optional[str] = None,
        file_path: Optional[str] = None
    ) -> list[StoredSuggestion]:
        """Get version history for a problem or file.
        
        Args:
            problem_id: Filter by problem ID (optional)
            file_path: Filter by file path (optional)
            
        Returns:
            List of stored suggestions matching the criteria
        """
        cursor = self.conn.cursor()
        
        conditions = []
        params = []
        
        if problem_id is not None:
            conditions.append("problem_id = ?")
            params.append(problem_id)
        
        if file_path is not None:
            conditions.append("file_path = ?")
            params.append(file_path)
        
        query = "SELECT * FROM suggestions"
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY created_at DESC"
        
        cursor.execute(query, params)
        return [self._row_to_suggestion(row) for row in cursor.fetchall()]
    
    def get_suggestion(self, suggestion_id: int) -> Optional[StoredSuggestion]:
        """Get a specific suggestion by ID.
        
        Args:
            suggestion_id: The ID of the suggestion to retrieve
            
        Returns:
            The stored suggestion, or None if not found
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM suggestions WHERE id = ?", (suggestion_id,))
        row = cursor.fetchone()
        return self._row_to_suggestion(row) if row else None
    
    def update_status(
        self,
        suggestion_id: int,
        status: SuggestionStatus
    ) -> None:
        """Update the status of a suggestion.
        
        Args:
            suggestion_id: The ID of the suggestion to update
            status: The new status
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE suggestions SET status = ? WHERE id = ?
        """, (status.value, suggestion_id))
        self.conn.commit()

    
    # Session tracking methods
    
    def create_session(self) -> str:
        """Create a new review session.
        
        Returns:
            The session ID
        """
        session_id = str(uuid.uuid4())
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO review_sessions (id) VALUES (?)
        """, (session_id,))
        self.conn.commit()
        return session_id
    
    def update_session(
        self,
        session_id: str,
        problems_reviewed: Optional[int] = None,
        suggestions_made: Optional[int] = None,
        approved_count: Optional[int] = None,
        rejected_count: Optional[int] = None,
        skipped_count: Optional[int] = None,
        completed: bool = False
    ) -> None:
        """Update session statistics.
        
        Args:
            session_id: The session ID to update
            problems_reviewed: Number of problems reviewed
            suggestions_made: Number of suggestions made
            approved_count: Number of approved suggestions
            rejected_count: Number of rejected suggestions
            skipped_count: Number of skipped suggestions
            completed: Whether to mark the session as completed
        """
        cursor = self.conn.cursor()
        
        updates = []
        params = []
        
        if problems_reviewed is not None:
            updates.append("problems_reviewed = ?")
            params.append(problems_reviewed)
        
        if suggestions_made is not None:
            updates.append("suggestions_made = ?")
            params.append(suggestions_made)
        
        if approved_count is not None:
            updates.append("approved_count = ?")
            params.append(approved_count)
        
        if rejected_count is not None:
            updates.append("rejected_count = ?")
            params.append(rejected_count)
        
        if skipped_count is not None:
            updates.append("skipped_count = ?")
            params.append(skipped_count)
        
        if completed:
            updates.append("completed_at = CURRENT_TIMESTAMP")
        
        if updates:
            query = f"UPDATE review_sessions SET {', '.join(updates)} WHERE id = ?"
            params.append(session_id)
            cursor.execute(query, params)
            self.conn.commit()
    
    def get_session(self, session_id: str) -> Optional[dict]:
        """Get session details.
        
        Args:
            session_id: The session ID to retrieve
            
        Returns:
            Session data as a dictionary, or None if not found
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM review_sessions WHERE id = ?", (session_id,))
        row = cursor.fetchone()
        if row:
            return {
                "id": row["id"],
                "started_at": row["started_at"],
                "completed_at": row["completed_at"],
                "problems_reviewed": row["problems_reviewed"],
                "suggestions_made": row["suggestions_made"],
                "approved_count": row["approved_count"],
                "rejected_count": row["rejected_count"],
                "skipped_count": row["skipped_count"],
                "output_dir": row["output_dir"] if "output_dir" in row.keys() else None,
                "remaining_problems": json.loads(row["remaining_problems"]) if "remaining_problems" in row.keys() and row["remaining_problems"] else None,
            }
        return None
    
    def get_incomplete_sessions(self) -> list[dict]:
        """Get all incomplete (interrupted) sessions.
        
        Returns:
            List of session data dictionaries for sessions without completed_at
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM review_sessions 
            WHERE completed_at IS NULL 
            ORDER BY started_at DESC
        """)
        sessions = []
        for row in cursor.fetchall():
            sessions.append({
                "id": row["id"],
                "started_at": row["started_at"],
                "completed_at": row["completed_at"],
                "problems_reviewed": row["problems_reviewed"],
                "suggestions_made": row["suggestions_made"],
                "approved_count": row["approved_count"],
                "rejected_count": row["rejected_count"],
                "skipped_count": row["skipped_count"],
                "output_dir": row["output_dir"] if "output_dir" in row.keys() else None,
                "remaining_problems": json.loads(row["remaining_problems"]) if "remaining_problems" in row.keys() and row["remaining_problems"] else None,
            })
        return sessions
    
    def save_session_state(
        self,
        session_id: str,
        output_dir: str,
        remaining_problems: list[str],
    ) -> None:
        """Save session state for potential resume.
        
        Args:
            session_id: The session ID to update
            output_dir: The output directory being reviewed
            remaining_problems: List of problem IDs not yet reviewed
        """
        cursor = self.conn.cursor()
        
        # Check if columns exist, add them if not
        cursor.execute("PRAGMA table_info(review_sessions)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if "output_dir" not in columns:
            cursor.execute("ALTER TABLE review_sessions ADD COLUMN output_dir TEXT")
        if "remaining_problems" not in columns:
            cursor.execute("ALTER TABLE review_sessions ADD COLUMN remaining_problems TEXT")
        
        cursor.execute("""
            UPDATE review_sessions 
            SET output_dir = ?, remaining_problems = ?
            WHERE id = ?
        """, (output_dir, json.dumps(remaining_problems), session_id))
        self.conn.commit()
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session and its associated suggestions.
        
        Args:
            session_id: The session ID to delete
            
        Returns:
            True if session was deleted, False if not found
        """
        cursor = self.conn.cursor()
        
        # Check if session exists
        cursor.execute("SELECT id FROM review_sessions WHERE id = ?", (session_id,))
        if not cursor.fetchone():
            return False
        
        # Delete associated suggestions
        cursor.execute("DELETE FROM suggestions WHERE session_id = ?", (session_id,))
        
        # Delete session
        cursor.execute("DELETE FROM review_sessions WHERE id = ?", (session_id,))
        self.conn.commit()
        return True

    
    def get_stats(self, days: Optional[int] = None) -> dict:
        """Get review statistics.
        
        Args:
            days: Filter to last N days (optional)
            
        Returns:
            Dictionary with review statistics
        """
        cursor = self.conn.cursor()
        
        # Build date filter
        date_filter = ""
        params = []
        if days is not None:
            date_filter = "WHERE created_at >= datetime('now', ?)"
            params.append(f"-{days} days")
        
        # Total suggestions
        cursor.execute(f"""
            SELECT COUNT(*) as count FROM suggestions {date_filter}
        """, params)
        total_suggestions = cursor.fetchone()["count"]
        
        # Count by status
        cursor.execute(f"""
            SELECT status, COUNT(*) as count 
            FROM suggestions 
            {date_filter}
            GROUP BY status
        """, params)
        status_counts = {row["status"]: row["count"] for row in cursor.fetchall()}
        
        approved_count = status_counts.get(SuggestionStatus.APPROVED.value, 0)
        rejected_count = status_counts.get(SuggestionStatus.REJECTED.value, 0)
        pending_count = status_counts.get(SuggestionStatus.PENDING.value, 0)
        
        # Issues by type
        cursor.execute(f"""
            SELECT issue_type, COUNT(*) as count 
            FROM suggestions 
            {date_filter}
            GROUP BY issue_type
        """, params)
        issues_by_type = {row["issue_type"]: row["count"] for row in cursor.fetchall()}
        
        # Session stats
        session_filter = ""
        session_params = []
        if days is not None:
            session_filter = "WHERE started_at >= datetime('now', ?)"
            session_params.append(f"-{days} days")
        
        cursor.execute(f"""
            SELECT 
                COALESCE(SUM(problems_reviewed), 0) as total_reviewed,
                COALESCE(SUM(skipped_count), 0) as skipped_count
            FROM review_sessions
            {session_filter}
        """, session_params)
        session_row = cursor.fetchone()
        total_reviewed = session_row["total_reviewed"]
        skipped_count = session_row["skipped_count"]
        
        # Calculate approval rate
        decided = approved_count + rejected_count
        approval_rate = approved_count / decided if decided > 0 else 0.0
        
        return {
            "total_reviewed": total_reviewed,
            "total_suggestions": total_suggestions,
            "approved_count": approved_count,
            "rejected_count": rejected_count,
            "skipped_count": skipped_count,
            "pending_count": pending_count,
            "approval_rate": approval_rate,
            "issues_by_type": issues_by_type,
        }
    
    def _row_to_suggestion(self, row: sqlite3.Row) -> StoredSuggestion:
        """Convert a database row to a StoredSuggestion."""
        created_at = row["created_at"]
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        
        return StoredSuggestion(
            id=row["id"],
            version=row["version"],
            problem_id=row["problem_id"],
            file_path=row["file_path"],
            issue_type=row["issue_type"],
            description=row["description"],
            reasoning=row["reasoning"],
            confidence=row["confidence"],
            original_content=row["original_content"],
            suggested_content=row["suggested_content"],
            diff=row["diff"],
            status=SuggestionStatus(row["status"]),
            created_at=created_at,
            session_id=row["session_id"],
        )

    # Problem check tracking methods
    
    def init_problem_checks(
        self,
        problem_ids: list[str],
        output_dir: str,
        reset: bool = False,
    ) -> int:
        """Initialize problem check tracking for a list of problems.
        
        Args:
            problem_ids: List of problem IDs to track
            output_dir: Output directory containing the problems
            reset: If True, reset existing entries to pending
            
        Returns:
            Number of problems initialized
        """
        cursor = self.conn.cursor()
        count = 0
        
        for pid in problem_ids:
            if reset:
                # Delete existing entry if reset requested
                cursor.execute("""
                    DELETE FROM problem_checks 
                    WHERE problem_id = ? AND output_dir = ?
                """, (pid, output_dir))
            
            try:
                cursor.execute("""
                    INSERT INTO problem_checks (problem_id, output_dir, status)
                    VALUES (?, ?, ?)
                """, (pid, output_dir, ProblemCheckStatus.PENDING.value))
                count += 1
            except sqlite3.IntegrityError:
                # Already exists, skip unless reset
                pass
        
        self.conn.commit()
        return count
    
    def update_problem_check(
        self,
        problem_id: str,
        output_dir: str,
        status: ProblemCheckStatus,
        suggestion_count: int = 0,
    ) -> None:
        """Update the check status of a problem.
        
        Args:
            problem_id: The problem ID
            output_dir: Output directory
            status: New status
            suggestion_count: Number of suggestions found
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE problem_checks 
            SET status = ?, suggestion_count = ?, checked_at = CURRENT_TIMESTAMP
            WHERE problem_id = ? AND output_dir = ?
        """, (status.value, suggestion_count, problem_id, output_dir))
        self.conn.commit()
    
    def get_pending_problems(
        self,
        output_dir: str,
        limit: Optional[int] = None,
    ) -> list[str]:
        """Get list of pending problem IDs.
        
        Args:
            output_dir: Output directory to filter by
            limit: Maximum number to return
            
        Returns:
            List of problem IDs with pending status
        """
        cursor = self.conn.cursor()
        query = """
            SELECT problem_id FROM problem_checks 
            WHERE output_dir = ? AND status = ?
            ORDER BY id
        """
        params = [output_dir, ProblemCheckStatus.PENDING.value]
        
        if limit:
            query += " LIMIT ?"
            params.append(limit)
        
        cursor.execute(query, params)
        return [row["problem_id"] for row in cursor.fetchall()]
    
    def get_problem_check_stats(self, output_dir: str) -> dict:
        """Get statistics for problem checks in a directory.
        
        Args:
            output_dir: Output directory to get stats for
            
        Returns:
            Dictionary with counts by status
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT status, COUNT(*) as count 
            FROM problem_checks 
            WHERE output_dir = ?
            GROUP BY status
        """, (output_dir,))
        
        stats = {s.value: 0 for s in ProblemCheckStatus}
        for row in cursor.fetchall():
            stats[row["status"]] = row["count"]
        
        stats["total"] = sum(stats.values())
        return stats
    
    def get_problems_by_status(
        self,
        output_dir: str,
        status: ProblemCheckStatus,
    ) -> list[str]:
        """Get problem IDs with a specific status.
        
        Args:
            output_dir: Output directory to filter by
            status: Status to filter by
            
        Returns:
            List of problem IDs
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT problem_id FROM problem_checks 
            WHERE output_dir = ? AND status = ?
            ORDER BY id
        """, (output_dir, status.value))
        return [row["problem_id"] for row in cursor.fetchall()]
    
    def reset_problem_checks(
        self,
        output_dir: str,
        problem_ids: Optional[list[str]] = None,
    ) -> int:
        """Reset problem checks to pending status.
        
        Args:
            output_dir: Output directory
            problem_ids: Specific problems to reset (None = all)
            
        Returns:
            Number of problems reset
        """
        cursor = self.conn.cursor()
        
        if problem_ids:
            placeholders = ",".join("?" * len(problem_ids))
            cursor.execute(f"""
                UPDATE problem_checks 
                SET status = ?, checked_at = NULL, suggestion_count = 0
                WHERE output_dir = ? AND problem_id IN ({placeholders})
            """, [ProblemCheckStatus.PENDING.value, output_dir] + problem_ids)
        else:
            cursor.execute("""
                UPDATE problem_checks 
                SET status = ?, checked_at = NULL, suggestion_count = 0
                WHERE output_dir = ?
            """, (ProblemCheckStatus.PENDING.value, output_dir))
        
        self.conn.commit()
        return cursor.rowcount
    
    def clear_problem_checks(self, output_dir: str) -> int:
        """Clear all problem check entries for a directory.
        
        Args:
            output_dir: Output directory
            
        Returns:
            Number of entries deleted
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            DELETE FROM problem_checks WHERE output_dir = ?
        """, (output_dir,))
        self.conn.commit()
        return cursor.rowcount

    # Checker progress tracking methods
    
    def mark_file_checked(
        self,
        file_path: str,
        checker_type: str,
        output_dir: str,
        passed: bool = False,
    ) -> None:
        """Mark a file as checked by a specific checker.
        
        Args:
            file_path: Path to the file that was checked
            checker_type: Type of checker (solution/grammar/clarity/tikz/alternate/idea)
            output_dir: Output directory context
            passed: Whether the file passed the check without issues
        """
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO checker_progress (file_path, checker_type, output_dir, passed)
                VALUES (?, ?, ?, ?)
            """, (file_path, checker_type, output_dir, 1 if passed else 0))
        except sqlite3.IntegrityError:
            # Already exists, update it
            cursor.execute("""
                UPDATE checker_progress 
                SET passed = ?, checked_at = CURRENT_TIMESTAMP
                WHERE file_path = ? AND checker_type = ? AND output_dir = ?
            """, (1 if passed else 0, file_path, checker_type, output_dir))
        self.conn.commit()
    
    def is_file_checked(
        self,
        file_path: str,
        checker_type: str,
        output_dir: str,
    ) -> bool:
        """Check if a file has already been checked by a specific checker.
        
        Args:
            file_path: Path to the file
            checker_type: Type of checker
            output_dir: Output directory context
            
        Returns:
            True if the file has been checked, False otherwise
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id FROM checker_progress 
            WHERE file_path = ? AND checker_type = ? AND output_dir = ?
        """, (file_path, checker_type, output_dir))
        return cursor.fetchone() is not None
    
    def get_checked_files(
        self,
        checker_type: str,
        output_dir: str,
    ) -> set[str]:
        """Get all files that have been checked by a specific checker.
        
        Args:
            checker_type: Type of checker
            output_dir: Output directory context
            
        Returns:
            Set of file paths that have been checked
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT file_path FROM checker_progress 
            WHERE checker_type = ? AND output_dir = ?
        """, (checker_type, output_dir))
        return {row["file_path"] for row in cursor.fetchall()}
    
    def get_checker_stats(
        self,
        checker_type: str,
        output_dir: str,
    ) -> dict:
        """Get statistics for a specific checker in a directory.
        
        Args:
            checker_type: Type of checker
            output_dir: Output directory context
            
        Returns:
            Dictionary with total checked, passed, and failed counts
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(passed) as passed
            FROM checker_progress 
            WHERE checker_type = ? AND output_dir = ?
        """, (checker_type, output_dir))
        row = cursor.fetchone()
        total = row["total"] or 0
        passed = row["passed"] or 0
        return {
            "total": total,
            "passed": passed,
            "failed": total - passed,
        }
    
    def reset_checker_progress(
        self,
        checker_type: str,
        output_dir: str,
        file_paths: Optional[list[str]] = None,
    ) -> int:
        """Reset checker progress for specific files or all files.
        
        Args:
            checker_type: Type of checker
            output_dir: Output directory context
            file_paths: Specific files to reset (None = all)
            
        Returns:
            Number of entries deleted
        """
        cursor = self.conn.cursor()
        
        if file_paths:
            placeholders = ",".join("?" * len(file_paths))
            cursor.execute(f"""
                DELETE FROM checker_progress 
                WHERE checker_type = ? AND output_dir = ? AND file_path IN ({placeholders})
            """, [checker_type, output_dir] + file_paths)
        else:
            cursor.execute("""
                DELETE FROM checker_progress 
                WHERE checker_type = ? AND output_dir = ?
            """, (checker_type, output_dir))
        
        self.conn.commit()
        return cursor.rowcount
