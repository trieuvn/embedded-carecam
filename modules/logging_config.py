"""
Logging Configuration Module

This module provides centralized logging configuration with structured logging,
log rotation, performance metrics tracking, and error rate monitoring.

Requirements:
- 19.1: Memory management for logging infrastructure
- 19.2: Performance tracking and metrics
- 19.3: Set up logging and monitoring infrastructure
"""

import logging
import logging.handlers
import json
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
from dataclasses import dataclass, field, asdict
from enum import Enum
import threading
import time


class LogLevel(Enum):
    """Log level enumeration"""
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


@dataclass
class PerformanceMetrics:
    """Performance metrics data structure"""
    wake_word_detections: int = 0
    wake_word_true_positives: int = 0
    wake_word_false_positives: int = 0
    
    stt_requests: int = 0
    stt_successes: int = 0
    stt_failures: int = 0
    stt_total_latency: float = 0.0
    
    ai_requests: int = 0
    ai_successes: int = 0
    ai_failures: int = 0
    ai_total_latency: float = 0.0
    
    tts_requests: int = 0
    tts_successes: int = 0
    tts_failures: int = 0
    tts_total_latency: float = 0.0
    
    conversation_turns: int = 0
    active_sessions: int = 0
    
    timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def wake_word_accuracy(self) -> float:
        """Calculate wake word detection accuracy"""
        if self.wake_word_detections == 0:
            return 0.0
        return self.wake_word_true_positives / self.wake_word_detections
    
    @property
    def stt_success_rate(self) -> float:
        """Calculate STT success rate"""
        if self.stt_requests == 0:
            return 0.0
        return self.stt_successes / self.stt_requests
    
    @property
    def stt_avg_latency(self) -> float:
        """Calculate average STT latency in seconds"""
        if self.stt_successes == 0:
            return 0.0
        return self.stt_total_latency / self.stt_successes
    
    @property
    def ai_success_rate(self) -> float:
        """Calculate AI success rate"""
        if self.ai_requests == 0:
            return 0.0
        return self.ai_successes / self.ai_requests
    
    @property
    def ai_avg_latency(self) -> float:
        """Calculate average AI response latency in seconds"""
        if self.ai_successes == 0:
            return 0.0
        return self.ai_total_latency / self.ai_successes
    
    @property
    def tts_success_rate(self) -> float:
        """Calculate TTS success rate"""
        if self.tts_requests == 0:
            return 0.0
        return self.tts_successes / self.tts_requests
    
    @property
    def tts_avg_latency(self) -> float:
        """Calculate average TTS latency in seconds"""
        if self.tts_successes == 0:
            return 0.0
        return self.tts_total_latency / self.tts_successes
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['wake_word_accuracy'] = self.wake_word_accuracy
        data['stt_success_rate'] = self.stt_success_rate
        data['stt_avg_latency_ms'] = self.stt_avg_latency * 1000
        data['ai_success_rate'] = self.ai_success_rate
        data['ai_avg_latency_ms'] = self.ai_avg_latency * 1000
        data['tts_success_rate'] = self.tts_success_rate
        data['tts_avg_latency_ms'] = self.tts_avg_latency * 1000
        return data


@dataclass
class ErrorRateTracker:
    """Track error rates by component"""
    component_errors: Dict[str, int] = field(default_factory=dict)
    component_requests: Dict[str, int] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    
    def record_request(self, component: str, success: bool = True) -> None:
        """Record a request for a component"""
        if component not in self.component_requests:
            self.component_requests[component] = 0
            self.component_errors[component] = 0
        
        self.component_requests[component] += 1
        if not success:
            self.component_errors[component] += 1
    
    def get_error_rate(self, component: str) -> float:
        """Get error rate for a component"""
        if component not in self.component_requests:
            return 0.0
        
        requests = self.component_requests[component]
        if requests == 0:
            return 0.0
        
        errors = self.component_errors.get(component, 0)
        return errors / requests
    
    def get_all_error_rates(self) -> Dict[str, float]:
        """Get error rates for all components"""
        return {
            component: self.get_error_rate(component)
            for component in self.component_requests.keys()
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error rates to dictionary"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'error_rates': self.get_all_error_rates(),
            'component_errors': self.component_errors.copy(),
            'component_requests': self.component_requests.copy()
        }


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, 'extra_fields'):
            log_data.update(record.extra_fields)
        
        return json.dumps(log_data, ensure_ascii=False)


class LoggingManager:
    """
    Centralized logging manager with structured logging, log rotation,
    performance metrics tracking, and error rate monitoring.
    
    Requirements: 19.1, 19.2, 19.3
    """
    
    def __init__(
        self,
        log_dir: str = "./logs",
        log_level: str = "INFO",
        enable_structured_logging: bool = True,
        max_log_size_mb: int = 10,
        backup_count: int = 5
    ):
        """
        Initialize the logging manager.
        
        Args:
            log_dir: Directory to store log files
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            enable_structured_logging: Enable JSON-formatted logs
            max_log_size_mb: Maximum size of each log file in MB
            backup_count: Number of backup log files to keep
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True, parents=True)
        
        self.log_level = getattr(logging, log_level.upper(), logging.INFO)
        self.enable_structured_logging = enable_structured_logging
        self.max_log_size = max_log_size_mb * 1024 * 1024  # Convert to bytes
        self.backup_count = backup_count
        
        # Performance metrics
        self.metrics = PerformanceMetrics()
        self.error_tracker = ErrorRateTracker()
        self.metrics_lock = threading.Lock()
        
        # Setup loggers
        self._setup_loggers()
        
        # Start metrics logging thread
        self._start_metrics_logging()
    
    def _setup_loggers(self) -> None:
        """Setup all logging handlers"""
        # Main application logger
        self.main_logger = self._create_logger(
            name="tyty_main",
            filename="tyty_main.log",
            level=self.log_level
        )
        
        # Error logger (ERROR and above only)
        self.error_logger = self._create_logger(
            name="tyty_errors",
            filename="tyty_errors.log",
            level=logging.ERROR
        )
        
        # Audio processing logger
        self.audio_logger = self._create_logger(
            name="tyty_audio",
            filename="tyty_audio.log",
            level=self.log_level
        )
        
        # Performance metrics logger
        self.metrics_logger = self._create_logger(
            name="tyty_metrics",
            filename="tyty_metrics.log",
            level=logging.INFO,
            structured_only=True  # Always use structured format for metrics
        )
        
        # Conversation logger (optional, privacy-sensitive)
        self.conversation_logger = self._create_logger(
            name="tyty_conversations",
            filename="tyty_conversations.log",
            level=logging.INFO
        )
    
    def _create_logger(
        self,
        name: str,
        filename: str,
        level: int,
        structured_only: bool = False
    ) -> logging.Logger:
        """
        Create a logger with rotating file handler.
        
        Args:
            name: Logger name
            filename: Log file name
            level: Logging level
            structured_only: Use structured format regardless of config
            
        Returns:
            Configured logger
        """
        logger = logging.getLogger(name)
        logger.setLevel(level)
        logger.propagate = False  # Don't propagate to root logger
        
        # Clear existing handlers
        logger.handlers.clear()
        
        # Create rotating file handler
        log_file = self.log_dir / filename
        handler = logging.handlers.RotatingFileHandler(
            filename=log_file,
            maxBytes=self.max_log_size,
            backupCount=self.backup_count,
            encoding='utf-8'
        )
        handler.setLevel(level)
        
        # Set formatter
        if self.enable_structured_logging or structured_only:
            formatter = StructuredFormatter()
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        # Also add console handler for main logger
        if name == "tyty_main":
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s',
                datefmt='%H:%M:%S'
            ))
            logger.addHandler(console_handler)
        
        return logger
    
    def get_logger(self, logger_type: str = "main") -> logging.Logger:
        """
        Get a logger by type.
        
        Args:
            logger_type: Type of logger (main, error, audio, metrics, conversation)
            
        Returns:
            Configured logger
        """
        loggers = {
            "main": self.main_logger,
            "error": self.error_logger,
            "audio": self.audio_logger,
            "metrics": self.metrics_logger,
            "conversation": self.conversation_logger
        }
        return loggers.get(logger_type, self.main_logger)
    
    def log_with_extra(
        self,
        logger_type: str,
        level: str,
        message: str,
        **extra_fields
    ) -> None:
        """
        Log a message with extra structured fields.
        
        Args:
            logger_type: Type of logger to use
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            message: Log message
            **extra_fields: Additional fields for structured logging
        """
        logger = self.get_logger(logger_type)
        log_level = getattr(logging, level.upper(), logging.INFO)
        
        # Create log record with extra fields
        extra = {'extra_fields': extra_fields} if extra_fields else {}
        logger.log(log_level, message, extra=extra)
    
    # Performance metrics methods
    
    def record_wake_word_detection(self, is_true_positive: bool = True) -> None:
        """Record a wake word detection event"""
        with self.metrics_lock:
            self.metrics.wake_word_detections += 1
            if is_true_positive:
                self.metrics.wake_word_true_positives += 1
            else:
                self.metrics.wake_word_false_positives += 1
    
    def record_stt_request(self, success: bool, latency_seconds: float = 0.0) -> None:
        """Record a speech-to-text request"""
        with self.metrics_lock:
            self.metrics.stt_requests += 1
            if success:
                self.metrics.stt_successes += 1
                self.metrics.stt_total_latency += latency_seconds
            else:
                self.metrics.stt_failures += 1
            
            self.error_tracker.record_request("speech_to_text", success)
    
    def record_ai_request(self, success: bool, latency_seconds: float = 0.0) -> None:
        """Record an AI service request"""
        with self.metrics_lock:
            self.metrics.ai_requests += 1
            if success:
                self.metrics.ai_successes += 1
                self.metrics.ai_total_latency += latency_seconds
            else:
                self.metrics.ai_failures += 1
            
            self.error_tracker.record_request("ai_service", success)
    
    def record_tts_request(self, success: bool, latency_seconds: float = 0.0) -> None:
        """Record a text-to-speech request"""
        with self.metrics_lock:
            self.metrics.tts_requests += 1
            if success:
                self.metrics.tts_successes += 1
                self.metrics.tts_total_latency += latency_seconds
            else:
                self.metrics.tts_failures += 1
            
            self.error_tracker.record_request("text_to_speech", success)
    
    def record_conversation_turn(self) -> None:
        """Record a conversation turn"""
        with self.metrics_lock:
            self.metrics.conversation_turns += 1
    
    def update_active_sessions(self, count: int) -> None:
        """Update the count of active sessions"""
        with self.metrics_lock:
            self.metrics.active_sessions = count
    
    def get_metrics(self) -> PerformanceMetrics:
        """Get current performance metrics"""
        with self.metrics_lock:
            return self.metrics
    
    def get_error_rates(self) -> Dict[str, float]:
        """Get error rates by component"""
        with self.metrics_lock:
            return self.error_tracker.get_all_error_rates()
    
    def _start_metrics_logging(self) -> None:
        """Start background thread to log metrics periodically"""
        def log_metrics():
            while True:
                time.sleep(60)  # Log metrics every 60 seconds
                
                with self.metrics_lock:
                    metrics_data = self.metrics.to_dict()
                    error_data = self.error_tracker.to_dict()
                
                # Log performance metrics
                self.metrics_logger.info(
                    "Performance Metrics",
                    extra={'extra_fields': metrics_data}
                )
                
                # Log error rates
                self.metrics_logger.info(
                    "Error Rates",
                    extra={'extra_fields': error_data}
                )
        
        metrics_thread = threading.Thread(target=log_metrics, daemon=True)
        metrics_thread.start()
    
    def reset_metrics(self) -> None:
        """Reset all performance metrics"""
        with self.metrics_lock:
            self.metrics = PerformanceMetrics()
            self.error_tracker = ErrorRateTracker()
    
    def log_conversation(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log a conversation message (privacy-sensitive).
        
        Args:
            session_id: Session identifier
            role: Message role (user, assistant, system)
            content: Message content
            metadata: Optional metadata
        """
        log_data = {
            'session_id': session_id,
            'role': role,
            'content': content
        }
        
        if metadata:
            log_data['metadata'] = metadata
        
        self.conversation_logger.info(
            f"Conversation: {role}",
            extra={'extra_fields': log_data}
        )


# Global logging manager instance
_logging_manager: Optional[LoggingManager] = None


def get_logging_manager(
    log_dir: str = "./logs",
    log_level: str = "INFO",
    enable_structured_logging: bool = True
) -> LoggingManager:
    """
    Get the global logging manager instance (singleton pattern).
    
    Args:
        log_dir: Directory to store log files
        log_level: Logging level
        enable_structured_logging: Enable JSON-formatted logs
        
    Returns:
        LoggingManager instance
    """
    global _logging_manager
    
    if _logging_manager is None:
        _logging_manager = LoggingManager(
            log_dir=log_dir,
            log_level=log_level,
            enable_structured_logging=enable_structured_logging
        )
    
    return _logging_manager


# Module-level test function
if __name__ == "__main__":
    """Test the logging configuration"""
    print("Testing Logging Configuration...")
    
    # Create logging manager
    manager = get_logging_manager(
        log_dir="./logs",
        log_level="DEBUG",
        enable_structured_logging=True
    )
    
    # Test 1: Basic logging
    print("\n1. Testing basic logging...")
    main_logger = manager.get_logger("main")
    main_logger.debug("Debug message")
    main_logger.info("Info message")
    main_logger.warning("Warning message")
    main_logger.error("Error message")
    main_logger.critical("Critical message")
    
    # Test 2: Audio logging
    print("\n2. Testing audio logging...")
    audio_logger = manager.get_logger("audio")
    audio_logger.info("Audio stream started", extra={'extra_fields': {
        'sample_rate': 16000,
        'channels': 1,
        'buffer_size': 1024
    }})
    
    # Test 3: Performance metrics
    print("\n3. Testing performance metrics...")
    manager.record_wake_word_detection(is_true_positive=True)
    manager.record_wake_word_detection(is_true_positive=True)
    manager.record_wake_word_detection(is_true_positive=False)
    
    manager.record_stt_request(success=True, latency_seconds=0.8)
    manager.record_stt_request(success=True, latency_seconds=1.2)
    manager.record_stt_request(success=False)
    
    manager.record_ai_request(success=True, latency_seconds=1.5)
    manager.record_ai_request(success=True, latency_seconds=2.1)
    
    manager.record_tts_request(success=True, latency_seconds=0.4)
    
    manager.record_conversation_turn()
    manager.record_conversation_turn()
    manager.update_active_sessions(2)
    
    # Get and display metrics
    metrics = manager.get_metrics()
    print(f"\nPerformance Metrics:")
    print(f"  Wake word accuracy: {metrics.wake_word_accuracy:.2%}")
    print(f"  STT success rate: {metrics.stt_success_rate:.2%}")
    print(f"  STT avg latency: {metrics.stt_avg_latency*1000:.1f}ms")
    print(f"  AI success rate: {metrics.ai_success_rate:.2%}")
    print(f"  AI avg latency: {metrics.ai_avg_latency*1000:.1f}ms")
    print(f"  TTS success rate: {metrics.tts_success_rate:.2%}")
    print(f"  TTS avg latency: {metrics.tts_avg_latency*1000:.1f}ms")
    print(f"  Active sessions: {metrics.active_sessions}")
    print(f"  Conversation turns: {metrics.conversation_turns}")
    
    # Test 4: Error rates
    print("\n4. Testing error rates...")
    error_rates = manager.get_error_rates()
    print(f"Error Rates:")
    for component, rate in error_rates.items():
        print(f"  {component}: {rate:.2%}")
    
    # Test 5: Conversation logging
    print("\n5. Testing conversation logging...")
    manager.log_conversation(
        session_id="test-session-123",
        role="user",
        content="Tỷ Tỷ 1+1 bằng mấy?",
        metadata={'wake_word': 'tỷ tỷ', 'duration': 2.5}
    )
    manager.log_conversation(
        session_id="test-session-123",
        role="assistant",
        content="1 cộng 1 bằng 2 nhé!",
        metadata={'ai_latency': 1.5, 'tts_latency': 0.4}
    )
    
    # Test 6: Structured logging with extra fields
    print("\n6. Testing structured logging...")
    manager.log_with_extra(
        logger_type="main",
        level="INFO",
        message="System initialized",
        mode="BASIC_MODE",
        ai_provider="gemini",
        vad_enabled=True
    )
    
    print("\n✓ All tests completed successfully!")
    print(f"✓ Log files created in: {manager.log_dir}")
    print(f"  - tyty_main.log")
    print(f"  - tyty_errors.log")
    print(f"  - tyty_audio.log")
    print(f"  - tyty_metrics.log")
    print(f"  - tyty_conversations.log")
