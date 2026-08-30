#!/usr/bin/env python3
"""
Log Analysis Script for Tỷ Tỷ Chatbot

This script analyzes log files to provide insights into system performance,
error patterns, and debugging information.

Usage:
    python analyze_logs.py --log-dir ./logs --type performance
    python analyze_logs.py --log-dir ./logs --type errors
    python analyze_logs.py --log-dir ./logs --type audio
    python analyze_logs.py --log-dir ./logs --type all
    python analyze_logs.py --log-dir ./logs --session-id <session-id>
"""

import argparse
import json
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from collections import defaultdict, Counter


class LogAnalyzer:
    """Analyze log files for debugging and performance monitoring"""
    
    def __init__(self, log_dir: str = "./logs"):
        """
        Initialize the log analyzer.
        
        Args:
            log_dir: Directory containing log files
        """
        self.log_dir = Path(log_dir)
        
        if not self.log_dir.exists():
            raise FileNotFoundError(f"Log directory not found: {log_dir}")
    
    def parse_log_line(self, line: str) -> Optional[Dict[str, Any]]:
        """
        Parse a log line (JSON or text format).
        
        Args:
            line: Log line to parse
            
        Returns:
            Parsed log entry or None if parsing fails
        """
        line = line.strip()
        if not line:
            return None
        
        # Try JSON format first
        if line.startswith('{'):
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                pass
        
        # Try text format: "2025-02-09 12:34:56 - logger - LEVEL - message"
        text_pattern = r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) - ([^ ]+) - ([^ ]+) - (.+)$'
        match = re.match(text_pattern, line)
        
        if match:
            return {
                'timestamp': match.group(1),
                'logger': match.group(2),
                'level': match.group(3),
                'message': match.group(4)
            }
        
        return None
    
    def read_log_file(self, filename: str) -> List[Dict[str, Any]]:
        """
        Read and parse a log file.
        
        Args:
            filename: Name of the log file
            
        Returns:
            List of parsed log entries
        """
        log_file = self.log_dir / filename
        
        if not log_file.exists():
            print(f"⚠️  Log file not found: {filename}")
            return []
        
        entries = []
        
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                entry = self.parse_log_line(line)
                if entry:
                    entries.append(entry)
        
        return entries
    
    def analyze_performance(self) -> None:
        """Analyze performance metrics from logs"""
        print("\n" + "="*60)
        print("PERFORMANCE ANALYSIS")
        print("="*60)
        
        entries = self.read_log_file("tyty_metrics.log")
        
        if not entries:
            print("⚠️  No performance metrics found")
            return
        
        # Get latest metrics
        performance_entries = [e for e in entries if 'Performance Metrics' in e.get('message', '')]
        
        if not performance_entries:
            print("⚠️  No performance metrics found")
            return
        
        latest = performance_entries[-1]
        extra_fields = latest.get('extra_fields', {})
        
        print(f"\n📊 Latest Performance Metrics ({latest.get('timestamp', 'N/A')})")
        print("-" * 60)
        
        # Wake word detection
        print("\n🎯 Wake Word Detection:")
        print(f"  Total detections: {extra_fields.get('wake_word_detections', 0)}")
        print(f"  True positives: {extra_fields.get('wake_word_true_positives', 0)}")
        print(f"  False positives: {extra_fields.get('wake_word_false_positives', 0)}")
        print(f"  Accuracy: {extra_fields.get('wake_word_accuracy', 0):.2%}")
        
        # Speech-to-Text
        print("\n🎤 Speech-to-Text:")
        print(f"  Total requests: {extra_fields.get('stt_requests', 0)}")
        print(f"  Successes: {extra_fields.get('stt_successes', 0)}")
        print(f"  Failures: {extra_fields.get('stt_failures', 0)}")
        print(f"  Success rate: {extra_fields.get('stt_success_rate', 0):.2%}")
        print(f"  Avg latency: {extra_fields.get('stt_avg_latency_ms', 0):.1f}ms")
        
        # AI Service
        print("\n🤖 AI Service:")
        print(f"  Total requests: {extra_fields.get('ai_requests', 0)}")
        print(f"  Successes: {extra_fields.get('ai_successes', 0)}")
        print(f"  Failures: {extra_fields.get('ai_failures', 0)}")
        print(f"  Success rate: {extra_fields.get('ai_success_rate', 0):.2%}")
        print(f"  Avg latency: {extra_fields.get('ai_avg_latency_ms', 0):.1f}ms")
        
        # Text-to-Speech
        print("\n🔊 Text-to-Speech:")
        print(f"  Total requests: {extra_fields.get('tts_requests', 0)}")
        print(f"  Successes: {extra_fields.get('tts_successes', 0)}")
        print(f"  Failures: {extra_fields.get('tts_failures', 0)}")
        print(f"  Success rate: {extra_fields.get('tts_success_rate', 0):.2%}")
        print(f"  Avg latency: {extra_fields.get('tts_avg_latency_ms', 0):.1f}ms")
        
        # Conversation metrics
        print("\n💬 Conversation Metrics:")
        print(f"  Active sessions: {extra_fields.get('active_sessions', 0)}")
        print(f"  Total turns: {extra_fields.get('conversation_turns', 0)}")
        
        # Calculate total end-to-end latency
        total_latency = (
            extra_fields.get('stt_avg_latency_ms', 0) +
            extra_fields.get('ai_avg_latency_ms', 0) +
            extra_fields.get('tts_avg_latency_ms', 0)
        )
        print(f"\n⚡ End-to-End Latency: {total_latency:.1f}ms")
        
        # Performance requirements check (from design doc: <4s target)
        if total_latency < 4000:
            print(f"   ✅ Within target (<4000ms)")
        else:
            print(f"   ⚠️  Exceeds target (>4000ms)")
    
    def analyze_errors(self) -> None:
        """Analyze error patterns from logs"""
        print("\n" + "="*60)
        print("ERROR ANALYSIS")
        print("="*60)
        
        # Read error log
        error_entries = self.read_log_file("tyty_errors.log")
        
        if not error_entries:
            print("✅ No errors found")
            return
        
        print(f"\n❌ Found {len(error_entries)} error entries")
        print("-" * 60)
        
        # Count errors by type
        error_types = Counter()
        error_components = Counter()
        error_messages = Counter()
        
        for entry in error_entries:
            level = entry.get('level', 'UNKNOWN')
            logger = entry.get('logger', 'unknown')
            message = entry.get('message', '')
            
            error_types[level] += 1
            error_components[logger] += 1
            
            # Extract error type from message
            if 'network' in message.lower() or 'connection' in message.lower():
                error_messages['Network Error'] += 1
            elif 'api' in message.lower() or 'quota' in message.lower():
                error_messages['API Error'] += 1
            elif 'audio' in message.lower():
                error_messages['Audio Error'] += 1
            elif 'recognition' in message.lower() or 'stt' in message.lower():
                error_messages['Recognition Error'] += 1
            elif 'tts' in message.lower():
                error_messages['TTS Error'] += 1
            else:
                error_messages['Other Error'] += 1
        
        # Display error types
        print("\n📊 Error Types:")
        for error_type, count in error_types.most_common():
            print(f"  {error_type}: {count}")
        
        # Display errors by component
        print("\n🔧 Errors by Component:")
        for component, count in error_components.most_common():
            print(f"  {component}: {count}")
        
        # Display error categories
        print("\n🏷️  Error Categories:")
        for category, count in error_messages.most_common():
            print(f"  {category}: {count}")
        
        # Show recent errors
        print("\n🕒 Recent Errors (last 5):")
        for entry in error_entries[-5:]:
            timestamp = entry.get('timestamp', 'N/A')
            logger = entry.get('logger', 'unknown')
            message = entry.get('message', '')
            print(f"\n  [{timestamp}] {logger}")
            print(f"  {message[:100]}...")
        
        # Analyze error rates from metrics
        print("\n" + "-" * 60)
        metrics_entries = self.read_log_file("tyty_metrics.log")
        error_rate_entries = [e for e in metrics_entries if 'Error Rates' in e.get('message', '')]
        
        if error_rate_entries:
            latest = error_rate_entries[-1]
            extra_fields = latest.get('extra_fields', {})
            error_rates = extra_fields.get('error_rates', {})
            
            print("\n📈 Error Rates by Component:")
            for component, rate in error_rates.items():
                status = "✅" if rate < 0.05 else "⚠️" if rate < 0.20 else "❌"
                print(f"  {status} {component}: {rate:.2%}")
    
    def analyze_audio(self) -> None:
        """Analyze audio processing logs"""
        print("\n" + "="*60)
        print("AUDIO PROCESSING ANALYSIS")
        print("="*60)
        
        entries = self.read_log_file("tyty_audio.log")
        
        if not entries:
            print("⚠️  No audio logs found")
            return
        
        print(f"\n🎵 Found {len(entries)} audio log entries")
        print("-" * 60)
        
        # Count events
        event_types = Counter()
        
        for entry in entries:
            message = entry.get('message', '')
            
            if 'start' in message.lower():
                event_types['Audio Started'] += 1
            elif 'stop' in message.lower():
                event_types['Audio Stopped'] += 1
            elif 'voice' in message.lower():
                event_types['Voice Activity'] += 1
            elif 'silence' in message.lower():
                event_types['Silence Detected'] += 1
            elif 'error' in message.lower():
                event_types['Audio Error'] += 1
            else:
                event_types['Other'] += 1
        
        print("\n📊 Audio Events:")
        for event, count in event_types.most_common():
            print(f"  {event}: {count}")
        
        # Show recent audio events
        print("\n🕒 Recent Audio Events (last 10):")
        for entry in entries[-10:]:
            timestamp = entry.get('timestamp', 'N/A')
            message = entry.get('message', '')
            print(f"  [{timestamp}] {message[:80]}")
    
    def analyze_conversations(self, session_id: Optional[str] = None) -> None:
        """
        Analyze conversation logs.
        
        Args:
            session_id: Optional session ID to filter conversations
        """
        print("\n" + "="*60)
        print("CONVERSATION ANALYSIS")
        print("="*60)
        
        entries = self.read_log_file("tyty_conversations.log")
        
        if not entries:
            print("⚠️  No conversation logs found")
            return
        
        # Filter by session ID if provided
        if session_id:
            entries = [e for e in entries if e.get('extra_fields', {}).get('session_id') == session_id]
            print(f"\n💬 Conversations for session: {session_id}")
        else:
            print(f"\n💬 All conversations ({len(entries)} messages)")
        
        print("-" * 60)
        
        if not entries:
            print("⚠️  No matching conversations found")
            return
        
        # Group by session
        sessions = defaultdict(list)
        for entry in entries:
            sid = entry.get('extra_fields', {}).get('session_id', 'unknown')
            sessions[sid].append(entry)
        
        print(f"\n📊 Session Statistics:")
        print(f"  Total sessions: {len(sessions)}")
        print(f"  Total messages: {len(entries)}")
        
        # Display conversations
        for sid, messages in sessions.items():
            print(f"\n{'='*60}")
            print(f"Session: {sid}")
            print(f"Messages: {len(messages)}")
            print(f"{'='*60}")
            
            for msg in messages:
                timestamp = msg.get('timestamp', 'N/A')
                extra = msg.get('extra_fields', {})
                role = extra.get('role', 'unknown')
                content = extra.get('content', '')
                
                icon = "👤" if role == "user" else "🤖"
                print(f"\n{icon} [{timestamp}] {role.upper()}")
                print(f"   {content}")
                
                # Show metadata if present
                metadata = extra.get('metadata', {})
                if metadata:
                    print(f"   Metadata: {json.dumps(metadata, ensure_ascii=False)}")
    
    def analyze_all(self) -> None:
        """Run all analyses"""
        self.analyze_performance()
        self.analyze_errors()
        self.analyze_audio()
        print("\n" + "="*60)
        print("Note: Use --session-id <id> to view specific conversations")
        print("="*60)


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Analyze Tỷ Tỷ Chatbot logs for debugging and performance monitoring"
    )
    
    parser.add_argument(
        "--log-dir",
        type=str,
        default="./logs",
        help="Directory containing log files (default: ./logs)"
    )
    
    parser.add_argument(
        "--type",
        type=str,
        choices=["performance", "errors", "audio", "conversations", "all"],
        default="all",
        help="Type of analysis to perform (default: all)"
    )
    
    parser.add_argument(
        "--session-id",
        type=str,
        help="Session ID to filter conversations"
    )
    
    args = parser.parse_args()
    
    try:
        analyzer = LogAnalyzer(log_dir=args.log_dir)
        
        print("\n" + "="*60)
        print("TỶTỶ CHATBOT LOG ANALYZER")
        print("="*60)
        print(f"Log directory: {args.log_dir}")
        print(f"Analysis type: {args.type}")
        
        if args.type == "performance":
            analyzer.analyze_performance()
        elif args.type == "errors":
            analyzer.analyze_errors()
        elif args.type == "audio":
            analyzer.analyze_audio()
        elif args.type == "conversations":
            analyzer.analyze_conversations(session_id=args.session_id)
        else:
            analyzer.analyze_all()
        
        print("\n" + "="*60)
        print("ANALYSIS COMPLETE")
        print("="*60 + "\n")
        
    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        print("Make sure the log directory exists and contains log files.\n")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
