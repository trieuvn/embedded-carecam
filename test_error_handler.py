"""
Unit tests for Error Handler Module

Tests requirements 15.5, 15.6, 15.7, 15.13, 15.14 from the specification:
- 15.5: Error categorization for different error types
- 15.6: Retry logic with exponential backoff timing
- 15.7: Fallback activation when retries exhausted
- 15.13: User notification message generation in Vietnamese
- 15.14: Recovery action selection for each error scenario
"""

import unittest
import time
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from modules.error_handler import (
    ErrorHandler,
    ErrorType,
    RecoveryActionType,
    Severity,
    ErrorContext,
    RecoveryAction
)


class TestErrorCategorization(unittest.TestCase):
    """Test Suite 1: Error categorization for different error types - Requirement 15.5"""
    
    def setUp(self):
        """Set up test error handler"""
        self.handler = ErrorHandler()
    
    def test_categorize_network_error_by_message(self):
        """Test 1.1: Network errors categorized by error message keywords"""
        context = ErrorContext(
            component="api_client",
            operation="connect"
        )
        
        # Test various network error messages
        network_errors = [
            ConnectionError("Network connection failed"),
            TimeoutError("Connection timeout"),
            Exception("Unable to reach server"),
            Exception("Connection refused")
        ]
        
        for error in network_errors:
            error_type = self.handler._categorize_error(error, context)
            self.assertEqual(
                error_type,
                ErrorType.NETWORK_ERROR,
                f"Failed to categorize: {error}"
            )
    
    def test_categorize_api_error_by_keywords(self):
        """Test 1.2: API errors categorized by API-specific keywords"""
        context = ErrorContext(
            component="gemini_api",
            operation="generate_content"
        )
        
        # Test various API error messages
        api_errors = [
            Exception("API rate limit exceeded"),
            Exception("Quota exceeded (429)"),
            Exception("Unauthorized (401)"),
            Exception("API key invalid")
        ]
        
        for error in api_errors:
            error_type = self.handler._categorize_error(error, context)
            self.assertEqual(
                error_type,
                ErrorType.API_ERROR,
                f"Failed to categorize: {error}"
            )
    
    def test_categorize_audio_capture_error_by_context(self):
        """Test 1.3: Audio capture errors categorized by component and operation context"""
        context = ErrorContext(
            component="audio_capture",
            operation="start_recording"
        )
        
        # Test audio-related errors
        audio_errors = [
            Exception("Audio device not found"),
            Exception("Microphone access denied"),
            Exception("PortAudio error"),
            Exception("Device disconnected")
        ]
        
        for error in audio_errors:
            error_type = self.handler._categorize_error(error, context)
            self.assertEqual(
                error_type,
                ErrorType.AUDIO_CAPTURE_ERROR,
                f"Failed to categorize: {error}"
            )
    
    def test_categorize_recognition_error_by_component(self):
        """Test 1.4: Recognition errors categorized by STT component name"""
        context = ErrorContext(
            component="speech_to_text",
            operation="transcribe"
        )
        
        # Test recognition-related errors
        recognition_errors = [
            Exception("Transcription failed"),
            Exception("Recognition timeout"),
            Exception("Speech not detected"),
            Exception("Invalid audio format")
        ]
        
        for error in recognition_errors:
            error_type = self.handler._categorize_error(error, context)
            self.assertEqual(
                error_type,
                ErrorType.RECOGNITION_ERROR,
                f"Failed to categorize: {error}"
            )
    
    def test_categorize_tts_error_by_component(self):
        """Test 1.5: TTS errors categorized by text-to-speech component name"""
        context = ErrorContext(
            component="text_to_speech",
            operation="synthesize"
        )
        
        # Test TTS-related errors
        tts_errors = [
            Exception("TTS synthesis failed"),
            Exception("Voice generation error"),
            Exception("Audio synthesis timeout")
        ]
        
        for error in tts_errors:
            error_type = self.handler._categorize_error(error, context)
            self.assertEqual(
                error_type,
                ErrorType.TTS_ERROR,
                f"Failed to categorize: {error}"
            )
    
    def test_categorize_unknown_error_as_default(self):
        """Test 1.6: Unknown errors categorized as UNKNOWN_ERROR"""
        context = ErrorContext(
            component="unknown_component",
            operation="unknown_operation"
        )
        
        error = Exception("Some random error")
        error_type = self.handler._categorize_error(error, context)
        
        self.assertEqual(error_type, ErrorType.UNKNOWN_ERROR)


class TestRetryLogicWithExponentialBackoff(unittest.TestCase):
    """Test Suite 2: Retry logic with exponential backoff timing - Requirement 15.6"""
    
    def setUp(self):
        """Set up test error handler"""
        self.handler = ErrorHandler()
    
    def test_network_error_retry_delays_exponential(self):
        """Test 2.1: Network error retry delays follow exponential backoff (1s, 2s, 4s)"""
        error = ConnectionError("Network connection failed")
        
        expected_delays = [1.0, 2.0, 4.0]
        
        for retry_count, expected_delay in enumerate(expected_delays):
            context = ErrorContext(
                component="api_client",
                operation="connect",
                retry_count=retry_count
            )
            
            action = self.handler.handle_error(error, context)
            
            self.assertEqual(action.action, RecoveryActionType.RETRY)
            self.assertEqual(
                action.retry_delay,
                expected_delay,
                f"Retry {retry_count}: Expected delay {expected_delay}s, got {action.retry_delay}s"
            )
    
    def test_api_error_retry_delays_exponential(self):
        """Test 2.2: API error retry delays follow exponential backoff (2s, 4s)"""
        error = Exception("API rate limit exceeded")
        
        expected_delays = [2.0, 4.0]
        
        for retry_count, expected_delay in enumerate(expected_delays):
            context = ErrorContext(
                component="gemini_api",
                operation="generate_content",
                retry_count=retry_count
            )
            
            action = self.handler.handle_error(error, context)
            
            self.assertEqual(action.action, RecoveryActionType.RETRY)
            self.assertEqual(
                action.retry_delay,
                expected_delay,
                f"Retry {retry_count}: Expected delay {expected_delay}s, got {action.retry_delay}s"
            )
    
    def test_max_retries_network_error(self):
        """Test 2.3: Network errors retry maximum 3 times before fallback"""
        error = ConnectionError("Network connection failed")
        
        # First 3 attempts should retry
        for retry_count in range(3):
            context = ErrorContext(
                component="api_client",
                operation="connect",
                retry_count=retry_count
            )
            
            action = self.handler.handle_error(error, context)
            
            self.assertEqual(
                action.action,
                RecoveryActionType.RETRY,
                f"Retry {retry_count} should return RETRY action"
            )
        
        # 4th attempt (retry_count=3) should fallback
        context = ErrorContext(
            component="api_client",
            operation="connect",
            retry_count=3
        )
        
        action = self.handler.handle_error(error, context)
        
        self.assertNotEqual(action.action, RecoveryActionType.RETRY)
    
    def test_max_retries_api_error(self):
        """Test 2.4: API errors retry maximum 2 times before fallback"""
        error = Exception("API quota exceeded")
        
        # First 2 attempts should retry
        for retry_count in range(2):
            context = ErrorContext(
                component="gemini_api",
                operation="generate_content",
                retry_count=retry_count
            )
            
            action = self.handler.handle_error(error, context)
            
            self.assertEqual(
                action.action,
                RecoveryActionType.RETRY,
                f"Retry {retry_count} should return RETRY action"
            )
        
        # 3rd attempt (retry_count=2) should fallback
        context = ErrorContext(
            component="gemini_api",
            operation="generate_content",
            retry_count=2
        )
        
        action = self.handler.handle_error(error, context)
        
        self.assertNotEqual(action.action, RecoveryActionType.RETRY)
    
    def test_tts_error_retry_once(self):
        """Test 2.5: TTS errors retry only 1 time before fallback"""
        error = Exception("TTS synthesis failed")
        
        # First attempt should retry
        context = ErrorContext(
            component="text_to_speech",
            operation="synthesize",
            retry_count=0
        )
        
        action = self.handler.handle_error(error, context)
        
        self.assertEqual(action.action, RecoveryActionType.RETRY)
        self.assertEqual(action.retry_delay, 0.5)
        
        # Second attempt (retry_count=1) should fallback
        context.retry_count = 1
        action = self.handler.handle_error(error, context)
        
        self.assertNotEqual(action.action, RecoveryActionType.RETRY)
    
    def test_exponential_backoff_formula(self):
        """Test 2.6: Exponential backoff follows formula: base_delay * (2 ^ retry_count)"""
        error = ConnectionError("Network error")
        base_delay = 1.0
        
        for retry_count in range(5):
            context = ErrorContext(
                component="api_client",
                operation="connect",
                retry_count=retry_count
            )
            
            expected_delay = base_delay * (2 ** retry_count)
            
            # Only test if within max retries
            if retry_count < 3:
                action = self.handler.handle_error(error, context)
                self.assertEqual(
                    action.retry_delay,
                    expected_delay,
                    f"Retry {retry_count}: Expected {expected_delay}s"
                )


class TestFallbackActivation(unittest.TestCase):
    """Test Suite 3: Fallback activation when retries exhausted - Requirement 15.7"""
    
    def setUp(self):
        """Set up test error handler"""
        self.handler = ErrorHandler()
    
    def test_network_error_fallback_to_offline_service(self):
        """Test 3.1: Network errors fallback to offline service after max retries"""
        error = ConnectionError("Network connection failed")
        context = ErrorContext(
            component="api_client",
            operation="connect",
            retry_count=3  # Exceeded max retries
        )
        
        action = self.handler.handle_error(error, context)
        
        self.assertEqual(action.action, RecoveryActionType.FALLBACK)
        self.assertEqual(action.fallback_component, "offline_service")
        self.assertIn("offline", action.user_message.lower())
    
    def test_api_error_fallback_to_cached_response(self):
        """Test 3.2: API errors fallback to cached response after max retries"""
        error = Exception("API rate limit exceeded")
        context = ErrorContext(
            component="gemini_api",
            operation="generate_content",
            retry_count=2  # Exceeded max retries
        )
        
        action = self.handler.handle_error(error, context)
        
        self.assertEqual(action.action, RecoveryActionType.FALLBACK)
        self.assertEqual(action.fallback_component, "cached_response")
    
    def test_recognition_error_fallback_to_vosk(self):
        """Test 3.3: Recognition errors fallback to Vosk STT after max retries"""
        error = Exception("Google STT API failed")
        context = ErrorContext(
            component="speech_to_text",
            operation="transcribe",
            retry_count=1  # Exceeded max retries for recognition
        )
        
        action = self.handler.handle_error(error, context)
        
        self.assertEqual(action.action, RecoveryActionType.FALLBACK)
        self.assertEqual(action.fallback_component, "vosk_stt")
    
    def test_tts_error_fallback_to_text_response(self):
        """Test 3.4: TTS errors fallback to text response after max retries"""
        error = Exception("TTS synthesis failed")
        context = ErrorContext(
            component="text_to_speech",
            operation="synthesize",
            retry_count=1  # Exceeded max retries for TTS
        )
        
        action = self.handler.handle_error(error, context)
        
        self.assertEqual(action.action, RecoveryActionType.FALLBACK)
        self.assertEqual(action.fallback_component, "text_response")
    
    def test_audio_capture_error_restart_component(self):
        """Test 3.5: Audio capture errors trigger component restart after max retries"""
        error = Exception("Audio device not found")
        context = ErrorContext(
            component="audio_capture",
            operation="start_recording",
            retry_count=2  # Exceeded max retries
        )
        
        action = self.handler.handle_error(error, context)
        
        self.assertEqual(action.action, RecoveryActionType.RESTART_COMPONENT)
        self.assertEqual(action.fallback_component, "audio_capture")
        self.assertIn("micro", action.user_message.lower())
    
    def test_fallback_message_not_empty(self):
        """Test 3.6: Fallback actions include non-empty user message"""
        error = ConnectionError("Network failed")
        context = ErrorContext(
            component="api_client",
            operation="connect",
            retry_count=3
        )
        
        action = self.handler.handle_error(error, context)
        
        self.assertTrue(len(action.user_message) > 0)
        self.assertIsInstance(action.user_message, str)


class TestVietnameseUserMessages(unittest.TestCase):
    """Test Suite 4: User notification message generation in Vietnamese - Requirement 15.13"""
    
    def setUp(self):
        """Set up test error handler"""
        self.handler = ErrorHandler()
    
    def test_network_error_message_in_vietnamese(self):
        """Test 4.1: Network error message is in Vietnamese"""
        message = self.handler.get_fallback_response(ErrorType.NETWORK_ERROR)
        
        # Check for Vietnamese keywords
        vietnamese_keywords = ["mạng", "kết nối", "thử"]
        self.assertTrue(
            any(keyword in message.lower() for keyword in vietnamese_keywords),
            f"Message should contain Vietnamese keywords: {message}"
        )
        
        # Message should not be empty
        self.assertTrue(len(message) > 0)
    
    def test_api_error_message_in_vietnamese(self):
        """Test 4.2: API error message is in Vietnamese"""
        message = self.handler.get_fallback_response(ErrorType.API_ERROR)
        
        # Check for Vietnamese keywords
        vietnamese_keywords = ["xin lỗi", "tỷ tỷ", "thử", "sau"]
        self.assertTrue(
            any(keyword in message.lower() for keyword in vietnamese_keywords),
            f"Message should contain Vietnamese keywords: {message}"
        )
    
    def test_audio_capture_error_message_in_vietnamese(self):
        """Test 4.3: Audio capture error message is in Vietnamese"""
        message = self.handler.get_fallback_response(ErrorType.AUDIO_CAPTURE_ERROR)
        
        # Check for Vietnamese keywords
        vietnamese_keywords = ["nghe", "âm thanh", "micro", "kiểm tra"]
        self.assertTrue(
            any(keyword in message.lower() for keyword in vietnamese_keywords),
            f"Message should contain Vietnamese keywords: {message}"
        )
    
    def test_recognition_error_message_in_vietnamese(self):
        """Test 4.4: Recognition error message is in Vietnamese"""
        message = self.handler.get_fallback_response(ErrorType.RECOGNITION_ERROR)
        
        # Check for Vietnamese keywords
        vietnamese_keywords = ["nghe", "rõ", "nói", "lại"]
        self.assertTrue(
            any(keyword in message.lower() for keyword in vietnamese_keywords),
            f"Message should contain Vietnamese keywords: {message}"
        )
    
    def test_tts_error_message_in_vietnamese(self):
        """Test 4.5: TTS error message is in Vietnamese"""
        message = self.handler.get_fallback_response(ErrorType.TTS_ERROR)
        
        # Check for Vietnamese keywords
        vietnamese_keywords = ["lỗi", "âm thanh", "phát", "thử"]
        self.assertTrue(
            any(keyword in message.lower() for keyword in vietnamese_keywords),
            f"Message should contain Vietnamese keywords: {message}"
        )
    
    def test_unknown_error_message_in_vietnamese(self):
        """Test 4.6: Unknown error message is in Vietnamese"""
        message = self.handler.get_fallback_response(ErrorType.UNKNOWN_ERROR)
        
        # Check for Vietnamese keywords
        vietnamese_keywords = ["xin lỗi", "tỷ tỷ", "lỗi", "thử"]
        self.assertTrue(
            any(keyword in message.lower() for keyword in vietnamese_keywords),
            f"Message should contain Vietnamese keywords: {message}"
        )
    
    def test_retry_messages_in_vietnamese(self):
        """Test 4.7: Retry messages are in Vietnamese"""
        retry_message_1 = self.handler._get_retry_message(ErrorType.NETWORK_ERROR, 1)
        retry_message_2 = self.handler._get_retry_message(ErrorType.NETWORK_ERROR, 2)
        
        # Check for Vietnamese keywords
        self.assertIn("thử", retry_message_1.lower())
        self.assertIn("thử", retry_message_2.lower())
        self.assertIn("lần", retry_message_2.lower())
    
    def test_fallback_messages_in_vietnamese(self):
        """Test 4.8: Fallback transition messages are in Vietnamese"""
        message = self.handler._get_fallback_message(ErrorType.NETWORK_ERROR)
        
        # Check for Vietnamese keywords
        vietnamese_keywords = ["mạng", "offline", "chế độ"]
        self.assertTrue(
            any(keyword in message.lower() for keyword in vietnamese_keywords),
            f"Message should contain Vietnamese keywords: {message}"
        )


class TestRecoveryActionSelection(unittest.TestCase):
    """Test Suite 5: Recovery action selection for each error scenario - Requirement 15.14"""
    
    def setUp(self):
        """Set up test error handler"""
        self.handler = ErrorHandler()
    
    def test_network_error_first_attempt_retry(self):
        """Test 5.1: Network error on first attempt returns RETRY action"""
        error = ConnectionError("Network connection failed")
        context = ErrorContext(
            component="api_client",
            operation="connect",
            retry_count=0
        )
        
        action = self.handler.handle_error(error, context)
        
        self.assertEqual(action.action, RecoveryActionType.RETRY)
        self.assertGreater(action.retry_delay, 0)
    
    def test_network_error_max_retries_fallback(self):
        """Test 5.2: Network error after max retries returns FALLBACK action"""
        error = ConnectionError("Network connection failed")
        context = ErrorContext(
            component="api_client",
            operation="connect",
            retry_count=3
        )
        
        action = self.handler.handle_error(error, context)
        
        self.assertEqual(action.action, RecoveryActionType.FALLBACK)
        self.assertEqual(action.fallback_component, "offline_service")
    
    def test_api_error_recovery_sequence(self):
        """Test 5.3: API error follows correct recovery sequence (retry → fallback)"""
        error = Exception("API rate limit exceeded")
        
        # First attempt: retry
        context = ErrorContext(
            component="gemini_api",
            operation="generate_content",
            retry_count=0
        )
        action = self.handler.handle_error(error, context)
        self.assertEqual(action.action, RecoveryActionType.RETRY)
        
        # Second attempt: retry
        context.retry_count = 1
        action = self.handler.handle_error(error, context)
        self.assertEqual(action.action, RecoveryActionType.RETRY)
        
        # Third attempt: fallback
        context.retry_count = 2
        action = self.handler.handle_error(error, context)
        self.assertEqual(action.action, RecoveryActionType.FALLBACK)
    
    def test_audio_capture_error_restart_component(self):
        """Test 5.4: Audio capture error triggers RESTART_COMPONENT action"""
        error = Exception("Audio device disconnected")
        context = ErrorContext(
            component="audio_capture",
            operation="start_recording",
            retry_count=2
        )
        
        action = self.handler.handle_error(error, context)
        
        self.assertEqual(action.action, RecoveryActionType.RESTART_COMPONENT)
    
    def test_tts_error_recovery_sequence(self):
        """Test 5.5: TTS error follows correct recovery sequence (retry → fallback)"""
        error = Exception("TTS synthesis failed")
        
        # First attempt: retry
        context = ErrorContext(
            component="text_to_speech",
            operation="synthesize",
            retry_count=0
        )
        action = self.handler.handle_error(error, context)
        self.assertEqual(action.action, RecoveryActionType.RETRY)
        
        # Second attempt: fallback
        context.retry_count = 1
        action = self.handler.handle_error(error, context)
        self.assertEqual(action.action, RecoveryActionType.FALLBACK)
        self.assertEqual(action.fallback_component, "text_response")
    
    def test_recognition_error_fallback_to_vosk(self):
        """Test 5.6: Recognition error fallback points to Vosk STT"""
        error = Exception("Google STT failed")
        context = ErrorContext(
            component="speech_to_text",
            operation="transcribe",
            retry_count=1
        )
        
        action = self.handler.handle_error(error, context)
        
        self.assertEqual(action.action, RecoveryActionType.FALLBACK)
        self.assertEqual(action.fallback_component, "vosk_stt")
    
    def test_unknown_error_notify_user(self):
        """Test 5.7: Unknown error notifies user when no fallback available"""
        error = Exception("Unknown error")
        context = ErrorContext(
            component="unknown_component",
            operation="unknown_operation",
            retry_count=1
        )
        
        action = self.handler.handle_error(error, context)
        
        # Should either retry or notify user
        self.assertIn(
            action.action,
            [RecoveryActionType.RETRY, RecoveryActionType.NOTIFY_USER]
        )
    
    def test_all_actions_have_user_messages(self):
        """Test 5.8: All recovery actions include user-friendly messages"""
        test_cases = [
            (ConnectionError("Network failed"), ErrorContext("api", "connect", 0)),
            (Exception("API error"), ErrorContext("gemini_api", "generate", 0)),
            (Exception("Audio error"), ErrorContext("audio_capture", "record", 0)),
            (Exception("TTS error"), ErrorContext("text_to_speech", "synthesize", 0)),
        ]
        
        for error, context in test_cases:
            action = self.handler.handle_error(error, context)
            
            self.assertIsNotNone(action.user_message)
            self.assertIsInstance(action.user_message, str)
            self.assertTrue(
                len(action.user_message) > 0,
                f"User message empty for {context.component}"
            )


class TestErrorHandlerIntegration(unittest.TestCase):
    """Integration tests for error handler functionality"""
    
    def setUp(self):
        """Set up test error handler"""
        self.handler = ErrorHandler()
    
    def test_component_registration(self):
        """Test component registration with health checks"""
        def test_health_check():
            return True
        
        self.handler.register_component("test_component", test_health_check)
        
        components = self.handler.get_registered_components()
        self.assertIn("test_component", components)
    
    def test_health_check_execution(self):
        """Test health check execution for registered components"""
        health_status = {"healthy": True}
        
        def test_health_check():
            return health_status["healthy"]
        
        self.handler.register_component("test_component", test_health_check)
        
        # Component is healthy
        self.assertTrue(self.handler.check_component_health("test_component"))
        
        # Component becomes unhealthy
        health_status["healthy"] = False
        self.assertFalse(self.handler.check_component_health("test_component"))
    
    @patch('builtins.print')
    def test_notify_user_displays_message(self, mock_print):
        """Test user notification displays Vietnamese message"""
        message = "Xin lỗi, có lỗi xảy ra"
        
        self.handler.notify_user(message, Severity.WARNING)
        
        # Should have called print with the message
        mock_print.assert_called()
        call_args = str(mock_print.call_args)
        self.assertIn(message, call_args)
    
    def test_error_logging_with_context(self):
        """Test error logging includes context information"""
        error = Exception("Test error")
        context = ErrorContext(
            component="test_component",
            operation="test_operation",
            retry_count=1,
            session_id="test-session-123"
        )
        
        # Should not raise exception
        self.handler.log_error(error, Severity.ERROR, context)


def run_tests():
    """Run all test suites"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestErrorCategorization))
    suite.addTests(loader.loadTestsFromTestCase(TestRetryLogicWithExponentialBackoff))
    suite.addTests(loader.loadTestsFromTestCase(TestFallbackActivation))
    suite.addTests(loader.loadTestsFromTestCase(TestVietnameseUserMessages))
    suite.addTests(loader.loadTestsFromTestCase(TestRecoveryActionSelection))
    suite.addTests(loader.loadTestsFromTestCase(TestErrorHandlerIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("="*70)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    import sys
    success = run_tests()
    sys.exit(0 if success else 1)
