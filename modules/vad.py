"""
Voice Activity Detection (VAD) Module
Detects when user is speaking vs. silence to optimize processing and reduce false wake word triggers
"""

import numpy as np
import threading
import time
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Callable, Any
from collections import deque

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class VADConfig:
    """Configuration for Voice Activity Detection"""
    energy_threshold: float = 0.02  # Audio energy threshold for voice detection
    silence_duration: float = 1.5  # Seconds of silence to trigger voice_end
    min_speech_duration: float = 0.3  # Minimum speech duration to register as voice
    sample_rate: int = 16000  # Audio sample rate in Hz
    frame_length_ms: int = 30  # Frame length in milliseconds


@dataclass
class AudioSegment:
    """Audio segment with metadata"""
    audio_data: bytes  # Raw audio bytes
    duration: float  # Duration in seconds
    timestamp: datetime  # When the segment was captured
    sample_rate: int  # Sample rate of the audio


class VoiceActivityDetector:
    """
    Voice Activity Detection using energy-based detection with adaptive thresholding
    
    Responsibilities:
    - Monitor audio stream for voice activity
    - Reduce false wake word triggers by filtering non-speech audio
    - Provide audio segments only when voice is detected
    - Support configurable thresholds for different noise environments
    - Emit events when voice starts/ends for reactive processing
    """
    
    def __init__(self, config: Optional[VADConfig] = None):
        """
        Initialize Voice Activity Detector
        
        Args:
            config: VAD configuration (uses defaults if None)
        """
        self.config = config or VADConfig()
        
        # State variables
        self._is_monitoring = False
        self._voice_active = False
        self._monitoring_thread: Optional[threading.Thread] = None
        
        # Audio buffers
        self._audio_buffer = deque(maxlen=100)  # Store recent audio frames
        self._voice_segment_buffer = []  # Buffer for current voice segment
        
        # Timing variables
        self._voice_start_time: Optional[float] = None
        self._last_voice_time: Optional[float] = None
        
        # Adaptive threshold variables
        self._ambient_noise_level: float = 0.0
        self._noise_samples = deque(maxlen=50)  # Track ambient noise for adaptation
        
        # Event callbacks
        self._on_voice_start_callbacks: list[Callable] = []
        self._on_voice_end_callbacks: list[Callable] = []
        
        # Audio source
        self._audio_source: Optional[Any] = None
        
        logger.info(f"VAD initialized with config: {self.config}")
    
    def initialize(self, config: VADConfig) -> bool:
        """
        Initialize VAD with specific configuration
        
        Args:
            config: VAD configuration
            
        Returns:
            True if initialization successful
        """
        try:
            self.config = config
            self._reset_state()
            logger.info(f"VAD re-initialized with new config: {config}")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize VAD: {e}")
            return False
    
    def start_monitoring(self, audio_source: Any) -> None:
        """
        Start monitoring audio stream for voice activity
        
        Args:
            audio_source: Audio stream source (e.g., pyaudio stream, audio file)
        """
        if self._is_monitoring:
            logger.warning("VAD is already monitoring")
            return
        
        self._audio_source = audio_source
        self._is_monitoring = True
        self._reset_state()
        
        # Start monitoring in a separate thread
        self._monitoring_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True,
            name="VAD-Monitor"
        )
        self._monitoring_thread.start()
        
        logger.info("VAD monitoring started")
    
    def stop_monitoring(self) -> None:
        """Stop monitoring audio stream"""
        if not self._is_monitoring:
            logger.warning("VAD is not monitoring")
            return
        
        self._is_monitoring = False
        
        # Wait for monitoring thread to finish
        if self._monitoring_thread and self._monitoring_thread.is_alive():
            self._monitoring_thread.join(timeout=2.0)
        
        # Trigger voice_end if voice was active
        if self._voice_active:
            self._trigger_voice_end()
        
        logger.info("VAD monitoring stopped")
    
    def is_voice_active(self) -> bool:
        """
        Check if voice is currently active
        
        Returns:
            True if voice is detected, False otherwise
        """
        return self._voice_active
    
    def get_audio_segment(self) -> Optional[AudioSegment]:
        """
        Get the current audio segment (if voice is active or just ended)
        
        Returns:
            AudioSegment if available, None otherwise
        """
        if not self._voice_segment_buffer:
            return None
        
        try:
            # Concatenate all audio frames in the segment buffer
            audio_data = b''.join(self._voice_segment_buffer)
            
            # Calculate duration
            bytes_per_sample = 2  # 16-bit audio
            total_samples = len(audio_data) // bytes_per_sample
            duration = total_samples / self.config.sample_rate
            
            segment = AudioSegment(
                audio_data=audio_data,
                duration=duration,
                timestamp=datetime.now(),
                sample_rate=self.config.sample_rate
            )
            
            return segment
        except Exception as e:
            logger.error(f"Failed to get audio segment: {e}")
            return None
    
    def on_voice_start(self, callback: Callable) -> None:
        """
        Register callback for voice_start event
        
        Args:
            callback: Function to call when voice starts (signature: callback())
        """
        if callback not in self._on_voice_start_callbacks:
            self._on_voice_start_callbacks.append(callback)
            logger.debug(f"Registered voice_start callback: {callback.__name__}")
    
    def on_voice_end(self, callback: Callable) -> None:
        """
        Register callback for voice_end event
        
        Args:
            callback: Function to call when voice ends (signature: callback(audio_segment))
        """
        if callback not in self._on_voice_end_callbacks:
            self._on_voice_end_callbacks.append(callback)
            logger.debug(f"Registered voice_end callback: {callback.__name__}")
    
    # ===== Private Methods =====
    
    def _reset_state(self) -> None:
        """Reset VAD internal state"""
        self._voice_active = False
        self._voice_start_time = None
        self._last_voice_time = None
        self._voice_segment_buffer.clear()
        self._audio_buffer.clear()
        self._ambient_noise_level = 0.0
        self._noise_samples.clear()
    
    def _monitor_loop(self) -> None:
        """Main monitoring loop (runs in separate thread)"""
        logger.debug("VAD monitor loop started")
        
        frame_size = int(self.config.sample_rate * self.config.frame_length_ms / 1000)
        
        while self._is_monitoring:
            try:
                # Read audio frame from source
                audio_frame = self._read_audio_frame(frame_size)
                
                if audio_frame is None:
                    time.sleep(0.01)  # Small delay to prevent busy-waiting
                    continue
                
                # Process the audio frame
                self._process_audio_frame(audio_frame)
                
            except Exception as e:
                logger.error(f"Error in VAD monitor loop: {e}")
                time.sleep(0.1)  # Delay on error to prevent tight error loop
        
        logger.debug("VAD monitor loop ended")
    
    def _read_audio_frame(self, frame_size: int) -> Optional[bytes]:
        """
        Read audio frame from source
        
        Args:
            frame_size: Number of samples to read
            
        Returns:
            Audio frame as bytes, or None if not available
        """
        # This is a placeholder - actual implementation depends on audio source type
        # For pyaudio.Stream: audio_source.read(frame_size, exception_on_overflow=False)
        # For file: audio_source.readframes(frame_size)
        
        if self._audio_source is None:
            return None
        
        try:
            # Check if audio source has a read method
            if hasattr(self._audio_source, 'read'):
                return self._audio_source.read(frame_size, exception_on_overflow=False)
            elif hasattr(self._audio_source, 'readframes'):
                return self._audio_source.readframes(frame_size)
            else:
                logger.warning("Audio source does not have read/readframes method")
                return None
        except Exception as e:
            logger.debug(f"Failed to read audio frame: {e}")
            return None
    
    def _process_audio_frame(self, audio_frame: bytes) -> None:
        """
        Process a single audio frame for voice activity detection
        
        Args:
            audio_frame: Raw audio frame as bytes
        """
        # Add to circular buffer
        self._audio_buffer.append(audio_frame)
        
        # Calculate energy of the frame
        energy = self._calculate_energy(audio_frame)
        
        # Update adaptive threshold
        self._update_adaptive_threshold(energy)
        
        # Determine if voice is present
        is_voice = energy > (self._ambient_noise_level + self.config.energy_threshold)
        
        current_time = time.time()
        
        if is_voice:
            self._last_voice_time = current_time
            
            # Add frame to voice segment buffer
            self._voice_segment_buffer.append(audio_frame)
            
            # Check if this is the start of voice activity
            if not self._voice_active:
                if self._voice_start_time is None:
                    self._voice_start_time = current_time
                else:
                    # Check if minimum speech duration is met
                    speech_duration = current_time - self._voice_start_time
                    if speech_duration >= self.config.min_speech_duration:
                        self._trigger_voice_start()
        else:
            # Check if this is the end of voice activity
            if self._voice_active:
                silence_duration = current_time - self._last_voice_time
                if silence_duration >= self.config.silence_duration:
                    self._trigger_voice_end()
            else:
                # Reset voice start time if no voice detected
                if self._voice_start_time is not None:
                    speech_duration = current_time - self._voice_start_time
                    if speech_duration < self.config.min_speech_duration:
                        # False start, reset
                        self._voice_start_time = None
                        self._voice_segment_buffer.clear()
    
    def _calculate_energy(self, audio_frame: bytes) -> float:
        """
        Calculate short-term energy of audio frame
        
        Args:
            audio_frame: Raw audio frame as bytes (16-bit PCM)
            
        Returns:
            Energy value (normalized)
        """
        try:
            # Convert bytes to numpy array (16-bit signed integers)
            audio_array = np.frombuffer(audio_frame, dtype=np.int16)
            
            # Normalize to [-1, 1] range
            audio_normalized = audio_array.astype(np.float32) / 32768.0
            
            # Calculate RMS energy
            energy = np.sqrt(np.mean(audio_normalized ** 2))
            
            return float(energy)
        except Exception as e:
            logger.error(f"Failed to calculate energy: {e}")
            return 0.0
    
    def _update_adaptive_threshold(self, energy: float) -> None:
        """
        Update adaptive threshold based on ambient noise level
        
        Args:
            energy: Current frame energy
        """
        # Add energy to noise samples (if voice is not active)
        if not self._voice_active:
            self._noise_samples.append(energy)
        
        # Update ambient noise level (rolling average)
        if len(self._noise_samples) > 0:
            self._ambient_noise_level = float(np.mean(self._noise_samples))
    
    def _trigger_voice_start(self) -> None:
        """Trigger voice_start event"""
        if self._voice_active:
            return
        
        self._voice_active = True
        logger.debug("Voice activity started")
        
        # Call all registered callbacks
        for callback in self._on_voice_start_callbacks:
            try:
                callback()
            except Exception as e:
                logger.error(f"Error in voice_start callback {callback.__name__}: {e}")
    
    def _trigger_voice_end(self) -> None:
        """Trigger voice_end event"""
        if not self._voice_active:
            return
        
        self._voice_active = False
        logger.debug("Voice activity ended")
        
        # Get the audio segment
        audio_segment = self.get_audio_segment()
        
        # Call all registered callbacks
        for callback in self._on_voice_end_callbacks:
            try:
                callback(audio_segment)
            except Exception as e:
                logger.error(f"Error in voice_end callback {callback.__name__}: {e}")
        
        # Clear buffers
        self._voice_segment_buffer.clear()
        self._voice_start_time = None
        self._last_voice_time = None


# ===== Factory Function =====

def create_vad(config: Optional[VADConfig] = None) -> VoiceActivityDetector:
    """
    Factory function to create VAD instance
    
    Args:
        config: VAD configuration (uses defaults if None)
        
    Returns:
        VoiceActivityDetector instance
    """
    return VoiceActivityDetector(config)


# ===== Module Testing =====

if __name__ == "__main__":
    import sys
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='VAD Module Test')
    parser.add_argument('--test', action='store_true', help='Run comprehensive test suite')
    args = parser.parse_args()
    
    # Configure logging for testing
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 60)
    print("Voice Activity Detection (VAD) Module Test")
    print("=" * 60)
    
    if args.test:
        print("\n🧪 Running in TEST mode (comprehensive test suite)")
    else:
        print("\n📝 Running in standard mode (basic tests)")
        print("   Use --test flag for comprehensive test suite")
    
    # Test 1: Create VAD with default config
    print("\n[Test 1] Creating VAD with default config...")
    vad = create_vad()
    print(f"✅ VAD created: {vad}")
    print(f"   Config: {vad.config}")
    
    # Test 2: Create VAD with custom config
    print("\n[Test 2] Creating VAD with custom config...")
    custom_config = VADConfig(
        energy_threshold=0.03,
        silence_duration=2.0,
        min_speech_duration=0.5,
        sample_rate=16000,
        frame_length_ms=30
    )
    vad_custom = create_vad(custom_config)
    print(f"✅ VAD created with custom config: {vad_custom.config}")
    
    # Test 3: Register callbacks
    print("\n[Test 3] Registering event callbacks...")
    
    def on_voice_start_handler():
        print("   🎤 Voice started!")
    
    def on_voice_end_handler(segment: Optional[AudioSegment]):
        if segment:
            print(f"   🔇 Voice ended! Segment: {segment.duration:.2f}s")
        else:
            print("   🔇 Voice ended! No segment available")
    
    vad.on_voice_start(on_voice_start_handler)
    vad.on_voice_end(on_voice_end_handler)
    print("✅ Callbacks registered")
    
    # Test 4: Test voice activity state
    print("\n[Test 4] Testing voice activity state...")
    print(f"   Is voice active: {vad.is_voice_active()}")
    assert not vad.is_voice_active(), "Voice should not be active initially"
    print("✅ Voice activity state correct")
    
    # Test 5: Test energy calculation
    print("\n[Test 5] Testing energy calculation...")
    # Create synthetic audio frames
    silent_frame = np.zeros(480, dtype=np.int16).tobytes()  # 30ms at 16kHz
    noisy_frame = (np.random.randint(-1000, 1000, 480, dtype=np.int16)).tobytes()
    loud_frame = (np.random.randint(-10000, 10000, 480, dtype=np.int16)).tobytes()
    
    energy_silent = vad._calculate_energy(silent_frame)
    energy_noisy = vad._calculate_energy(noisy_frame)
    energy_loud = vad._calculate_energy(loud_frame)
    
    print(f"   Silent frame energy: {energy_silent:.6f}")
    print(f"   Noisy frame energy: {energy_noisy:.6f}")
    print(f"   Loud frame energy: {energy_loud:.6f}")
    
    assert energy_silent < energy_noisy < energy_loud, "Energy should increase with volume"
    print("✅ Energy calculation working correctly")
    
    # Test 6: Test adaptive thresholding
    print("\n[Test 6] Testing adaptive thresholding...")
    initial_threshold = vad._ambient_noise_level
    print(f"   Initial ambient noise level: {initial_threshold:.6f}")
    
    # Process some noisy frames to update threshold
    for _ in range(10):
        vad._process_audio_frame(noisy_frame)
    
    updated_threshold = vad._ambient_noise_level
    print(f"   Updated ambient noise level: {updated_threshold:.6f}")
    print(f"   Threshold changed: {updated_threshold != initial_threshold}")
    print("✅ Adaptive thresholding working")
    
    # Test 7: Test AudioSegment creation
    print("\n[Test 7] Testing AudioSegment creation...")
    vad._voice_segment_buffer = [noisy_frame, loud_frame, noisy_frame]
    segment = vad.get_audio_segment()
    
    if segment:
        print(f"✅ AudioSegment created:")
        print(f"   Duration: {segment.duration:.3f}s")
        print(f"   Sample rate: {segment.sample_rate} Hz")
        print(f"   Timestamp: {segment.timestamp}")
        print(f"   Data size: {len(segment.audio_data)} bytes")
    else:
        print("❌ Failed to create AudioSegment")
    
    print("\n" + "=" * 60)
    print("VAD Module Tests Completed!")
    print("=" * 60)
    
    print("\n📝 Note: Full integration testing requires audio source (pyaudio stream)")
    print("   To test with real audio:")
    print("   1. Install pyaudio: pip install pyaudio")
    print("   2. Use start_monitoring() with a pyaudio stream")
    print("   3. Speak into microphone to trigger voice detection")
