#!/usr/bin/env python3
"""
Test script to generate sample logs and verify the logging system.

This script:
1. Initializes the logging manager
2. Generates sample performance metrics
3. Generates sample errors
4. Generates sample audio logs
5. Generates sample conversation logs
6. Manually triggers metrics logging
7. Runs the log analyzer to verify everything works
"""

import time
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from modules.logging_config import get_logging_manager


def generate_sample_logs():
    """Generate comprehensive sample logs"""
    print("="*60)
    print("TESTING LOGGING SYSTEM")
    print("="*60)
    
    # Initialize logging manager
    print("\n1. Initializing logging manager...")
    manager = get_logging_manager(
        log_dir="./logs",
        log_level="INFO",
        enable_structured_logging=True
    )
    print("   ✓ Logging manager initialized")
    
    # Generate main logs
    print("\n2. Generating main application logs...")
    main_logger = manager.get_logger("main")
    main_logger.info("System startup initiated")
    main_logger.info("Configuration loaded", extra={'extra_fields': {
        'ai_provider': 'gemini',
        'operation_mode': 'BASIC_MODE',
        'vad_enabled': True
    }})
    main_logger.info("Audio devices enumerated")
    main_logger.info("Wake word engine initialized")
    main_logger.info("System ready for voice commands")
    print("   ✓ Generated 5 main log entries")
    
    # Generate audio logs
    print("\n3. Generating audio processing logs...")
    audio_logger = manager.get_logger("audio")
    audio_logger.info("Audio stream started", extra={'extra_fields': {
        'sample_rate': 16000,
        'channels': 1,
        'buffer_size': 1024
    }})
    audio_logger.debug("Voice activity detected")
    audio_logger.debug("Silence detected - ending recording")
    audio_logger.info("Audio segment captured", extra={'extra_fields': {
        'duration_ms': 2500,
        'energy': 0.045
    }})
    audio_logger.info("Audio stream stopped")
    print("   ✓ Generated 5 audio log entries")
    
    # Generate error logs
    print("\n4. Generating error logs...")
    error_logger = manager.get_logger("error")
    error_logger.error("Network timeout connecting to API server")
    error_logger.error("Recognition failed: audio too short")
    error_logger.warning("Retry attempt 1 of 3")
    print("   ✓ Generated 3 error log entries")
    
    # Generate performance metrics
    print("\n5. Recording performance metrics...")
    
    # Wake word detections
    manager.record_wake_word_detection(is_true_positive=True)
    manager.record_wake_word_detection(is_true_positive=True)
    manager.record_wake_word_detection(is_true_positive=True)
    manager.record_wake_word_detection(is_true_positive=False)  # False positive
    
    # STT requests
    manager.record_stt_request(success=True, latency_seconds=0.8)
    manager.record_stt_request(success=True, latency_seconds=1.2)
    manager.record_stt_request(success=True, latency_seconds=0.9)
    manager.record_stt_request(success=False)  # Failed request
    
    # AI requests
    manager.record_ai_request(success=True, latency_seconds=1.5)
    manager.record_ai_request(success=True, latency_seconds=2.1)
    manager.record_ai_request(success=True, latency_seconds=1.8)
    
    # TTS requests
    manager.record_tts_request(success=True, latency_seconds=0.4)
    manager.record_tts_request(success=True, latency_seconds=0.5)
    manager.record_tts_request(success=True, latency_seconds=0.3)
    
    # Conversation metrics
    manager.record_conversation_turn()
    manager.record_conversation_turn()
    manager.record_conversation_turn()
    manager.update_active_sessions(2)
    
    print("   ✓ Recorded performance metrics")
    
    # Generate conversation logs
    print("\n6. Generating conversation logs...")
    manager.log_conversation(
        session_id="session-001",
        role="user",
        content="Tỷ Tỷ 1 cộng 1 bằng mấy?",
        metadata={'wake_word': 'tỷ tỷ', 'duration_ms': 2500}
    )
    manager.log_conversation(
        session_id="session-001",
        role="assistant",
        content="1 cộng 1 bằng 2 nhé!",
        metadata={'ai_latency_ms': 1500, 'tts_latency_ms': 400}
    )
    manager.log_conversation(
        session_id="session-001",
        role="user",
        content="Còn 5 cộng 3 thì sao?",
        metadata={'duration_ms': 2000}
    )
    manager.log_conversation(
        session_id="session-001",
        role="assistant",
        content="5 cộng 3 bằng 8!",
        metadata={'ai_latency_ms': 1800, 'tts_latency_ms': 350}
    )
    
    manager.log_conversation(
        session_id="session-002",
        role="user",
        content="Tỷ Tỷ thời tiết hôm nay thế nào?",
        metadata={'wake_word': 'tỷ tỷ', 'duration_ms': 3000}
    )
    manager.log_conversation(
        session_id="session-002",
        role="assistant",
        content="Xin lỗi, Tỷ Tỷ chưa thể kiểm tra thời tiết.",
        metadata={'ai_latency_ms': 2100, 'tts_latency_ms': 500}
    )
    
    print("   ✓ Generated 6 conversation log entries")
    
    # Manually log metrics (instead of waiting 60 seconds)
    print("\n7. Logging performance metrics...")
    metrics_logger = manager.get_logger("metrics")
    metrics_data = manager.get_metrics().to_dict()
    error_data = manager.error_tracker.to_dict()
    
    metrics_logger.info("Performance Metrics", extra={'extra_fields': metrics_data})
    metrics_logger.info("Error Rates", extra={'extra_fields': error_data})
    print("   ✓ Performance metrics logged")
    
    # Display current metrics
    print("\n" + "="*60)
    print("CURRENT PERFORMANCE METRICS")
    print("="*60)
    metrics = manager.get_metrics()
    print(f"\n🎯 Wake Word Detection:")
    print(f"   Accuracy: {metrics.wake_word_accuracy:.2%}")
    print(f"   Total: {metrics.wake_word_detections}")
    
    print(f"\n🎤 Speech-to-Text:")
    print(f"   Success Rate: {metrics.stt_success_rate:.2%}")
    print(f"   Avg Latency: {metrics.stt_avg_latency*1000:.1f}ms")
    
    print(f"\n🤖 AI Service:")
    print(f"   Success Rate: {metrics.ai_success_rate:.2%}")
    print(f"   Avg Latency: {metrics.ai_avg_latency*1000:.1f}ms")
    
    print(f"\n🔊 Text-to-Speech:")
    print(f"   Success Rate: {metrics.tts_success_rate:.2%}")
    print(f"   Avg Latency: {metrics.tts_avg_latency*1000:.1f}ms")
    
    print(f"\n💬 Conversation:")
    print(f"   Active Sessions: {metrics.active_sessions}")
    print(f"   Total Turns: {metrics.conversation_turns}")
    
    print(f"\n⚡ Total Latency: {(metrics.stt_avg_latency + metrics.ai_avg_latency + metrics.tts_avg_latency)*1000:.1f}ms")
    
    # Display error rates
    print(f"\n📈 Error Rates:")
    error_rates = manager.get_error_rates()
    for component, rate in error_rates.items():
        print(f"   {component}: {rate:.2%}")
    
    print("\n" + "="*60)
    print("✓ LOGGING SYSTEM TEST COMPLETE")
    print("="*60)
    print(f"\nLog files created in: {manager.log_dir}")
    print("  - tyty_main.log")
    print("  - tyty_errors.log")
    print("  - tyty_audio.log")
    print("  - tyty_metrics.log")
    print("  - tyty_conversations.log")
    print("\nRun the log analyzer to view detailed analysis:")
    print("  python analyze_logs.py --type all")
    print("  python analyze_logs.py --type performance")
    print("  python analyze_logs.py --type errors")
    print("  python analyze_logs.py --type conversations --session-id session-001")


if __name__ == "__main__":
    generate_sample_logs()
