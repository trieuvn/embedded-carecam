"""
Unit tests for ConversationManager
Tests state machine logic, transitions, and hardware constraint enforcement
"""

import unittest
import time
import logging
from unittest.mock import Mock, MagicMock, call
from modules.conversation_manager import ConversationManager, ConversationState


class TestConversationManager(unittest.TestCase):
    """Test suite for ConversationManager"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create mock CareCam controller
        self.mock_controller = Mock()
        self.mock_controller.click_mic_button = Mock(return_value=True)
        self.mock_controller.click_speaker_button = Mock(return_value=True)
        
        # Create ConversationManager instance
        self.manager = ConversationManager(self.mock_controller)
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
    
    def tearDown(self):
        """Clean up after tests"""
        # Force back to default state
        self.manager.force_default_state()
    
    def test_initial_state_is_default(self):
        """Test that initial state is DEFAULT_STATE"""
        self.assertEqual(self.manager.get_current_state(), ConversationState.DEFAULT_STATE)
    
    def test_wake_word_detected_transitions_to_speaking(self):
        """
        Requirement 3.2: WHEN Wake_Word_Detector detects "Tỷ Tỷ", 
        THE Conversation_Manager SHALL transition to Speaking_State
        """
        # Initial state should be DEFAULT
        self.assertEqual(self.manager.get_current_state(), ConversationState.DEFAULT_STATE)
        
        # Wake word detected
        success = self.manager.on_wake_word_detected()
        
        # Should transition to SPEAKING_STATE
        self.assertTrue(success)
        self.assertEqual(self.manager.get_current_state(), ConversationState.SPEAKING_STATE)
        
        # Should have clicked mic button (to enable mic, disable speaker)
        self.mock_controller.click_mic_button.assert_called()
    
    def test_acknowledgment_complete_transitions_to_listening(self):
        """
        Requirement 3.5: WHEN acknowledgment "Dạ" ends, 
        THE Conversation_Manager SHALL transition to Listening_State
        """
        # Start in SPEAKING state
        self.manager.on_wake_word_detected()
        self.assertEqual(self.manager.get_current_state(), ConversationState.SPEAKING_STATE)
        
        # Acknowledgment complete
        success = self.manager.on_acknowledgment_complete()
        
        # Should transition to LISTENING_STATE
        self.assertTrue(success)
        self.assertEqual(self.manager.get_current_state(), ConversationState.LISTENING_STATE)
        
        # Should have clicked speaker button (to enable speaker, disable mic)
        self.mock_controller.click_speaker_button.assert_called()
    
    def test_user_input_ready_transitions_to_speaking(self):
        """
        Requirement 3.9: WHEN processing complete, 
        THE Conversation_Manager SHALL transition to Speaking_State
        """
        # Start in LISTENING state
        self.manager.on_wake_word_detected()
        self.manager.on_acknowledgment_complete()
        self.assertEqual(self.manager.get_current_state(), ConversationState.LISTENING_STATE)
        
        # User input ready
        success = self.manager.on_user_input_ready()
        
        # Should transition to SPEAKING_STATE
        self.assertTrue(success)
        self.assertEqual(self.manager.get_current_state(), ConversationState.SPEAKING_STATE)
    
    def test_response_complete_transitions_to_default(self):
        """
        Requirement 3.10: WHEN response playback completes, 
        THE Conversation_Manager SHALL transition to Default_State
        """
        # Start in SPEAKING state
        self.manager.on_wake_word_detected()
        self.assertEqual(self.manager.get_current_state(), ConversationState.SPEAKING_STATE)
        
        # Response complete
        success = self.manager.on_response_complete()
        
        # Should transition to DEFAULT_STATE
        self.assertTrue(success)
        self.assertEqual(self.manager.get_current_state(), ConversationState.DEFAULT_STATE)
    
    def test_full_conversation_flow(self):
        """
        Test complete conversation flow:
        DEFAULT → SPEAKING → LISTENING → SPEAKING → DEFAULT
        """
        # Start in DEFAULT
        self.assertEqual(self.manager.get_current_state(), ConversationState.DEFAULT_STATE)
        
        # Wake word detected → SPEAKING
        self.manager.on_wake_word_detected()
        self.assertEqual(self.manager.get_current_state(), ConversationState.SPEAKING_STATE)
        
        # Acknowledgment complete → LISTENING
        self.manager.on_acknowledgment_complete()
        self.assertEqual(self.manager.get_current_state(), ConversationState.LISTENING_STATE)
        
        # User input ready → SPEAKING
        self.manager.on_user_input_ready()
        self.assertEqual(self.manager.get_current_state(), ConversationState.SPEAKING_STATE)
        
        # Response complete → DEFAULT
        self.manager.on_response_complete()
        self.assertEqual(self.manager.get_current_state(), ConversationState.DEFAULT_STATE)
    
    def test_mic_speaker_exclusivity_speaking_state(self):
        """
        Requirement 3.3: WHILE in Speaking_State, 
        THE Conversation_Manager SHALL enable mic and disable speaker
        
        Requirement 3.11: THE Conversation_Manager SHALL ensure 
        mic and speaker not on simultaneously
        """
        # Transition to SPEAKING state
        self.manager.on_wake_word_detected()
        
        # Should have called click_mic_button (which disables speaker due to hardware)
        self.mock_controller.click_mic_button.assert_called()
        
        # Verify exclusivity
        self.assertTrue(self.manager.ensure_mic_speaker_exclusivity())
    
    def test_mic_speaker_exclusivity_listening_state(self):
        """
        Requirement 3.6: WHILE in Listening_State, 
        THE Conversation_Manager SHALL enable speaker and disable mic
        
        Requirement 3.11: THE Conversation_Manager SHALL ensure 
        mic and speaker not on simultaneously
        """
        # Transition to LISTENING state
        self.manager.on_wake_word_detected()
        self.manager.on_acknowledgment_complete()
        
        # Should have called click_speaker_button (which disables mic due to hardware)
        self.mock_controller.click_speaker_button.assert_called()
        
        # Verify exclusivity
        self.assertTrue(self.manager.ensure_mic_speaker_exclusivity())
    
    def test_state_transition_logging(self):
        """
        Requirement 3.7: THE Conversation_Manager SHALL log all state transitions
        """
        # This test verifies that _log_state_transition is called
        # The actual logging is verified by manual inspection of logs
        
        with self.assertLogs(level='INFO') as log_context:
            self.manager.on_wake_word_detected()
            
            # Check that transition was logged
            self.assertTrue(any('State transition' in msg for msg in log_context.output))
            self.assertTrue(any('default -> speaking' in msg for msg in log_context.output))
    
    def test_force_default_state(self):
        """
        Requirement 4.8: THE Conversation_Manager SHALL provide 
        method force_default_state() to reset to Default_State
        """
        # Go to LISTENING state
        self.manager.on_wake_word_detected()
        self.manager.on_acknowledgment_complete()
        self.assertEqual(self.manager.get_current_state(), ConversationState.LISTENING_STATE)
        
        # Force default state
        success = self.manager.force_default_state()
        
        self.assertTrue(success)
        self.assertEqual(self.manager.get_current_state(), ConversationState.DEFAULT_STATE)
    
    def test_get_current_state(self):
        """
        Requirement 4.7: THE Conversation_Manager SHALL provide 
        method get_current_state() returning current state
        """
        # Test in different states
        self.assertEqual(self.manager.get_current_state(), ConversationState.DEFAULT_STATE)
        
        self.manager.on_wake_word_detected()
        self.assertEqual(self.manager.get_current_state(), ConversationState.SPEAKING_STATE)
        
        self.manager.on_acknowledgment_complete()
        self.assertEqual(self.manager.get_current_state(), ConversationState.LISTENING_STATE)
    
    def test_retry_logic_on_button_failure(self):
        """
        Requirement 4.5: IF CareCam_Controller fails to click button, 
        THEN retry up to 3 times
        """
        # Mock controller to fail first 2 times, succeed on 3rd
        self.mock_controller.click_mic_button = Mock(side_effect=[False, False, True])
        
        # Try to transition to SPEAKING
        success = self.manager.on_wake_word_detected()
        
        # Should succeed after retries
        self.assertTrue(success)
        self.assertEqual(self.mock_controller.click_mic_button.call_count, 3)
    
    def test_fail_after_max_retries(self):
        """
        Requirement 4.6: IF retry 3 times fails, 
        THEN log error and return to Default_State
        """
        # Mock controller to always fail
        self.mock_controller.click_mic_button = Mock(return_value=False)
        
        # Try to transition to SPEAKING
        success = self.manager.on_wake_word_detected()
        
        # Should fail
        self.assertFalse(success)
        
        # Should have tried MAX_BUTTON_RETRIES times
        self.assertEqual(
            self.mock_controller.click_mic_button.call_count, 
            ConversationManager.MAX_BUTTON_RETRIES
        )
    
    def test_state_change_callbacks(self):
        """Test that state change callbacks are invoked"""
        callback = Mock()
        self.manager.register_state_change_callback(callback)
        
        # Transition to SPEAKING
        self.manager.on_wake_word_detected()
        
        # Callback should have been called
        callback.assert_called_once_with(
            ConversationState.DEFAULT_STATE,
            ConversationState.SPEAKING_STATE
        )
    
    def test_is_in_conversation(self):
        """Test is_in_conversation helper method"""
        # DEFAULT state - not in conversation
        self.assertFalse(self.manager.is_in_conversation())
        
        # SPEAKING state - in conversation
        self.manager.on_wake_word_detected()
        self.assertTrue(self.manager.is_in_conversation())
        
        # LISTENING state - in conversation
        self.manager.on_acknowledgment_complete()
        self.assertTrue(self.manager.is_in_conversation())
        
        # Back to DEFAULT - not in conversation
        self.manager.force_default_state()
        self.assertFalse(self.manager.is_in_conversation())
    
    def test_silence_timeout_configuration(self):
        """
        Requirement 3.8: Implement timeout logic for silence detection (3 seconds)
        """
        # Verify timeout is set correctly
        self.assertEqual(self.manager.SILENCE_TIMEOUT, 3.0)
    
    def test_conversation_state_enum(self):
        """Test ConversationState enum values"""
        self.assertEqual(ConversationState.DEFAULT_STATE.value, "default")
        self.assertEqual(ConversationState.SPEAKING_STATE.value, "speaking")
        self.assertEqual(ConversationState.LISTENING_STATE.value, "listening")
    
    def test_sequential_transition_order(self):
        """
        Requirement 3.12: WHEN transitioning from Speaking to Listening,
        disable mic before enabling speaker
        
        Requirement 3.13: WHEN transitioning from Listening to Speaking,
        disable speaker before enabling mic
        
        Note: Hardware constraint automatically enforces this, but we verify
        the correct button is clicked
        """
        # SPEAKING → LISTENING: Should click speaker button
        self.manager.on_wake_word_detected()  # Go to SPEAKING
        self.mock_controller.click_speaker_button.reset_mock()
        
        self.manager.on_acknowledgment_complete()  # SPEAKING → LISTENING
        self.mock_controller.click_speaker_button.assert_called()
        
        # LISTENING → SPEAKING: Should click mic button
        self.mock_controller.click_mic_button.reset_mock()
        
        self.manager.on_user_input_ready()  # LISTENING → SPEAKING
        self.mock_controller.click_mic_button.assert_called()


class TestConversationStateEnum(unittest.TestCase):
    """Test ConversationState enum"""
    
    def test_enum_values(self):
        """Test that enum has correct values"""
        self.assertEqual(ConversationState.DEFAULT_STATE.value, "default")
        self.assertEqual(ConversationState.SPEAKING_STATE.value, "speaking")
        self.assertEqual(ConversationState.LISTENING_STATE.value, "listening")
    
    def test_enum_members(self):
        """Test that enum has exactly 3 members"""
        self.assertEqual(len(ConversationState), 3)


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)
