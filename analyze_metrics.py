"""
Log Analysis Script for Performance Metrics

This script analyzes the tyty_metrics.log file to provide insights into:
- Wake word detection accuracy
- STT/AI/TTS latency trends
- Error rates by component
- System performance over time

Requirements: 19.3 - Create log analysis scripts for debugging
"""

import json
import argparse
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
from collections import defaultdict
import statistics


class MetricsAnalyzer:
    """Analyze performance metrics from log files"""
    
    def __init__(self, log_file: str):
        """
        Initialize the metrics analyzer.
        
        Args:
            log_file: Path to tyty_metrics.log file
        """
        self.log_file = Path(log_file)
        self.metrics_entries: List[Dict[str, Any]] = []
        self.error_rate_entries: List[Dict[str, Any]] = []
        
        if not self.log_file.exists():
            raise FileNotFoundError(f"Log file not found: {log_file}")
        
        self._load_metrics()
    
    def _load_metrics(self) -> None:
        """Load and parse metrics from log file"""
        with open(self.log_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    log_entry = json.loads(line.strip())
                    
                    if 'extra_fields' in log_entry:
                        extra = log_entry['extra_fields']
                        
                        # Separate performance metrics from error rates
                        if 'wake_word_detections' in extra:
                            self.metrics_entries.append(extra)
                        elif 'error_rates' in extra:
                            self.error_rate_entries.append(extra)
                
                except json.JSONDecodeError:
                    continue
    
    def analyze_wake_word_accuracy(self) -> Dict[str, Any]:
        """Analyze wake word detection accuracy"""
        if not self.metrics_entries:
            return {'error': 'No metrics data available'}
        
        accuracies = [entry.get('wake_word_accuracy', 0.0) for entry in self.metrics_entries]
        detections = [entry.get('wake_word_detections', 0) for entry in self.metrics_entries]
        true_positives = [entry.get('wake_word_true_positives', 0) for entry in self.metrics_entries]
        false_positives = [entry.get('wake_word_false_positives', 0) for entry in self.metrics_entries]
        
        return {
            'average_accuracy': statistics.mean(accuracies) if accuracies else 0.0,
            'min_accuracy': min(accuracies) if accuracies else 0.0,
            'max_accuracy': max(accuracies) if accuracies else 0.0,
            'total_detections': max(detections) if detections else 0,
            'total_true_positives': max(true_positives) if true_positives else 0,
            'total_false_positives': max(false_positives) if false_positives else 0
        }
    
    def analyze_stt_performance(self) -> Dict[str, Any]:
        """Analyze speech-to-text performance"""
        if not self.metrics_entries:
            return {'error': 'No metrics data available'}
        
        success_rates = [entry.get('stt_success_rate', 0.0) for entry in self.metrics_entries]
        latencies = [entry.get('stt_avg_latency_ms', 0.0) for entry in self.metrics_entries if entry.get('stt_avg_latency_ms', 0.0) > 0]
        requests = [entry.get('stt_requests', 0) for entry in self.metrics_entries]
        
        return {
            'average_success_rate': statistics.mean(success_rates) if success_rates else 0.0,
            'min_success_rate': min(success_rates) if success_rates else 0.0,
            'max_success_rate': max(success_rates) if success_rates else 0.0,
            'average_latency_ms': statistics.mean(latencies) if latencies else 0.0,
            'min_latency_ms': min(latencies) if latencies else 0.0,
            'max_latency_ms': max(latencies) if latencies else 0.0,
            'total_requests': max(requests) if requests else 0
        }
    
    def analyze_ai_performance(self) -> Dict[str, Any]:
        """Analyze AI service performance"""
        if not self.metrics_entries:
            return {'error': 'No metrics data available'}
        
        success_rates = [entry.get('ai_success_rate', 0.0) for entry in self.metrics_entries]
        latencies = [entry.get('ai_avg_latency_ms', 0.0) for entry in self.metrics_entries if entry.get('ai_avg_latency_ms', 0.0) > 0]
        requests = [entry.get('ai_requests', 0) for entry in self.metrics_entries]
        
        return {
            'average_success_rate': statistics.mean(success_rates) if success_rates else 0.0,
            'min_success_rate': min(success_rates) if success_rates else 0.0,
            'max_success_rate': max(success_rates) if success_rates else 0.0,
            'average_latency_ms': statistics.mean(latencies) if latencies else 0.0,
            'min_latency_ms': min(latencies) if latencies else 0.0,
            'max_latency_ms': max(latencies) if latencies else 0.0,
            'total_requests': max(requests) if requests else 0
        }
    
    def analyze_tts_performance(self) -> Dict[str, Any]:
        """Analyze text-to-speech performance"""
        if not self.metrics_entries:
            return {'error': 'No metrics data available'}
        
        success_rates = [entry.get('tts_success_rate', 0.0) for entry in self.metrics_entries]
        latencies = [entry.get('tts_avg_latency_ms', 0.0) for entry in self.metrics_entries if entry.get('tts_avg_latency_ms', 0.0) > 0]
        requests = [entry.get('tts_requests', 0) for entry in self.metrics_entries]
        
        return {
            'average_success_rate': statistics.mean(success_rates) if success_rates else 0.0,
            'min_success_rate': min(success_rates) if success_rates else 0.0,
            'max_success_rate': max(success_rates) if success_rates else 0.0,
            'average_latency_ms': statistics.mean(latencies) if latencies else 0.0,
            'min_latency_ms': min(latencies) if latencies else 0.0,
            'max_latency_ms': max(latencies) if latencies else 0.0,
            'total_requests': max(requests) if requests else 0
        }
    
    def analyze_error_rates(self) -> Dict[str, Any]:
        """Analyze error rates by component"""
        if not self.error_rate_entries:
            return {'error': 'No error rate data available'}
        
        # Collect error rates by component over time
        component_rates = defaultdict(list)
        
        for entry in self.error_rate_entries:
            error_rates = entry.get('error_rates', {})
            for component, rate in error_rates.items():
                component_rates[component].append(rate)
        
        # Calculate statistics for each component
        analysis = {}
        for component, rates in component_rates.items():
            analysis[component] = {
                'average_error_rate': statistics.mean(rates) if rates else 0.0,
                'min_error_rate': min(rates) if rates else 0.0,
                'max_error_rate': max(rates) if rates else 0.0,
                'samples': len(rates)
            }
        
        return analysis
    
    def analyze_conversation_metrics(self) -> Dict[str, Any]:
        """Analyze conversation-related metrics"""
        if not self.metrics_entries:
            return {'error': 'No metrics data available'}
        
        turns = [entry.get('conversation_turns', 0) for entry in self.metrics_entries]
        sessions = [entry.get('active_sessions', 0) for entry in self.metrics_entries]
        
        return {
            'total_conversation_turns': max(turns) if turns else 0,
            'peak_active_sessions': max(sessions) if sessions else 0,
            'average_active_sessions': statistics.mean(sessions) if sessions else 0.0
        }
    
    def generate_report(self) -> str:
        """Generate a comprehensive analysis report"""
        report = []
        report.append("=" * 70)
        report.append("PERFORMANCE METRICS ANALYSIS REPORT")
        report.append("=" * 70)
        report.append(f"Log file: {self.log_file}")
        report.append(f"Metrics entries analyzed: {len(self.metrics_entries)}")
        report.append(f"Error rate entries analyzed: {len(self.error_rate_entries)}")
        report.append("")
        
        # Wake word analysis
        report.append("-" * 70)
        report.append("WAKE WORD DETECTION ACCURACY")
        report.append("-" * 70)
        wake_word = self.analyze_wake_word_accuracy()
        if 'error' not in wake_word:
            report.append(f"  Average Accuracy: {wake_word['average_accuracy']:.2%}")
            report.append(f"  Min Accuracy: {wake_word['min_accuracy']:.2%}")
            report.append(f"  Max Accuracy: {wake_word['max_accuracy']:.2%}")
            report.append(f"  Total Detections: {wake_word['total_detections']}")
            report.append(f"  True Positives: {wake_word['total_true_positives']}")
            report.append(f"  False Positives: {wake_word['total_false_positives']}")
        else:
            report.append(f"  {wake_word['error']}")
        report.append("")
        
        # STT analysis
        report.append("-" * 70)
        report.append("SPEECH-TO-TEXT PERFORMANCE")
        report.append("-" * 70)
        stt = self.analyze_stt_performance()
        if 'error' not in stt:
            report.append(f"  Average Success Rate: {stt['average_success_rate']:.2%}")
            report.append(f"  Min Success Rate: {stt['min_success_rate']:.2%}")
            report.append(f"  Max Success Rate: {stt['max_success_rate']:.2%}")
            report.append(f"  Average Latency: {stt['average_latency_ms']:.1f}ms")
            report.append(f"  Min Latency: {stt['min_latency_ms']:.1f}ms")
            report.append(f"  Max Latency: {stt['max_latency_ms']:.1f}ms")
            report.append(f"  Total Requests: {stt['total_requests']}")
        else:
            report.append(f"  {stt['error']}")
        report.append("")
        
        # AI analysis
        report.append("-" * 70)
        report.append("AI SERVICE PERFORMANCE")
        report.append("-" * 70)
        ai = self.analyze_ai_performance()
        if 'error' not in ai:
            report.append(f"  Average Success Rate: {ai['average_success_rate']:.2%}")
            report.append(f"  Min Success Rate: {ai['min_success_rate']:.2%}")
            report.append(f"  Max Success Rate: {ai['max_success_rate']:.2%}")
            report.append(f"  Average Latency: {ai['average_latency_ms']:.1f}ms")
            report.append(f"  Min Latency: {ai['min_latency_ms']:.1f}ms")
            report.append(f"  Max Latency: {ai['max_latency_ms']:.1f}ms")
            report.append(f"  Total Requests: {ai['total_requests']}")
        else:
            report.append(f"  {ai['error']}")
        report.append("")
        
        # TTS analysis
        report.append("-" * 70)
        report.append("TEXT-TO-SPEECH PERFORMANCE")
        report.append("-" * 70)
        tts = self.analyze_tts_performance()
        if 'error' not in tts:
            report.append(f"  Average Success Rate: {tts['average_success_rate']:.2%}")
            report.append(f"  Min Success Rate: {tts['min_success_rate']:.2%}")
            report.append(f"  Max Success Rate: {tts['max_success_rate']:.2%}")
            report.append(f"  Average Latency: {tts['average_latency_ms']:.1f}ms")
            report.append(f"  Min Latency: {tts['min_latency_ms']:.1f}ms")
            report.append(f"  Max Latency: {tts['max_latency_ms']:.1f}ms")
            report.append(f"  Total Requests: {tts['total_requests']}")
        else:
            report.append(f"  {tts['error']}")
        report.append("")
        
        # Error rates analysis
        report.append("-" * 70)
        report.append("ERROR RATES BY COMPONENT")
        report.append("-" * 70)
        error_rates = self.analyze_error_rates()
        if 'error' not in error_rates:
            for component, stats in error_rates.items():
                report.append(f"  {component}:")
                report.append(f"    Average Error Rate: {stats['average_error_rate']:.2%}")
                report.append(f"    Min Error Rate: {stats['min_error_rate']:.2%}")
                report.append(f"    Max Error Rate: {stats['max_error_rate']:.2%}")
                report.append(f"    Samples: {stats['samples']}")
        else:
            report.append(f"  {error_rates['error']}")
        report.append("")
        
        # Conversation metrics
        report.append("-" * 70)
        report.append("CONVERSATION METRICS")
        report.append("-" * 70)
        conversation = self.analyze_conversation_metrics()
        if 'error' not in conversation:
            report.append(f"  Total Conversation Turns: {conversation['total_conversation_turns']}")
            report.append(f"  Peak Active Sessions: {conversation['peak_active_sessions']}")
            report.append(f"  Average Active Sessions: {conversation['average_active_sessions']:.1f}")
        else:
            report.append(f"  {conversation['error']}")
        report.append("")
        
        report.append("=" * 70)
        
        return "\n".join(report)


def main():
    """Main function for command-line usage"""
    parser = argparse.ArgumentParser(
        description='Analyze performance metrics from tyty_metrics.log'
    )
    parser.add_argument(
        '--log-file',
        default='./logs/tyty_metrics.log',
        help='Path to tyty_metrics.log file (default: ./logs/tyty_metrics.log)'
    )
    parser.add_argument(
        '--output',
        help='Output file path (default: print to console)'
    )
    
    args = parser.parse_args()
    
    try:
        # Create analyzer
        analyzer = MetricsAnalyzer(args.log_file)
        
        # Generate report
        report = analyzer.generate_report()
        
        # Output report
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"Report saved to: {args.output}")
        else:
            print(report)
    
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
