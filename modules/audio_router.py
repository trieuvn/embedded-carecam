"""
Audio Router and Mode Controller Module
Manages audio routing between different input/output devices and operation modes

Requirements: 16.1-16.15
"""

import logging
import pyaudio
from dataclasses import dataclass
from enum import Enum
from typing import Optional, List
import time

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class AudioConfig:
    """Configuration for Audio Router"""
    operation_mode: 'OperationMode'
    sample_rate: int = 16000
    channels: int = 1
    buffer_size: int = 1024
    virtual_cable_enabled: bool = False


class OperationMode(Enum):
    """Operation modes for the audio system"""
    BASIC_MODE = "basic"  # PC microphone to PC speakers
    FULL_AUTOMATION_MODE = "full_automation"  # VB-Cable routing
    HYBRID_MODE = "hybrid"  # PC mic + VB-Cable to both outputs


class DeviceType(Enum):
    """Types of audio devices"""
    MICROPHONE = "microphone"
    SPEAKER = "speaker"
    VIRTUAL_CABLE_INPUT = "virtual_cable_input"
    VIRTUAL_CABLE_OUTPUT = "virtual_cable_output"
    RTSP_STREAM = "rtsp_stream"


@dataclass
class AudioDevice:
    """Represents an audio device (physical or virtual)"""
    device_id: int
    name: str
    device_type: DeviceType
    is_virtual: bool
    sample_rate: int
    channels: int
    
    def __str__(self) -> str:
        virtual_flag = "[VIRTUAL]" if self.is_virtual else "[PHYSICAL]"
        return f"{virtual_flag} [{self.device_id}] {self.name} ({self.device_type.value})"


@dataclass
class TestResult:
    """Result of audio path testing"""
    success: bool
    message: str
    input_device: Optional[AudioDevice] = None
    output_device: Optional[AudioDevice] = None
    latency_ms: Optional[float] = None


class AudioRouter:
    """
    Audio Router and Mode Controller
    
    Responsibilities:
    - Detect and enumerate audio devices (physical and virtual)
    - Configure audio routing based on operation mode
    - Manage VB-Cable integration for full automation
    - Test audio paths before starting conversation
    - Switch between modes dynamically
    - Handle device disconnection/reconnection
    """
    
    def __init__(self, config: Optional[AudioConfig] = None):
        """
        Initialize Audio Router
        
        Args:
            config: Audio configuration (uses defaults if None)
        """
        self.config = config or AudioConfig(operation_mode=OperationMode.BASIC_MODE)
        
        # PyAudio instance
        self._audio: Optional[pyaudio.PyAudio] = None
        
        # Current devices
        self._current_input_device: Optional[AudioDevice] = None
        self._current_output_device: Optional[AudioDevice] = None
        
        # Available devices cache
        self._available_devices: List[AudioDevice] = []
        self._devices_cached: bool = False
        
        logger.info(f"AudioRouter created with mode: {self.config.operation_mode.value}")
    
    def initialize(self) -> bool:
        """
        Initialize audio router and detect/enumerate audio devices
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            # Initialize PyAudio
            if self._audio is None:
                self._audio = pyaudio.PyAudio()
                logger.info("PyAudio initialized")
            
            # Enumerate all audio devices
            self._enumerate_devices()
            
            # Set devices based on operation mode
            success = self._configure_mode_devices()
            
            if success:
                logger.info("AudioRouter initialized successfully")
                logger.info(f"Input device: {self._current_input_device}")
                logger.info(f"Output device: {self._current_output_device}")
            else:
                logger.error("Failed to configure devices for current mode")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to initialize AudioRouter: {e}")
            return False
    
    def set_mode(self, mode: OperationMode) -> bool:
        """
        Switch between operation modes
        
        Args:
            mode: Target operation mode
            
        Returns:
            True if mode switch successful
        """
        try:
            logger.info(f"Switching mode: {self.config.operation_mode.value} -> {mode.value}")
            
            # Update configuration
            old_mode = self.config.operation_mode
            self.config.operation_mode = mode
            
            # Reconfigure devices for new mode
            success = self._configure_mode_devices()
            
            if success:
                logger.info(f"Successfully switched to {mode.value} mode")
            else:
                logger.error(f"Failed to switch to {mode.value} mode, reverting to {old_mode.value}")
                self.config.operation_mode = old_mode
                self._configure_mode_devices()
            
            return success
            
        except Exception as e:
            logger.error(f"Error switching mode: {e}")
            return False
    
    def get_input_device(self) -> Optional[AudioDevice]:
        """
        Get current input audio device
        
        Returns:
            Current input AudioDevice or None
        """
        return self._current_input_device
    
    def get_output_device(self) -> Optional[AudioDevice]:
        """
        Get current output audio device
        
        Returns:
            Current output AudioDevice or None
        """
        return self._current_output_device
    
    def list_available_devices(self) -> List[AudioDevice]:
        """
        List all available audio devices
        
        Returns:
            List of AudioDevice objects
        """
        if not self._devices_cached or not self._available_devices:
            self._enumerate_devices()
        
        return self._available_devices.copy()
    
    def test_audio_path(self) -> TestResult:
        """
        Test audio routing before starting conversation
        
        Returns:
            TestResult with success status and details
        """
        try:
            logger.info("Testing audio path...")
            
            # Check if devices are configured
            if self._current_input_device is None:
                return TestResult(
                    success=False,
                    message="No input device configured"
                )
            
            if self._current_output_device is None:
                return TestResult(
                    success=False,
                    message="No output device configured"
                )
            
            # Test input device accessibility
            input_test = self._test_device_access(
                self._current_input_device.device_id,
                is_input=True
            )
            
            if not input_test:
                return TestResult(
                    success=False,
                    message=f"Cannot access input device: {self._current_input_device.name}",
                    input_device=self._current_input_device
                )
            
            # Test output device accessibility
            output_test = self._test_device_access(
                self._current_output_device.device_id,
                is_input=False
            )
            
            if not output_test:
                return TestResult(
                    success=False,
                    message=f"Cannot access output device: {self._current_output_device.name}",
                    output_device=self._current_output_device
                )
            
            # Measure approximate latency
            latency = self._estimate_latency()
            
            logger.info("Audio path test passed")
            return TestResult(
                success=True,
                message="Audio path is functional",
                input_device=self._current_input_device,
                output_device=self._current_output_device,
                latency_ms=latency
            )
            
        except Exception as e:
            logger.error(f"Audio path test failed: {e}")
            return TestResult(
                success=False,
                message=f"Test error: {str(e)}"
            )
    
    def cleanup(self) -> None:
        """Cleanup audio resources"""
        try:
            if self._audio:
                self._audio.terminate()
                self._audio = None
                logger.info("AudioRouter cleaned up")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    # ===== Private Methods =====
    
    def _enumerate_devices(self) -> None:
        """Detect and enumerate all audio devices"""
        if self._audio is None:
            logger.error("PyAudio not initialized")
            return
        
        self._available_devices.clear()
        
        try:
            device_count = self._audio.get_device_count()
            logger.debug(f"Found {device_count} audio devices")
            
            for i in range(device_count):
                try:
                    dev_info = self._audio.get_device_info_by_index(i)
                    
                    # Determine device type and create AudioDevice objects
                    devices = self._parse_device_info(i, dev_info)
                    self._available_devices.extend(devices)
                    
                except Exception as e:
                    logger.warning(f"Failed to get info for device {i}: {e}")
            
            self._devices_cached = True
            logger.info(f"Enumerated {len(self._available_devices)} audio devices")
            
        except Exception as e:
            logger.error(f"Failed to enumerate devices: {e}")
    
    def _parse_device_info(self, device_id: int, dev_info: dict) -> List[AudioDevice]:
        """
        Parse PyAudio device info and create AudioDevice objects
        
        Args:
            device_id: Device index
            dev_info: Device info dictionary from PyAudio
            
        Returns:
            List of AudioDevice objects (may include both input and output for same device)
        """
        devices = []
        name = dev_info['name']
        max_input_channels = dev_info['maxInputChannels']
        max_output_channels = dev_info['maxOutputChannels']
        sample_rate = int(dev_info['defaultSampleRate'])
        
        # Check if device is virtual (VB-Cable)
        is_virtual = self._is_virtual_device(name)
        
        # Create input device if available
        if max_input_channels > 0:
            device_type = self._determine_device_type(name, is_input=True, is_virtual=is_virtual)
            devices.append(AudioDevice(
                device_id=device_id,
                name=name,
                device_type=device_type,
                is_virtual=is_virtual,
                sample_rate=sample_rate,
                channels=max_input_channels
            ))
        
        # Create output device if available
        if max_output_channels > 0:
            device_type = self._determine_device_type(name, is_input=False, is_virtual=is_virtual)
            devices.append(AudioDevice(
                device_id=device_id,
                name=name,
                device_type=device_type,
                is_virtual=is_virtual,
                sample_rate=sample_rate,
                channels=max_output_channels
            ))
        
        return devices
    
    def _is_virtual_device(self, name: str) -> bool:
        """Check if device is virtual (VB-Cable)"""
        virtual_keywords = ['cable', 'virtual', 'vb-audio', 'loopback']
        name_lower = name.lower()
        return any(keyword in name_lower for keyword in virtual_keywords)
    
    def _determine_device_type(self, name: str, is_input: bool, is_virtual: bool) -> DeviceType:
        """Determine device type from name and properties"""
        name_lower = name.lower()
        
        if is_virtual:
            if is_input:
                # Virtual cable output (source for recording)
                if 'output' in name_lower:
                    return DeviceType.VIRTUAL_CABLE_OUTPUT
                return DeviceType.VIRTUAL_CABLE_INPUT
            else:
                # Virtual cable input (sink for playback)
                if 'input' in name_lower or 'cable input' in name_lower:
                    return DeviceType.VIRTUAL_CABLE_INPUT
                return DeviceType.VIRTUAL_CABLE_OUTPUT
        else:
            if is_input:
                return DeviceType.MICROPHONE
            else:
                return DeviceType.SPEAKER
    
    def _configure_mode_devices(self) -> bool:
        """
        Configure input/output devices based on current operation mode
        
        Returns:
            True if configuration successful
        """
        try:
            mode = self.config.operation_mode
            
            if mode == OperationMode.BASIC_MODE:
                return self._configure_basic_mode()
            elif mode == OperationMode.FULL_AUTOMATION_MODE:
                return self._configure_full_automation_mode()
            elif mode == OperationMode.HYBRID_MODE:
                return self._configure_hybrid_mode()
            else:
                logger.error(f"Unknown operation mode: {mode}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to configure mode devices: {e}")
            return False
    
    def _configure_basic_mode(self) -> bool:
        """Configure devices for BASIC_MODE (PC microphone to PC speakers)"""
        logger.debug("Configuring BASIC_MODE")
        
        # Find default PC microphone
        input_device = self._find_device(
            device_type=DeviceType.MICROPHONE,
            is_virtual=False,
            prefer_default=True
        )
        
        # Find default PC speakers
        output_device = self._find_device(
            device_type=DeviceType.SPEAKER,
            is_virtual=False,
            prefer_default=True
        )
        
        if input_device is None or output_device is None:
            logger.error("Could not find PC microphone or speakers")
            return False
        
        self._current_input_device = input_device
        self._current_output_device = output_device
        return True
    
    def _configure_full_automation_mode(self) -> bool:
        """Configure devices for FULL_AUTOMATION_MODE (VB-Cable routing)"""
        logger.debug("Configuring FULL_AUTOMATION_MODE")
        
        # Find VB-Cable Output (audio from CareCam app)
        input_device = self._find_device(
            device_type=DeviceType.VIRTUAL_CABLE_OUTPUT,
            is_virtual=True
        )
        
        # Find VB-Cable Input (audio to CareCam app)
        output_device = self._find_device(
            device_type=DeviceType.VIRTUAL_CABLE_INPUT,
            is_virtual=True
        )
        
        if input_device is None or output_device is None:
            logger.error("VB-Cable not found. Install VB-Cable for full automation mode.")
            self.config.virtual_cable_enabled = False
            return False
        
        self._current_input_device = input_device
        self._current_output_device = output_device
        self.config.virtual_cable_enabled = True
        return True
    
    def _configure_hybrid_mode(self) -> bool:
        """Configure devices for HYBRID_MODE (PC mic + VB-Cable to both outputs)"""
        logger.debug("Configuring HYBRID_MODE")
        
        # For hybrid mode, we'll use PC mic as primary input
        # This is a simplified implementation - full hybrid requires audio mixing
        input_device = self._find_device(
            device_type=DeviceType.MICROPHONE,
            is_virtual=False,
            prefer_default=True
        )
        
        # Use PC speakers as primary output
        output_device = self._find_device(
            device_type=DeviceType.SPEAKER,
            is_virtual=False,
            prefer_default=True
        )
        
        if input_device is None or output_device is None:
            logger.error("Could not configure hybrid mode devices")
            return False
        
        # Check if VB-Cable is available for secondary routing
        vb_cable_available = self._find_device(
            device_type=DeviceType.VIRTUAL_CABLE_OUTPUT,
            is_virtual=True
        ) is not None
        
        self.config.virtual_cable_enabled = vb_cable_available
        self._current_input_device = input_device
        self._current_output_device = output_device
        
        logger.info(f"Hybrid mode configured (VB-Cable available: {vb_cable_available})")
        return True
    
    def _find_device(
        self,
        device_type: DeviceType,
        is_virtual: bool,
        prefer_default: bool = False
    ) -> Optional[AudioDevice]:
        """
        Find a device matching criteria
        
        Args:
            device_type: Type of device to find
            is_virtual: Whether to find virtual or physical device
            prefer_default: If True, try to find system default device
            
        Returns:
            AudioDevice or None if not found
        """
        # Get default device IDs if needed
        default_input_id = None
        default_output_id = None
        
        if prefer_default and self._audio:
            try:
                default_input_id = self._audio.get_default_input_device_info()['index']
            except:
                pass
            
            try:
                default_output_id = self._audio.get_default_output_device_info()['index']
            except:
                pass
        
        # Search for matching device
        candidates = []
        
        for device in self._available_devices:
            if device.device_type == device_type and device.is_virtual == is_virtual:
                candidates.append(device)
        
        if not candidates:
            return None
        
        # Prefer default device if requested
        if prefer_default:
            target_id = default_input_id if device_type in [DeviceType.MICROPHONE, DeviceType.VIRTUAL_CABLE_OUTPUT] else default_output_id
            
            if target_id is not None:
                for device in candidates:
                    if device.device_id == target_id:
                        return device
        
        # Return first candidate
        return candidates[0]
    
    def _test_device_access(self, device_id: int, is_input: bool) -> bool:
        """
        Test if a device can be opened
        
        Args:
            device_id: Device ID to test
            is_input: True for input device, False for output
            
        Returns:
            True if device is accessible
        """
        if self._audio is None:
            return False
        
        try:
            stream = self._audio.open(
                format=pyaudio.paInt16,
                channels=self.config.channels,
                rate=self.config.sample_rate,
                input=is_input,
                output=not is_input,
                input_device_index=device_id if is_input else None,
                output_device_index=device_id if not is_input else None,
                frames_per_buffer=self.config.buffer_size
            )
            
            stream.close()
            return True
            
        except Exception as e:
            logger.debug(f"Device {device_id} access test failed: {e}")
            return False
    
    def _estimate_latency(self) -> float:
        """
        Estimate audio routing latency
        
        Returns:
            Estimated latency in milliseconds
        """
        # Basic latency estimation based on buffer size and sample rate
        buffer_latency = (self.config.buffer_size / self.config.sample_rate) * 1000
        
        # Add processing overhead estimate
        processing_overhead = 10.0  # ms
        
        # Virtual cables add latency
        if self.config.virtual_cable_enabled:
            processing_overhead += 20.0
        
        total_latency = buffer_latency + processing_overhead
        return round(total_latency, 2)


# ===== Factory Function =====

def create_audio_router(config: Optional[AudioConfig] = None) -> AudioRouter:
    """
    Factory function to create AudioRouter instance
    
    Args:
        config: Audio configuration (uses defaults if None)
        
    Returns:
        AudioRouter instance
    """
    return AudioRouter(config)


# ===== Module Testing =====

if __name__ == "__main__":
    # Configure logging for testing
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 70)
    print("Audio Router and Mode Controller Module Test")
    print("=" * 70)
    
    # Test 1: Create AudioRouter with default config
    print("\n[Test 1] Creating AudioRouter with default config (BASIC_MODE)...")
    router = create_audio_router()
    print(f"✅ AudioRouter created: {router.config.operation_mode.value}")
    
    # Test 2: Initialize and enumerate devices
    print("\n[Test 2] Initializing AudioRouter and enumerating devices...")
    success = router.initialize()
    
    if success:
        print("✅ AudioRouter initialized successfully")
        print(f"   Input device: {router.get_input_device()}")
        print(f"   Output device: {router.get_output_device()}")
    else:
        print("❌ Failed to initialize AudioRouter")
    
    # Test 3: List all available devices
    print("\n[Test 3] Listing all available audio devices...")
    devices = router.list_available_devices()
    print(f"   Found {len(devices)} audio devices:")
    
    for i, device in enumerate(devices, 1):
        print(f"   {i}. {device}")
    
    # Test 4: Test audio path
    print("\n[Test 4] Testing audio path...")
    test_result = router.test_audio_path()
    
    if test_result.success:
        print("✅ Audio path test passed")
        print(f"   Message: {test_result.message}")
        if test_result.latency_ms:
            print(f"   Estimated latency: {test_result.latency_ms} ms")
    else:
        print(f"❌ Audio path test failed: {test_result.message}")
    
    # Test 5: Try switching to FULL_AUTOMATION_MODE
    print("\n[Test 5] Attempting to switch to FULL_AUTOMATION_MODE...")
    success = router.set_mode(OperationMode.FULL_AUTOMATION_MODE)
    
    if success:
        print("✅ Successfully switched to FULL_AUTOMATION_MODE")
        print(f"   Input device: {router.get_input_device()}")
        print(f"   Output device: {router.get_output_device()}")
        print(f"   VB-Cable enabled: {router.config.virtual_cable_enabled}")
    else:
        print("❌ Failed to switch to FULL_AUTOMATION_MODE")
        print("   (This is expected if VB-Cable is not installed)")
    
    # Test 6: Try switching to HYBRID_MODE
    print("\n[Test 6] Attempting to switch to HYBRID_MODE...")
    success = router.set_mode(OperationMode.HYBRID_MODE)
    
    if success:
        print("✅ Successfully switched to HYBRID_MODE")
        print(f"   Input device: {router.get_input_device()}")
        print(f"   Output device: {router.get_output_device()}")
        print(f"   VB-Cable available: {router.config.virtual_cable_enabled}")
    else:
        print("❌ Failed to switch to HYBRID_MODE")
    
    # Test 7: Switch back to BASIC_MODE
    print("\n[Test 7] Switching back to BASIC_MODE...")
    success = router.set_mode(OperationMode.BASIC_MODE)
    
    if success:
        print("✅ Successfully switched back to BASIC_MODE")
        print(f"   Input device: {router.get_input_device()}")
        print(f"   Output device: {router.get_output_device()}")
    else:
        print("❌ Failed to switch back to BASIC_MODE")
    
    # Test 8: Test with custom configuration
    print("\n[Test 8] Creating AudioRouter with custom configuration...")
    custom_config = AudioConfig(
        operation_mode=OperationMode.BASIC_MODE,
        sample_rate=44100,
        channels=2,
        buffer_size=2048,
        virtual_cable_enabled=False
    )
    
    custom_router = create_audio_router(custom_config)
    success = custom_router.initialize()
    
    if success:
        print("✅ Custom AudioRouter initialized")
        print(f"   Sample rate: {custom_router.config.sample_rate} Hz")
        print(f"   Channels: {custom_router.config.channels}")
        print(f"   Buffer size: {custom_router.config.buffer_size}")
    else:
        print("❌ Failed to initialize custom AudioRouter")
    
    # Cleanup
    print("\n[Cleanup] Cleaning up resources...")
    router.cleanup()
    custom_router.cleanup()
    print("✅ Cleanup complete")
    
    print("\n" + "=" * 70)
    print("Audio Router Module Tests Completed!")
    print("=" * 70)
    
    print("\n📝 Notes:")
    print("   - BASIC_MODE: Uses PC microphone and speakers")
    print("   - FULL_AUTOMATION_MODE: Requires VB-Cable installation")
    print("   - HYBRID_MODE: Uses PC devices with optional VB-Cable monitoring")
    print("   - Install VB-Cable from: https://vb-audio.com/Cable/")
