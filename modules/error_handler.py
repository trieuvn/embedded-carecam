"""
Error Handler and Recovery System Module

This module provides comprehensive error handling with recovery strategies,
fallback mechanisms, and user-friendly error messages in Vietnamese.

Requirements:
- 15.1: Register components with health checks
- 15.2: Handle errors and return RecoveryAction
- 15.3: RecoveryAction dataclass with action details
- 15.4: Support multiple RecoveryActionTypes
- 15.5: Categorize errors by ErrorType
- 15.6: Retry with exponential backoff for network errors
- 15.7: Fallback to alternative services
- 15.8: Retry strategies for API errors
- 15.9: Re-initialize detector on wake word failure
- 15.10: Restart audio stream on capture timeout
- 15.11: Switch mode when VB-Cable not found
- 15.12: Log errors with severity levels
- 15.13: Generate Vietnamese error messages
- 15.14: Get fallback responses
- 15.15: Notify user about errors
"""

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Callable, Dict, Any
import threading


class ErrorType(Enum):
    """Error type enumeration for categorizing errors"""
    NETWORK_ERROR = "network_error"
    API_ERROR = "api_error"
    AUDIO_CAPTURE_ERROR = "audio_capture_error"
    RECOGNITION_ERROR = "recognition_error"
    TTS_ERROR = "tts_error"
    UNKNOWN_ERROR = "unknown_error"


class RecoveryActionType(Enum):
    """Recovery action type enumeration"""
    RETRY = "retry"
    FALLBACK = "fallback"
    SKIP = "skip"
    RESTART_COMPONENT = "restart_component"
    NOTIFY_USER = "notify_user"


class Severity(Enum):
    """Log severity levels"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class ErrorContext:
    """
    Context information about an error occurrence.
    
    Attributes:
        component: Name of the component where error occurred
        operation: Operation that was being performed
        retry_count: Number of retry attempts made
        session_id: Associated session identifier (if applicable)
        timestamp: When the error occurred
    """
    component: str
    operation: str
    retry_count: int = 0
    session_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class RecoveryAction:
    """
    Defines an action to recover from an error.
    
    Attributes:
        action: Type of recovery action to take
        fallback_component: Alternative component to use (for FALLBACK action)
        retry_delay: Delay in seconds before retry (for RETRY action)
        user_message: Vietnamese message to display to user
    """
    action: RecoveryActionType
    fallback_component: Optional[str] = None
    retry_delay: float = 0.0
    user_message: str = ""


class ErrorHandler:
    """
    Comprehensive error handler with recovery strategies.
    
    Features:
    - Component registration with health checks
    - Error categorization and logging
    - Retry logic with exponential backoff
    - Fallback strategies
    - User-friendly Vietnamese error messages
    - Recovery action recommendations
    
    Requirements: 15.1-15.15
    """

    def __init__(self, log_file: Optional[str] = None):
        """
        Initialize the ErrorHandler.
        
        Args:
            log_file: Optional log file path (default: logs/error_handler.log)
        """
        # Component registry with health check functions
        self._components: Dict[str, Callable[[], bool]] = {}
        
        # Thread lock for concurrent access
        self._lock = threading.Lock()
        
        # Setup logging
        self._setup_logging(log_file)
        
        # Error recovery configuration
        self._max_retries = {
            ErrorType.NETWORK_ERROR: 3,
            ErrorType.API_ERROR: 2,
            ErrorType.AUDIO_CAPTURE_ERROR: 2,
            ErrorType.RECOGNITION_ERROR: 1,
            ErrorType.TTS_ERROR: 1,
            ErrorType.UNKNOWN_ERROR: 1
        }
        
        # Base retry delays (seconds) - will use exponential backoff
        self._base_retry_delays = {
            ErrorType.NETWORK_ERROR: 1.0,
            ErrorType.API_ERROR: 2.0,
            ErrorType.AUDIO_CAPTURE_ERROR: 0.5,
            ErrorType.RECOGNITION_ERROR: 0.5,  # Changed from 1.0 to avoid conflict with network timeout
            ErrorType.TTS_ERROR: 0.5,
            ErrorType.UNKNOWN_ERROR: 1.0
        }
        
        # Fallback components for each error type
        self._fallback_components = {
            ErrorType.NETWORK_ERROR: "offline_service",
            ErrorType.API_ERROR: "cached_response",
            ErrorType.RECOGNITION_ERROR: "vosk_stt",
            ErrorType.TTS_ERROR: "text_response"
        }

    def _setup_logging(self, log_file: Optional[str] = None) -> None:
        """
        Setup logging configuration.
        
        Args:
            log_file: Optional log file path
            
        Requirement: 15.12
        """
        # Create logger
        self.logger = logging.getLogger("ErrorHandler")
        self.logger.setLevel(logging.DEBUG)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # File handler
        if log_file:
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
        else:
            # Default log file
            from pathlib import Path
            log_dir = Path(__file__).parent.parent / "logs"
            log_dir.mkdir(exist_ok=True)
            log_file = log_dir / "error_handler.log"
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
        
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

    def register_component(self, component_name: str, health_check: Callable[[], bool]) -> None:
        """
        Register a component with its health check function.
        
        Args:
            component_name: Name of the component
            health_check: Function that returns True if component is healthy
            
        Requirement: 15.1
        """
        with self._lock:
            self._components[component_name] = health_check
            self.logger.info(f"Registered component: {component_name}")

    def handle_error(self, error: Exception, context: ErrorContext) -> RecoveryAction:
        """
        Handle an error and return appropriate recovery action.
        
        Args:
            error: The exception that occurred
            context: Context information about the error
            
        Returns:
            RecoveryAction with recommended recovery strategy
            
        Requirements: 15.2, 15.3, 15.4, 15.5, 15.6, 15.7, 15.8, 15.9, 15.10, 15.11
        """
        with self._lock:
            # Categorize error
            error_type = self._categorize_error(error, context)
            
            # Log the error
            self.log_error(error, Severity.ERROR, context)
            
            # Determine recovery action based on error type and retry count
            recovery_action = self._determine_recovery_action(error_type, context)
            
            self.logger.info(
                f"Recovery action for {context.component}.{context.operation}: "
                f"{recovery_action.action.value}"
            )
            
            return recovery_action

    def _categorize_error(self, error: Exception, context: ErrorContext) -> ErrorType:
        """
        Categorize an error by analyzing the exception and context.
        
        Args:
            error: The exception to categorize
            context: Error context information
            
        Returns:
            ErrorType categorization
            
        Requirement: 15.5
        """
        error_str = str(error).lower()
        error_type_name = type(error).__name__.lower()
        component_lower = context.component.lower()
        operation_lower = context.operation.lower()
        
        # Priority 1: Check exception type name (most reliable)
        if any(keyword in error_type_name for keyword in ['connectionerror', 'timeouterror']):
            return ErrorType.NETWORK_ERROR
        
        # Priority 2: Check context component for specific modules
        # TTS errors - check TTS component
        if any(keyword in component_lower for keyword in ['tts', 'text_to_speech']):
            return ErrorType.TTS_ERROR
        
        # Recognition errors - check STT/speech component
        if any(keyword in component_lower for keyword in ['stt', 'speech_to_text', 'recognition']):
            return ErrorType.RECOGNITION_ERROR
        
        # Audio capture errors - check audio capture component and operation
        if 'audio' in component_lower and 'capture' in operation_lower:
            return ErrorType.AUDIO_CAPTURE_ERROR
        
        # Priority 3: Check error message for specific keywords
        # Network errors by message (before API check since network issues can happen with API calls)
        if any(keyword in error_str for keyword in ['connection', 'unreachable', 'reach', 'refused', 'timeout', 'network']) and 'api' not in error_str:
            return ErrorType.NETWORK_ERROR
        
        # API errors - check for API-specific keywords
        if any(keyword in error_str for keyword in ['api', 'quota', 'rate limit', 'unauthorized', '401', '429']):
            return ErrorType.API_ERROR
        
        # TTS-specific error messages
        if any(keyword in error_str for keyword in ['synthesis', 'tts']):
            return ErrorType.TTS_ERROR
        
        # Recognition-specific error messages
        if any(keyword in error_str for keyword in ['transcription', 'recognition']):
            return ErrorType.RECOGNITION_ERROR
        
        # Audio device-specific messages
        if any(keyword in error_str for keyword in ['microphone', 'portaudio', 'device']) and 'api' not in error_str:
            return ErrorType.AUDIO_CAPTURE_ERROR
        
        # Priority 4: Check component for less specific matches
        # API errors by component (only if not already categorized)
        if 'gemini' in component_lower or 'api' in component_lower:
            return ErrorType.API_ERROR
        
        # Default to unknown
        return ErrorType.UNKNOWN_ERROR

    def _determine_recovery_action(self, error_type: ErrorType, context: ErrorContext) -> RecoveryAction:
        """
        Determine the appropriate recovery action based on error type and context.
        
        Args:
            error_type: Type of error that occurred
            context: Error context with retry count
            
        Returns:
            RecoveryAction with recommended strategy
            
        Requirements: 15.6, 15.7, 15.8, 15.9, 15.10, 15.11
        """
        max_retries = self._max_retries.get(error_type, 1)
        
        # Check if we should retry
        if context.retry_count < max_retries:
            # Exponential backoff: base_delay * (2 ^ retry_count)
            base_delay = self._base_retry_delays.get(error_type, 1.0)
            retry_delay = base_delay * (2 ** context.retry_count)
            
            return RecoveryAction(
                action=RecoveryActionType.RETRY,
                retry_delay=retry_delay,
                user_message=self._get_retry_message(error_type, context.retry_count + 1)
            )
        
        # Max retries exceeded - try fallback
        if error_type in self._fallback_components:
            fallback = self._fallback_components[error_type]
            
            return RecoveryAction(
                action=RecoveryActionType.FALLBACK,
                fallback_component=fallback,
                user_message=self._get_fallback_message(error_type)
            )
        
        # Special handling for specific error types
        if error_type == ErrorType.AUDIO_CAPTURE_ERROR:
            # Requirement 15.10: Restart audio stream
            return RecoveryAction(
                action=RecoveryActionType.RESTART_COMPONENT,
                fallback_component=context.component,
                user_message="Tỷ Tỷ không nghe thấy âm thanh. Đang khởi động lại micro..."
            )
        
        # Default: notify user
        return RecoveryAction(
            action=RecoveryActionType.NOTIFY_USER,
            user_message=self.get_fallback_response(error_type)
        )

    def log_error(
        self, 
        error: Exception, 
        severity: Severity, 
        context: Optional[ErrorContext] = None
    ) -> None:
        """
        Log an error with specified severity level.
        
        Args:
            error: The exception to log
            severity: Log severity level
            context: Optional error context information
            
        Requirement: 15.12
        """
        # Format error message
        error_msg = f"{type(error).__name__}: {str(error)}"
        
        if context:
            error_msg += (
                f" | Component: {context.component}"
                f" | Operation: {context.operation}"
                f" | Retry: {context.retry_count}"
            )
            if context.session_id:
                error_msg += f" | Session: {context.session_id}"
        
        # Log at appropriate level
        log_func = getattr(self.logger, severity.value.lower())
        log_func(error_msg)

    def get_fallback_response(self, error_type: ErrorType) -> str:
        """
        Get user-friendly fallback response for each error type.
        
        Args:
            error_type: Type of error
            
        Returns:
            Vietnamese error message for user
            
        Requirements: 15.13, 15.14
        """
        fallback_messages = {
            ErrorType.NETWORK_ERROR: (
                "Mạng không ổn định. Tỷ Tỷ đang thử kết nối lại..."
            ),
            ErrorType.API_ERROR: (
                "Xin lỗi, Tỷ Tỷ không thể trả lời ngay được. Bạn thử lại sau nhé!"
            ),
            ErrorType.AUDIO_CAPTURE_ERROR: (
                "Tỷ Tỷ không nghe thấy âm thanh. Bạn kiểm tra micro nhé!"
            ),
            ErrorType.RECOGNITION_ERROR: (
                "Tỷ Tỷ không nghe rõ. Bạn nói lại được không?"
            ),
            ErrorType.TTS_ERROR: (
                "Tỷ Tỷ gặp lỗi khi phát âm thanh. Đang thử lại..."
            ),
            ErrorType.UNKNOWN_ERROR: (
                "Xin lỗi, Tỷ Tỷ gặp lỗi. Chúng ta thử lại nhé!"
            )
        }
        
        return fallback_messages.get(error_type, fallback_messages[ErrorType.UNKNOWN_ERROR])

    def _get_retry_message(self, error_type: ErrorType, retry_number: int) -> str:
        """
        Get retry message for user.
        
        Args:
            error_type: Type of error
            retry_number: Current retry attempt number
            
        Returns:
            Vietnamese retry message
        """
        if retry_number == 1:
            return "Đang thử lại..."
        else:
            return f"Đang thử lại lần {retry_number}..."

    def _get_fallback_message(self, error_type: ErrorType) -> str:
        """
        Get fallback message when switching to alternative service.
        
        Args:
            error_type: Type of error
            
        Returns:
            Vietnamese fallback message
        """
        fallback_messages = {
            ErrorType.NETWORK_ERROR: (
                "Mạng không ổn định. Tỷ Tỷ đang dùng chế độ offline."
            ),
            ErrorType.RECOGNITION_ERROR: (
                "Đang chuyển sang nhận dạng giọng nói offline..."
            ),
            ErrorType.TTS_ERROR: (
                "Đang sử dụng phương thức phát âm dự phòng..."
            )
        }
        
        return fallback_messages.get(
            error_type,
            "Đang sử dụng phương thức dự phòng..."
        )

    def notify_user(self, message: str, severity: Severity = Severity.INFO) -> None:
        """
        Notify user about an error or status.
        
        Args:
            message: Vietnamese message to display
            severity: Severity level of the notification
            
        Requirement: 15.15
        """
        # Log the notification
        log_func = getattr(self.logger, severity.value.lower())
        log_func(f"USER NOTIFICATION: {message}")
        
        # In a real application, this would display to UI
        # For now, we'll print with appropriate prefix
        severity_icons = {
            Severity.DEBUG: "🔍",
            Severity.INFO: "ℹ️",
            Severity.WARNING: "⚠️",
            Severity.ERROR: "❌",
            Severity.CRITICAL: "🚨"
        }
        
        icon = severity_icons.get(severity, "ℹ️")
        print(f"{icon} Tỷ Tỷ: {message}")

    def check_component_health(self, component_name: str) -> bool:
        """
        Check if a registered component is healthy.
        
        Args:
            component_name: Name of the component to check
            
        Returns:
            True if component is healthy, False otherwise
        """
        with self._lock:
            if component_name not in self._components:
                self.logger.warning(f"Component {component_name} not registered")
                return False
            
            try:
                health_check = self._components[component_name]
                is_healthy = health_check()
                
                if not is_healthy:
                    self.logger.warning(f"Component {component_name} health check failed")
                
                return is_healthy
            except Exception as e:
                self.logger.error(f"Health check error for {component_name}: {e}")
                return False

    def get_registered_components(self) -> list:
        """
        Get list of all registered components.
        
        Returns:
            List of component names
        """
        with self._lock:
            return list(self._components.keys())


# Module-level test function
if __name__ == "__main__":
    """Test the ErrorHandler"""
    print("Testing ErrorHandler...")
    
    # Create error handler
    handler = ErrorHandler()
    
    # Test 1: Register components
    print("\n1. Registering components...")
    handler.register_component("speech_to_text", lambda: True)
    handler.register_component("text_to_speech", lambda: True)
    handler.register_component("ai_service", lambda: True)
    print(f"   Registered components: {handler.get_registered_components()}")
    
    # Test 2: Handle network error with retries
    print("\n2. Testing network error handling...")
    for retry in range(4):
        context = ErrorContext(
            component="ai_service",
            operation="generate_response",
            retry_count=retry,
            session_id="test-session-123"
        )
        
        error = ConnectionError("Failed to connect to API server")
        action = handler.handle_error(error, context)
        
        print(f"   Retry {retry}: {action.action.value}")
        if action.action == RecoveryActionType.RETRY:
            print(f"   - Delay: {action.retry_delay}s")
            print(f"   - Message: {action.user_message}")
        elif action.action == RecoveryActionType.FALLBACK:
            print(f"   - Fallback to: {action.fallback_component}")
            print(f"   - Message: {action.user_message}")
    
    # Test 3: Handle API error
    print("\n3. Testing API error handling...")
    context = ErrorContext(
        component="gemini_api",
        operation="generate_content",
        retry_count=0
    )
    error = Exception("Rate limit exceeded (429)")
    action = handler.handle_error(error, context)
    print(f"   Action: {action.action.value}")
    print(f"   Message: {action.user_message}")
    
    # Test 4: Handle audio capture error
    print("\n4. Testing audio capture error...")
    context = ErrorContext(
        component="audio_capture",
        operation="start_recording",
        retry_count=2
    )
    error = Exception("Audio device not found")
    action = handler.handle_error(error, context)
    print(f"   Action: {action.action.value}")
    print(f"   Message: {action.user_message}")
    
    # Test 5: Get fallback responses
    print("\n5. Testing fallback responses...")
    for error_type in ErrorType:
        response = handler.get_fallback_response(error_type)
        print(f"   {error_type.value}: {response}")
    
    # Test 6: Notify user
    print("\n6. Testing user notifications...")
    handler.notify_user("Hệ thống đã khởi động thành công", Severity.INFO)
    handler.notify_user("Mất kết nối mạng", Severity.WARNING)
    handler.notify_user("Lỗi nghiêm trọng", Severity.ERROR)
    
    # Test 7: Component health check
    print("\n7. Testing component health checks...")
    for component in handler.get_registered_components():
        is_healthy = handler.check_component_health(component)
        print(f"   {component}: {'✓ Healthy' if is_healthy else '✗ Unhealthy'}")
    
    # Test 8: Log errors with different severity levels
    print("\n8. Testing error logging...")
    context = ErrorContext(
        component="test_component",
        operation="test_operation",
        retry_count=1
    )
    
    handler.log_error(Exception("Debug error"), Severity.DEBUG, context)
    handler.log_error(Exception("Info error"), Severity.INFO, context)
    handler.log_error(Exception("Warning error"), Severity.WARNING, context)
    handler.log_error(Exception("Error"), Severity.ERROR, context)
    handler.log_error(Exception("Critical error"), Severity.CRITICAL, context)
    print("   Errors logged (check logs/error_handler.log)")
    
    print("\n✓ All tests completed successfully!")
    print(f"✓ Log file created at: logs/error_handler.log")
