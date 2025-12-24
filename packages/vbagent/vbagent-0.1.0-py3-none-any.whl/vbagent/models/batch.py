"""Batch processing database models.

SQLite-based tracking for batch image processing with resume capability.
"""

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional


class ProcessingStatus(str, Enum):
    """Status of an image in the processing pipeline."""
    PENDING = "pending"
    CLASSIFYING = "classifying"
    SCANNING = "scanning"
    TIKZ = "tikz"
    IDEAS = "ideas"
    ALTERNATES = "alternates"
    VARIANTS = "variants"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ImageRecord:
    """Record of an image in the batch processing queue."""
    id: int
    image_path: str
    status: ProcessingStatus
    current_stage: Optional[str]
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]
    
    # Processing results stored as JSON strings
    classification_json: Optional[str] = None
    latex: Optional[str] = None
    tikz_code: Optional[str] = None
    ideas_json: Optional[str] = None


class BatchDatabase:
    """SQLite database for batch processing state."""
    
    DB_NAME = ".vbagent_batch.db"
    
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
        
        # Main images table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_path TEXT UNIQUE NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                current_stage TEXT,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                classification_json TEXT,
                latex TEXT,
                tikz_code TEXT,
                ideas_json TEXT
            )
        """)

        # Variants table (one-to-many with images)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS variants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_id INTEGER NOT NULL,
                variant_type TEXT NOT NULL,
                latex TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (image_id) REFERENCES images(id),
                UNIQUE(image_id, variant_type)
            )
        """)
        
        # Alternates table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alternates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_id INTEGER NOT NULL,
                latex TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (image_id) REFERENCES images(id)
            )
        """)
        
        # Batch config table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS batch_config (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                images_dir TEXT NOT NULL,
                output_dir TEXT NOT NULL,
                variant_types TEXT,
                generate_alternates INTEGER DEFAULT 0,
                use_context INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self.conn.commit()
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def save_config(
        self,
        images_dir: str,
        output_dir: str,
        variant_types: list[str],
        generate_alternates: bool,
        use_context: bool = True,
    ):
        """Save batch configuration."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO batch_config 
            (id, images_dir, output_dir, variant_types, generate_alternates, use_context)
            VALUES (1, ?, ?, ?, ?, ?)
        """, (
            images_dir,
            output_dir,
            ",".join(variant_types),
            1 if generate_alternates else 0,
            1 if use_context else 0,
        ))
        self.conn.commit()
    
    def get_config(self) -> Optional[dict]:
        """Get batch configuration."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM batch_config WHERE id = 1")
        row = cursor.fetchone()
        if row:
            # Handle older databases without use_context column
            use_context = True
            try:
                use_context = bool(row["use_context"])
            except (KeyError, IndexError):
                pass
            
            return {
                "images_dir": row["images_dir"],
                "output_dir": row["output_dir"],
                "variant_types": row["variant_types"].split(",") if row["variant_types"] else [],
                "generate_alternates": bool(row["generate_alternates"]),
                "use_context": use_context,
            }
        return None
    
    def add_image(self, image_path: str) -> int:
        """Add an image to the processing queue.
        
        Returns the image ID.
        """
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO images (image_path, status)
                VALUES (?, ?)
            """, (image_path, ProcessingStatus.PENDING.value))
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            # Image already exists, return existing ID
            cursor.execute(
                "SELECT id FROM images WHERE image_path = ?",
                (image_path,)
            )
            return cursor.fetchone()["id"]
    
    def update_status(
        self,
        image_id: int,
        status: ProcessingStatus,
        stage: Optional[str] = None,
        error: Optional[str] = None,
    ):
        """Update image processing status."""
        cursor = self.conn.cursor()
        
        completed_at = None
        if status == ProcessingStatus.COMPLETED:
            completed_at = datetime.now().isoformat()
        
        cursor.execute("""
            UPDATE images 
            SET status = ?, current_stage = ?, error_message = ?,
                updated_at = CURRENT_TIMESTAMP, completed_at = ?
            WHERE id = ?
        """, (status.value, stage, error, completed_at, image_id))
        self.conn.commit()
    
    def save_classification(self, image_id: int, classification_json: str):
        """Save classification result."""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE images SET classification_json = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (classification_json, image_id))
        self.conn.commit()
    
    def save_latex(self, image_id: int, latex: str):
        """Save scanned LaTeX."""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE images SET latex = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (latex, image_id))
        self.conn.commit()
    
    def save_tikz(self, image_id: int, tikz_code: str):
        """Save TikZ code."""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE images SET tikz_code = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (tikz_code, image_id))
        self.conn.commit()
    
    def save_ideas(self, image_id: int, ideas_json: str):
        """Save ideas JSON."""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE images SET ideas_json = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (ideas_json, image_id))
        self.conn.commit()
    
    def save_variant(self, image_id: int, variant_type: str, latex: str):
        """Save a variant."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO variants (image_id, variant_type, latex)
            VALUES (?, ?, ?)
        """, (image_id, variant_type, latex))
        self.conn.commit()
    
    def save_alternate(self, image_id: int, latex: str):
        """Save an alternate solution."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO alternates (image_id, latex)
            VALUES (?, ?)
        """, (image_id, latex))
        self.conn.commit()
    
    def get_pending_images(self) -> list[ImageRecord]:
        """Get all images that need processing."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM images 
            WHERE status != ? AND status != ?
            ORDER BY id
        """, (ProcessingStatus.COMPLETED.value, ProcessingStatus.FAILED.value))
        
        return [self._row_to_record(row) for row in cursor.fetchall()]
    
    def get_image(self, image_id: int) -> Optional[ImageRecord]:
        """Get an image record by ID."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM images WHERE id = ?", (image_id,))
        row = cursor.fetchone()
        return self._row_to_record(row) if row else None
    
    def get_image_by_path(self, image_path: str) -> Optional[ImageRecord]:
        """Get an image record by path."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM images WHERE image_path = ?", (image_path,))
        row = cursor.fetchone()
        return self._row_to_record(row) if row else None
    
    def get_variants(self, image_id: int) -> dict[str, str]:
        """Get all variants for an image."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT variant_type, latex FROM variants WHERE image_id = ?",
            (image_id,)
        )
        return {row["variant_type"]: row["latex"] for row in cursor.fetchall()}
    
    def get_alternates(self, image_id: int) -> list[str]:
        """Get all alternates for an image."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT latex FROM alternates WHERE image_id = ?",
            (image_id,)
        )
        return [row["latex"] for row in cursor.fetchall()]
    
    def get_stats(self) -> dict:
        """Get processing statistics."""
        cursor = self.conn.cursor()
        
        cursor.execute("SELECT COUNT(*) as total FROM images")
        total = cursor.fetchone()["total"]
        
        cursor.execute(
            "SELECT COUNT(*) as count FROM images WHERE status = ?",
            (ProcessingStatus.COMPLETED.value,)
        )
        completed = cursor.fetchone()["count"]
        
        cursor.execute(
            "SELECT COUNT(*) as count FROM images WHERE status = ?",
            (ProcessingStatus.FAILED.value,)
        )
        failed = cursor.fetchone()["count"]
        
        cursor.execute(
            "SELECT COUNT(*) as count FROM images WHERE status = ?",
            (ProcessingStatus.PENDING.value,)
        )
        pending = cursor.fetchone()["count"]
        
        in_progress = total - completed - failed - pending
        
        return {
            "total": total,
            "completed": completed,
            "failed": failed,
            "pending": pending,
            "in_progress": in_progress,
        }
    
    def reset_failed(self):
        """Reset failed images to pending status."""
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE images 
            SET status = ?, error_message = NULL, updated_at = CURRENT_TIMESTAMP
            WHERE status = ?
        """, (ProcessingStatus.PENDING.value, ProcessingStatus.FAILED.value))
        self.conn.commit()
        return cursor.rowcount
    
    def _row_to_record(self, row: sqlite3.Row) -> ImageRecord:
        """Convert a database row to an ImageRecord."""
        return ImageRecord(
            id=row["id"],
            image_path=row["image_path"],
            status=ProcessingStatus(row["status"]),
            current_stage=row["current_stage"],
            error_message=row["error_message"],
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else datetime.now(),
            updated_at=datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else datetime.now(),
            completed_at=datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None,
            classification_json=row["classification_json"],
            latex=row["latex"],
            tikz_code=row["tikz_code"],
            ideas_json=row["ideas_json"],
        )
