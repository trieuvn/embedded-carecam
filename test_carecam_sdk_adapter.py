"""
Unit Tests for CareCam SDK Adapter
Tests core functionality and error handling of the SDK integration layer
"""

import unittest
from unittest.mock import Mock, MagicMock, patch, call
import ctypes
import time
import sys
import os

# Add modules to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'modules'))

from modules.carecam_sdk_adapter import (
    CareCamSDKAdapter,
    CameraConfig,
    CameraStatus,
    ConnectionState,
    create_sdk_adapter
)


class TestCameraConfig(unittest.TestCase):
    """Test CameraConfig dataclass"""
    
    def test_camera_config_creation(self):
        """Test creating CameraConfig with all parameters"""
        config = CameraConfig(
            ip_address="192.168.1.100",
            port=8554,
            username="admin",
            password="test123",
            rtsp_enabled=True
        )
        
        self.assertEqual(config.ip_address, "192.168.1.100")
        self.assertEqual(config.port, 8554)
        self.assertEqual(config.username, "admin")
        self.assertEqual(config.password, "test123")
        self.assertTrue(config.rtsp_enabled)
    
    def test_camera_config_defaults(self):
        """Test CameraConfig with default values"""
        config = CameraConfig(ip_address="192.168.1.8")
        
        self.assertEqual(config.ip_address, "192.168.1.8")
        self.assertEqual(config.port, 8554)
        self.assertEqual(config.username, "admin")
        self.assertEqual(config.password, "")
        self.assertTrue(config.rtsp_enabled)


class TestCameraStatus(unittest.TestCase):
    """Test CameraStatus dataclass"""
    
    def test_camera_status_creation(self):
        """Test creating CameraStatus"""
        status = CameraStatus(
            connected=True,
            mic_active=False,
            speaker_active=True,
            signal_quality=0.95
        )
        
        self.assertTrue(status.connected)
        self.assertFalse(status.mic_active)
        self.assertTrue(status.speaker_active)
        self.assertAlmostEqual(status.signal_quality, 0.95)


class TestCareCamSDKAdapterInitialization(unittest.TestCase):
    """Test SDK adapter initialization"""
    
    def test_adapter_creation_default_path(self):
        """Test creating adapter with default SDK path"""
        adapter = CareCamSDKAdapter()
        
        self.assertIsNotNone(adapter)
        self.assertEqual(adapter.sdk_path, CareCamSDKAdapter.DEFAULT_SDK_PATH)
        self.assertEqual(adapter.connection_state, ConnectionState.DISCONNECTED)
        self.assertFalse(adapter._mic_active)
        self.assertFalse(adapter._speaker_active)
    
    def test_adapter_creation_custom_path(self):
        """Test creating adapter with custom SDK path"""
        custom_path = "C:\\custom\\path\\sdk.dll"
        adapter = CareCamSDKAdapter(sdk_path=custom_path)
        
        self.assertEqual(adapter.sdk_path, custom_path)
    
    def test_adapter_creation_with_config(self):
        """Test creating adapter with camera config"""
        config = CameraConfig(ip_address="192.168.1.100")
        adapter = CareCamSDKAdapter(camera_config=config)
        
        self.assertIsNotNone(adapter.camera_config)
        self.assertEqual(adapter.camera_config.ip_address, "192.168.1.100")
    
    @patch('os.path.exists')
    @patch('ctypes.CDLL')
    def test_initialize_success(self, mock_cdll, mock_exists):
        """Test successful SDK initialization"""
        mock_exists.return_value = True
        mock_dll = MagicMock()
        mock_cdll.return_value = mock_dll
        
        adapter = CareCamSDKAdapter()
        result = adapter.initialize()
        
        self.assertTrue(result)
        self.assertIsNotNone(adapter.dll)
        mock_cdll.assert_called_once_with(adapter.sdk_path)
    
    @patch('os.path.exists')
    def test_initialize_dll_not_found(self, mock_exists):
        """Test initialization when DLL file not found"""
        mock_exists.return_value = False
        
        adapter = CareCamSDKAdapter()
        result = adapter.initialize()
        
        self.assertFalse(result)
        self.assertIsNone(adapter.dll)
    
    @patch('os.path.exists')
    @patch('ctypes.CDLL')
    def test_initialize_dll_load_error(self, mock_cdll, mock_exists):
        """Test initialization when DLL load fails"""
        mock_exists.return_value = True
        mock_cdll.side_effect = OSError("DLL load failed")
        
        adapter = CareCamSDKAdapter()
        result = adapter.initialize()
        
        self.assertFalse(result)
        self.assertIsNone(adapter.dll)


class TestCareCamSDKAdapterConnection(unittest.TestCase):
    """Test camera connection functionality"""
    
    def setUp(self):
        """Setup test fixtures"""
        self.adapter = CareCamSDKAdapter()
        self.adapter.dll = MagicMock()
    
    def test_connect_camera_with_camera_id(self):
        """Test connecting camera with explicit camera ID"""
        result = self.adapter.connect_camera(camera_id="192.168.1.100")
        
        self.assertTrue(result)
        self.assertEqual(self.adapter._camera_id, "192.168.1.100")
        self.assertEqual(self.adapter.connection_state, ConnectionState.CONNECTED)
        self.assertEqual(self.adapter._reconnect_attempts, 0)
    
    def test_connect_camera_with_config(self):
        """Test connecting camera using camera config"""
        config = CameraConfig(ip_address="192.168.1.200")
        self.adapter.camera_config = config
        
        result = self.adapter.connect_camera()
        
        self.assertTrue(result)
        self.assertEqual(self.adapter._camera_id, "192.168.1.200")
        self.assertEqual(self.adapter.connection_state, ConnectionState.CONNECTED)
    
    def test_connect_camera_no_id_or_config(self):
        """Test connecting camera without ID or config"""
        result = self.adapter.connect_camera()
        
        self.assertFalse(result)
    
    def test_connect_camera_without_dll(self):
        """Test connecting camera when SDK not initialized"""
        adapter = CareCamSDKAdapter()  # No DLL
        result = adapter.connect_camera(camera_id="192.168.1.100")
        
        self.assertFalse(result)


class TestCareCamSDKAdapterMicrophoneControl(unittest.TestCase):
    """Test microphone control functionality"""
    
    def setUp(self):
        """Setup test fixtures"""
        self.adapter = CareCamSDKAdapter()
        self.adapter.dll = MagicMock()
        self.adapter.dll.Cfg_SetMicStatus.return_value = 0  # Success
    
    def test_enable_microphone_success(self):
        """Test successful microphone enable"""
        result = self.adapter.enable_microphone()
        
        self.assertTrue(result)
        self.assertTrue(self.adapter._mic_active)
        self.adapter.dll.Cfg_SetMicStatus.assert_called_once_with(1)
    
    def test_enable_microphone_with_duration(self):
        """Test enabling microphone with duration"""
        result = self.adapter.enable_microphone(duration=5.0)
        
        self.assertTrue(result)
        self.assertTrue(self.adapter._mic_active)
    
    def test_enable_microphone_sdk_error(self):
        """Test enabling microphone when SDK returns error"""
        self.adapter.dll.Cfg_SetMicStatus.return_value = -1  # Error
        
        result = self.adapter.enable_microphone()
        
        self.assertFalse(result)
        self.assertFalse(self.adapter._mic_active)
    
    def test_disable_microphone_success(self):
        """Test successful microphone disable"""
        self.adapter._mic_active = True
        
        result = self.adapter.disable_microphone()
        
        self.assertTrue(result)
        self.assertFalse(self.adapter._mic_active)
        self.adapter.dll.Cfg_SetMicStatus.assert_called_once_with(0)
    
    def test_disable_microphone_sdk_error(self):
        """Test disabling microphone when SDK returns error"""
        self.adapter._mic_active = True
        self.adapter.dll.Cfg_SetMicStatus.return_value = -1  # Error
        
        result = self.adapter.disable_microphone()
        
        self.assertFalse(result)
        self.assertTrue(self.adapter._mic_active)  # State unchanged
    
    def test_is_microphone_active(self):
        """Test querying microphone status"""
        self.assertFalse(self.adapter.is_microphone_active())
        
        self.adapter._mic_active = True
        self.assertTrue(self.adapter.is_microphone_active())
        
        self.adapter._mic_active = False
        self.assertFalse(self.adapter.is_microphone_active())
    
    @patch('modules.carecam_controller.get_controller')
    def test_enable_microphone_fallback_to_ui(self, mock_get_controller):
        """Test microphone enable fallback to UI automation"""
        adapter = CareCamSDKAdapter()  # No DLL
        mock_controller = MagicMock()
        mock_get_controller.return_value = mock_controller
        
        result = adapter.enable_microphone(duration=3.0)
        
        self.assertTrue(result)
        mock_controller.hold_mic_button.assert_called_once_with(3.0)
    
    @patch('modules.carecam_controller.get_controller')
    def test_disable_microphone_fallback_to_ui(self, mock_get_controller):
        """Test microphone disable fallback to UI automation"""
        adapter = CareCamSDKAdapter()  # No DLL
        mock_controller = MagicMock()
        mock_get_controller.return_value = mock_controller
        
        result = adapter.disable_microphone()
        
        self.assertTrue(result)
        mock_controller.click_mic_button.assert_called_once()


class TestCareCamSDKAdapterStatus(unittest.TestCase):
    """Test status retrieval functionality"""
    
    def test_get_camera_status_connected(self):
        """Test getting status when camera connected"""
        adapter = CareCamSDKAdapter()
        adapter.connection_state = ConnectionState.CONNECTED
        adapter._mic_active = True
        adapter._speaker_active = False
        
        status = adapter.get_camera_status()
        
        self.assertTrue(status.connected)
        self.assertTrue(status.mic_active)
        self.assertFalse(status.speaker_active)
        self.assertAlmostEqual(status.signal_quality, 1.0)
    
    def test_get_camera_status_disconnected(self):
        """Test getting status when camera disconnected"""
        adapter = CareCamSDKAdapter()
        adapter.connection_state = ConnectionState.DISCONNECTED
        
        status = adapter.get_camera_status()
        
        self.assertFalse(status.connected)
        self.assertAlmostEqual(status.signal_quality, 0.0)
    
    def test_get_camera_status_reconnecting(self):
        """Test getting status when camera reconnecting"""
        adapter = CareCamSDKAdapter()
        adapter.connection_state = ConnectionState.RECONNECTING
        
        status = adapter.get_camera_status()
        
        self.assertFalse(status.connected)
        self.assertAlmostEqual(status.signal_quality, 0.5)


class TestCareCamSDKAdapterAudio(unittest.TestCase):
    """Test audio streaming functionality"""
    
    def test_play_audio_to_camera_success(self):
        """Test playing audio to camera speaker"""
        adapter = CareCamSDKAdapter()
        adapter.dll = MagicMock()
        adapter.connection_state = ConnectionState.CONNECTED
        
        audio_data = b'\x00\x01\x02\x03' * 100
        result = adapter.play_audio_to_camera(audio_data)
        
        self.assertTrue(result)
        self.assertTrue(adapter._speaker_active)
    
    def test_play_audio_to_camera_not_connected(self):
        """Test playing audio when camera not connected"""
        adapter = CareCamSDKAdapter()
        adapter.dll = MagicMock()
        adapter.connection_state = ConnectionState.DISCONNECTED
        
        audio_data = b'\x00\x01\x02\x03' * 100
        result = adapter.play_audio_to_camera(audio_data)
        
        self.assertFalse(result)
    
    def test_play_audio_to_camera_no_dll(self):
        """Test playing audio when SDK not initialized"""
        adapter = CareCamSDKAdapter()
        
        audio_data = b'\x00\x01\x02\x03' * 100
        result = adapter.play_audio_to_camera(audio_data)
        
        self.assertFalse(result)
    
    def test_on_camera_audio_received_callback(self):
        """Test registering audio receive callback"""
        adapter = CareCamSDKAdapter()
        
        callback = Mock()
        adapter.on_camera_audio_received(callback)
        
        self.assertEqual(adapter._audio_callback, callback)


class TestCareCamSDKAdapterErrorHandling(unittest.TestCase):
    """Test error handling and reconnection logic"""
    
    def test_handle_sdk_error_reconnect_success(self):
        """Test successful reconnection after error"""
        adapter = CareCamSDKAdapter()
        adapter.dll = MagicMock()
        adapter._camera_id = "192.168.1.100"
        adapter._reconnect_attempts = 0
        
        error = Exception("SDK error")
        result = adapter._handle_sdk_error(error)
        
        # Should attempt reconnection
        self.assertEqual(adapter._reconnect_attempts, 1)
    
    def test_handle_sdk_error_max_attempts_reached(self):
        """Test fallback after max reconnection attempts"""
        adapter = CareCamSDKAdapter()
        adapter.dll = MagicMock()
        adapter._camera_id = "192.168.1.100"
        adapter._reconnect_attempts = 5  # Max reached
        
        with patch.object(adapter, '_fallback_to_ui_automation'):
            error = Exception("SDK error")
            result = adapter._handle_sdk_error(error)
            
            # Should fallback to UI automation
            adapter._fallback_to_ui_automation.assert_called_once()
    
    @patch('modules.carecam_controller.get_controller')
    def test_fallback_to_ui_automation(self, mock_get_controller):
        """Test initializing UI automation fallback"""
        adapter = CareCamSDKAdapter()
        mock_controller = MagicMock()
        mock_get_controller.return_value = mock_controller
        
        adapter._fallback_to_ui_automation()
        
        self.assertIsNotNone(adapter._fallback_controller)
        mock_get_controller.assert_called_once()


class TestCareCamSDKAdapterDisconnect(unittest.TestCase):
    """Test disconnect functionality"""
    
    def test_disconnect_from_connected_state(self):
        """Test disconnecting from connected camera"""
        adapter = CareCamSDKAdapter()
        adapter.dll = MagicMock()
        adapter.dll.Cfg_SetMicStatus.return_value = 0
        adapter.connection_state = ConnectionState.CONNECTED
        adapter._camera_id = "192.168.1.100"
        adapter._mic_active = True
        
        adapter.disconnect()
        
        self.assertEqual(adapter.connection_state, ConnectionState.DISCONNECTED)
        self.assertIsNone(adapter._camera_id)
        self.assertFalse(adapter._mic_active)
    
    def test_disconnect_from_disconnected_state(self):
        """Test disconnecting when already disconnected"""
        adapter = CareCamSDKAdapter()
        adapter.connection_state = ConnectionState.DISCONNECTED
        
        adapter.disconnect()  # Should not raise error
        
        self.assertEqual(adapter.connection_state, ConnectionState.DISCONNECTED)


class TestCareCamSDKAdapterContextManager(unittest.TestCase):
    """Test context manager functionality"""
    
    @patch('os.path.exists')
    @patch('ctypes.CDLL')
    def test_context_manager_usage(self, mock_cdll, mock_exists):
        """Test using adapter as context manager"""
        mock_exists.return_value = True
        mock_dll = MagicMock()
        mock_cdll.return_value = mock_dll
        
        with CareCamSDKAdapter() as adapter:
            self.assertIsNotNone(adapter.dll)
            self.assertEqual(adapter.connection_state, ConnectionState.DISCONNECTED)
        
        # After context exit, should be disconnected
        self.assertEqual(adapter.connection_state, ConnectionState.DISCONNECTED)


class TestFactoryFunction(unittest.TestCase):
    """Test factory function for creating adapter"""
    
    @patch('os.path.exists')
    @patch('ctypes.CDLL')
    def test_create_sdk_adapter(self, mock_cdll, mock_exists):
        """Test factory function with all parameters"""
        mock_exists.return_value = True
        mock_dll = MagicMock()
        mock_cdll.return_value = mock_dll
        
        adapter = create_sdk_adapter(
            camera_ip="192.168.1.150",
            camera_port=9000,
            username="user",
            password="pass123"
        )
        
        self.assertIsNotNone(adapter)
        self.assertIsNotNone(adapter.camera_config)
        self.assertEqual(adapter.camera_config.ip_address, "192.168.1.150")
        self.assertEqual(adapter.camera_config.port, 9000)
        self.assertEqual(adapter.camera_config.username, "user")
        self.assertEqual(adapter.camera_config.password, "pass123")
    
    @patch('os.path.exists')
    @patch('ctypes.CDLL')
    def test_create_sdk_adapter_defaults(self, mock_cdll, mock_exists):
        """Test factory function with default parameters"""
        mock_exists.return_value = True
        mock_dll = MagicMock()
        mock_cdll.return_value = mock_dll
        
        adapter = create_sdk_adapter(camera_ip="192.168.1.8")
        
        self.assertIsNotNone(adapter)
        self.assertEqual(adapter.camera_config.port, 8554)
        self.assertEqual(adapter.camera_config.username, "admin")
        self.assertEqual(adapter.camera_config.password, "")


if __name__ == "__main__":
    # Run tests with verbose output
    unittest.main(verbosity=2)
