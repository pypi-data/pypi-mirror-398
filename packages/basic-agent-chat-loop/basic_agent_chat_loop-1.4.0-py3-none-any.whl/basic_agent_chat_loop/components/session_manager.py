"""
Session management for conversation persistence and resumption.

Handles saving, loading, and managing conversation sessions with both
human-readable markdown and machine-readable JSON formats.
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class SessionInfo:
    """Metadata about a saved session."""

    session_id: str
    agent_name: str
    agent_path: str
    created: datetime
    last_updated: datetime
    query_count: int
    total_tokens: int
    total_cost: float
    preview: str  # First query text

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "session_id": self.session_id,
            "agent_name": self.agent_name,
            "agent_path": self.agent_path,
            "created": self.created.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "query_count": self.query_count,
            "total_tokens": self.total_tokens,
            "total_cost": self.total_cost,
            "preview": self.preview,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SessionInfo":
        """Create SessionInfo from dictionary."""
        return cls(
            session_id=data["session_id"],
            agent_name=data["agent_name"],
            agent_path=data["agent_path"],
            created=datetime.fromisoformat(data["created"]),
            last_updated=datetime.fromisoformat(data["last_updated"]),
            query_count=data["query_count"],
            total_tokens=data["total_tokens"],
            total_cost=data["total_cost"],
            preview=data["preview"],
        )


class SessionManager:
    """Manage saved conversation sessions."""

    def __init__(self, sessions_dir: Optional[Path] = None):
        """
        Initialize session manager.

        Args:
            sessions_dir: Directory for session files
                         (defaults to ~/agent-conversations)
        """
        self.sessions_dir = sessions_dir or Path.home() / "agent-conversations"
        self.index_file = self.sessions_dir / ".index.json"

    def _ensure_sessions_dir(self) -> bool:
        """
        Ensure sessions directory exists.

        Returns:
            True if directory exists or was created, False on error
        """
        try:
            self.sessions_dir.mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            logger.error(f"Failed to create sessions directory: {e}")
            return False

    def _load_index(self) -> dict[str, Any]:
        """
        Load session index.

        Returns:
            Index dictionary with sessions list
        """
        if not self.index_file.exists():
            return {"sessions": [], "last_updated": datetime.now().isoformat()}

        try:
            with open(self.index_file, encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, dict) or "sessions" not in data:
                logger.warning("Invalid index format, creating new index")
                return {"sessions": [], "last_updated": datetime.now().isoformat()}

            return data

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse index file: {e}")
            return {"sessions": [], "last_updated": datetime.now().isoformat()}
        except Exception as e:
            logger.error(f"Failed to load index: {e}")
            return {"sessions": [], "last_updated": datetime.now().isoformat()}

    def _save_index(self, index: dict[str, Any]) -> bool:
        """
        Save session index.

        Args:
            index: Index dictionary to save

        Returns:
            True if successful, False otherwise
        """
        if not self._ensure_sessions_dir():
            return False

        try:
            # Update timestamp
            index["last_updated"] = datetime.now().isoformat()

            # Write with pretty formatting
            with open(self.index_file, "w", encoding="utf-8") as f:
                json.dump(index, f, indent=2)

            return True

        except Exception as e:
            logger.error(f"Failed to save index: {e}")
            return False

    def _update_index(self, session_info: SessionInfo) -> bool:
        """
        Update index with session information.

        Args:
            session_info: Session metadata to add/update

        Returns:
            True if successful, False otherwise
        """
        index = self._load_index()

        # Remove existing entry if present
        index["sessions"] = [
            s for s in index["sessions"] if s["session_id"] != session_info.session_id
        ]

        # Add new entry at the beginning (most recent first)
        index["sessions"].insert(0, session_info.to_dict())

        return self._save_index(index)

    def _remove_from_index(self, session_id: str) -> bool:
        """
        Remove session from index.

        Args:
            session_id: Session ID to remove

        Returns:
            True if successful, False otherwise
        """
        index = self._load_index()

        # Remove entry
        index["sessions"] = [
            s for s in index["sessions"] if s["session_id"] != session_id
        ]

        return self._save_index(index)

    def save_session(
        self,
        session_id: str,
        agent_name: str,
        agent_path: str,
        agent_description: str,
        conversation: list[dict[str, Any]],
        metadata: Optional[dict[str, Any]] = None,
    ) -> tuple[bool, str]:
        """
        Save session to both JSON and markdown formats.

        Args:
            session_id: Unique session identifier
            agent_name: Name of the agent
            agent_path: Path to agent file
            agent_description: Agent description
            conversation: List of conversation entries
            metadata: Optional additional metadata

        Returns:
            Tuple of (success, message)
        """
        if not self._ensure_sessions_dir():
            return False, "Failed to create sessions directory"

        if not conversation:
            return False, "No conversation to save"

        try:
            json_path = self.sessions_dir / f"{session_id}.json"
            md_path = self.sessions_dir / f"{session_id}.md"

            # Calculate metadata
            total_tokens = sum(
                (entry.get("usage") or {}).get("input_tokens", 0)
                + (entry.get("usage") or {}).get("output_tokens", 0)
                for entry in conversation
            )

            # Get first query for preview (truncate to 100 chars)
            preview = conversation[0]["query"][:100] if conversation else ""
            if len(conversation[0]["query"]) > 100:
                preview += "..."

            created = datetime.fromtimestamp(conversation[0]["timestamp"])
            last_updated = datetime.fromtimestamp(conversation[-1]["timestamp"])

            # Prepare JSON data
            json_data = {
                "session_id": session_id,
                "agent_name": agent_name,
                "agent_path": agent_path,
                "agent_description": agent_description,
                "created": created.isoformat(),
                "last_updated": last_updated.isoformat(),
                "metadata": {
                    "total_queries": len(conversation),
                    "total_tokens": total_tokens,
                    "total_cost": metadata.get("total_cost", 0.0) if metadata else 0.0,
                    "duration": metadata.get("duration", 0) if metadata else 0,
                },
                "conversation": conversation,
            }

            # Save JSON
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(json_data, f, indent=2)

            # Set secure permissions (owner read/write only)
            json_path.chmod(0o600)

            # Save markdown (for human readability)
            self._save_markdown(md_path, session_id, json_data)

            # Update index
            metadata_dict: dict[str, Any] = json_data["metadata"]  # type: ignore[assignment]
            session_info = SessionInfo(
                session_id=session_id,
                agent_name=agent_name,
                agent_path=agent_path,
                created=created,
                last_updated=last_updated,
                query_count=len(conversation),
                total_tokens=total_tokens,
                total_cost=float(metadata_dict["total_cost"]),
                preview=preview,
            )

            self._update_index(session_info)

            logger.info(f"Saved session: {session_id}")
            return True, f"Session saved: {json_path}"

        except Exception as e:
            logger.error(f"Failed to save session: {e}", exc_info=True)
            return False, f"Failed to save session: {e}"

    def _save_markdown(
        self, md_path: Path, session_id: str, json_data: dict[str, Any]
    ) -> None:
        """
        Save session as markdown file.

        Args:
            md_path: Path to markdown file
            session_id: Session identifier
            json_data: Session data
        """
        content_lines = [
            f"# {json_data['agent_name']} Conversation",
            f"\n**Session ID:** {session_id}",
            f"\n**Date:** {json_data['created']}",
            f"\n**Agent:** {json_data['agent_name']}",
            f"\n**Description:** {json_data['agent_description']}",
            f"\n**Total Queries:** {json_data['metadata']['total_queries']}",
            "\n---\n",
        ]

        # Add each conversation entry
        for i, entry in enumerate(json_data["conversation"], 1):
            ts = entry["timestamp"]
            entry_timestamp = datetime.fromtimestamp(ts).strftime("%H:%M:%S")
            duration = entry.get("duration", 0)

            # Add query
            content_lines.append(f"\n## Query {i} ({entry_timestamp})\n")
            content_lines.append(f"**You:** {entry['query']}\n")

            # Add response
            content_lines.append(
                f"\n**{json_data['agent_name']}:** {entry['response']}\n"
            )

            # Add metadata
            metadata_parts = [f"Time: {duration:.1f}s"]

            # Add token info if available
            usage = entry.get("usage")
            if usage:
                input_tok = usage.get("input_tokens", 0)
                output_tok = usage.get("output_tokens", 0)
                total_tok = input_tok + output_tok
                if total_tok > 0:
                    tok_str = f"Tokens: {total_tok:,} "
                    tok_str += f"(in: {input_tok:,}, out: {output_tok:,})"
                    metadata_parts.append(tok_str)

            if metadata_parts:
                content_lines.append(f"\n*{' | '.join(metadata_parts)}*\n")

            content_lines.append("\n---\n")

        # Write to file
        with open(md_path, "w", encoding="utf-8") as f:
            f.writelines(content_lines)

        # Set secure permissions
        md_path.chmod(0o600)

    def load_session(self, session_id: str) -> Optional[dict[str, Any]]:
        """
        Load session data from JSON file.

        Args:
            session_id: Session identifier

        Returns:
            Session data dictionary or None if not found
        """
        json_path = self.sessions_dir / f"{session_id}.json"

        if not json_path.exists():
            logger.warning(f"Session not found: {session_id}")
            return None

        try:
            with open(json_path, encoding="utf-8") as f:
                data = json.load(f)

            logger.info(f"Loaded session: {session_id}")
            return data

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse session file: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to load session: {e}")
            return None

    def list_sessions(
        self, agent_name: Optional[str] = None, limit: int = 20
    ) -> list[SessionInfo]:
        """
        List available sessions.

        Args:
            agent_name: Optional filter by agent name
            limit: Maximum number of sessions to return

        Returns:
            List of SessionInfo objects
        """
        index = self._load_index()
        sessions = []

        for session_data in index["sessions"][:limit]:
            # Filter by agent name if specified
            if agent_name and session_data.get("agent_name") != agent_name:
                continue

            try:
                sessions.append(SessionInfo.from_dict(session_data))
            except Exception as e:
                logger.warning(f"Skipping invalid session entry: {e}")
                continue

        return sessions

    def delete_session(self, session_id: str) -> tuple[bool, str]:
        """
        Delete a session (both JSON and markdown files).

        Args:
            session_id: Session identifier

        Returns:
            Tuple of (success, message)
        """
        json_path = self.sessions_dir / f"{session_id}.json"
        md_path = self.sessions_dir / f"{session_id}.md"

        if not json_path.exists():
            return False, f"Session not found: {session_id}"

        try:
            # Delete files
            json_path.unlink()
            if md_path.exists():
                md_path.unlink()

            # Remove from index
            self._remove_from_index(session_id)

            logger.info(f"Deleted session: {session_id}")
            return True, f"Deleted session: {session_id}"

        except Exception as e:
            logger.error(f"Failed to delete session: {e}")
            return False, f"Failed to delete session: {e}"

    def search_sessions(self, query: str) -> list[SessionInfo]:
        """
        Search sessions by query text.

        Args:
            query: Search query

        Returns:
            List of matching SessionInfo objects
        """
        index = self._load_index()
        results = []
        query_lower = query.lower()

        for session_data in index["sessions"]:
            # Search in preview and agent name
            preview = session_data.get("preview", "").lower()
            agent_name = session_data.get("agent_name", "").lower()

            if query_lower in preview or query_lower in agent_name:
                try:
                    results.append(SessionInfo.from_dict(session_data))
                except Exception as e:
                    logger.warning(f"Skipping invalid session entry: {e}")
                    continue

        return results

    def get_session_metadata(self, session_id: str) -> Optional[SessionInfo]:
        """
        Get session metadata without loading full conversation.

        Args:
            session_id: Session identifier

        Returns:
            SessionInfo object or None if not found
        """
        index = self._load_index()

        for session_data in index["sessions"]:
            if session_data.get("session_id") == session_id:
                try:
                    return SessionInfo.from_dict(session_data)
                except Exception as e:
                    logger.warning(f"Invalid session metadata: {e}")
                    return None

        return None

    def cleanup_old_sessions(self, max_age_days: int = 30) -> tuple[int, str]:
        """
        Delete sessions older than specified days.

        Args:
            max_age_days: Maximum age in days

        Returns:
            Tuple of (count_deleted, message)
        """
        from datetime import timedelta

        cutoff = datetime.now() - timedelta(days=max_age_days)
        deleted_count = 0

        sessions = self.list_sessions(limit=1000)  # Get all sessions

        for session in sessions:
            if session.last_updated < cutoff:
                success, _ = self.delete_session(session.session_id)
                if success:
                    deleted_count += 1

        msg = f"Deleted {deleted_count} sessions older than {max_age_days} days"
        logger.info(msg)
        return deleted_count, msg
