import sqlite3
from pathlib import Path
from typing import Optional


class TokenCache:
    """Local SQLite cache for GitHub tokens."""

    def __init__(self, cache_path: Path | None = None):
        if cache_path is None:
            cache_path = Path.home() / ".cache" / "git-miner" / "tokens.db"
        self.cache_path = Path(cache_path)
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Initialize SQLite database."""
        with sqlite3.connect(self.cache_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tokens (
                    name TEXT PRIMARY KEY,
                    token TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def get_token(self, name: str = "default") -> Optional[str]:
        """Get cached token by name."""
        with sqlite3.connect(self.cache_path) as conn:
            cursor = conn.execute(
                "SELECT token FROM tokens WHERE name = ?",
                (name,)
            )
            row = cursor.fetchone()
            return row[0] if row else None

    def set_token(self, token: str, name: str = "default"):
        """Store token in cache."""
        with sqlite3.connect(self.cache_path) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO tokens (name, token) VALUES (?, ?)",
                (name, token)
            )
            conn.commit()

    def delete_token(self, name: str = "default"):
        """Delete token from cache."""
        with sqlite3.connect(self.cache_path) as conn:
            conn.execute("DELETE FROM tokens WHERE name = ?", (name,))
            conn.commit()

    def list_tokens(self) -> list[dict]:
        """List all cached tokens."""
        with sqlite3.connect(self.cache_path) as conn:
            cursor = conn.execute("SELECT name, created_at FROM tokens ORDER BY created_at DESC")
            return [{"name": row[0], "created_at": row[1]} for row in cursor.fetchall()]
