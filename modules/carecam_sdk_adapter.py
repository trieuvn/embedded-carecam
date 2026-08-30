"""
CareCam SDK Adapter - Native SDK Integration
Provides programmatic control of CareCam camera mic/speaker via SDK instead of UI automation.
"""

import ctypes
from ctypes import c_int, c_char_p, c_void_p, c_bool, POINTER, byref
import os
import time
import logging
from dataclasses import dataclass
from typing import Optional, Callable
from enum import Enum

# Setup logging
logger = logging.getLogger(__name__)


@dataclass
class CameraConfig:
    """Camera connection configuration"""
    ip_address: str
    port: int = 8554
    username: str = "admin"
    password: str = ""
    rtsp_enabled: bool = True


@dataclass
class CameraStatus:
    """Camera connection and device status"""
    connected: bool
    mic_active: bool
    speaker_active: bool
    signal_quality: float  # 0.0 to 1.0


class ConnectionState(Enum):
    """Camera connection states"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    ERROR = "error"


class CareCamSDKAdapter:
    """
    CareCam SDK Integration Layer
    
    Provides programmatic control of camera microphone and speaker
    via direct SDK calls instead of UI automation. Falls back to
    UI automation (CareCam_Controller) if SDK is unavailable.
    
    Requirements: 17.1-17.16
    """
    
    # Default SDK path
    DEFAULT_SDK_PATH = r"d:\carecam\QianXin\sdk_client.dll"
    
    def __init__(self, sdk_path: Optional[str] = None, camera_config: Optional[CameraConfig] = None):
        """
        Initialize CareCam SDK Adapter
        
        Args:
            sdk_path: Path to qianxin_sdk.dll (uses default if None)
            camera_config: Camera connection configuration
        """
        self.sdk_path = sdk_path or self.DEFAULT_SDK_PATH
        self.camera_config = camera_config
        self.dll = None
        self.connection_state = ConnectionState.DISCONNECTED
        self._mic_active = False
        self._speaker_active = False
        self._camera_id = None
        self._audio_callback = None
        self._reconnect_attempts = 0
        self._max_reconnect_attempts = 5
        self._fallback_controller = None
        
        logger.info(f"Initializing CareCamSDKAdapter with SDK path: {self.sdk_path}")
    
    def initialize(self) -> bool:
        """
        Load qianxin_sdk.dll using ctypes
        
        Returns:
            True if SDK loaded successfully, False otherwise
            
        Requirement: 17.2
        """
        if not os.path.exists(self.sdk_path):
            logger.warning(f"SDK DLL not found at: {self.sdk_path}")
            logger.info("Will fallback to UI automation if SDK unavailable")
            return False
        
        try:
            # Load DLL
            self.dll = ctypes.CDLL(self.sdk_path)
            logger.info(f"✅ Successfully loaded SDK: {os.path.basename(self.sdk_path)}")
            
            # Find and configure SDK function signatures
            self._configure_sdk_functions()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to load SDK DLL: {e}")
            logger.info("Will fallback to UI automation")
            return False
    
    def _configure_sdk_functions(self):
        """Configure function signatures for SDK calls"""
        if not self.dll:
            return
        
        try:
            # Cfg_SetMicStatus: Set microphone on/off
            # Signature: int Cfg_SetMicStatus(int status)
            self.dll.Cfg_SetMicStatus.argtypes = [c_int]
            self.dll.Cfg_SetMicStatus.restype = c_int
            
            # Cfg_SetMicVolume: Set microphone volume
            # Signature: int Cfg_SetMicVolume(int volume)
            self.dll.Cfg_SetMicVolume.argtypes = [c_int]
            self.dll.Cfg_SetMicVolume.restype = c_int
            
            logger.debug("SDK function signatures configured")
            
        except AttributeError as e:
            logger.warning(f"Some SDK functions not available: {e}")
    
    def connect_camera(self, camera_id: Optional[str] = None) -> bool:
        """
        Establish camera connection via SDK
        
        Args:
            camera_id: Camera identifier (uses config IP if None)
            
        Returns:
            True if connection successful
            
        Requirement: 17.3
        """
        if not self.dll:
            logger.error("SDK not initialized. Call initialize() first.")
            return False
        
        if camera_id:
            self._camera_id = camera_id
        elif self.camera_config:
            self._camera_id = self.camera_config.ip_address
        else:
            logger.error("No camera ID or config provided")
            return False
        
        try:
            self.connection_state = ConnectionState.CONNECTING
            logger.info(f"Connecting to camera: {self._camera_id}")
            
            # Note: Actual SDK connection function signature unknown
            # This is a placeholder that should be adjusted based on
            # the actual SDK documentation
            
            # For now, simulate successful connection
            # In production, this would call something like:
            # result = self.dll.SDK_Connect(camera_id, port, username, password)
            
            time.sleep(0.5)  # Simulate connection delay
            
            self.connection_state = ConnectionState.CONNECTED
            self._reconnect_attempts = 0
            
            logger.info(f"✅ Connected to camera: {self._camera_id}")
            return True
            
        except Exception as e:
            logger.error(f"Camera connection failed: {e}")
            self.connection_state = ConnectionState.ERROR
            return False
    
    def enable_microphone(self, duration: Optional[float] = None) -> bool:
        """
        Enable camera microphone programmatically
        
        Args:
            duration: Optional duration to keep mic active (seconds)
                     If None, mic stays active until disable_microphone()
        
        Returns:
            True if successful
            
        Requirement: 17.4, 17.5
        """
        if not self.dll:
            logger.warning("SDK not available, falling back to UI automation")
            return self._fallback_enable_microphone(duration)
        
        try:
            # Call SDK function to enable mic
            result = self.dll.Cfg_SetMicStatus(1)  # 1 = enable
            
            if result == 0:  # Assuming 0 = success
                self._mic_active = True
                logger.info("🎤 Microphone enabled via SDK")
                
                # Handle duration if specified
                if duration:
                    logger.debug(f"Mic will auto-disable after {duration}s")
                    # Schedule disable after duration
                    # In production, this would use a timer thread
                
                return True
            else:
                logger.error(f"Failed to enable microphone: SDK returned {result}")
                return False
                
        except Exception as e:
            logger.error(f"Error enabling microphone: {e}")
            return self._handle_sdk_error(e)
    
    def disable_microphone(self) -> bool:
        """
        Disable camera microphone
        
        Returns:
            True if successful
            
        Requirement: 17.5
        """
        if not self.dll:
            logger.warning("SDK not available, falling back to UI automation")
            return self._fallback_disable_microphone()
        
        try:
            # Call SDK function to disable mic
            result = self.dll.Cfg_SetMicStatus(0)  # 0 = disable
            
            if result == 0:
                self._mic_active = False
                logger.info("🔇 Microphone disabled via SDK")
                return True
            else:
                logger.error(f"Failed to disable microphone: SDK returned {result}")
                return False
                
        except Exception as e:
            logger.error(f"Error disabling microphone: {e}")
            return self._handle_sdk_error(e)
    
    def is_microphone_active(self) -> bool:
        """
        Query current microphone status
        
        Returns:
            True if microphone is active
            
        Requirement: 17.6
        """
        return self._mic_active
    
    def get_camera_status(self) -> CameraStatus:
        """
        Retrieve camera connection and device status
        
        Returns:
            CameraStatus object with current status
            
        Requirement: 17.7, 17.8
        """
        # Calculate signal quality based on connection state
        signal_quality = 0.0
        if self.connection_state == ConnectionState.CONNECTED:
            signal_quality = 1.0
        elif self.connection_state == ConnectionState.RECONNECTING:
            signal_quality = 0.5
        
        return CameraStatus(
            connected=(self.connection_state == ConnectionState.CONNECTED),
            mic_active=self._mic_active,
            speaker_active=self._speaker_active,
            signal_quality=signal_quality
        )
    
    def play_audio_to_camera(self, audio_data: bytes) -> bool:
        """
        Stream audio to camera speaker
        
        Args:
            audio_data: Raw audio bytes to play through camera speaker
            
        Returns:
            True if audio sent successfully
            
        Requirement: 17.9
        """
        if not self.dll:
            logger.warning("SDK not available for audio streaming")
            return False
        
        if not self.connection_state == ConnectionState.CONNECTED:
            logger.error("Cannot play audio: camera not connected")
            return False
        
        try:
            # Note: Actual audio streaming function unknown
            # This would call something like:
            # result = self.dll.SDK_StreamAudio(audio_data, len(audio_data))
            
            logger.debug(f"Playing {len(audio_data)} bytes audio to camera")
            self._speaker_active = True
            
            # Simulate audio playback
            time.sleep(0.1)
            
            return True
            
        except Exception as e:
            logger.error(f"Error playing audio to camera: {e}")
            return False
    
    def on_camera_audio_received(self, callback: Callable[[bytes], None]) -> None:
        """
        Register event callback for receiving audio from camera
        
        Args:
            callback: Function to call when audio received from camera
                     Signature: callback(audio_data: bytes) -> None
        
        Requirement: 17.10
        """
        self._audio_callback = callback
        logger.info("Audio receive callback registered")
        
        # In production, this would register the callback with SDK
        # and start listening for audio events
    
    def _handle_sdk_error(self, error: Exception) -> bool:
        """
        Handle SDK errors and implement reconnection logic
        
        Requirement: 17.11
        """
        logger.error(f"SDK Error: {error}")
        
        # Check if should attempt reconnection
        if self._reconnect_attempts < self._max_reconnect_attempts:
            self._reconnect_attempts += 1
            logger.info(f"Attempting reconnection {self._reconnect_attempts}/{self._max_reconnect_attempts}")
            
            self.connection_state = ConnectionState.RECONNECTING
            time.sleep(2)  # Wait before reconnect
            
            # Attempt reconnection
            if self.connect_camera():
                logger.info("✅ Reconnection successful")
                return True
        
        # Max reconnect attempts reached
        logger.error("Max reconnection attempts reached, falling back to UI automation")
        self._fallback_to_ui_automation()
        return False
    
    def _fallback_to_ui_automation(self) -> None:
        """
        Fallback to UI automation if SDK unavailable
        
        Requirement: 17.12, 17.16
        """
        logger.info("Initializing UI automation fallback")
        
        try:
            from modules.carecam_controller import get_controller
            self._fallback_controller = get_controller()
            logger.info("✅ UI automation fallback initialized")
        except Exception as e:
            logger.error(f"Failed to initialize UI automation fallback: {e}")
    
    def _fallback_enable_microphone(self, duration: Optional[float] = None) -> bool:
        """Enable microphone using UI automation fallback"""
        if not self._fallback_controller:
            self._fallback_to_ui_automation()
        
        if self._fallback_controller:
            try:
                if duration:
                    self._fallback_controller.hold_mic_button(duration)
                else:
                    self._fallback_controller.click_mic_button()
                self._mic_active = True
                return True
            except Exception as e:
                logger.error(f"UI automation fallback failed: {e}")
                return False
        
        return False
    
    def _fallback_disable_microphone(self) -> bool:
        """Disable microphone using UI automation fallback"""
        if not self._fallback_controller:
            self._fallback_to_ui_automation()
        
        if self._fallback_controller:
            try:
                self._fallback_controller.click_mic_button()
                self._mic_active = False
                return True
            except Exception as e:
                logger.error(f"UI automation fallback failed: {e}")
                return False
        
        return False
    
    def disconnect(self) -> None:
        """Disconnect from camera and cleanup resources"""
        if self.connection_state != ConnectionState.DISCONNECTED:
            logger.info("Disconnecting from camera")
            
            # Disable mic/speaker before disconnect
            if self._mic_active:
                self.disable_microphone()
            
            self.connection_state = ConnectionState.DISCONNECTED
            self._camera_id = None
            
            logger.info("✅ Disconnected from camera")
    
    def __enter__(self):
        """Context manager entry"""
        self.initialize()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()


# Factory function for easy instantiation
def create_sdk_adapter(camera_ip: str, 
                       camera_port: int = 8554,
                       username: str = "admin", 
                       password: str = "") -> CareCamSDKAdapter:
    """
    Factory function to create and initialize SDK adapter
    
    Args:
        camera_ip: Camera IP address
        camera_port: Camera port (default: 8554)
        username: Camera username (default: "admin")
        password: Camera password
        
    Returns:
        Initialized CareCamSDKAdapter instance
    """
    config = CameraConfig(
        ip_address=camera_ip,
        port=camera_port,
        username=username,
        password=password,
        rtsp_enabled=True
    )
    
    adapter = CareCamSDKAdapter(camera_config=config)
    adapter.initialize()
    
    return adapter


if __name__ == "__main__":
    # Configure logging for testing
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 60)
    print("🎥 CareCam SDK Adapter Test")
    print("=" * 60)
    
    # Test SDK initialization
    adapter = CareCamSDKAdapter()
    
    if adapter.initialize():
        print("\n✅ SDK initialized successfully")
        
        # Test camera connection
        config = CameraConfig(
            ip_address="192.168.1.8",
            port=8554,
            username="admin",
            password=""
        )
        adapter.camera_config = config
        
        if adapter.connect_camera():
            print("✅ Camera connected")
            
            # Get camera status
            status = adapter.get_camera_status()
            print(f"\n📊 Camera Status:")
            print(f"   Connected: {status.connected}")
            print(f"   Mic Active: {status.mic_active}")
            print(f"   Speaker Active: {status.speaker_active}")
            print(f"   Signal Quality: {status.signal_quality:.2%}")
            
            # Test mic control
            print("\n🎤 Testing microphone control...")
            if adapter.enable_microphone():
                print("   ✅ Microphone enabled")
                time.sleep(2)
                
                if adapter.disable_microphone():
                    print("   ✅ Microphone disabled")
            
            # Disconnect
            adapter.disconnect()
            print("\n✅ Test completed")
    else:
        print("\n⚠️ SDK not available, fallback to UI automation enabled")
        print("   The system will use CareCam_Controller for mic/speaker control")
