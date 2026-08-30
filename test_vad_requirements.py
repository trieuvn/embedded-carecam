"""
Test VAD Module Against Requirements
Validates all acceptance criteria from Requirement 10
"""

import time
import numpy as np
import logging
from modules.vad import VoiceActivityDetector, VADConfig, AudioSegment, create_vad

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


class MockAudioSource:
    """Mock audio source for testing"""
    def __init__(self):
        self.frames = []
        self.current_index = 0
    
    def add_frame(self, frame: bytes):
        """Add a frame to the mock source"""
        self.frames.append(frame)
    
    def read(self, frame_size: int, exception_on_overflow: bool = False) -> bytes:
        """Read next frame"""
        if self.current_index < len(self.frames):
            frame = self.frames[self.current_index]
            self.current_index += 1
            return frame
        return b''  # Return empty if no more frames
    
    def reset(self):
        """Reset to beginning"""
        self.current_index = 0


def create_audio_frame(amplitude: int, duration_ms: int = 30, sample_rate: int = 16000) -> bytes:
    """
    Create synthetic audio frame
    
    Args:
        amplitude: Audio amplitude (0 = silence, higher = louder)
        duration_ms: Duration in milliseconds
        sample_rate: Sample rate in Hz
    
    Returns:
        Audio frame as bytes
    """
    num_samples = int(sample_rate * duration_ms / 1000)
    if amplitude == 0:
        # Pure silence
        audio_array = np.zeros(num_samples, dtype=np.int16)
    else:
        # Random noise with specified amplitude
        audio_array = np.random.randint(-amplitude, amplitude, num_samples, dtype=np.int16)
    return audio_array.tobytes()


def test_requirement_10_1():
    """
    Requirement 10.1: THE VAD_Module SHALL khởi tạo với cấu hình 
    energy_threshold, silence_duration, min_speech_duration, sample_rate
    """
    logger.info("\n[Test 10.1] VAD initialization with config")
    
    config = VADConfig(
        energy_threshold=0.025,
        silence_duration=2.0,
        min_speech_duration=0.5,
        sample_rate=16000,
        frame_length_ms=30
    )
    
    vad = VoiceActivityDetector(config)
    
    assert vad.config.energy_threshold == 0.025, "energy_threshold not set correctly"
    assert vad.config.silence_duration == 2.0, "silence_duration not set correctly"
    assert vad.config.min_speech_duration == 0.5, "min_speech_duration not set correctly"
    assert vad.config.sample_rate == 16000, "sample_rate not set correctly"
    assert vad.config.frame_length_ms == 30, "frame_length_ms not set correctly"
    
    logger.info("✅ PASS: VAD initializes with all config parameters")
    return True


def test_requirement_10_2():
    """
    Requirement 10.2: WHEN VAD_Module bắt đầu monitoring, 
    THE VAD_Module SHALL nhận audio stream từ audio source
    """
    logger.info("\n[Test 10.2] VAD starts monitoring audio stream")
    
    vad = create_vad()
    mock_source = MockAudioSource()
    
    # Add some test frames
    for _ in range(10):
        mock_source.add_frame(create_audio_frame(1000))
    
    # Start monitoring
    vad.start_monitoring(mock_source)
    
    # Give it time to process
    time.sleep(0.5)
    
    # Check that monitoring is active
    assert vad._is_monitoring, "VAD should be monitoring"
    assert vad._audio_source is not None, "Audio source should be set"
    
    # Stop monitoring
    vad.stop_monitoring()
    
    logger.info("✅ PASS: VAD starts monitoring and receives audio stream")
    return True


def test_requirement_10_3():
    """
    Requirement 10.3: THE VAD_Module SHALL tính short-term energy của audio frames
    """
    logger.info("\n[Test 10.3] VAD calculates short-term energy")
    
    vad = create_vad()
    
    # Create frames with different amplitudes
    silent_frame = create_audio_frame(0)  # Silence
    quiet_frame = create_audio_frame(500)  # Quiet
    loud_frame = create_audio_frame(10000)  # Loud
    
    energy_silent = vad._calculate_energy(silent_frame)
    energy_quiet = vad._calculate_energy(quiet_frame)
    energy_loud = vad._calculate_energy(loud_frame)
    
    logger.info(f"   Silent energy: {energy_silent:.6f}")
    logger.info(f"   Quiet energy: {energy_quiet:.6f}")
    logger.info(f"   Loud energy: {energy_loud:.6f}")
    
    # Verify energy increases with amplitude
    assert energy_silent < energy_quiet, "Silent should have less energy than quiet"
    assert energy_quiet < energy_loud, "Quiet should have less energy than loud"
    
    logger.info("✅ PASS: VAD calculates short-term energy correctly")
    return True


def test_requirement_10_4():
    """
    Requirement 10.4: WHEN audio energy vượt threshold, 
    THE VAD_Module SHALL phát event on_voice_start
    """
    logger.info("\n[Test 10.4] VAD triggers on_voice_start event")
    
    config = VADConfig(
        energy_threshold=0.01,
        silence_duration=1.0,
        min_speech_duration=0.1,  # Short duration for quick testing
        sample_rate=16000,
        frame_length_ms=30
    )
    vad = VoiceActivityDetector(config)
    
    voice_start_triggered = {'value': False}
    
    def on_start():
        voice_start_triggered['value'] = True
        logger.info("   🎤 on_voice_start triggered!")
    
    vad.on_voice_start(on_start)
    
    # Create mock source with loud frames (should trigger voice start)
    mock_source = MockAudioSource()
    for _ in range(10):  # Enough frames to exceed min_speech_duration
        mock_source.add_frame(create_audio_frame(8000))  # Loud audio
    
    vad.start_monitoring(mock_source)
    time.sleep(0.5)  # Wait for processing
    vad.stop_monitoring()
    
    assert voice_start_triggered['value'], "on_voice_start should have been triggered"
    
    logger.info("✅ PASS: VAD triggers on_voice_start when energy exceeds threshold")
    return True


def test_requirement_10_5():
    """
    Requirement 10.5: WHEN audio energy dưới threshold trong silence_duration,
    THE VAD_Module SHALL phát event on_voice_end
    """
    logger.info("\n[Test 10.5] VAD triggers on_voice_end event")
    
    config = VADConfig(
        energy_threshold=0.01,
        silence_duration=0.3,  # Short for quick testing
        min_speech_duration=0.1,
        sample_rate=16000,
        frame_length_ms=30
    )
    vad = VoiceActivityDetector(config)
    
    voice_end_triggered = {'value': False}
    
    def on_end(segment):
        voice_end_triggered['value'] = True
        logger.info(f"   🔇 on_voice_end triggered! Segment: {segment}")
    
    vad.on_voice_end(on_end)
    
    # Create mock source: loud frames (voice) followed by silent frames
    mock_source = MockAudioSource()
    
    # Voice frames
    for _ in range(10):
        mock_source.add_frame(create_audio_frame(8000))
    
    # Silence frames (enough to trigger voice_end)
    for _ in range(15):
        mock_source.add_frame(create_audio_frame(0))
    
    vad.start_monitoring(mock_source)
    time.sleep(1.0)  # Wait for processing
    vad.stop_monitoring()
    
    assert voice_end_triggered['value'], "on_voice_end should have been triggered"
    
    logger.info("✅ PASS: VAD triggers on_voice_end after silence duration")
    return True


def test_requirement_10_6():
    """
    Requirement 10.6: THE VAD_Module SHALL áp dụng adaptive thresholding 
    dựa trên ambient noise level
    """
    logger.info("\n[Test 10.6] VAD applies adaptive thresholding")
    
    vad = create_vad()
    
    initial_noise_level = vad._ambient_noise_level
    logger.info(f"   Initial ambient noise level: {initial_noise_level:.6f}")
    
    # Process some noisy frames
    for _ in range(20):
        noisy_frame = create_audio_frame(2000)
        vad._process_audio_frame(noisy_frame)
    
    updated_noise_level = vad._ambient_noise_level
    logger.info(f"   Updated ambient noise level: {updated_noise_level:.6f}")
    
    assert updated_noise_level > initial_noise_level, "Ambient noise level should increase"
    assert len(vad._noise_samples) > 0, "Noise samples should be collected"
    
    logger.info("✅ PASS: VAD applies adaptive thresholding based on ambient noise")
    return True


def test_requirement_10_7():
    """
    Requirement 10.7: THE VAD_Module SHALL cung cấp method is_voice_active() 
    trả về trạng thái hiện tại
    """
    logger.info("\n[Test 10.7] VAD provides is_voice_active() method")
    
    vad = create_vad()
    
    # Initially no voice
    assert not vad.is_voice_active(), "Voice should not be active initially"
    logger.info("   Initial state: not active ✓")
    
    # Simulate voice activation
    vad._voice_active = True
    assert vad.is_voice_active(), "Voice should be active"
    logger.info("   After activation: active ✓")
    
    # Simulate voice deactivation
    vad._voice_active = False
    assert not vad.is_voice_active(), "Voice should not be active"
    logger.info("   After deactivation: not active ✓")
    
    logger.info("✅ PASS: is_voice_active() method works correctly")
    return True


def test_requirement_10_8():
    """
    Requirement 10.8: WHEN voice detected, THE VAD_Module SHALL cung cấp 
    audio segment qua method get_audio_segment()
    """
    logger.info("\n[Test 10.8] VAD provides audio segment via get_audio_segment()")
    
    vad = create_vad()
    
    # Add some frames to voice segment buffer
    frame1 = create_audio_frame(5000)
    frame2 = create_audio_frame(6000)
    frame3 = create_audio_frame(5500)
    
    vad._voice_segment_buffer = [frame1, frame2, frame3]
    
    # Get audio segment
    segment = vad.get_audio_segment()
    
    assert segment is not None, "Audio segment should not be None"
    assert isinstance(segment, AudioSegment), "Should return AudioSegment instance"
    assert segment.audio_data == frame1 + frame2 + frame3, "Audio data should be concatenated"
    assert segment.sample_rate == vad.config.sample_rate, "Sample rate should match config"
    assert segment.duration > 0, "Duration should be positive"
    
    logger.info(f"   Segment duration: {segment.duration:.3f}s")
    logger.info(f"   Segment data size: {len(segment.audio_data)} bytes")
    
    logger.info("✅ PASS: get_audio_segment() returns correct AudioSegment")
    return True


def test_requirement_10_9():
    """
    Requirement 10.9: THE VAD_Module SHALL lọc non-speech audio 
    để giảm false wake word triggers
    """
    logger.info("\n[Test 10.9] VAD filters non-speech audio")
    
    config = VADConfig(
        energy_threshold=0.05,  # Higher threshold to filter low-energy audio
        silence_duration=1.0,
        min_speech_duration=0.3,
        sample_rate=16000,
        frame_length_ms=30
    )
    vad = VoiceActivityDetector(config)
    
    voice_start_count = {'value': 0}
    
    def on_start():
        voice_start_count['value'] += 1
    
    vad.on_voice_start(on_start)
    
    # Create mock source with mostly quiet frames (should be filtered)
    mock_source = MockAudioSource()
    for _ in range(30):
        mock_source.add_frame(create_audio_frame(500))  # Quiet audio (below threshold)
    
    vad.start_monitoring(mock_source)
    time.sleep(0.5)
    vad.stop_monitoring()
    
    # Voice start should not be triggered for low-energy audio
    assert voice_start_count['value'] == 0, "Low-energy audio should be filtered"
    logger.info("   Low-energy audio filtered: no false triggers ✓")
    
    # Now test with high-energy audio (should trigger)
    vad._reset_state()
    voice_start_count['value'] = 0
    mock_source.reset()
    mock_source.frames.clear()
    
    for _ in range(30):
        mock_source.add_frame(create_audio_frame(10000))  # Loud audio (above threshold)
    
    vad.start_monitoring(mock_source)
    time.sleep(0.5)
    vad.stop_monitoring()
    
    assert voice_start_count['value'] > 0, "High-energy audio should trigger voice start"
    logger.info("   High-energy audio detected: trigger occurred ✓")
    
    logger.info("✅ PASS: VAD filters non-speech audio correctly")
    return True


def test_requirement_10_10():
    """
    Requirement 10.10: THE VAD_Module SHALL support configurable thresholds 
    cho các môi trường noise khác nhau
    """
    logger.info("\n[Test 10.10] VAD supports configurable thresholds")
    
    # Test with low threshold (sensitive, for quiet environments)
    config_sensitive = VADConfig(
        energy_threshold=0.01,
        silence_duration=1.0,
        min_speech_duration=0.2,
        sample_rate=16000,
        frame_length_ms=30
    )
    vad_sensitive = VoiceActivityDetector(config_sensitive)
    logger.info("   Created VAD with low threshold (sensitive mode) ✓")
    
    # Test with high threshold (less sensitive, for noisy environments)
    config_robust = VADConfig(
        energy_threshold=0.1,
        silence_duration=2.0,
        min_speech_duration=0.5,
        sample_rate=16000,
        frame_length_ms=30
    )
    vad_robust = VoiceActivityDetector(config_robust)
    logger.info("   Created VAD with high threshold (robust mode) ✓")
    
    # Test re-initialization with new config
    new_config = VADConfig(
        energy_threshold=0.05,
        silence_duration=1.5,
        min_speech_duration=0.3,
        sample_rate=16000,
        frame_length_ms=30
    )
    success = vad_sensitive.initialize(new_config)
    
    assert success, "Initialization should succeed"
    assert vad_sensitive.config.energy_threshold == 0.05, "Config should be updated"
    logger.info("   Successfully re-initialized with new config ✓")
    
    logger.info("✅ PASS: VAD supports configurable thresholds for different environments")
    return True


def run_all_tests():
    """Run all requirement tests"""
    logger.info("=" * 70)
    logger.info("VAD Module - Requirements Validation Test Suite")
    logger.info("Testing against Requirement 10: Voice Activity Detection (VAD)")
    logger.info("=" * 70)
    
    tests = [
        test_requirement_10_1,
        test_requirement_10_2,
        test_requirement_10_3,
        test_requirement_10_4,
        test_requirement_10_5,
        test_requirement_10_6,
        test_requirement_10_7,
        test_requirement_10_8,
        test_requirement_10_9,
        test_requirement_10_10,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append((test.__name__, result))
        except Exception as e:
            logger.error(f"\n❌ FAIL: {test.__name__}")
            logger.error(f"   Error: {e}")
            import traceback
            traceback.print_exc()
            results.append((test.__name__, False))
    
    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("Test Summary")
    logger.info("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status}: {test_name}")
    
    logger.info("\n" + "=" * 70)
    logger.info(f"Results: {passed}/{total} tests passed")
    logger.info("=" * 70)
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
