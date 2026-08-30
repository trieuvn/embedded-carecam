"""
Unit tests for ConversationContextManager module

Tests all requirements from Requirement 12:
- 12.1: Create session with unique ID
- 12.4: Retrieve context with sliding window
- 12.6: Implement sliding window (last N turns)
- 12.7: Automatic cleanup of expired sessions
- 12.9: Support user preferences
"""

import unittest
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import shutil

from modules.context_manager import (
    ConversationContextManager,
    ConversationContext,
    Message,
    Role,
    SessionState
)


class TestSessionCreation(unittest.TestCase):
    """Test session creation and unique ID generation - Requirement 12.1"""
    
    def setUp(self):
        """Set up test context manager without persistence"""
        self.manager = ConversationContextManager(
            max_context_turns=10,
            session_timeout_minutes=30,
            persistence_enabled=False
        )
    
    def test_create_session_returns_unique_id(self):
        """Test that create_session returns a unique session ID"""
        session_id = self.manager.create_session()
        
        # Should be a valid UUID string
        self.assertIsInstance(session_id, str)
        # Should be parseable as UUID
        try:
            uuid.UUID(session_id)
        except ValueError:
            self.fail("Session ID is not a valid UUID")
    
    def test_create_session_with_user_id(self):
        """Test creating session with user_id metadata"""
        user_id = "test_user_123"
        session_id = self.manager.create_session(user_id=user_id)
        
        context = self.manager.get_context(session_id)
        self.assertEqual(context.metadata.get('user_id'), user_id)
    
    def test_multiple_sessions_have_unique_ids(self):
        """Test that multiple sessions get unique IDs"""
        session_ids = set()
        for _ in range(10):
            session_id = self.manager.create_session()
            session_ids.add(session_id)
        
        # All IDs should be unique
        self.assertEqual(len(session_ids), 10)
    
    def test_new_session_has_empty_message_list(self):
        """Test that new session starts with no messages"""
        session_id = self.manager.create_session()
        context = self.manager.get_context(session_id)
        
        self.assertEqual(len(context.messages), 0)
    
    def test_new_session_has_active_state(self):
        """Test that new session is in ACTIVE state"""
        session_id = self.manager.create_session()
        state = self.manager.get_session_state(session_id)
        
        self.assertEqual(state, SessionState.ACTIVE)


class TestMessageStorage(unittest.TestCase):
    """Test message storage and retrieval - Requirements 12.2, 12.3"""
    
    def setUp(self):
        """Set up test context manager and session"""
        self.manager = ConversationContextManager(
            max_context_turns=10,
            persistence_enabled=False
        )
        self.session_id = self.manager.create_session()
    
    def test_add_user_message(self):
        """Test adding a user message to conversation history"""
        content = "Hello, Tỷ Tỷ!"
        self.manager.add_message(self.session_id, Role.USER, content)
        
        context = self.manager.get_context(self.session_id)
        self.assertEqual(len(context.messages), 1)
        self.assertEqual(context.messages[0].role, Role.USER)
        self.assertEqual(context.messages[0].content, content)
    
    def test_add_assistant_message(self):
        """Test adding an assistant message to conversation history"""
        content = "Xin chào! Tỷ Tỷ có thể giúp gì cho bạn?"
        self.manager.add_message(self.session_id, Role.ASSISTANT, content)
        
        context = self.manager.get_context(self.session_id)
        self.assertEqual(len(context.messages), 1)
        self.assertEqual(context.messages[0].role, Role.ASSISTANT)
        self.assertEqual(context.messages[0].content, content)
    
    def test_add_multiple_messages(self):
        """Test adding multiple messages maintains order"""
        messages = [
            (Role.USER, "First question"),
            (Role.ASSISTANT, "First answer"),
            (Role.USER, "Second question"),
            (Role.ASSISTANT, "Second answer")
        ]
        
        for role, content in messages:
            self.manager.add_message(self.session_id, role, content)
        
        context = self.manager.get_context(self.session_id)
        self.assertEqual(len(context.messages), 4)
        
        # Verify order is maintained
        for i, (role, content) in enumerate(messages):
            self.assertEqual(context.messages[i].role, role)
            self.assertEqual(context.messages[i].content, content)
    
    def test_add_message_with_metadata(self):
        """Test adding message with custom metadata"""
        content = "Test message"
        metadata = {"source": "test", "confidence": 0.95}
        
        self.manager.add_message(self.session_id, Role.USER, content, metadata=metadata)
        
        context = self.manager.get_context(self.session_id)
        self.assertEqual(context.messages[0].metadata, metadata)
    
    def test_add_message_updates_last_activity(self):
        """Test that adding message updates last_activity timestamp"""
        context_before = self.manager.get_context(self.session_id)
        timestamp_before = context_before.last_activity
        
        time.sleep(0.1)  # Small delay to ensure timestamp difference
        
        self.manager.add_message(self.session_id, Role.USER, "Test")
        
        context_after = self.manager.get_context(self.session_id)
        timestamp_after = context_after.last_activity
        
        self.assertGreater(timestamp_after, timestamp_before)
    
    def test_add_message_invalid_session_raises_error(self):
        """Test that adding message to non-existent session raises KeyError"""
        with self.assertRaises(KeyError):
            self.manager.add_message("invalid-session-id", Role.USER, "Test")
    
    def test_message_has_timestamp(self):
        """Test that messages automatically get timestamps"""
        self.manager.add_message(self.session_id, Role.USER, "Test")
        
        context = self.manager.get_context(self.session_id)
        message = context.messages[0]
        
        self.assertIsInstance(message.timestamp, datetime)
        # Should be recent (within last second)
        time_diff = (datetime.now() - message.timestamp).total_seconds()
        self.assertLess(time_diff, 1.0)


class TestSlidingWindow(unittest.TestCase):
    """Test sliding window with max_turns constraint - Requirement 12.6"""
    
    def setUp(self):
        """Set up test context manager with small max_turns"""
        self.manager = ConversationContextManager(
            max_context_turns=3,  # Keep last 3 turns (6 messages)
            persistence_enabled=False
        )
        self.session_id = self.manager.create_session()
    
    def test_sliding_window_keeps_last_n_turns(self):
        """Test that sliding window keeps only last N turns"""
        # Add 5 turns (10 messages)
        for i in range(5):
            self.manager.add_message(self.session_id, Role.USER, f"Question {i+1}")
            self.manager.add_message(self.session_id, Role.ASSISTANT, f"Answer {i+1}")
        
        # Get context with default max_turns (3)
        context = self.manager.get_context(self.session_id)
        
        # Should only have last 3 turns = 6 messages
        self.assertEqual(len(context.messages), 6)
        
        # Verify it's the most recent messages
        self.assertEqual(context.messages[0].content, "Question 3")
        self.assertEqual(context.messages[-1].content, "Answer 5")
    
    def test_sliding_window_with_custom_max_turns(self):
        """Test sliding window with custom max_turns parameter"""
        # Add 5 turns (10 messages)
        for i in range(5):
            self.manager.add_message(self.session_id, Role.USER, f"Question {i+1}")
            self.manager.add_message(self.session_id, Role.ASSISTANT, f"Answer {i+1}")
        
        # Get context with max_turns=2
        context = self.manager.get_context(self.session_id, max_turns=2)
        
        # Should only have last 2 turns = 4 messages
        self.assertEqual(len(context.messages), 4)
        self.assertEqual(context.messages[0].content, "Question 4")
        self.assertEqual(context.messages[-1].content, "Answer 5")
    
    def test_sliding_window_with_fewer_messages_than_limit(self):
        """Test that sliding window doesn't truncate when under limit"""
        # Add 2 turns (4 messages), max_turns is 3
        self.manager.add_message(self.session_id, Role.USER, "Question 1")
        self.manager.add_message(self.session_id, Role.ASSISTANT, "Answer 1")
        self.manager.add_message(self.session_id, Role.USER, "Question 2")
        self.manager.add_message(self.session_id, Role.ASSISTANT, "Answer 2")
        
        context = self.manager.get_context(self.session_id)
        
        # Should have all 4 messages
        self.assertEqual(len(context.messages), 4)
    
    def test_sliding_window_max_turns_zero(self):
        """Test sliding window with max_turns=0"""
        # Add some messages
        self.manager.add_message(self.session_id, Role.USER, "Question")
        self.manager.add_message(self.session_id, Role.ASSISTANT, "Answer")
        
        context = self.manager.get_context(self.session_id, max_turns=0)
        
        # Should return no messages
        self.assertEqual(len(context.messages), 0)
    
    def test_sliding_window_preserves_context_structure(self):
        """Test that sliding window preserves all context fields"""
        # Add some messages
        self.manager.add_message(self.session_id, Role.USER, "Test")
        self.manager.set_user_preference(self.session_id, "test_key", "test_value")
        
        context = self.manager.get_context(self.session_id, max_turns=1)
        
        # Verify all fields are present
        self.assertEqual(context.session_id, self.session_id)
        self.assertIsInstance(context.messages, list)
        self.assertIsInstance(context.user_preferences, dict)
        self.assertIsInstance(context.session_start, datetime)
        self.assertIsInstance(context.last_activity, datetime)
        self.assertIsInstance(context.metadata, dict)
    
    def test_sliding_window_does_not_modify_original_context(self):
        """Test that sliding window returns a copy, not modifying original"""
        # Add 5 turns
        for i in range(5):
            self.manager.add_message(self.session_id, Role.USER, f"Q{i+1}")
            self.manager.add_message(self.session_id, Role.ASSISTANT, f"A{i+1}")
        
        # Get windowed context
        windowed = self.manager.get_context(self.session_id, max_turns=2)
        self.assertEqual(len(windowed.messages), 4)
        
        # Get full context by accessing internal storage
        # (In real scenario, original messages should still be stored)
        context_full = self.manager.get_context(self.session_id, max_turns=100)
        self.assertEqual(len(context_full.messages), 10)


class TestSessionExpiration(unittest.TestCase):
    """Test session expiration after inactivity timeout - Requirement 12.7"""
    
    def test_cleanup_removes_expired_sessions(self):
        """Test that cleanup_expired_sessions removes expired sessions"""
        # Create manager with 0.1 minute (6 second) timeout
        manager = ConversationContextManager(
            max_context_turns=10,
            session_timeout_minutes=0.01,  # ~0.6 seconds
            persistence_enabled=False
        )
        
        # Create session and add message
        session_id = manager.create_session()
        manager.add_message(session_id, Role.USER, "Test")
        
        # Verify session exists
        self.assertEqual(manager.get_active_session_count(), 1)
        
        # Wait for expiration
        time.sleep(1.0)  # Wait longer than timeout
        
        # Run cleanup
        cleaned = manager.cleanup_expired_sessions()
        
        # Should have cleaned 1 session
        self.assertEqual(cleaned, 1)
        self.assertEqual(manager.get_active_session_count(), 0)
    
    def test_cleanup_keeps_active_sessions(self):
        """Test that cleanup keeps sessions that are not expired"""
        manager = ConversationContextManager(
            max_context_turns=10,
            session_timeout_minutes=10,  # Long timeout
            persistence_enabled=False
        )
        
        # Create multiple active sessions
        session_ids = []
        for i in range(3):
            session_id = manager.create_session()
            manager.add_message(session_id, Role.USER, f"Test {i}")
            session_ids.append(session_id)
        
        # Run cleanup immediately
        cleaned = manager.cleanup_expired_sessions()
        
        # Should not clean any sessions
        self.assertEqual(cleaned, 0)
        self.assertEqual(manager.get_active_session_count(), 3)
    
    def test_get_context_marks_expired_sessions(self):
        """Test that get_context marks session as EXPIRED if inactive"""
        manager = ConversationContextManager(
            max_context_turns=10,
            session_timeout_minutes=0.01,  # Very short timeout
            persistence_enabled=False
        )
        
        session_id = manager.create_session()
        
        # Wait for expiration
        time.sleep(1.0)
        
        # Get context (should mark as expired)
        manager.get_context(session_id)
        
        # Check state is EXPIRED
        state = manager.get_session_state(session_id)
        self.assertEqual(state, SessionState.EXPIRED)
    
    def test_adding_message_resets_expiration(self):
        """Test that adding message updates last_activity and prevents expiration"""
        manager = ConversationContextManager(
            max_context_turns=10,
            session_timeout_minutes=0.02,  # 1.2 seconds
            persistence_enabled=False
        )
        
        session_id = manager.create_session()
        
        # Wait half the timeout
        time.sleep(0.7)
        
        # Add message (should reset expiration)
        manager.add_message(session_id, Role.USER, "Keep alive")
        
        # Wait another half timeout
        time.sleep(0.7)
        
        # Should not be expired yet (total wait < 2 * half timeout from last message)
        cleaned = manager.cleanup_expired_sessions()
        self.assertEqual(cleaned, 0)


class TestUserPreferences(unittest.TestCase):
    """Test user preference storage and retrieval - Requirement 12.9"""
    
    def setUp(self):
        """Set up test context manager and session"""
        self.manager = ConversationContextManager(
            persistence_enabled=False
        )
        self.session_id = self.manager.create_session()
    
    def test_set_user_preference(self):
        """Test setting a user preference"""
        self.manager.set_user_preference(self.session_id, "response_mode", "concise")
        
        value = self.manager.get_user_preference(self.session_id, "response_mode")
        self.assertEqual(value, "concise")
    
    def test_get_user_preference_with_default(self):
        """Test getting non-existent preference returns default"""
        value = self.manager.get_user_preference(
            self.session_id, 
            "non_existent_key", 
            default="default_value"
        )
        
        self.assertEqual(value, "default_value")
    
    def test_set_multiple_preferences(self):
        """Test setting multiple user preferences"""
        preferences = {
            "response_mode": "detailed",
            "voice_name": "vi-VN-Standard-A",
            "language": "vi",
            "max_context_turns": 5
        }
        
        for key, value in preferences.items():
            self.manager.set_user_preference(self.session_id, key, value)
        
        # Verify all preferences
        for key, expected_value in preferences.items():
            actual_value = self.manager.get_user_preference(self.session_id, key)
            self.assertEqual(actual_value, expected_value)
    
    def test_update_existing_preference(self):
        """Test updating an existing preference"""
        self.manager.set_user_preference(self.session_id, "mode", "old_value")
        self.manager.set_user_preference(self.session_id, "mode", "new_value")
        
        value = self.manager.get_user_preference(self.session_id, "mode")
        self.assertEqual(value, "new_value")
    
    def test_preferences_persist_across_get_context_calls(self):
        """Test that preferences are preserved when getting context"""
        self.manager.set_user_preference(self.session_id, "test_key", "test_value")
        
        # Get context multiple times
        context1 = self.manager.get_context(self.session_id)
        context2 = self.manager.get_context(self.session_id)
        
        self.assertEqual(context1.user_preferences["test_key"], "test_value")
        self.assertEqual(context2.user_preferences["test_key"], "test_value")
    
    def test_preference_invalid_session_raises_error(self):
        """Test that preference operations on invalid session raise KeyError"""
        with self.assertRaises(KeyError):
            self.manager.set_user_preference("invalid-id", "key", "value")
        
        with self.assertRaises(KeyError):
            self.manager.get_user_preference("invalid-id", "key")


class TestContextClearing(unittest.TestCase):
    """Test context clearing for privacy - Requirement 12.8"""
    
    def setUp(self):
        """Set up test context manager and session"""
        self.manager = ConversationContextManager(
            persistence_enabled=False
        )
        self.session_id = self.manager.create_session()
    
    def test_clear_context_removes_messages(self):
        """Test that clear_context removes all messages"""
        # Add messages
        for i in range(5):
            self.manager.add_message(self.session_id, Role.USER, f"Message {i}")
        
        # Clear context
        self.manager.clear_context(self.session_id)
        
        # Verify messages are cleared
        context = self.manager.get_context(self.session_id)
        self.assertEqual(len(context.messages), 0)
    
    def test_clear_context_preserves_session(self):
        """Test that clear_context keeps session active"""
        self.manager.add_message(self.session_id, Role.USER, "Test")
        
        # Clear context
        self.manager.clear_context(self.session_id)
        
        # Session should still exist
        self.assertEqual(self.manager.get_active_session_count(), 1)
        
        # Should still be able to get context
        context = self.manager.get_context(self.session_id)
        self.assertEqual(context.session_id, self.session_id)
    
    def test_clear_context_preserves_preferences(self):
        """Test that clear_context preserves user preferences"""
        self.manager.set_user_preference(self.session_id, "test_key", "test_value")
        self.manager.add_message(self.session_id, Role.USER, "Test")
        
        # Clear context
        self.manager.clear_context(self.session_id)
        
        # Preferences should still be there
        value = self.manager.get_user_preference(self.session_id, "test_key")
        self.assertEqual(value, "test_value")
    
    def test_clear_context_updates_last_activity(self):
        """Test that clear_context updates last_activity timestamp"""
        context_before = self.manager.get_context(self.session_id)
        timestamp_before = context_before.last_activity
        
        time.sleep(0.1)
        
        self.manager.clear_context(self.session_id)
        
        context_after = self.manager.get_context(self.session_id)
        timestamp_after = context_after.last_activity
        
        self.assertGreater(timestamp_after, timestamp_before)
    
    def test_clear_context_invalid_session_raises_error(self):
        """Test that clearing non-existent session raises KeyError"""
        with self.assertRaises(KeyError):
            self.manager.clear_context("invalid-session-id")


class TestSessionDuration(unittest.TestCase):
    """Test session duration calculation - Requirement 12.12"""
    
    def setUp(self):
        """Set up test context manager"""
        self.manager = ConversationContextManager(
            persistence_enabled=False
        )
    
    def test_get_session_duration_new_session(self):
        """Test that new session has minimal duration"""
        session_id = self.manager.create_session()
        
        duration = self.manager.get_session_duration(session_id)
        
        # Should be very small (< 1 second)
        self.assertLess(duration, 1.0)
        self.assertGreaterEqual(duration, 0)
    
    def test_get_session_duration_increases_over_time(self):
        """Test that session duration increases over time"""
        session_id = self.manager.create_session()
        
        duration1 = self.manager.get_session_duration(session_id)
        
        time.sleep(0.5)
        self.manager.add_message(session_id, Role.USER, "Test")
        
        duration2 = self.manager.get_session_duration(session_id)
        
        # Duration should increase
        self.assertGreater(duration2, duration1)
        self.assertGreater(duration2, 0.4)  # At least 0.4 seconds
    
    def test_get_session_duration_invalid_session_raises_error(self):
        """Test that getting duration of invalid session raises KeyError"""
        with self.assertRaises(KeyError):
            self.manager.get_session_duration("invalid-session-id")


class TestSessionStateManagement(unittest.TestCase):
    """Test session state management"""
    
    def setUp(self):
        """Set up test context manager"""
        self.manager = ConversationContextManager(
            persistence_enabled=False
        )
    
    def test_new_session_state_is_active(self):
        """Test that newly created session is ACTIVE"""
        session_id = self.manager.create_session()
        state = self.manager.get_session_state(session_id)
        
        self.assertEqual(state, SessionState.ACTIVE)
    
    def test_end_session_changes_state_to_terminated(self):
        """Test that end_session removes session from tracking"""
        session_id = self.manager.create_session()
        
        self.manager.end_session(session_id)
        
        # Session should no longer exist
        with self.assertRaises(KeyError):
            self.manager.get_session_state(session_id)
    
    def test_end_session_removes_from_active_count(self):
        """Test that end_session decreases active count"""
        session_id = self.manager.create_session()
        self.assertEqual(self.manager.get_active_session_count(), 1)
        
        self.manager.end_session(session_id)
        
        self.assertEqual(self.manager.get_active_session_count(), 0)
    
    def test_add_message_sets_state_to_active(self):
        """Test that adding message sets state to ACTIVE"""
        session_id = self.manager.create_session()
        
        self.manager.add_message(session_id, Role.USER, "Test")
        
        state = self.manager.get_session_state(session_id)
        self.assertEqual(state, SessionState.ACTIVE)


class TestPersistence(unittest.TestCase):
    """Test optional persistence to disk - Requirement 12.10"""
    
    def setUp(self):
        """Set up temporary directory for persistence"""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up temporary directory"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_persistence_enabled_creates_directory(self):
        """Test that persistence creates storage directory"""
        persistence_dir = Path(self.temp_dir) / "sessions"
        
        manager = ConversationContextManager(
            persistence_enabled=True,
            persistence_dir=str(persistence_dir)
        )
        
        # Directory should be created
        self.assertTrue(persistence_dir.exists())
        self.assertTrue(persistence_dir.is_dir())
    
    def test_session_persisted_to_disk(self):
        """Test that session is saved to disk"""
        persistence_dir = Path(self.temp_dir) / "sessions"
        
        manager = ConversationContextManager(
            persistence_enabled=True,
            persistence_dir=str(persistence_dir)
        )
        
        session_id = manager.create_session()
        manager.add_message(session_id, Role.USER, "Test message")
        
        # Session file should exist
        session_file = persistence_dir / f"{session_id}.json"
        self.assertTrue(session_file.exists())
    
    def test_persisted_session_loaded_on_startup(self):
        """Test that persisted sessions are loaded on manager initialization"""
        persistence_dir = Path(self.temp_dir) / "sessions"
        
        # Create manager and session
        manager1 = ConversationContextManager(
            persistence_enabled=True,
            persistence_dir=str(persistence_dir)
        )
        
        session_id = manager1.create_session()
        manager1.add_message(session_id, Role.USER, "Persisted message")
        manager1.set_user_preference(session_id, "test_key", "test_value")
        
        # Create new manager instance (simulates restart)
        manager2 = ConversationContextManager(
            persistence_enabled=True,
            persistence_dir=str(persistence_dir)
        )
        
        # Session should be loaded
        context = manager2.get_context(session_id)
        self.assertEqual(len(context.messages), 1)
        self.assertEqual(context.messages[0].content, "Persisted message")
        
        # Preferences should be loaded
        value = manager2.get_user_preference(session_id, "test_key")
        self.assertEqual(value, "test_value")
    
    def test_expired_persisted_sessions_deleted_on_load(self):
        """Test that expired sessions are not loaded on startup"""
        persistence_dir = Path(self.temp_dir) / "sessions"
        
        # Create manager with very short timeout
        manager1 = ConversationContextManager(
            session_timeout_minutes=0.01,
            persistence_enabled=True,
            persistence_dir=str(persistence_dir)
        )
        
        session_id = manager1.create_session()
        manager1.add_message(session_id, Role.USER, "Test")
        
        # Wait for expiration
        time.sleep(1.0)
        
        # Create new manager (should not load expired session)
        manager2 = ConversationContextManager(
            session_timeout_minutes=0.01,
            persistence_enabled=True,
            persistence_dir=str(persistence_dir)
        )
        
        # Session should not be loaded
        self.assertEqual(manager2.get_active_session_count(), 0)
    
    def test_end_session_deletes_persisted_file(self):
        """Test that ending session removes persisted file"""
        persistence_dir = Path(self.temp_dir) / "sessions"
        
        manager = ConversationContextManager(
            persistence_enabled=True,
            persistence_dir=str(persistence_dir)
        )
        
        session_id = manager.create_session()
        session_file = persistence_dir / f"{session_id}.json"
        
        # File should exist
        self.assertTrue(session_file.exists())
        
        # End session
        manager.end_session(session_id)
        
        # File should be deleted
        self.assertFalse(session_file.exists())


class TestConcurrency(unittest.TestCase):
    """Test thread safety with concurrent access"""
    
    def test_concurrent_session_creation(self):
        """Test that concurrent session creation produces unique IDs"""
        import threading
        
        manager = ConversationContextManager(persistence_enabled=False)
        session_ids = []
        lock = threading.Lock()
        
        def create_sessions():
            for _ in range(10):
                session_id = manager.create_session()
                with lock:
                    session_ids.append(session_id)
        
        # Create multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=create_sessions)
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # All IDs should be unique
        self.assertEqual(len(session_ids), 50)
        self.assertEqual(len(set(session_ids)), 50)
    
    def test_concurrent_message_addition(self):
        """Test that concurrent message addition is thread-safe"""
        import threading
        
        manager = ConversationContextManager(persistence_enabled=False)
        session_id = manager.create_session()
        
        def add_messages(thread_id):
            for i in range(10):
                manager.add_message(
                    session_id, 
                    Role.USER, 
                    f"Thread {thread_id} Message {i}"
                )
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=add_messages, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Should have 50 messages total
        context = manager.get_context(session_id, max_turns=100)
        self.assertEqual(len(context.messages), 50)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions"""
    
    def setUp(self):
        """Set up test context manager"""
        self.manager = ConversationContextManager(
            persistence_enabled=False
        )
    
    def test_empty_message_content(self):
        """Test adding message with empty content"""
        session_id = self.manager.create_session()
        
        self.manager.add_message(session_id, Role.USER, "")
        
        context = self.manager.get_context(session_id)
        self.assertEqual(context.messages[0].content, "")
    
    def test_very_long_message_content(self):
        """Test adding very long message"""
        session_id = self.manager.create_session()
        
        long_content = "x" * 100000  # 100k characters
        self.manager.add_message(session_id, Role.USER, long_content)
        
        context = self.manager.get_context(session_id)
        self.assertEqual(len(context.messages[0].content), 100000)
    
    def test_unicode_message_content(self):
        """Test messages with Vietnamese and special characters"""
        session_id = self.manager.create_session()
        
        unicode_content = "Xin chào! 你好! こんにちは! 🎉"
        self.manager.add_message(session_id, Role.USER, unicode_content)
        
        context = self.manager.get_context(session_id)
        self.assertEqual(context.messages[0].content, unicode_content)
    
    def test_max_turns_larger_than_message_count(self):
        """Test sliding window with max_turns larger than available messages"""
        session_id = self.manager.create_session()
        
        self.manager.add_message(session_id, Role.USER, "Q1")
        self.manager.add_message(session_id, Role.ASSISTANT, "A1")
        
        # Request more turns than available
        context = self.manager.get_context(session_id, max_turns=100)
        
        # Should return all available messages
        self.assertEqual(len(context.messages), 2)
    
    def test_cleanup_with_no_sessions(self):
        """Test cleanup when there are no sessions"""
        cleaned = self.manager.cleanup_expired_sessions()
        
        self.assertEqual(cleaned, 0)
    
    def test_multiple_cleanup_calls(self):
        """Test multiple consecutive cleanup calls"""
        # Create expired session
        manager = ConversationContextManager(
            session_timeout_minutes=0.01,
            persistence_enabled=False
        )
        
        session_id = manager.create_session()
        time.sleep(1.0)
        
        # First cleanup
        cleaned1 = manager.cleanup_expired_sessions()
        self.assertEqual(cleaned1, 1)
        
        # Second cleanup (should find nothing)
        cleaned2 = manager.cleanup_expired_sessions()
        self.assertEqual(cleaned2, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
