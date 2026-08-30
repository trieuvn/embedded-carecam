"""
Conversation Context Manager Module

This module manages conversation history and context for multi-turn dialogues.
It maintains conversation sessions, tracks messages, handles user preferences,
and implements automatic session cleanup.

Requirements:
- 12.1: Create session with unique ID
- 12.2: Store conversation history with user/assistant messages
- 12.3: Add messages to conversation history
- 12.4: Retrieve context with sliding window
- 12.5: Store user preferences
- 12.6: Implement sliding window (last N turns)
- 12.7: Automatic cleanup of expired sessions
- 12.8: Clear context for privacy
- 12.9: Support user preferences
- 12.10: In-memory storage with optional persistence
- 12.11: Session state management (EXPIRED after timeout)
- 12.12: Get session duration
"""

import json
import os
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Any, Optional
import threading


class Role(Enum):
    """Message role enumeration"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class SessionState(Enum):
    """Session state enumeration"""
    ACTIVE = "active"
    IDLE = "idle"
    EXPIRED = "expired"
    TERMINATED = "terminated"


@dataclass
class Message:
    """
    Represents a single message in the conversation.
    
    Attributes:
        role: Message role (USER, ASSISTANT, SYSTEM)
        content: Message text content
        timestamp: When the message was created
        metadata: Additional message metadata
    """
    role: Role
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary"""
        return {
            'role': self.role.value,
            'content': self.content,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """Create message from dictionary"""
        return cls(
            role=Role(data['role']),
            content=data['content'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            metadata=data.get('metadata', {})
        )


@dataclass
class ConversationContext:
    """
    Represents the full context of a conversation session.
    
    Attributes:
        session_id: Unique session identifier
        messages: List of conversation messages
        user_preferences: User preference settings
        session_start: Session start timestamp
        last_activity: Last activity timestamp
        metadata: Additional session metadata
    """
    session_id: str
    messages: List[Message] = field(default_factory=list)
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    session_start: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary"""
        return {
            'session_id': self.session_id,
            'messages': [msg.to_dict() for msg in self.messages],
            'user_preferences': self.user_preferences,
            'session_start': self.session_start.isoformat(),
            'last_activity': self.last_activity.isoformat(),
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationContext':
        """Create context from dictionary"""
        return cls(
            session_id=data['session_id'],
            messages=[Message.from_dict(msg) for msg in data['messages']],
            user_preferences=data.get('user_preferences', {}),
            session_start=datetime.fromisoformat(data['session_start']),
            last_activity=datetime.fromisoformat(data['last_activity']),
            metadata=data.get('metadata', {})
        )


class ConversationContextManager:
    """
    Manages conversation contexts and sessions for multi-turn dialogues.
    
    Features:
    - Session creation with unique IDs
    - Message history tracking
    - User preference management
    - Sliding window context retrieval
    - Automatic session expiration and cleanup
    - Optional persistence to disk
    
    Requirements: 12.1-12.12
    """

    def __init__(
        self,
        max_context_turns: int = 10,
        session_timeout_minutes: int = 30,
        persistence_enabled: bool = True,
        persistence_dir: Optional[str] = None
    ):
        """
        Initialize the ConversationContextManager.
        
        Args:
            max_context_turns: Maximum number of conversation turns to keep (default: 10)
            session_timeout_minutes: Minutes of inactivity before session expires (default: 30)
            persistence_enabled: Enable persistence to disk (default: True)
            persistence_dir: Directory for persistence files (default: logs/ directory)
        """
        self.max_context_turns = max_context_turns
        self.session_timeout = timedelta(minutes=session_timeout_minutes)
        self.persistence_enabled = persistence_enabled
        
        # Set persistence directory
        if persistence_dir:
            self.persistence_dir = Path(persistence_dir)
        else:
            # Default to logs/sessions directory
            self.persistence_dir = Path(__file__).parent.parent / "logs" / "sessions"
        
        # Create persistence directory if needed
        if self.persistence_enabled:
            self.persistence_dir.mkdir(parents=True, exist_ok=True)
        
        # In-memory session storage
        self._sessions: Dict[str, ConversationContext] = {}
        self._session_states: Dict[str, SessionState] = {}
        
        # Thread lock for concurrent access
        self._lock = threading.Lock()
        
        # Load persisted sessions if available
        if self.persistence_enabled:
            self._load_persisted_sessions()

    def create_session(self, user_id: Optional[str] = None) -> str:
        """
        Create a new conversation session with a unique session ID.
        
        Args:
            user_id: Optional user identifier for the session
            
        Returns:
            Unique session ID (UUID)
            
        Requirement: 12.1
        """
        with self._lock:
            # Generate unique session ID
            session_id = str(uuid.uuid4())
            
            # Create new conversation context
            context = ConversationContext(
                session_id=session_id,
                metadata={'user_id': user_id} if user_id else {}
            )
            
            # Store session
            self._sessions[session_id] = context
            self._session_states[session_id] = SessionState.ACTIVE
            
            # Persist to disk if enabled
            if self.persistence_enabled:
                self._persist_session(session_id)
            
            return session_id

    def add_message(self, session_id: str, role: Role, content: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Add a message to the conversation history.
        
        Args:
            session_id: Session identifier
            role: Message role (USER, ASSISTANT, SYSTEM)
            content: Message content
            metadata: Optional message metadata
            
        Raises:
            KeyError: If session_id does not exist
            
        Requirements: 12.2, 12.3
        """
        with self._lock:
            if session_id not in self._sessions:
                raise KeyError(f"Session {session_id} not found")
            
            context = self._sessions[session_id]
            
            # Create message
            message = Message(
                role=role,
                content=content,
                timestamp=datetime.now(),
                metadata=metadata or {}
            )
            
            # Add to conversation history
            context.messages.append(message)
            context.last_activity = datetime.now()
            
            # Update session state to ACTIVE
            self._session_states[session_id] = SessionState.ACTIVE
            
            # Persist to disk if enabled
            if self.persistence_enabled:
                self._persist_session(session_id)

    def get_context(self, session_id: str, max_turns: Optional[int] = None) -> ConversationContext:
        """
        Retrieve conversation context with sliding window.
        
        Args:
            session_id: Session identifier
            max_turns: Maximum number of turns to retrieve (default: use configured max_context_turns)
            
        Returns:
            ConversationContext with messages limited to sliding window
            
        Raises:
            KeyError: If session_id does not exist
            
        Requirements: 12.4, 12.5, 12.6
        """
        with self._lock:
            if session_id not in self._sessions:
                raise KeyError(f"Session {session_id} not found")
            
            context = self._sessions[session_id]
            
            # Check if session should be expired BEFORE updating last_activity
            if self._is_session_expired(context):
                self._session_states[session_id] = SessionState.EXPIRED
            
            # Apply sliding window to messages
            turns = max_turns if max_turns is not None else self.max_context_turns
            max_messages = turns * 2  # Each turn has user + assistant message
            
            # Handle edge case: max_turns=0 should return empty messages
            if turns == 0:
                windowed_messages = []
            elif len(context.messages) > max_messages:
                windowed_messages = context.messages[-max_messages:]
            else:
                windowed_messages = context.messages.copy()
            
            # Create a copy of context with windowed messages
            windowed_context = ConversationContext(
                session_id=context.session_id,
                messages=windowed_messages,
                user_preferences=context.user_preferences.copy(),
                session_start=context.session_start,
                last_activity=context.last_activity,
                metadata=context.metadata.copy()
            )
            
            return windowed_context

    def clear_context(self, session_id: str) -> None:
        """
        Clear conversation history for privacy.
        
        Args:
            session_id: Session identifier
            
        Raises:
            KeyError: If session_id does not exist
            
        Requirement: 12.8
        """
        with self._lock:
            if session_id not in self._sessions:
                raise KeyError(f"Session {session_id} not found")
            
            # Clear messages but keep session structure
            context = self._sessions[session_id]
            context.messages.clear()
            context.last_activity = datetime.now()
            
            # Persist cleared state
            if self.persistence_enabled:
                self._persist_session(session_id)

    def end_session(self, session_id: str) -> None:
        """
        End a conversation session.
        
        Args:
            session_id: Session identifier
            
        Raises:
            KeyError: If session_id does not exist
        """
        with self._lock:
            if session_id not in self._sessions:
                raise KeyError(f"Session {session_id} not found")
            
            # Update session state
            self._session_states[session_id] = SessionState.TERMINATED
            
            # Remove from memory
            del self._sessions[session_id]
            del self._session_states[session_id]
            
            # Remove persisted file
            if self.persistence_enabled:
                self._delete_persisted_session(session_id)

    def get_session_duration(self, session_id: str) -> float:
        """
        Get the duration of a session in seconds.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session duration in seconds
            
        Raises:
            KeyError: If session_id does not exist
            
        Requirement: 12.12
        """
        with self._lock:
            if session_id not in self._sessions:
                raise KeyError(f"Session {session_id} not found")
            
            context = self._sessions[session_id]
            duration = (context.last_activity - context.session_start).total_seconds()
            return duration

    def set_user_preference(self, session_id: str, key: str, value: Any) -> None:
        """
        Set a user preference for the session.
        
        Args:
            session_id: Session identifier
            key: Preference key
            value: Preference value
            
        Raises:
            KeyError: If session_id does not exist
            
        Requirement: 12.9
        """
        with self._lock:
            if session_id not in self._sessions:
                raise KeyError(f"Session {session_id} not found")
            
            context = self._sessions[session_id]
            context.user_preferences[key] = value
            context.last_activity = datetime.now()
            
            # Persist to disk if enabled
            if self.persistence_enabled:
                self._persist_session(session_id)

    def get_user_preference(self, session_id: str, key: str, default: Any = None) -> Any:
        """
        Get a user preference from the session.
        
        Args:
            session_id: Session identifier
            key: Preference key
            default: Default value if key not found
            
        Returns:
            Preference value or default
            
        Raises:
            KeyError: If session_id does not exist
            
        Requirement: 12.9
        """
        with self._lock:
            if session_id not in self._sessions:
                raise KeyError(f"Session {session_id} not found")
            
            context = self._sessions[session_id]
            return context.user_preferences.get(key, default)

    def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions automatically.
        
        Returns:
            Number of sessions cleaned up
            
        Requirement: 12.7, 12.11
        """
        with self._lock:
            expired_sessions = []
            
            # Find expired sessions
            for session_id, context in self._sessions.items():
                if self._is_session_expired(context):
                    expired_sessions.append(session_id)
                    self._session_states[session_id] = SessionState.EXPIRED
            
            # Remove expired sessions
            for session_id in expired_sessions:
                del self._sessions[session_id]
                del self._session_states[session_id]
                
                # Remove persisted file
                if self.persistence_enabled:
                    self._delete_persisted_session(session_id)
            
            return len(expired_sessions)

    def get_session_state(self, session_id: str) -> SessionState:
        """
        Get the current state of a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Current session state
            
        Raises:
            KeyError: If session_id does not exist
            
        Requirement: 12.11
        """
        with self._lock:
            if session_id not in self._session_states:
                raise KeyError(f"Session {session_id} not found")
            
            return self._session_states[session_id]

    def get_active_session_count(self) -> int:
        """
        Get the number of active sessions.
        
        Returns:
            Number of active sessions
        """
        with self._lock:
            return len(self._sessions)

    def _is_session_expired(self, context: ConversationContext) -> bool:
        """
        Check if a session has expired due to inactivity.
        
        Args:
            context: Conversation context to check
            
        Returns:
            True if session is expired, False otherwise
            
        Requirement: 12.7, 12.11
        """
        inactivity_duration = datetime.now() - context.last_activity
        return inactivity_duration > self.session_timeout

    def _persist_session(self, session_id: str) -> None:
        """
        Persist session to disk.
        
        Args:
            session_id: Session identifier
            
        Requirement: 12.10
        """
        if not self.persistence_enabled:
            return
        
        try:
            context = self._sessions[session_id]
            session_file = self.persistence_dir / f"{session_id}.json"
            
            # Convert context to dictionary and save
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(context.to_dict(), f, ensure_ascii=False, indent=2)
        except Exception as e:
            # Log error but don't fail the operation
            print(f"Warning: Failed to persist session {session_id}: {e}")

    def _delete_persisted_session(self, session_id: str) -> None:
        """
        Delete persisted session file.
        
        Args:
            session_id: Session identifier
        """
        if not self.persistence_enabled:
            return
        
        try:
            session_file = self.persistence_dir / f"{session_id}.json"
            if session_file.exists():
                session_file.unlink()
        except Exception as e:
            # Log error but don't fail the operation
            print(f"Warning: Failed to delete persisted session {session_id}: {e}")

    def _load_persisted_sessions(self) -> None:
        """
        Load persisted sessions from disk on startup.
        
        Requirement: 12.10
        """
        if not self.persistence_enabled:
            return
        
        try:
            # Load all session files
            for session_file in self.persistence_dir.glob("*.json"):
                try:
                    with open(session_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # Reconstruct context
                    context = ConversationContext.from_dict(data)
                    
                    # Check if session should be expired
                    if self._is_session_expired(context):
                        # Delete expired session file
                        session_file.unlink()
                        continue
                    
                    # Load into memory
                    session_id = context.session_id
                    self._sessions[session_id] = context
                    self._session_states[session_id] = SessionState.IDLE
                    
                except Exception as e:
                    print(f"Warning: Failed to load session from {session_file}: {e}")
                    
        except Exception as e:
            print(f"Warning: Failed to load persisted sessions: {e}")


# Module-level test function
if __name__ == "__main__":
    """Test the ConversationContextManager"""
    print("Testing ConversationContextManager...")
    
    # Create manager
    manager = ConversationContextManager(
        max_context_turns=5,
        session_timeout_minutes=30,
        persistence_enabled=False  # Disable for testing
    )
    
    # Test 1: Create session
    print("\n1. Creating session...")
    session_id = manager.create_session(user_id="test_user")
    print(f"   Session created: {session_id}")
    
    # Test 2: Add messages
    print("\n2. Adding messages...")
    manager.add_message(session_id, Role.USER, "Xin chào Tỷ Tỷ")
    manager.add_message(session_id, Role.ASSISTANT, "Xin chào! Tỷ Tỷ có thể giúp gì cho bạn?")
    manager.add_message(session_id, Role.USER, "1 + 1 bằng mấy?")
    manager.add_message(session_id, Role.ASSISTANT, "1 + 1 bằng 2")
    print("   Messages added successfully")
    
    # Test 3: Get context
    print("\n3. Getting context...")
    context = manager.get_context(session_id)
    print(f"   Session ID: {context.session_id}")
    print(f"   Message count: {len(context.messages)}")
    print(f"   Session start: {context.session_start}")
    print(f"   Last activity: {context.last_activity}")
    
    # Test 4: Get context with sliding window
    print("\n4. Testing sliding window (max_turns=1)...")
    windowed_context = manager.get_context(session_id, max_turns=1)
    print(f"   Windowed message count: {len(windowed_context.messages)} (should be 2)")
    
    # Test 5: User preferences
    print("\n5. Testing user preferences...")
    manager.set_user_preference(session_id, "response_mode", "concise")
    manager.set_user_preference(session_id, "language", "vi")
    response_mode = manager.get_user_preference(session_id, "response_mode")
    language = manager.get_user_preference(session_id, "language")
    print(f"   Response mode: {response_mode}")
    print(f"   Language: {language}")
    
    # Test 6: Get session duration
    print("\n6. Getting session duration...")
    duration = manager.get_session_duration(session_id)
    print(f"   Session duration: {duration:.2f} seconds")
    
    # Test 7: Get session state
    print("\n7. Getting session state...")
    state = manager.get_session_state(session_id)
    print(f"   Session state: {state.value}")
    
    # Test 8: Clear context
    print("\n8. Clearing context...")
    manager.clear_context(session_id)
    context = manager.get_context(session_id)
    print(f"   Message count after clear: {len(context.messages)} (should be 0)")
    
    # Test 9: End session
    print("\n9. Ending session...")
    manager.end_session(session_id)
    print(f"   Active sessions: {manager.get_active_session_count()} (should be 0)")
    
    print("\n✓ All tests completed successfully!")
