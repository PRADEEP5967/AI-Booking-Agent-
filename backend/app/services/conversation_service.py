import logging
import json
import os
from typing import Optional, Dict
from pathlib import Path
from ..models.schemas import ConversationState

logger = logging.getLogger(__name__)

class ConversationService:
    """Service for managing conversation state and session storage"""
    
    def __init__(self):
        # File-based persistence for sessions
        self.storage_dir = Path("sessions")
        self.storage_dir.mkdir(exist_ok=True)
        self._conversations: Dict[str, ConversationState] = {}
        self._load_persisted_sessions()
    
    def _load_persisted_sessions(self):
        """Load persisted sessions from disk"""
        try:
            for session_file in self.storage_dir.glob("*.json"):
                session_id = session_file.stem
                try:
                    with open(session_file, 'r') as f:
                        data = json.load(f)
                        # Convert back to ConversationState
                        state = ConversationState(**data)
                        self._conversations[session_id] = state
                        logger.info(f"Loaded persisted session: {session_id}")
                except Exception as e:
                    logger.error(f"Failed to load session {session_id}: {e}")
        except Exception as e:
            logger.error(f"Failed to load persisted sessions: {e}")
    
    def _persist_session(self, session_id: str, state: ConversationState):
        """Persist session to disk"""
        try:
            session_file = self.storage_dir / f"{session_id}.json"
            with open(session_file, 'w') as f:
                json.dump(state.dict(), f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to persist session {session_id}: {e}")
    
    def store_conversation(self, session_id: str, state: ConversationState) -> bool:
        """Store conversation state for a session"""
        try:
            self._conversations[session_id] = state
            self._persist_session(session_id, state)
            logger.info(f"Stored conversation state for session {session_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to store conversation for session {session_id}: {e}")
            return False
    
    def get_conversation(self, session_id: str) -> Optional[ConversationState]:
        """Retrieve conversation state for a session"""
        try:
            state = self._conversations.get(session_id)
            if state:
                logger.debug(f"Retrieved conversation state for session {session_id}")
            else:
                logger.warning(f"Conversation not found for session {session_id}")
            return state
        except Exception as e:
            logger.error(f"Failed to retrieve conversation for session {session_id}: {e}")
            return None
    
    def delete_conversation(self, session_id: str) -> bool:
        """Delete conversation state for a session"""
        try:
            if session_id in self._conversations:
                del self._conversations[session_id]
                # Remove persisted file
                session_file = self.storage_dir / f"{session_id}.json"
                if session_file.exists():
                    session_file.unlink()
                logger.info(f"Deleted conversation state for session {session_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete conversation for session {session_id}: {e}")
            return False
    
    def list_conversations(self) -> Dict[str, ConversationState]:
        """List all active conversations (for debugging/admin)"""
        return self._conversations.copy()
    
    def cleanup_old_sessions(self, max_age_hours: int = 24):
        """Clean up old sessions"""
        try:
            import time
            current_time = time.time()
            for session_id, state in list(self._conversations.items()):
                # Check if session is old (simple heuristic)
                if hasattr(state, 'messages') and state.messages:
                    last_message_time = state.messages[-1].timestamp
                    if last_message_time and (current_time - last_message_time.timestamp()) > (max_age_hours * 3600):
                        self.delete_conversation(session_id)
        except Exception as e:
            logger.error(f"Failed to cleanup old sessions: {e}") 