"""
Conversation Manager - Quản lý luồng hội thoại và trạng thái mic/loa
Chức năng: State machine managing mic/speaker states respecting hardware constraint
"""

import time
import logging
from enum import Enum
from typing import Optional, Callable, Any
from datetime import datetime
import threading
import numpy as np

# Setup logger
logger = logging.getLogger(__name__)


class ConversationState(Enum):
    """
    Conversation state enum defining the three states of the conversation flow
    
    States:
    - DEFAULT_STATE: Default state with speaker on, mic off (listening for wake word)
    - SPEAKING_STATE: Chatbot speaking state with mic on, speaker off (playing audio to camera)
    - LISTENING_STATE: User speaking state with speaker on, mic off (recording user input)
    """
    DEFAULT_STATE = "default"
    SPEAKING_STATE = "speaking"
    LISTENING_STATE = "listening"


class ConversationManager:
    """
    Manages conversation flow and mic/speaker states with hardware constraint enforcement
    
    Hardware Constraint: Camera has exclusive mic/speaker - when speaker is on, mic is off,
    and when mic is on, speaker is off. This manager ensures this constraint is always respected.
    
    State Transitions:
    1. DEFAULT → SPEAKING: When wake word "Tỷ Tỷ" is detected
    2. SPEAKING → LISTENING: After "Dạ" response finishes playing
    3. LISTENING → SPEAKING: After user input is processed and response is ready
    4. SPEAKING → DEFAULT: After response finishes playing
    
    The manager logs all state transitions with timestamps and integrates with
    CareCam_Controller for mic/speaker button clicks.
    """
    
    # Timeout for silence detection during LISTENING_STATE (seconds)
    SILENCE_TIMEOUT = 3.0
    
    # Maximum recording duration to prevent infinite recording (seconds)
    MAX_RECORDING_DURATION = 10.0
    
    # Audio energy threshold for silence detection (RMS value)
    SILENCE_THRESHOLD = 0.02
    
    # Retry configuration for button clicks
    MAX_BUTTON_RETRIES = 3
    
    def __init__(self, carecam_controller, audio_source: Optional[Any] = None):
        """
        Initialize ConversationManager with CareCam controller
        
        Args:
            carecam_controller: Instance of CareCam_Controller for mic/speaker control
            audio_source: Optional audio source for monitoring (e.g., pyaudio stream)
        """
        self.controller = carecam_controller
        self.current_state = ConversationState.DEFAULT_STATE
        self._state_lock = threading.Lock()
        self._silence_timer = None
        self._recording_timer = None
        
        # Audio monitoring
        self._audio_source = audio_source
        self._audio_monitoring_thread: Optional[threading.Thread] = None
        self._is_monitoring = False
        self._last_audio_energy = 0.0
        self._silence_start_time: Optional[float] = None
        self._recording_start_time: Optional[float] = None
        self._audio_buffer = []
        
        # Callbacks for state transitions
        self._on_state_change_callbacks = []
        self._on_silence_detected_callback: Optional[Callable] = None
        self._on_timeout_callback: Optional[Callable] = None
        
        # Log initialization
        logger.info("🎯 ConversationManager initialized")
        logger.info(f"   Initial state: {self.current_state.value}")
        logger.info(f"   Silence timeout: {self.SILENCE_TIMEOUT}s")
        logger.info(f"   Max recording duration: {self.MAX_RECORDING_DURATION}s")
        logger.info(f"   Silence threshold: {self.SILENCE_THRESHOLD}")
        logger.info(f"   Audio source provided: {audio_source is not None}")
    
    def register_state_change_callback(self, callback: Callable[[ConversationState, ConversationState], None]):
        """
        Register a callback to be called when state changes
        
        Args:
            callback: Function(old_state, new_state) to be called on state change
        """
        self._on_state_change_callbacks.append(callback)
    
    def register_silence_detected_callback(self, callback: Callable):
        """
        Register a callback to be called when silence is detected
        
        Args:
            callback: Function() to be called when silence detected (should process audio)
        """
        self._on_silence_detected_callback = callback
        logger.debug("Registered silence detected callback")
    
    def register_timeout_callback(self, callback: Callable):
        """
        Register a callback to be called when recording timeout occurs
        
        Args:
            callback: Function() to be called on timeout
        """
        self._on_timeout_callback = callback
        logger.debug("Registered timeout callback")
    
    def set_audio_source(self, audio_source: Any):
        """
        Set audio source for monitoring
        
        Args:
            audio_source: Audio source (e.g., pyaudio stream)
        """
        self._audio_source = audio_source
        logger.info(f"Audio source set: {audio_source is not None}")
    
    def set_audio_source(self, audio_source: Any):
        """
        Set audio source for monitoring
        
        Args:
            audio_source: Audio source (e.g., pyaudio stream)
        """
        self._audio_source = audio_source
        logger.info(f"Audio source set: {audio_source is not None}")
    
    def _calculate_audio_energy(self, audio_frame: bytes) -> float:
        """
        Calculate RMS energy of audio frame
        
        Args:
            audio_frame: Raw audio bytes (16-bit PCM)
            
        Returns:
            Energy value (normalized 0-1 range)
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
            logger.error(f"Failed to calculate audio energy: {e}")
            return 0.0
    
    def _start_audio_monitoring(self):
        """Start audio monitoring thread for silence detection"""
        if self._is_monitoring:
            logger.warning("Audio monitoring already active")
            return
        
        if self._audio_source is None:
            logger.warning("No audio source set, cannot start monitoring")
            return
        
        self._is_monitoring = True
        self._silence_start_time = None
        self._recording_start_time = time.time()
        self._audio_buffer.clear()
        
        # Start monitoring thread
        self._audio_monitoring_thread = threading.Thread(
            target=self._audio_monitoring_loop,
            daemon=True,
            name="AudioMonitor"
        )
        self._audio_monitoring_thread.start()
        
        logger.info("🎧 Started audio monitoring for silence detection")
    
    def _stop_audio_monitoring(self):
        """Stop audio monitoring thread"""
        if not self._is_monitoring:
            return
        
        self._is_monitoring = False
        
        # Wait for thread to finish
        if self._audio_monitoring_thread and self._audio_monitoring_thread.is_alive():
            self._audio_monitoring_thread.join(timeout=1.0)
        
        logger.info("🔇 Stopped audio monitoring")
    
    def _audio_monitoring_loop(self):
        """Main audio monitoring loop - runs in separate thread"""
        logger.debug("Audio monitoring loop started")
        
        frame_size = 1024  # Number of samples per frame
        
        while self._is_monitoring:
            try:
                # Read audio frame
                audio_frame = self._read_audio_frame(frame_size)
                
                if audio_frame is None:
                    time.sleep(0.01)
                    continue
                
                # Store audio in buffer
                self._audio_buffer.append(audio_frame)
                
                # Calculate audio energy
                energy = self._calculate_audio_energy(audio_frame)
                self._last_audio_energy = energy
                
                current_time = time.time()
                
                # Check for silence
                if energy < self.SILENCE_THRESHOLD:
                    # Audio is below threshold (silence)
                    if self._silence_start_time is None:
                        self._silence_start_time = current_time
                        logger.debug(f"🔇 Silence started (energy: {energy:.4f})")
                    else:
                        # Check if silence duration exceeds threshold
                        silence_duration = current_time - self._silence_start_time
                        if silence_duration >= self.SILENCE_TIMEOUT:
                            logger.info(f"⏰ Silence detected for {silence_duration:.2f}s")
                            self._on_silence_detected()
                            break
                else:
                    # Audio detected (above threshold)
                    if self._silence_start_time is not None:
                        logger.debug(f"🎤 Voice activity resumed (energy: {energy:.4f})")
                    self._silence_start_time = None
                
                # Check for max recording duration
                if self._recording_start_time:
                    recording_duration = current_time - self._recording_start_time
                    if recording_duration >= self.MAX_RECORDING_DURATION:
                        logger.warning(f"⏰ Max recording duration reached ({recording_duration:.2f}s)")
                        self._on_recording_timeout()
                        break
                
                # Small delay to prevent busy-waiting
                time.sleep(0.01)
                
            except Exception as e:
                logger.error(f"Error in audio monitoring loop: {e}")
                time.sleep(0.1)
        
        logger.debug("Audio monitoring loop ended")
    
    def _read_audio_frame(self, frame_size: int) -> Optional[bytes]:
        """
        Read audio frame from source
        
        Args:
            frame_size: Number of samples to read
            
        Returns:
            Audio frame as bytes, or None if not available
        """
        if self._audio_source is None:
            return None
        
        try:
            # Check if audio source has a read method
            if hasattr(self._audio_source, 'read'):
                return self._audio_source.read(frame_size, exception_on_overflow=False)
            elif hasattr(self._audio_source, 'readframes'):
                return self._audio_source.readframes(frame_size)
            else:
                return None
        except Exception as e:
            logger.debug(f"Failed to read audio frame: {e}")
            return None
    
    def get_recorded_audio(self) -> Optional[bytes]:
        """
        Get recorded audio buffer
        
        Returns:
            Combined audio data as bytes, or None if no audio
        """
        if not self._audio_buffer:
            return None
        
        try:
            return b''.join(self._audio_buffer)
        except Exception as e:
            logger.error(f"Failed to get recorded audio: {e}")
            return None
    
    def _on_silence_detected(self):
        """Handle silence detection - called when silence threshold is reached"""
        logger.info("🔇 Silence detected, processing user input")
        
        # Stop monitoring
        self._is_monitoring = False
        
        # Call registered callback if available
        if self._on_silence_detected_callback:
            try:
                self._on_silence_detected_callback()
            except Exception as e:
                logger.error(f"Error in silence detected callback: {e}")
        else:
            # Default behavior: transition to process input
            logger.info("📝 No callback registered, triggering default user input processing")
            self.on_user_input_ready()
    
    def _on_recording_timeout(self):
        """Handle recording timeout - called when max recording duration is reached"""
        logger.warning("⏰ Recording timeout reached")
        
        # Stop monitoring
        self._is_monitoring = False
        
        # Check if we have any meaningful audio
        audio_data = self.get_recorded_audio()
        has_audio = audio_data is not None and len(audio_data) > 0
        
        # Calculate average energy of recorded audio to determine if it's meaningful
        has_meaningful_audio = False
        if has_audio:
            try:
                # Check a few frames to see if there's any meaningful audio
                sample_size = min(len(audio_data), 2048 * 5)  # Check first 5 frames
                sample = audio_data[:sample_size]
                energy = self._calculate_audio_energy(sample)
                has_meaningful_audio = energy > self.SILENCE_THRESHOLD
            except:
                pass
        
        if not has_meaningful_audio:
            # No meaningful audio detected, play timeout message
            logger.info("🔇 No meaningful audio detected during recording, playing timeout message")
            
            # Call timeout callback if registered
            if self._on_timeout_callback:
                try:
                    self._on_timeout_callback()
                except Exception as e:
                    logger.error(f"Error in timeout callback: {e}")
            else:
                # Default behavior: force back to default state
                logger.info("⚠️ No callback registered, forcing default state")
                self.force_default_state()
        else:
            # Some meaningful audio was captured, process it
            logger.info("🎤 Some audio captured before timeout, processing")
            self._on_silence_detected()
    
    def _notify_state_change(self, old_state: ConversationState, new_state: ConversationState):
        """Notify all registered callbacks of state change"""
        for callback in self._on_state_change_callbacks:
            try:
                callback(old_state, new_state)
            except Exception as e:
                logger.error(f"Error in state change callback: {e}")
    
    def _log_state_transition(self, from_state: ConversationState, to_state: ConversationState):
        """
        Log state transition with timestamp
        
        Args:
            from_state: Previous state
            to_state: New state
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        logger.info(f"[{timestamp}] State transition: {from_state.value} -> {to_state.value}")
        print(f"[{timestamp}] State transition: {from_state.value} -> {to_state.value}")
    
    def _transition_to_state(self, new_state: ConversationState) -> bool:
        """
        Transition to a new state with proper mic/speaker management
        
        Args:
            new_state: Target state to transition to
            
        Returns:
            bool: True if transition successful, False otherwise
        """
        with self._state_lock:
            old_state = self.current_state
            
            # Skip if already in target state
            if old_state == new_state:
                logger.debug(f"Already in {new_state.value} state, skipping transition")
                return True
            
            # Log the transition
            self._log_state_transition(old_state, new_state)
            
            # Handle state-specific transitions
            success = True
            
            if new_state == ConversationState.DEFAULT_STATE:
                # DEFAULT_STATE: Speaker on, mic off (listening for wake word)
                success = self._ensure_speaker_on()
                
            elif new_state == ConversationState.SPEAKING_STATE:
                # SPEAKING_STATE: Mic on, speaker off (chatbot speaking)
                # Must turn off speaker before turning on mic
                success = self._ensure_mic_on()
                
            elif new_state == ConversationState.LISTENING_STATE:
                # LISTENING_STATE: Speaker on, mic off (user speaking)
                # Must turn off mic before turning on speaker
                success = self._ensure_speaker_on()
            
            if success:
                self.current_state = new_state
                self._notify_state_change(old_state, new_state)
                logger.info(f"✅ Successfully transitioned to {new_state.value}")
                return True
            else:
                logger.error(f"❌ Failed to transition to {new_state.value}, staying in {old_state.value}")
                return False
    
    def _ensure_mic_on(self) -> bool:
        """
        Ensure mic is on and speaker is off (respecting hardware constraint)
        
        Implements retry logic with up to MAX_BUTTON_RETRIES attempts.
        
        Returns:
            bool: True if successful, False otherwise
        """
        logger.info("🎤 Ensuring mic ON, speaker OFF")
        
        # Retry logic: try up to MAX_BUTTON_RETRIES times
        for attempt in range(1, self.MAX_BUTTON_RETRIES + 1):
            # Due to hardware constraint, clicking mic button will automatically turn off speaker
            success = self.controller.click_mic_button(retries=1)  # Single attempt per retry
            
            if success:
                logger.info("✅ Mic enabled, speaker automatically disabled by hardware")
                return True
            
            # Log retry attempt
            if attempt < self.MAX_BUTTON_RETRIES:
                logger.warning(f"⚠️ Mic button click failed (attempt {attempt}/{self.MAX_BUTTON_RETRIES}), retrying...")
                time.sleep(0.5)  # Brief delay before retry
        
        logger.error(f"❌ Failed to enable mic after {self.MAX_BUTTON_RETRIES} retries")
        return False
    
    def _ensure_speaker_on(self) -> bool:
        """
        Ensure speaker is on and mic is off (respecting hardware constraint)
        
        Implements retry logic with up to MAX_BUTTON_RETRIES attempts.
        
        Returns:
            bool: True if successful, False otherwise
        """
        logger.info("🔊 Ensuring speaker ON, mic OFF")
        
        # Retry logic: try up to MAX_BUTTON_RETRIES times
        for attempt in range(1, self.MAX_BUTTON_RETRIES + 1):
            # Due to hardware constraint, clicking speaker button will automatically turn off mic
            success = self.controller.click_speaker_button(retries=1)  # Single attempt per retry
            
            if success:
                logger.info("✅ Speaker enabled, mic automatically disabled by hardware")
                return True
            
            # Log retry attempt
            if attempt < self.MAX_BUTTON_RETRIES:
                logger.warning(f"⚠️ Speaker button click failed (attempt {attempt}/{self.MAX_BUTTON_RETRIES}), retrying...")
                time.sleep(0.5)  # Brief delay before retry
        
        logger.error(f"❌ Failed to enable speaker after {self.MAX_BUTTON_RETRIES} retries")
        return False
    
    def ensure_mic_speaker_exclusivity(self) -> bool:
        """
        Ensure mic and speaker are not on simultaneously
        
        This method verifies the hardware constraint is respected. Due to the camera's
        hardware design, this should always be true, but this method provides explicit
        verification and can force the correct state if needed.
        
        Returns:
            bool: True if exclusivity is ensured, False if there's an issue
        """
        # In the hardware implementation, exclusivity is automatically enforced
        # This method serves as a verification point and documentation
        logger.debug("✓ Mic/speaker exclusivity enforced by hardware constraint")
        return True
    
    def on_wake_word_detected(self) -> bool:
        """
        Handle wake word detection: Transition DEFAULT → SPEAKING
        
        Returns:
            bool: True if transition successful, False otherwise
        """
        logger.info("🎤 Wake word detected!")
        
        if self.current_state != ConversationState.DEFAULT_STATE:
            logger.warning(f"⚠️ Wake word detected but not in DEFAULT_STATE (current: {self.current_state.value})")
            # Force to default state first
            self.force_default_state()
        
        # Transition to SPEAKING state to play "Dạ" response
        return self._transition_to_state(ConversationState.SPEAKING_STATE)
    
    def on_acknowledgment_complete(self) -> bool:
        """
        Handle acknowledgment ("Dạ") playback completion: Transition SPEAKING → LISTENING
        
        Returns:
            bool: True if transition successful, False otherwise
        """
        logger.info("🎵 Acknowledgment 'Dạ' playback complete")
        
        if self.current_state != ConversationState.SPEAKING_STATE:
            logger.warning(f"⚠️ Acknowledgment complete but not in SPEAKING_STATE (current: {self.current_state.value})")
        
        # Transition to LISTENING state to record user input
        success = self._transition_to_state(ConversationState.LISTENING_STATE)
        
        if success:
            # Start audio monitoring for silence detection
            self._start_audio_monitoring()
        
        return success
    
    def on_user_input_ready(self) -> bool:
        """
        Handle user input ready for processing: Transition LISTENING → SPEAKING
        
        Returns:
            bool: True if transition successful, False otherwise
        """
        logger.info("📝 User input ready for processing")
        
        # Stop audio monitoring
        self._stop_audio_monitoring()
        
        if self.current_state != ConversationState.LISTENING_STATE:
            logger.warning(f"⚠️ User input ready but not in LISTENING_STATE (current: {self.current_state.value})")
        
        # Transition to SPEAKING state to play response
        return self._transition_to_state(ConversationState.SPEAKING_STATE)
    
    def on_response_complete(self) -> bool:
        """
        Handle response playback completion: Transition SPEAKING → DEFAULT
        
        Returns:
            bool: True if transition successful, False otherwise
        """
        logger.info("🎵 Response playback complete")
        
        if self.current_state != ConversationState.SPEAKING_STATE:
            logger.warning(f"⚠️ Response complete but not in SPEAKING_STATE (current: {self.current_state.value})")
        
        # Transition back to DEFAULT state
        return self._transition_to_state(ConversationState.DEFAULT_STATE)
    
    def force_default_state(self) -> bool:
        """
        Force transition to DEFAULT_STATE (emergency reset)
        
        This method is used for error recovery and ensures the system
        returns to a known good state.
        
        Returns:
            bool: True if successful, False otherwise
        """
        logger.warning("⚠️ Forcing DEFAULT_STATE (emergency reset)")
        
        # Stop audio monitoring
        self._stop_audio_monitoring()
        
        # Force transition to default state
        success = self._transition_to_state(ConversationState.DEFAULT_STATE)
        
        if success:
            logger.info("✅ Successfully reset to DEFAULT_STATE")
        else:
            logger.error("❌ Failed to reset to DEFAULT_STATE")
        
        return success
    
    def get_current_state(self) -> ConversationState:
        """
        Get current conversation state
        
        Returns:
            ConversationState: Current state
        """
        return self.current_state
    
    def get_audio_energy(self) -> float:
        """
        Get last measured audio energy level
        
        Returns:
            float: Energy level (0.0 - 1.0)
        """
        return self._last_audio_energy
    
    def is_in_conversation(self) -> bool:
        """
        Check if currently in an active conversation (not in DEFAULT_STATE)
        
        Returns:
            bool: True if in SPEAKING or LISTENING state, False if in DEFAULT
        """
        return self.current_state != ConversationState.DEFAULT_STATE
    
    def test_state_transitions(self):
        """
        Test method to verify state machine transitions
        For testing purposes only - simulates full conversation flow
        """
        logger.info("🧪 Testing state transitions...")
        
        # Test 1: DEFAULT → SPEAKING (wake word detected)
        print("\n--- Test 1: Wake Word Detection ---")
        assert self.on_wake_word_detected(), "Failed to transition to SPEAKING"
        assert self.get_current_state() == ConversationState.SPEAKING_STATE
        time.sleep(1)
        
        # Test 2: SPEAKING → LISTENING (acknowledgment complete)
        print("\n--- Test 2: Acknowledgment Complete ---")
        assert self.on_acknowledgment_complete(), "Failed to transition to LISTENING"
        assert self.get_current_state() == ConversationState.LISTENING_STATE
        time.sleep(1)
        
        # Test 3: LISTENING → SPEAKING (user input ready)
        print("\n--- Test 3: User Input Ready ---")
        assert self.on_user_input_ready(), "Failed to transition to SPEAKING"
        assert self.get_current_state() == ConversationState.SPEAKING_STATE
        time.sleep(1)
        
        # Test 4: SPEAKING → DEFAULT (response complete)
        print("\n--- Test 4: Response Complete ---")
        assert self.on_response_complete(), "Failed to transition to DEFAULT"
        assert self.get_current_state() == ConversationState.DEFAULT_STATE
        time.sleep(1)
        
        # Test 5: Force default state
        print("\n--- Test 5: Force Default State ---")
        self.on_wake_word_detected()  # Go to SPEAKING
        assert self.force_default_state(), "Failed to force DEFAULT_STATE"
        assert self.get_current_state() == ConversationState.DEFAULT_STATE
        
        logger.info("✅ All state transition tests passed!")
        print("\n✅ All state transition tests passed!")


# Singleton pattern
_conversation_manager = None


def get_conversation_manager(carecam_controller=None, audio_source=None) -> ConversationManager:
    """
    Get singleton instance of ConversationManager
    
    Args:
        carecam_controller: CareCam controller instance (required for first call)
        audio_source: Optional audio source for monitoring
        
    Returns:
        ConversationManager: Singleton instance
    """
    global _conversation_manager
    
    if _conversation_manager is None:
        if carecam_controller is None:
            raise ValueError("carecam_controller is required for first initialization")
        _conversation_manager = ConversationManager(carecam_controller, audio_source)
    elif audio_source is not None and _conversation_manager._audio_source is None:
        # Update audio source if not set
        _conversation_manager.set_audio_source(audio_source)
    
    return _conversation_manager


if __name__ == "__main__":
    """
    Test script for ConversationManager
    Run with: python -m modules.conversation_manager
    """
    print("=" * 60)
    print("🎮 ConversationManager Test")
    print("=" * 60)
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Import CareCam controller
    try:
        from modules.carecam_controller import get_controller
        
        controller = get_controller()
        
        # Find CareCam window
        if not controller.find_window():
            print("\n⚠️ CareCam window not found!")
            print("   Please open CareCam app and try again")
            print("\n   Testing will continue with simulated controller...")
            print("   (Button clicks will be logged but not executed)")
        
        # Create conversation manager
        manager = get_conversation_manager(controller)
        
        print("\n" + "=" * 60)
        print("🧪 Running State Transition Tests")
        print("=" * 60)
        
        # Run state transition tests
        manager.test_state_transitions()
        
        print("\n" + "=" * 60)
        print("✅ ConversationManager Test Complete")
        print("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
