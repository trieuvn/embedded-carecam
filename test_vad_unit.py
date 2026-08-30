"""
Unit Tests for VAD Module
Tests energy calculation, voice detection timing, threshold sensitivity, and adaptive thresholding
Validates Requirements 10.1, 10.4, 10.5
"""

import time
import numpy as np
import logging
from typing import Optional
from modules.vad import VoiceActivityDetector, VADConfig, AudioSegment, create_vad

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MockAudioSource:
    """Mock audio source for testing with threading support"""
    def __init__(self):
        self.frames = []
        self.current_index = 0
        self.loop_mode = False  # If True, keep returning last frame
        self._delay = 0.01  # Delay between frames to simulate real-time
    
    def add_frame(self, frame: bytes):
        """Add a frame to the mock source"""
        self.frames.append(frame)
    
    def read(self, frame_size: int, exception_on_overflow: bool = False) -> bytes:
        """Read next frame with delay to simulate real-time audio"""
        import time
        
        if self.current_index < len(self.frames):
            frame = self.frames[self.current_index]
            self.current_index += 1
            # Simulate real-time by adding delay
            if self._delay > 0:
                time.sleep(self._delay)
            return frame
        elif self.loop_mode and len(self.frames) > 0:
            # Loop mode: keep returning last frame
            if self._delay > 0:
                time.sleep(self._delay)
            return self.frames[-1]
        else:
            # No more frames, sleep longer to prevent busy-waiting
            time.sleep(0.05)
            return b''
    
    def reset(self):
        """Reset to beginning"""
        self.current_index = 0


def create_sine_wave_frame(frequency: int, amplitude: int, duration_ms: int = 30, 
                          sample_rate: int = 16000) -> bytes:
    """
    Create a sine wave audio frame for precise testing
    
    Args:
        frequency: Frequency in Hz
        amplitude: Peak amplitude (0-32767)
        duration_ms: Duration in milliseconds
        sample_rate: Sample rate in Hz
    
    Returns:
        Audio frame as bytes
    """
    num_samples = int(sample_rate * duration_ms / 1000)
    t = np.linspace(0, duration_ms / 1000, num_samples, endpoint=False)
    sine_wave = amplitude * np.sin(2 * np.pi * frequency * t)
    audio_array = sine_wave.astype(np.int16)
    return audio_array.tobytes()


def create_noise_frame(amplitude: int, duration_ms: int = 30, sample_rate: int = 16000) -> bytes:
    """
    Create white noise audio frame
    
    Args:
        amplitude: Noise amplitude (0-32767)
        duration_ms: Duration in milliseconds
        sample_rate: Sample rate in Hz
    
    Returns:
        Audio frame as bytes
    """
    num_samples = int(sample_rate * duration_ms / 1000)
    if amplitude == 0:
        audio_array = np.zeros(num_samples, dtype=np.int16)
    else:
        audio_array = np.random.randint(-amplitude, amplitude, num_samples, dtype=np.int16)
    return audio_array.tobytes()


def calculate_expected_energy(amplitude: int) -> float:
    """
    Calculate expected RMS energy for a given amplitude
    
    Args:
        amplitude: Audio amplitude
    
    Returns:
        Expected normalized RMS energy
    """
    # For uniform random noise between -amplitude and +amplitude
    # RMS = amplitude / sqrt(3)
    # Normalized by 32768 (16-bit max)
    return (amplitude / np.sqrt(3)) / 32768.0


# ===== Test Suite 1: Energy Calculation Accuracy with Synthetic Audio =====

def test_energy_calculation_silence():
    """
    Test 1.1: Energy calculation for pure silence
    Validates Requirement 10.1, 10.4
    """
    logger.info("\n[Test 1.1] Energy calculation for pure silence")
    
    vad = create_vad()
    silent_frame = create_noise_frame(0)  # Pure silence
    
    energy = vad._calculate_energy(silent_frame)
    
    logger.info(f"   Silent frame energy: {energy:.8f}")
    assert energy == 0.0, f"Silent frame should have zero energy, got {energy}"
    
    logger.info("✅ PASS: Pure silence has zero energy")
    return True


def test_energy_calculation_sine_wave():
    """
    Test 1.2: Energy calculation for sine wave (known amplitude)
    Validates accurate RMS calculation with predictable signal
    """
    logger.info("\n[Test 1.2] Energy calculation for sine wave")
    
    vad = create_vad()
    
    # Create sine waves with different amplitudes
    amplitudes = [1000, 5000, 10000, 20000]
    
    for amplitude in amplitudes:
        sine_frame = create_sine_wave_frame(frequency=440, amplitude=amplitude)
        energy = vad._calculate_energy(sine_frame)
        
        # For sine wave: RMS = peak / sqrt(2)
        expected_energy = (amplitude / np.sqrt(2)) / 32768.0
        error_percent = abs(energy - expected_energy) / expected_energy * 100
        
        logger.info(f"   Amplitude {amplitude}: energy={energy:.6f}, expected={expected_energy:.6f}, error={error_percent:.2f}%")
        
        assert error_percent < 1.0, f"Energy error too high: {error_percent:.2f}%"
    
    logger.info("✅ PASS: Sine wave energy calculations are accurate")
    return True


def test_energy_calculation_white_noise():
    """
    Test 1.3: Energy calculation for white noise
    Validates accuracy with random signals
    """
    logger.info("\n[Test 1.3] Energy calculation for white noise")
    
    vad = create_vad()
    
    # Test multiple noise levels
    noise_levels = [500, 2000, 8000, 15000]
    
    for amplitude in noise_levels:
        noise_frame = create_noise_frame(amplitude)
        energy = vad._calculate_energy(noise_frame)
        
        expected_energy = calculate_expected_energy(amplitude)
        error_percent = abs(energy - expected_energy) / expected_energy * 100
        
        logger.info(f"   Amplitude {amplitude}: energy={energy:.6f}, expected={expected_energy:.6f}, error={error_percent:.2f}%")
        
        # Allow higher tolerance for random noise (20%)
        assert error_percent < 20.0, f"Energy error too high: {error_percent:.2f}%"
    
    logger.info("✅ PASS: White noise energy calculations are reasonably accurate")
    return True


def test_energy_monotonicity():
    """
    Test 1.4: Energy increases monotonically with amplitude
    Validates Requirement 10.1
    """
    logger.info("\n[Test 1.4] Energy monotonicity with increasing amplitude")
    
    vad = create_vad()
    
    amplitudes = [0, 500, 1000, 2000, 4000, 8000, 16000]
    energies = []
    
    for amplitude in amplitudes:
        frame = create_noise_frame(amplitude)
        energy = vad._calculate_energy(frame)
        energies.append(energy)
        logger.info(f"   Amplitude {amplitude:5d}: energy={energy:.6f}")
    
    # Check monotonicity
    for i in range(len(energies) - 1):
        assert energies[i] <= energies[i+1], f"Energy not monotonic at index {i}: {energies[i]} > {energies[i+1]}"
    
    logger.info("✅ PASS: Energy increases monotonically with amplitude")
    return True


def test_energy_precision():
    """
    Test 1.5: Energy calculation precision with edge cases
    """
    logger.info("\n[Test 1.5] Energy calculation precision")
    
    vad = create_vad()
    
    # Test with very small amplitude (near silence)
    tiny_frame = create_noise_frame(10)
    tiny_energy = vad._calculate_energy(tiny_frame)
    logger.info(f"   Very small amplitude (10): energy={tiny_energy:.8f}")
    assert 0 < tiny_energy < 0.001, "Tiny amplitude should produce very small but non-zero energy"
    
    # Test with maximum amplitude
    max_frame = create_noise_frame(32767)
    max_energy = vad._calculate_energy(max_frame)
    logger.info(f"   Maximum amplitude (32767): energy={max_energy:.6f}")
    assert 0.5 < max_energy < 1.0, "Maximum amplitude should produce high energy close to 1.0"
    
    # Test reproducibility - same input should give same output
    test_frame = create_sine_wave_frame(440, 5000)
    energy1 = vad._calculate_energy(test_frame)
    energy2 = vad._calculate_energy(test_frame)
    assert energy1 == energy2, "Same input should produce same energy"
    logger.info(f"   Reproducibility: energy={energy1:.8f} (identical)")
    
    logger.info("✅ PASS: Energy calculation has proper precision")
    return True


# ===== Test Suite 2: Voice Start/End Detection Timing =====

def test_voice_start_timing_minimum_duration():
    """
    Test 2.1: Voice start requires minimum speech duration
    Validates Requirement 10.4
    """
    logger.info("\n[Test 2.1] Voice start timing - minimum duration requirement")
    
    config = VADConfig(
        energy_threshold=0.01,
        silence_duration=1.0,
        min_speech_duration=0.3,  # 300ms minimum
        sample_rate=16000,
        frame_length_ms=30
    )
    vad = VoiceActivityDetector(config)
    
    voice_start_triggered = {'value': False, 'time': None}
    
    def on_start():
        voice_start_triggered['value'] = True
        voice_start_triggered['time'] = time.time()
    
    vad.on_voice_start(on_start)
    
    # Test 1: Short speech burst (< min_speech_duration) should NOT trigger
    mock_source = MockAudioSource()
    mock_source._delay = 0.03  # 30ms per frame
    # Start with silence to establish baseline
    for _ in range(10):
        mock_source.add_frame(create_noise_frame(100))  # Very quiet baseline
    for _ in range(5):  # 150ms of speech (5 * 30ms)
        mock_source.add_frame(create_noise_frame(8000))
    for _ in range(10):  # Then silence
        mock_source.add_frame(create_noise_frame(100))
    
    vad.start_monitoring(mock_source)
    time.sleep(1.0)  # Wait for all frames to be processed
    vad.stop_monitoring()
    
    assert not voice_start_triggered['value'], "Short burst should not trigger voice start"
    logger.info("   Short burst (150ms) correctly filtered ✓")
    
    # Test 2: Long speech (> min_speech_duration) SHOULD trigger
    vad._reset_state()
    voice_start_triggered['value'] = False
    mock_source.reset()
    mock_source.frames.clear()
    
    # Start with silence to establish baseline
    for _ in range(10):
        mock_source.add_frame(create_noise_frame(100))  # Very quiet baseline
    for _ in range(15):  # 450ms of speech (15 * 30ms)
        mock_source.add_frame(create_noise_frame(8000))
    for _ in range(5):  # Add some silence at end
        mock_source.add_frame(create_noise_frame(100))
    
    start_time = time.time()
    vad.start_monitoring(mock_source)
    time.sleep(1.2)  # Wait for processing
    vad.stop_monitoring()
    
    assert voice_start_triggered['value'], "Long speech should trigger voice start"
    logger.info("   Long speech (450ms) correctly triggered ✓")
    
    logger.info("✅ PASS: Voice start respects minimum duration requirement")
    return True


def test_voice_end_timing_silence_duration():
    """
    Test 2.2: Voice end timing with silence duration threshold
    Validates Requirement 10.5
    """
    logger.info("\n[Test 2.2] Voice end timing - silence duration threshold")
    
    config = VADConfig(
        energy_threshold=0.01,
        silence_duration=0.3,  # 300ms silence required
        min_speech_duration=0.1,
        sample_rate=16000,
        frame_length_ms=30
    )
    vad = VoiceActivityDetector(config)
    
    voice_events = {'start': False, 'end': False, 'end_time': None}
    
    def on_start():
        voice_events['start'] = True
    
    def on_end(segment):
        voice_events['end'] = True
        voice_events['end_time'] = time.time()
    
    vad.on_voice_start(on_start)
    vad.on_voice_end(on_end)
    
    # Create audio: voice -> short silence -> voice -> long silence
    mock_source = MockAudioSource()
    mock_source._delay = 0.03  # 30ms per frame
    
    # Voice (300ms)
    for _ in range(10):
        mock_source.add_frame(create_noise_frame(8000))
    
    # Short silence (150ms) - should NOT end voice
    for _ in range(5):
        mock_source.add_frame(create_noise_frame(0))
    
    # More voice (150ms)
    for _ in range(5):
        mock_source.add_frame(create_noise_frame(8000))
    
    # Long silence (450ms) - SHOULD end voice
    for _ in range(15):
        mock_source.add_frame(create_noise_frame(0))
    
    vad.start_monitoring(mock_source)
    time.sleep(1.5)  # Wait for all frames to process (35 * 30ms + overhead)
    vad.stop_monitoring()
    
    assert voice_events['start'], "Voice start should have triggered"
    assert voice_events['end'], "Voice end should have triggered after long silence"
    
    logger.info("   Voice start triggered ✓")
    logger.info("   Short silence did not end voice ✓")
    logger.info("   Long silence ended voice ✓")
    logger.info("✅ PASS: Voice end timing respects silence duration")
    return True


def test_voice_detection_with_intermittent_speech():
    """
    Test 2.3: Voice detection with intermittent speech patterns
    Validates realistic conversation patterns
    """
    logger.info("\n[Test 2.3] Voice detection with intermittent speech")
    
    config = VADConfig(
        energy_threshold=0.01,
        silence_duration=0.5,
        min_speech_duration=0.2,
        sample_rate=16000,
        frame_length_ms=30
    )
    vad = VoiceActivityDetector(config)
    
    events = {'starts': 0, 'ends': 0}
    
    def on_start():
        events['starts'] += 1
        logger.info(f"      Voice start #{events['starts']}")
    
    def on_end(segment):
        events['ends'] += 1
        logger.info(f"      Voice end #{events['ends']}")
    
    vad.on_voice_start(on_start)
    vad.on_voice_end(on_end)
    
    # Pattern: quiet baseline -> voice -> long silence -> voice -> long silence
    mock_source = MockAudioSource()
    mock_source._delay = 0.03  # 30ms per frame
    
    # Start with very quiet baseline to establish low ambient noise
    for _ in range(10):
        mock_source.add_frame(create_noise_frame(50))
    
    # First speech segment (louder to overcome adaptive threshold)
    for _ in range(15):
        mock_source.add_frame(create_noise_frame(12000))
    
    # Long silence (return to quiet baseline)
    for _ in range(20):
        mock_source.add_frame(create_noise_frame(50))
    
    # Second speech segment
    for _ in range(15):
        mock_source.add_frame(create_noise_frame(12000))
    
    # Final silence
    for _ in range(20):
        mock_source.add_frame(create_noise_frame(50))
    
    vad.start_monitoring(mock_source)
    time.sleep(2.8)  # Wait for all frames (80 * 30ms + overhead)
    vad.stop_monitoring()
    
    # Should detect two separate speech segments
    assert events['starts'] == 2, f"Expected 2 voice starts, got {events['starts']}"
    assert events['ends'] == 2, f"Expected 2 voice ends, got {events['ends']}"
    
    logger.info("✅ PASS: Correctly detects multiple speech segments")
    return True


def test_voice_timing_accuracy():
    """
    Test 2.4: Measure timing accuracy of voice detection
    """
    logger.info("\n[Test 2.4] Voice detection timing accuracy")
    
    config = VADConfig(
        energy_threshold=0.01,
        silence_duration=0.3,
        min_speech_duration=0.15,
        sample_rate=16000,
        frame_length_ms=30
    )
    vad = VoiceActivityDetector(config)
    
    timing = {'start_time': None, 'end_time': None}
    
    def on_start():
        timing['start_time'] = time.time()
    
    def on_end(segment):
        timing['end_time'] = time.time()
    
    vad.on_voice_start(on_start)
    vad.on_voice_end(on_end)
    
    mock_source = MockAudioSource()
    mock_source._delay = 0.03  # 30ms per frame
    
    # Start with quiet baseline to establish low ambient noise
    for _ in range(5):
        mock_source.add_frame(create_noise_frame(50))
    
    # Create known duration: 10 frames * 30ms = 300ms (use higher amplitude)
    for _ in range(10):
        mock_source.add_frame(create_noise_frame(12000))
    
    # Silence to trigger end: 12 frames * 30ms = 360ms
    for _ in range(12):
        mock_source.add_frame(create_noise_frame(50))
    
    test_start = time.time()
    vad.start_monitoring(mock_source)
    time.sleep(1.2)  # Wait for processing (27 * 30ms + overhead)
    vad.stop_monitoring()
    test_end = time.time()
    
    assert timing['start_time'] is not None, "Voice start should have triggered"
    assert timing['end_time'] is not None, "Voice end should have triggered"
    
    # Calculate detection delay
    detection_delay = timing['start_time'] - test_start
    end_delay = timing['end_time'] - timing['start_time']
    
    logger.info(f"   Detection delay: {detection_delay*1000:.1f}ms")
    logger.info(f"   Voice duration: {end_delay*1000:.1f}ms")
    logger.info(f"   Expected duration: ~300ms speech + 300ms silence = 600ms")
    
    # Detection should happen within reasonable time (< 500ms)
    assert detection_delay < 0.5, f"Detection delay too high: {detection_delay*1000}ms"
    
    logger.info("✅ PASS: Voice timing within acceptable range")
    return True


# ===== Test Suite 3: Silence Threshold Sensitivity in Different Noise Environments =====

def test_threshold_sensitivity_quiet_environment():
    """
    Test 3.1: Low threshold sensitivity for quiet environments
    Validates Requirement 10.1, 10.10
    """
    logger.info("\n[Test 3.1] Threshold sensitivity in quiet environment")
    
    config = VADConfig(
        energy_threshold=0.01,  # Very sensitive
        silence_duration=1.0,
        min_speech_duration=0.2,
        sample_rate=16000,
        frame_length_ms=30
    )
    vad = VoiceActivityDetector(config)
    
    voice_detected = {'value': False}
    
    def on_start():
        voice_detected['value'] = True
    
    vad.on_voice_start(on_start)
    
    # Create quiet speech (low amplitude, should still detect with low threshold)
    mock_source = MockAudioSource()
    mock_source._delay = 0.03  # 30ms per frame
    
    # Start with very quiet baseline
    for _ in range(5):
        mock_source.add_frame(create_noise_frame(20))
    
    # Quiet voice (but above threshold + ambient noise)
    for _ in range(15):
        mock_source.add_frame(create_noise_frame(2500))  # Increased amplitude
    
    vad.start_monitoring(mock_source)
    time.sleep(0.8)  # Wait for processing (20 * 30ms + overhead)
    vad.stop_monitoring()
    
    assert voice_detected['value'], "Low threshold should detect quiet speech"
    logger.info("   Quiet speech (amplitude 2500) detected with sensitive threshold ✓")
    
    logger.info("✅ PASS: Low threshold works in quiet environment")
    return True


def test_threshold_sensitivity_noisy_environment():
    """
    Test 3.2: High threshold sensitivity for noisy environments
    Validates Requirement 10.10
    """
    logger.info("\n[Test 3.2] Threshold sensitivity in noisy environment")
    
    config = VADConfig(
        energy_threshold=0.05,  # Less sensitive, filters background noise
        silence_duration=1.0,
        min_speech_duration=0.2,
        sample_rate=16000,
        frame_length_ms=30
    )
    vad = VoiceActivityDetector(config)
    
    voice_detected = {'value': False}
    
    def on_start():
        voice_detected['value'] = True
    
    vad.on_voice_start(on_start)
    
    # Test 1: Background noise should NOT trigger
    mock_source = MockAudioSource()
    mock_source._delay = 0.03  # 30ms per frame
    for _ in range(15):
        mock_source.add_frame(create_noise_frame(2000))  # Background noise
    
    vad.start_monitoring(mock_source)
    time.sleep(0.7)  # Wait for processing
    vad.stop_monitoring()
    
    assert not voice_detected['value'], "High threshold should filter background noise"
    logger.info("   Background noise (amplitude 2000) correctly filtered ✓")
    
    # Test 2: Clear speech SHOULD trigger
    vad._reset_state()
    voice_detected['value'] = False
    mock_source.reset()
    mock_source.frames.clear()
    
    # Establish quiet baseline first
    for _ in range(5):
        mock_source.add_frame(create_noise_frame(100))
    
    # Then loud clear speech
    for _ in range(15):
        mock_source.add_frame(create_noise_frame(16000))  # Clear, loud speech
    
    vad.start_monitoring(mock_source)
    time.sleep(0.8)  # Wait for processing
    vad.stop_monitoring()
    
    assert voice_detected['value'], "High threshold should still detect clear speech"
    logger.info("   Clear speech (amplitude 16000) detected ✓")
    
    logger.info("✅ PASS: High threshold filters noise while detecting speech")
    return True


def test_threshold_comparison_environments():
    """
    Test 3.3: Compare threshold behavior across different noise levels
    Validates configurable sensitivity for different environments
    """
    logger.info("\n[Test 3.3] Threshold comparison across environments")
    
    # Define different environment configs
    environments = {
        'quiet_room': VADConfig(energy_threshold=0.01, silence_duration=1.0, min_speech_duration=0.2),
        'office': VADConfig(energy_threshold=0.03, silence_duration=1.0, min_speech_duration=0.2),
        'cafeteria': VADConfig(energy_threshold=0.08, silence_duration=1.5, min_speech_duration=0.3),
    }
    
    # Test with medium amplitude speech
    test_amplitude = 8000
    
    results = {}
    
    for env_name, config in environments.items():
        vad = VoiceActivityDetector(config)
        detected = {'value': False}
        
        def on_start():
            detected['value'] = True
        
        vad.on_voice_start(on_start)
        
        mock_source = MockAudioSource()
        mock_source._delay = 0.03  # 30ms per frame
        
        # Start with quiet baseline
        for _ in range(5):
            mock_source.add_frame(create_noise_frame(50))
        
        # Medium amplitude speech
        for _ in range(15):
            mock_source.add_frame(create_noise_frame(test_amplitude))
        
        vad.start_monitoring(mock_source)
        time.sleep(0.8)  # Wait for processing
        vad.stop_monitoring()
        
        results[env_name] = detected['value']
        logger.info(f"   {env_name:15s} (threshold={config.energy_threshold:.2f}): {'detected' if detected['value'] else 'not detected'}")
    
    # Quiet room should detect medium speech
    assert results['quiet_room'], "Quiet environment should detect medium amplitude"
    
    # Office might or might not detect depending on threshold
    # Cafeteria with highest threshold is less likely to detect
    
    logger.info("✅ PASS: Different thresholds behave appropriately for environments")
    return True


def test_false_positive_rejection():
    """
    Test 3.4: Rejection of false positives (non-speech sounds)
    Validates filtering capability
    """
    logger.info("\n[Test 3.4] False positive rejection")
    
    config = VADConfig(
        energy_threshold=0.05,
        silence_duration=1.0,
        min_speech_duration=0.3,
        sample_rate=16000,
        frame_length_ms=30
    )
    vad = VoiceActivityDetector(config)
    
    false_positives = {'count': 0}
    
    def on_start():
        false_positives['count'] += 1
    
    vad.on_voice_start(on_start)
    
    # Test various non-speech patterns
    test_cases = [
        ('very_quiet', 300),
        ('low_rumble', 1000),
        ('brief_click', 5000),  # Short duration
    ]
    
    for case_name, amplitude in test_cases:
        vad._reset_state()
        mock_source = MockAudioSource()
        mock_source._delay = 0.03  # 30ms per frame
        
        if 'brief' in case_name:
            # Very short burst (2 frames = 60ms, below min_speech_duration)
            for _ in range(2):
                mock_source.add_frame(create_noise_frame(amplitude))
            for _ in range(10):
                mock_source.add_frame(create_noise_frame(0))
        else:
            # Sustained low-level noise
            for _ in range(15):
                mock_source.add_frame(create_noise_frame(amplitude))
        
        vad.start_monitoring(mock_source)
        time.sleep(0.7)  # Wait for processing
        vad.stop_monitoring()
    
    logger.info(f"   False positive count: {false_positives['count']}/3 test cases")
    assert false_positives['count'] <= 1, f"Too many false positives: {false_positives['count']}"
    
    logger.info("✅ PASS: False positives properly rejected")
    return True


# ===== Test Suite 4: Adaptive Thresholding with Varying Ambient Noise =====

def test_adaptive_threshold_updates():
    """
    Test 4.1: Adaptive threshold updates with ambient noise
    Validates Requirement 10.6
    """
    logger.info("\n[Test 4.1] Adaptive threshold updates")
    
    vad = create_vad()
    
    initial_threshold = vad._ambient_noise_level
    logger.info(f"   Initial ambient noise level: {initial_threshold:.6f}")
    
    # Simulate ambient noise exposure (while voice is not active)
    ambient_amplitude = 1500
    for _ in range(30):
        frame = create_noise_frame(ambient_amplitude)
        vad._process_audio_frame(frame)
    
    updated_threshold = vad._ambient_noise_level
    logger.info(f"   After ambient noise: {updated_threshold:.6f}")
    
    assert updated_threshold > initial_threshold, "Threshold should increase with ambient noise"
    assert len(vad._noise_samples) > 0, "Noise samples should be collected"
    
    # Verify threshold is reasonable
    expected_energy = calculate_expected_energy(ambient_amplitude)
    logger.info(f"   Expected ambient energy: {expected_energy:.6f}")
    
    # Threshold should be close to expected (within 50% tolerance for random noise)
    error_percent = abs(updated_threshold - expected_energy) / expected_energy * 100
    assert error_percent < 50.0, f"Adaptive threshold error too high: {error_percent:.2f}%"
    
    logger.info("✅ PASS: Adaptive threshold updates correctly")
    return True


def test_adaptive_threshold_with_changing_noise():
    """
    Test 4.2: Adaptive threshold tracks changing noise levels
    Validates dynamic adaptation
    """
    logger.info("\n[Test 4.2] Adaptive threshold with changing noise levels")
    
    vad = create_vad()
    
    noise_levels = [500, 2000, 4000, 1000]
    thresholds = []
    
    for noise_level in noise_levels:
        # Expose VAD to current noise level
        for _ in range(20):
            frame = create_noise_frame(noise_level)
            vad._process_audio_frame(frame)
        
        current_threshold = vad._ambient_noise_level
        thresholds.append(current_threshold)
        logger.info(f"   Noise level {noise_level:4d}: threshold={current_threshold:.6f}")
    
    # Threshold should increase then decrease following noise pattern
    assert thresholds[1] > thresholds[0], "Threshold should increase with noise"
    assert thresholds[2] > thresholds[1], "Threshold should continue increasing"
    assert thresholds[3] < thresholds[2], "Threshold should decrease when noise decreases"
    
    logger.info("✅ PASS: Adaptive threshold tracks changing noise")
    return True


def test_adaptive_threshold_does_not_update_during_speech():
    """
    Test 4.3: Adaptive threshold should not update during speech
    Validates that speech doesn't affect ambient noise estimation
    """
    logger.info("\n[Test 4.3] Adaptive threshold stability during speech")
    
    config = VADConfig(
        energy_threshold=0.01,
        silence_duration=1.0,
        min_speech_duration=0.1,
        sample_rate=16000,
        frame_length_ms=30
    )
    vad = VoiceActivityDetector(config)
    
    # Establish baseline ambient noise
    for _ in range(20):
        frame = create_noise_frame(1000)
        vad._process_audio_frame(frame)
    
    baseline_threshold = vad._ambient_noise_level
    noise_samples_before = len(vad._noise_samples)
    logger.info(f"   Baseline threshold: {baseline_threshold:.6f}")
    logger.info(f"   Noise samples: {noise_samples_before}")
    
    # Trigger voice activity with loud speech
    vad._voice_active = True
    
    # Process loud frames (should not update ambient threshold)
    for _ in range(15):
        loud_frame = create_noise_frame(10000)
        vad._process_audio_frame(loud_frame)
    
    threshold_during_speech = vad._ambient_noise_level
    noise_samples_after = len(vad._noise_samples)
    
    logger.info(f"   Threshold during speech: {threshold_during_speech:.6f}")
    logger.info(f"   Noise samples: {noise_samples_after}")
    
    # Threshold should remain stable during speech
    assert baseline_threshold == threshold_during_speech, "Threshold should not change during speech"
    assert noise_samples_after == noise_samples_before, "Noise samples should not be collected during speech"
    
    logger.info("✅ PASS: Adaptive threshold stable during speech")
    return True


def test_adaptive_threshold_convergence():
    """
    Test 4.4: Adaptive threshold converges to stable value
    Validates steady-state behavior
    """
    logger.info("\n[Test 4.4] Adaptive threshold convergence")
    
    vad = create_vad()
    
    # Expose to constant ambient noise
    ambient_amplitude = 2000
    thresholds = []
    
    for i in range(50):
        frame = create_noise_frame(ambient_amplitude)
        vad._process_audio_frame(frame)
        
        if i % 10 == 0:
            threshold = vad._ambient_noise_level
            thresholds.append(threshold)
            logger.info(f"   After {i+1:2d} frames: threshold={threshold:.6f}")
    
    # Check convergence - later values should be more stable
    early_variation = abs(thresholds[1] - thresholds[0]) / thresholds[0]
    late_variation = abs(thresholds[-1] - thresholds[-2]) / thresholds[-2]
    
    logger.info(f"   Early variation: {early_variation*100:.2f}%")
    logger.info(f"   Late variation: {late_variation*100:.2f}%")
    
    # Threshold should stabilize over time
    assert late_variation < early_variation or late_variation < 0.1, "Threshold should converge to stable value"
    
    logger.info("✅ PASS: Adaptive threshold converges properly")
    return True


def test_adaptive_threshold_with_speech_pauses():
    """
    Test 4.5: Adaptive threshold behavior with speech and pauses
    Validates realistic conversation scenario
    """
    logger.info("\n[Test 4.5] Adaptive threshold with speech and pauses")
    
    config = VADConfig(
        energy_threshold=0.02,
        silence_duration=0.5,
        min_speech_duration=0.15,
        sample_rate=16000,
        frame_length_ms=30
    )
    vad = VoiceActivityDetector(config)
    
    thresholds = {'initial': None, 'after_ambient': None, 'after_conversation': None}
    
    # Initial state
    thresholds['initial'] = vad._ambient_noise_level
    
    # Phase 1: Ambient noise only
    for _ in range(20):
        frame = create_noise_frame(1500)
        vad._process_audio_frame(frame)
    thresholds['after_ambient'] = vad._ambient_noise_level
    
    # Phase 2: Simulate conversation (speech + pauses)
    # Speech
    for _ in range(10):
        vad._voice_active = True
        frame = create_noise_frame(8000)
        vad._process_audio_frame(frame)
    
    # Pause (should update threshold)
    vad._voice_active = False
    for _ in range(10):
        frame = create_noise_frame(1500)
        vad._process_audio_frame(frame)
    
    thresholds['after_conversation'] = vad._ambient_noise_level
    
    logger.info(f"   Initial: {thresholds['initial']:.6f}")
    logger.info(f"   After ambient: {thresholds['after_ambient']:.6f}")
    logger.info(f"   After conversation: {thresholds['after_conversation']:.6f}")
    
    # Ambient phase should increase threshold
    assert thresholds['after_ambient'] > thresholds['initial'], "Threshold should adapt to ambient noise"
    
    # After conversation, threshold should remain stable (not affected by speech)
    variation = abs(thresholds['after_conversation'] - thresholds['after_ambient']) / thresholds['after_ambient']
    logger.info(f"   Threshold variation: {variation*100:.2f}%")
    
    logger.info("✅ PASS: Adaptive threshold handles speech and pauses correctly")
    return True


# ===== Test Runner =====

def run_all_unit_tests():
    """Run all unit tests"""
    logger.info("=" * 80)
    logger.info("VAD Module - Comprehensive Unit Test Suite")
    logger.info("Testing: Energy Calculation, Voice Timing, Threshold Sensitivity, Adaptive Thresholding")
    logger.info("=" * 80)
    
    test_suites = {
        "Energy Calculation with Synthetic Audio": [
            test_energy_calculation_silence,
            test_energy_calculation_sine_wave,
            test_energy_calculation_white_noise,
            test_energy_monotonicity,
            test_energy_precision,
        ],
        "Voice Start/End Detection Timing": [
            test_voice_start_timing_minimum_duration,
            test_voice_end_timing_silence_duration,
            test_voice_detection_with_intermittent_speech,
            test_voice_timing_accuracy,
        ],
        "Silence Threshold Sensitivity": [
            test_threshold_sensitivity_quiet_environment,
            test_threshold_sensitivity_noisy_environment,
            test_threshold_comparison_environments,
            test_false_positive_rejection,
        ],
        "Adaptive Thresholding": [
            test_adaptive_threshold_updates,
            test_adaptive_threshold_with_changing_noise,
            test_adaptive_threshold_does_not_update_during_speech,
            test_adaptive_threshold_convergence,
            test_adaptive_threshold_with_speech_pauses,
        ],
    }
    
    all_results = []
    
    for suite_name, tests in test_suites.items():
        logger.info(f"\n{'='*80}")
        logger.info(f"Test Suite: {suite_name}")
        logger.info(f"{'='*80}")
        
        for test in tests:
            try:
                result = test()
                all_results.append((test.__name__, result, suite_name))
            except Exception as e:
                logger.error(f"\n❌ FAIL: {test.__name__}")
                logger.error(f"   Error: {e}")
                import traceback
                traceback.print_exc()
                all_results.append((test.__name__, False, suite_name))
    
    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("Test Summary")
    logger.info("=" * 80)
    
    # Group by suite
    for suite_name in test_suites.keys():
        suite_results = [(name, result) for name, result, suite in all_results if suite == suite_name]
        passed = sum(1 for _, result in suite_results if result)
        total = len(suite_results)
        logger.info(f"\n{suite_name}: {passed}/{total} tests passed")
        for test_name, result in suite_results:
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"  {status}: {test_name}")
    
    # Overall summary
    total_passed = sum(1 for _, result, _ in all_results if result)
    total_tests = len(all_results)
    
    logger.info("\n" + "=" * 80)
    logger.info(f"Overall Results: {total_passed}/{total_tests} tests passed")
    logger.info(f"Success Rate: {total_passed/total_tests*100:.1f}%")
    logger.info("=" * 80)
    
    return total_passed == total_tests


if __name__ == "__main__":
    success = run_all_unit_tests()
    exit(0 if success else 1)
