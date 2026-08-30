"""
Unit tests for ConversationManager silence detection and timeout logic
Tests Requirements 5.1-5.7 for silence detection during LISTENING_STATE
"""

import unittest
import time
import logging
import numpy as np
from unittest.mock import Mock, MagicMock, patch
from modules.conversation_manager import ConversationManager, ConversationState


class MockAudioSource:
    """Mock audio source for testing"""
    
    def __init__(self, audio_frames=None):
        """
        Initialize mock audio source
        
        Args:
            audio_frames: List of audio frames to return (bytes)
        """
        self.audio_frames = audio_frames or []
        self.current_index = 0
    
    def read(self, frame_size, exception_on_overflow=False):
        """
        Mock read method to simulate pyaudio stream
        
        Args:
            frame_size: Number of samples to read
            exception_on_overflow: Ignored for mock
            
        Returns:
            Audio frame as bytes
        """
        if self.current_index >= len(self.audio_frames):
            # Return silence when no more frames
            return np.zeros(frame_size, dtype=np.int16).tobytes()
        
        frame = self.audio_frames[self.current_index]
        self.current_index += 1
        return frame
    
    def reset(self):
        """Reset to beginning of frames"""
        self.current_index = 0


class TestSilenceDetection(unittest.TestCase):
    """Test suite for silence detection and timeout logic"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create mock CareCam controller
        self.mock_controller = Mock()
        self.mock_controller.click_mic_button = Mock(return_value=True)
        self.mock_controller.click_speaker_button = Mock(return_value=True)
        
        # Create audio frames for testing
        self.silent_frame = np.zeros(1024, dtype=np.int16).tobytes()
        self.noisy_frame = (np.random.randint(-1000, 1000, 1024, dtype=np.int16)).tobytes()
        self.loud_frame = (np.random.randint(-10000, 10000, 1024, dtype=np.int16)).tobytes()
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
    
    def test_silence_threshold_constant(self):
        """
        Requirement 5.2: THE Conversation_Manager SHALL detect silence when 
        audio energy below SILENCE_THRESHOLD
        """
        manager = ConversationManager(self.mock_controller)
        self.assertEqual(manager.SILENCE_THRESHOLD, 0.02)
    
    def test_silence_timeout_constant(self):
        """
        Requirement 5.2: WHEN audio energy below threshold for 3 seconds,
        THE Conversation_Manager SHALL end recording
        """
        manager = ConversationManager(self.mock_controller)
        self.assertEqual(manager.SILENCE_TIMEOUT, 3.0)
    
    def test_max_recording_duration_constant(self):
        """
        Requirement 5.6: IF no audio in MAX_RECORDING_DURATION (10 seconds),
        THEN timeout and return to DEFAULT_STATE
        """
        manager = ConversationManager(self.mock_controller)
        self.assertEqual(manager.MAX_RECORDING_DURATION, 10.0)
    
    def test_audio_energy_calculation_silent(self):
        """
        Requirement 5.1: THE Conversation_Manager SHALL monitor audio level
        during LISTENING_STATE
        """
        manager = ConversationManager(self.mock_controller)
        
        # Calculate energy of silent frame
        energy = manager._calculate_audio_energy(self.silent_frame)
        
        # Silent frame should have very low energy
        self.assertLess(energy, 0.01)
        self.assertGreaterEqual(energy, 0.0)
    
    def test_audio_energy_calculation_loud(self):
        """Test that loud audio has higher energy than silent audio"""
        manager = ConversationManager(self.mock_controller)
        
        # Calculate energies
        silent_energy = manager._calculate_audio_energy(self.silent_frame)
        loud_energy = manager._calculate_audio_energy(self.loud_frame)
        
        # Loud should have higher energy than silent
        self.assertGreater(loud_energy, silent_energy)
        self.assertGreater(loud_energy, manager.SILENCE_THRESHOLD)
    
    def test_audio_source_can_be_set(self):
        """Test that audio source can be set after initialization"""
        manager = ConversationManager(self.mock_controller)
        
        mock_source = MockAudioSource()
        manager.set_audio_source(mock_source)
        
        self.assertIsNotNone(manager._audio_source)
    
    def test_get_audio_energy(self):
        """Test that audio energy can be retrieved"""
        manager = ConversationManager(self.mock_controller)
        
        # Initially should be 0
        self.assertEqual(manager.get_audio_energy(), 0.0)
        
        # After processing audio, should update
        manager._last_audio_energy = 0.05
        self.assertEqual(manager.get_audio_energy(), 0.05)
    
    def test_silence_detected_callback_registration(self):
        """Test that silence detected callback can be registered"""
        manager = ConversationManager(self.mock_controller)
        
        callback = Mock()
        manager.register_silence_detected_callback(callback)
        
        self.assertIsNotNone(manager._on_silence_detected_callback)
    
    def test_timeout_callback_registration(self):
        """
        Requirement 5.7: WHEN timeout occurs, play timeout message
        """
        manager = ConversationManager(self.mock_controller)
        
        callback = Mock()
        manager.register_timeout_callback(callback)
        
        self.assertIsNotNone(manager._on_timeout_callback)
    
    def test_get_recorded_audio_empty(self):
        """Test getting recorded audio when buffer is empty"""
        manager = ConversationManager(self.mock_controller)
        
        audio = manager.get_recorded_audio()
        self.assertIsNone(audio)
    
    def test_get_recorded_audio_with_data(self):
        """Test getting recorded audio when buffer has data"""
        manager = ConversationManager(self.mock_controller)
        
        # Add some audio to buffer
        manager._audio_buffer = [self.loud_frame, self.noisy_frame]
        
        audio = manager.get_recorded_audio()
        self.assertIsNotNone(audio)
        self.assertEqual(len(audio), len(self.loud_frame) + len(self.noisy_frame))
    
    def test_audio_monitoring_starts_on_listening(self):
        """
        Requirement 5.1: Monitor audio during LISTENING_STATE
        Requirement 5.4: Send audio to STT when silence detected
        """
        # Create manager with mock audio source
        frames = [self.loud_frame] * 5 + [self.silent_frame] * 100
        mock_source = MockAudioSource(frames)
        manager = ConversationManager(self.mock_controller, mock_source)
        
        # Transition to LISTENING state
        manager.on_wake_word_detected()
        manager.on_acknowledgment_complete()
        
        # Verify monitoring started
        self.assertTrue(manager._is_monitoring)
    
    def test_audio_monitoring_stops_on_user_input_ready(self):
        """Test that audio monitoring stops when user input is ready"""
        mock_source = MockAudioSource([self.loud_frame] * 10)
        manager = ConversationManager(self.mock_controller, mock_source)
        
        # Start monitoring
        manager.on_wake_word_detected()
        manager.on_acknowledgment_complete()
        self.assertTrue(manager._is_monitoring)
        
        # Stop monitoring
        manager.on_user_input_ready()
        time.sleep(0.1)  # Give thread time to stop
        
        self.assertFalse(manager._is_monitoring)
    
    def test_silence_detected_triggers_callback(self):
        """
        Requirement 5.2: Detect silence when energy below threshold for 3 seconds
        Requirement 5.4: Send audio to STT when silence detected
        """
        # Create audio: loud frames then silent frames
        # With small SILENCE_TIMEOUT for faster testing
        frames = [self.loud_frame] * 3 + [self.silent_frame] * 100
        mock_source = MockAudioSource(frames)
        manager = ConversationManager(self.mock_controller, mock_source)
        
        # Override timeout for faster testing
        manager.SILENCE_TIMEOUT = 0.5
        
        # Register callback
        callback = Mock()
        manager.register_silence_detected_callback(callback)
        
        # Start monitoring
        manager.on_wake_word_detected()
        manager.on_acknowledgment_complete()
        
        # Wait for silence detection
        time.sleep(1.5)
        
        # Callback should have been called
        callback.assert_called_once()
    
    def test_recording_timeout_triggers_callback(self):
        """
        Requirement 5.6: IF no audio in MAX_RECORDING_DURATION, timeout
        Requirement 5.7: Play timeout message when timeout occurs
        """
        # Create all silent frames
        frames = [self.silent_frame] * 200
        mock_source = MockAudioSource(frames)
        manager = ConversationManager(self.mock_controller, mock_source)
        
        # Override timeout for faster testing
        manager.MAX_RECORDING_DURATION = 0.5
        
        # Register callback
        callback = Mock()
        manager.register_timeout_callback(callback)
        
        # Start monitoring
        manager.on_wake_word_detected()
        manager.on_acknowledgment_complete()
        
        # Wait for timeout
        time.sleep(1.5)
        
        # Callback should have been called
        callback.assert_called_once()
    
    def test_force_default_stops_monitoring(self):
        """Test that forcing default state stops audio monitoring"""
        mock_source = MockAudioSource([self.loud_frame] * 100)
        manager = ConversationManager(self.mock_controller, mock_source)
        
        # Start monitoring
        manager.on_wake_word_detected()
        manager.on_acknowledgment_complete()
        self.assertTrue(manager._is_monitoring)
        
        # Force default
        manager.force_default_state()
        time.sleep(0.1)
        
        self.assertFalse(manager._is_monitoring)
    
    def test_audio_buffer_stores_frames(self):
        """
        Requirement 5.4: Send audio to STT when silence detected
        (Audio must be buffered during recording)
        """
        frames = [self.loud_frame] * 5
        mock_source = MockAudioSource(frames)
        manager = ConversationManager(self.mock_controller, mock_source)
        
        # Override timeout for faster testing
        manager.SILENCE_TIMEOUT = 0.3
        
        # Start monitoring
        manager.on_wake_word_detected()
        manager.on_acknowledgment_complete()
        
        # Wait for some frames to be processed
        time.sleep(0.5)
        
        # Stop monitoring
        manager._stop_audio_monitoring()
        
        # Audio buffer should have frames
        self.assertGreater(len(manager._audio_buffer), 0)
    
    def test_conversation_manager_with_no_audio_source(self):
        """Test that manager works without audio source (graceful degradation)"""
        manager = ConversationManager(self.mock_controller)
        
        # Should initialize successfully
        self.assertIsNone(manager._audio_source)
        
        # Transitions should still work
        manager.on_wake_word_detected()
        self.assertEqual(manager.get_current_state(), ConversationState.SPEAKING_STATE)
        
        # Attempting to start monitoring should log warning but not crash
        manager.on_acknowledgment_complete()
        self.assertEqual(manager.get_current_state(), ConversationState.LISTENING_STATE)


class TestSilenceDetectionIntegration(unittest.TestCase):
    """Integration tests for silence detection in full conversation flow"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_controller = Mock()
        self.mock_controller.click_mic_button = Mock(return_value=True)
        self.mock_controller.click_speaker_button = Mock(return_value=True)
        
        # Create audio frames
        self.silent_frame = np.zeros(1024, dtype=np.int16).tobytes()
        self.loud_frame = (np.random.randint(-10000, 10000, 1024, dtype=np.int16)).tobytes()
        
        logging.basicConfig(level=logging.INFO)
    
    def test_full_conversation_with_silence_detection(self):
        """
        Test full conversation flow with silence detection:
        DEFAULT → SPEAKING → LISTENING (with silence) → SPEAKING → DEFAULT
        """
        # Create audio: loud then silent
        frames = [self.loud_frame] * 3 + [self.silent_frame] * 100
        mock_source = MockAudioSource(frames)
        manager = ConversationManager(self.mock_controller, mock_source)
        manager.SILENCE_TIMEOUT = 0.3
        
        # Track state transitions
        states = []
        def track_state(old, new):
            states.append((old, new))
        manager.register_state_change_callback(track_state)
        
        # Register silence callback
        silence_detected = Mock()
        manager.register_silence_detected_callback(silence_detected)
        
        # Start conversation
        manager.on_wake_word_detected()
        self.assertEqual(manager.get_current_state(), ConversationState.SPEAKING_STATE)
        
        # Acknowledgment complete → LISTENING
        manager.on_acknowledgment_complete()
        self.assertEqual(manager.get_current_state(), ConversationState.LISTENING_STATE)
        
        # Wait for silence detection
        time.sleep(1.0)
        
        # Silence should have been detected
        silence_detected.assert_called_once()
        
        # Should have audio recorded
        audio = manager.get_recorded_audio()
        self.assertIsNotNone(audio)
    
    def test_timeout_with_no_audio(self):
        """
        Requirement 5.7: When timeout with no audio, play message:
        "Tỷ Tỷ không nghe rõ. Bạn nói lại được không?"
        """
        # All silent frames
        frames = [self.silent_frame] * 100
        mock_source = MockAudioSource(frames)
        manager = ConversationManager(self.mock_controller, mock_source)
        manager.MAX_RECORDING_DURATION = 0.3
        
        # Register timeout callback
        timeout_callback = Mock()
        manager.register_timeout_callback(timeout_callback)
        
        # Start conversation
        manager.on_wake_word_detected()
        manager.on_acknowledgment_complete()
        
        # Wait for timeout
        time.sleep(1.0)
        
        # Timeout callback should have been called
        timeout_callback.assert_called_once()


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
