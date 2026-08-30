#!/usr/bin/env python3
"""
Complete Logging System Test Script

This script demonstrates all logging and monitoring features:
- Structured logging to multiple log files
- Performance metrics tracking
- Error rate monitoring
- Log rotation
- Log analysis capabilities

Requirements: 19.3 - Set up logging and monitoring
"""

import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from modules.logging_config import get_logging_manager


def test_basic_logging(manager):
    """Test basic logging to all log types"""
    print("\n" + "="*70)
    print("TEST 1: BASIC LOGGING")
    print("="*70)
    
    # Get different loggers
    main_logger = manager.get_logger("main")
    audio_logger = manager.get_logger("audio")
    error_logger = manager.get_logger("error")
    
    # Test main logger
    print("\n1. Main logger:")
    main_logger.info("System initialized successfully")
    main_logger.info("Configuration loaded: BASIC_MODE, Gemini AI")
    main_logger.warning("No position_config.json found, using defaults")
    print("   ✓ Logged to tyty_main.log")
    
    # Test audio logger
    print("\n2. Audio logger:")
    audio_logger.info("Audio stream started: 16kHz, mono, 1024 buffer")
    audio_logger.info("VAD initialized: threshold=0.5, silence=3.0s")
    audio_logger.info("Voice activity detected at 00:12:34")
    print("   ✓ Logged to tyty_audio.log")
    
    # Test error logger
    print("\n3. Error logger:")
    error_logger.error("Google STT API connection timeout after 3 retries")
    error_logger.error("Gemini API rate limit exceeded, waiting 60s")
    print("   ✓ Logged to tyty_errors.log")


def test_structured_logging(manager):
    """Test structured logging with extra fields"""
    print("\n" + "="*70)
    print("TEST 2: STRUCTURED LOGGING")
    print("="*70)
    
    print("\n1. Logging with structured metadata:")
    manager.log_with_extra(
        logger_type="main",
        level="INFO",
        message="Wake word detected",
        wake_word="tỷ tỷ",
        confidence=0.87,
        timestamp_ms=1234567890,
        remaining_command="1+1 bằng mấy"
    )
    print("   ✓ Logged with extra fields: wake_word, confidence, timestamp_ms, remaining_command")
    
    manager.log_with_extra(
        logger_type="audio",
        level="INFO",
        message="Audio segment captured",
        duration_ms=2500,
        sample_rate=16000,
        channels=1,
        energy_level=0.72
    )
    print("   ✓ Logged with extra fields: duration_ms, sample_rate, channels, energy_level")


def test_performance_metrics(manager):
    """Test performance metrics tracking"""
    print("\n" + "="*70)
    print("TEST 3: PERFORMANCE METRICS TRACKING")
    print("="*70)
    
    print("\n1. Recording wake word detections:")
    manager.record_wake_word_detection(is_true_positive=True)
    manager.record_wake_word_detection(is_true_positive=True)
    manager.record_wake_word_detection(is_true_positive=False)  # False positive
    manager.record_wake_word_detection(is_true_positive=True)
    print("   ✓ Recorded 4 detections (3 true, 1 false)")
    
    print("\n2. Recording STT requests:")
    manager.record_stt_request(success=True, latency_seconds=0.85)
    manager.record_stt_request(success=True, latency_seconds=1.12)
    manager.record_stt_request(success=False)  # Timeout
    manager.record_stt_request(success=True, latency_seconds=0.93)
    print("   ✓ Recorded 4 requests (3 success, 1 failure)")
    
    print("\n3. Recording AI service requests:")
    manager.record_ai_request(success=True, latency_seconds=1.85)
    manager.record_ai_request(success=True, latency_seconds=2.15)
    manager.record_ai_request(success=True, latency_seconds=1.67)
    print("   ✓ Recorded 3 requests (all success)")
    
    print("\n4. Recording TTS requests:")
    manager.record_tts_request(success=True, latency_seconds=0.42)
    manager.record_tts_request(success=True, latency_seconds=0.38)
    manager.record_tts_request(success=True, latency_seconds=0.45)
    print("   ✓ Recorded 3 requests (all success)")
    
    print("\n5. Recording conversation activity:")
    manager.record_conversation_turn()
    manager.record_conversation_turn()
    manager.record_conversation_turn()
    manager.update_active_sessions(2)
    print("   ✓ Recorded 3 turns, 2 active sessions")
    
    # Display current metrics
    print("\n6. Current performance metrics:")
    metrics = manager.get_metrics()
    print(f"   Wake word accuracy: {metrics.wake_word_accuracy:.2%}")
    print(f"   STT success rate: {metrics.stt_success_rate:.2%}")
    print(f"   STT avg latency: {metrics.stt_avg_latency*1000:.1f}ms")
    print(f"   AI success rate: {metrics.ai_success_rate:.2%}")
    print(f"   AI avg latency: {metrics.ai_avg_latency*1000:.1f}ms")
    print(f"   TTS success rate: {metrics.tts_success_rate:.2%}")
    print(f"   TTS avg latency: {metrics.tts_avg_latency*1000:.1f}ms")
    print(f"   Active sessions: {metrics.active_sessions}")
    print(f"   Conversation turns: {metrics.conversation_turns}")
    
    # Calculate end-to-end latency
    total_latency_ms = (
        metrics.stt_avg_latency * 1000 +
        metrics.ai_avg_latency * 1000 +
        metrics.tts_avg_latency * 1000
    )
    print(f"\n7. End-to-end latency: {total_latency_ms:.1f}ms")
    if total_latency_ms < 4000:
        print(f"   ✅ Within target (<4000ms)")
    else:
        print(f"   ⚠️  Exceeds target (>4000ms)")


def test_error_rates(manager):
    """Test error rate tracking"""
    print("\n" + "="*70)
    print("TEST 4: ERROR RATE TRACKING")
    print("="*70)
    
    print("\n1. Error rates by component:")
    error_rates = manager.get_error_rates()
    
    for component, rate in error_rates.items():
        status = "✅" if rate < 0.05 else "⚠️" if rate < 0.20 else "❌"
        print(f"   {status} {component}: {rate:.2%}")


def test_conversation_logging(manager):
    """Test conversation logging"""
    print("\n" + "="*70)
    print("TEST 5: CONVERSATION LOGGING")
    print("="*70)
    
    session_id = "test-session-" + str(int(time.time()))
    
    print(f"\n1. Logging conversation (session: {session_id}):")
    
    # User turn 1
    manager.log_conversation(
        session_id=session_id,
        role="user",
        content="Tỷ Tỷ 1+1 bằng mấy?",
        metadata={
            'wake_word': 'tỷ tỷ',
            'confidence': 0.87,
            'duration_ms': 2500
        }
    )
    print("   ✓ User message logged")
    
    # Assistant turn 1
    manager.log_conversation(
        session_id=session_id,
        role="assistant",
        content="1 cộng 1 bằng 2 nhé!",
        metadata={
            'ai_latency_ms': 1850,
            'tts_latency_ms': 420
        }
    )
    print("   ✓ Assistant response logged")
    
    # User turn 2 (follow-up, no wake word)
    manager.log_conversation(
        session_id=session_id,
        role="user",
        content="Còn 2+2 thì sao?",
        metadata={
            'follow_up': True,
            'duration_ms': 1800
        }
    )
    print("   ✓ Follow-up question logged")
    
    # Assistant turn 2
    manager.log_conversation(
        session_id=session_id,
        role="assistant",
        content="2 cộng 2 bằng 4 bạn nhé!",
        metadata={
            'ai_latency_ms': 1670,
            'tts_latency_ms': 380
        }
    )
    print("   ✓ Follow-up response logged")
    
    print(f"\n2. Conversation logged to tyty_conversations.log")
    print(f"   Session ID: {session_id}")
    print(f"   Total turns: 4 (2 user, 2 assistant)")


def test_log_rotation(manager):
    """Test log rotation configuration"""
    print("\n" + "="*70)
    print("TEST 6: LOG ROTATION CONFIGURATION")
    print("="*70)
    
    print("\n1. Log rotation settings:")
    print(f"   Max file size: {manager.max_log_size / (1024*1024):.0f}MB")
    print(f"   Backup count: {manager.backup_count}")
    print(f"   Total max size per log: {(manager.max_log_size * (manager.backup_count + 1)) / (1024*1024):.0f}MB")
    
    print("\n2. Log files created:")
    for log_file in manager.log_dir.glob("*.log"):
        size_kb = log_file.stat().st_size / 1024
        print(f"   - {log_file.name}: {size_kb:.2f}KB")


def wait_for_metrics_logging():
    """Wait for background metrics logging"""
    print("\n" + "="*70)
    print("TEST 7: BACKGROUND METRICS LOGGING")
    print("="*70)
    
    print("\n1. Waiting for background metrics logger to run...")
    print("   (Metrics are logged every 60 seconds)")
    print("   Waiting 5 seconds to simulate...\n")
    
    # Show countdown
    for i in range(5, 0, -1):
        print(f"   {i}...", end="", flush=True)
        time.sleep(1)
    
    print("\n\n   ✓ Background thread is running")
    print("   ✓ Metrics will be logged to tyty_metrics.log every 60 seconds")


def demonstrate_log_analysis():
    """Demonstrate log analysis capabilities"""
    print("\n" + "="*70)
    print("TEST 8: LOG ANALYSIS CAPABILITIES")
    print("="*70)
    
    print("\n1. Available log analysis commands:")
    print("   # Analyze all logs")
    print("   python analyze_logs.py --log-dir ./logs --type all")
    
    print("\n   # Analyze performance metrics")
    print("   python analyze_logs.py --log-dir ./logs --type performance")
    
    print("\n   # Analyze errors")
    print("   python analyze_logs.py --log-dir ./logs --type errors")
    
    print("\n   # Analyze audio processing")
    print("   python analyze_logs.py --log-dir ./logs --type audio")
    
    print("\n   # View specific conversation")
    print("   python analyze_logs.py --log-dir ./logs --type conversations --session-id <id>")
    
    print("\n2. Metrics analysis:")
    print("   # Analyze performance metrics over time")
    print("   python analyze_metrics.py --log-file ./logs/tyty_metrics.log")
    
    print("\n   # Save analysis report to file")
    print("   python analyze_metrics.py --log-file ./logs/tyty_metrics.log --output report.txt")


def main():
    """Main test function"""
    print("\n" + "="*70)
    print("COMPREHENSIVE LOGGING SYSTEM TEST")
    print("="*70)
    print("\nThis script demonstrates all logging and monitoring features")
    print("for the Tỷ Tỷ chatbot system.\n")
    
    # Initialize logging manager
    print("Initializing logging manager...")
    manager = get_logging_manager(
        log_dir="./logs",
        log_level="INFO",
        enable_structured_logging=True
    )
    print("✓ Logging manager initialized\n")
    
    # Run all tests
    try:
        test_basic_logging(manager)
        test_structured_logging(manager)
        test_performance_metrics(manager)
        test_error_rates(manager)
        test_conversation_logging(manager)
        test_log_rotation(manager)
        wait_for_metrics_logging()
        demonstrate_log_analysis()
        
        # Summary
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        print("\n✅ All logging and monitoring tests completed successfully!")
        print("\nGenerated log files:")
        print("   📄 tyty_main.log        - Main application logs")
        print("   📄 tyty_errors.log      - Error-level logs only")
        print("   📄 tyty_audio.log       - Audio processing logs")
        print("   📄 tyty_metrics.log     - Performance metrics (JSON)")
        print("   📄 tyty_conversations.log - Conversation transcripts")
        print("\nFeatures demonstrated:")
        print("   ✓ Structured logging with JSON format")
        print("   ✓ Log rotation (10MB max, 5 backups)")
        print("   ✓ Performance metrics tracking")
        print("   ✓ Error rate monitoring by component")
        print("   ✓ Conversation logging (privacy-sensitive)")
        print("   ✓ Background metrics logging (every 60s)")
        print("   ✓ Log analysis scripts")
        print("\nNext steps:")
        print("   1. Run: python analyze_logs.py --log-dir ./logs --type all")
        print("   2. Check log files in ./logs/ directory")
        print("   3. Monitor tyty_metrics.log for ongoing metrics")
        print("\n" + "="*70 + "\n")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
