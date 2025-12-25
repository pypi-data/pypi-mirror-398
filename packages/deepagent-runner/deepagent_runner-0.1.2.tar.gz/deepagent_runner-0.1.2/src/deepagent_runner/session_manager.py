"""Session management for persistent agent sessions."""

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

from deepagent_runner.config import get_default_model


@dataclass
class SessionInfo:
    """Session metadata."""
    session_id: str
    workspace: str
    model: str
    created_at: datetime
    last_used: datetime
    message_count: int
    name: Optional[str] = None
    description: Optional[str] = None


class SessionManager:
    """Manages persistent agent sessions."""
    
    def __init__(self, sessions_dir: Optional[Path] = None):
        """
        Initialize session manager.
        
        Args:
            sessions_dir: Directory to store sessions (default: ~/.deepagent/sessions)
        """
        if sessions_dir is None:
            home = Path.home()
            sessions_dir = home / ".deepagent" / "sessions"
        
        self.sessions_dir = sessions_dir
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        
        self.db_path = self.sessions_dir / "sessions.db"
        self._init_database()
    
    def _init_database(self) -> None:
        """Initialize SQLite database for session metadata."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                workspace TEXT NOT NULL,
                model TEXT NOT NULL,
                created_at TEXT NOT NULL,
                last_used TEXT NOT NULL,
                message_count INTEGER DEFAULT 0,
                name TEXT,
                description TEXT
            )
        """)
        
        conn.commit()
        conn.close()
    
    def create_session(
        self,
        session_id: str,
        workspace: Path,
        model: Optional[str] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> SessionInfo:
        """
        Create a new session.
        
        Args:
            session_id: Unique session identifier
            workspace: Workspace directory path
            model: Model identifier (default: from config)
            name: Optional session name
            description: Optional session description
            
        Returns:
            SessionInfo object
        """
        if model is None:
            model = get_default_model()
        
        now = datetime.now().isoformat()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO sessions (
                session_id, workspace, model, created_at, last_used,
                message_count, name, description
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session_id,
            str(workspace.resolve()),
            model,
            now,
            now,
            0,
            name,
            description,
        ))
        
        conn.commit()
        conn.close()
        
        return self.get_session(session_id)
    
    def get_session(self, session_id: str) -> Optional[SessionInfo]:
        """
        Get session by ID.
        
        Args:
            session_id: Session identifier
            
        Returns:
            SessionInfo or None if not found
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM sessions WHERE session_id = ?
        """, (session_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row is None:
            return None
        
        return self._row_to_session_info(row)
    
    def update_session(
        self,
        session_id: str,
        message_count: Optional[int] = None,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Optional[SessionInfo]:
        """
        Update session metadata.
        
        Args:
            session_id: Session identifier
            message_count: Update message count
            name: Update session name
            description: Update description
            
        Returns:
            Updated SessionInfo or None if not found
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        if message_count is not None:
            updates.append("message_count = ?")
            params.append(message_count)
        
        if name is not None:
            updates.append("name = ?")
            params.append(name)
        
        if description is not None:
            updates.append("description = ?")
            params.append(description)
        
        # Always update last_used
        updates.append("last_used = ?")
        params.append(datetime.now().isoformat())
        
        params.append(session_id)
        
        cursor.execute(f"""
            UPDATE sessions
            SET {', '.join(updates)}
            WHERE session_id = ?
        """, params)
        
        conn.commit()
        conn.close()
        
        return self.get_session(session_id)
    
    def list_sessions(
        self,
        workspace: Optional[Path] = None,
    ) -> list[SessionInfo]:
        """
        List all sessions, optionally filtered by workspace.
        
        Args:
            workspace: Filter by workspace path
            
        Returns:
            List of SessionInfo objects, sorted by last_used (newest first)
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if workspace:
            workspace_str = str(workspace.resolve())
            cursor.execute("""
                SELECT * FROM sessions
                WHERE workspace = ?
                ORDER BY last_used DESC
            """, (workspace_str,))
        else:
            cursor.execute("""
                SELECT * FROM sessions
                ORDER BY last_used DESC
            """)
        
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_session_info(row) for row in rows]
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if deleted, False if not found
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
        deleted = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        
        return deleted
    
    def _row_to_session_info(self, row: sqlite3.Row) -> SessionInfo:
        """Convert database row to SessionInfo."""
        return SessionInfo(
            session_id=row["session_id"],
            workspace=row["workspace"],
            model=row["model"],
            created_at=datetime.fromisoformat(row["created_at"]),
            last_used=datetime.fromisoformat(row["last_used"]),
            message_count=row["message_count"],
            name=row["name"],
            description=row["description"],
        )


# Global session manager instance
_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """Get or create global session manager instance."""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager

