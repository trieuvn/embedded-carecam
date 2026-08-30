"""
Unit tests for Audio Router and Mode Controller module

Tests requirements 16.4, 16.5, 16.6, 16.7, 16.13, 16.14:
- 16.4: Set mode to switch between BASIC, FULL_AUTOMATION, and HYBRID modes
- 16.5: Mode switching in BASIC_MODE routes PC microphone to PC speakers
- 16.6: Mode switching in FULL_AUTOMATION_MODE routes VB-Cable Output to VB-Cable Input
- 16.7: Mode switching in HYBRID_MODE routes PC mic + VB-Cable to both outputs
- 16.13: Detect and enumerate audio devices (physical and virtual)
- 16.14: Handle device disconnection/reconnection gracefully
"""

import unittest
from unittest.mock import Mock, MagicMock, patch, PropertyMock
import pyaudio

from modules.audio_router import (
    AudioRouter,
    AudioConfig,
    AudioDevice,
    OperationMode,
    DeviceType,
    TestResult,
    create_audio_router
)


class TestDeviceEnumeration(unittest.TestCase):
    """Test device enumeration includes physical and virtual devices - Requirement 16.13"""
    
    def setUp(self):
        """Set up mock PyAudio with sample devices"""
        self.router = AudioRouter()
        
        # Mock PyAudio instance
        self.mock_audio = MagicMock()
        self.router._audio = self.mock_audio
        
    def test_enumerate_detects_physical_microphone(self):
        """Test that enumerate_devices detects physical microphones"""
        # Mock device info for physical microphone
        self.mock_audio.get_device_count.return_value = 1
        self.mock_audio.get_device_info_by_index.return_value = {
            'name': 'Built-in Microphone',
            'maxInputChannels': 2,
            'maxOutputChannels': 0,
            'defaultSampleRate': 44100.0
        }
        
        self.router._enumerate_devices()
        
        devices = self.router.list_available_devices()
        self.assertGreater(len(devices), 0)
        
        # Find microphone device
        mic_devices = [d for d in devices if d.device_type == DeviceType.MICROPHONE]
        self.assertGreater(len(mic_devices), 0)
        self.assertFalse(mic_devices[0].is_virtual)
        
    def test_enumerate_detects_physical_speaker(self):
        """Test that enumerate_devices detects physical speakers"""
        # Mock device info for physical speaker
        self.mock_audio.get_device_count.return_value = 1
        self.mock_audio.get_device_info_by_index.return_value = {
            'name': 'Built-in Speakers',
            'maxInputChannels': 0,
            'maxOutputChannels': 2,
            'defaultSampleRate': 44100.0
        }
        
        self.router._enumerate_devices()
        
        devices = self.router.list_available_devices()
        
        # Find speaker device
        speaker_devices = [d for d in devices if d.device_type == DeviceType.SPEAKER]
        self.assertGreater(len(speaker_devices), 0)
        self.assertFalse(speaker_devices[0].is_virtual)
        
    def test_enumerate_detects_virtual_cable(self):
        """Test that enumerate_devices detects VB-Cable virtual devices"""
        # Mock device info for VB-Cable
        self.mock_audio.get_device_count.return_value = 1
        self.mock_audio.get_device_info_by_index.return_value = {
            'name': 'CABLE Output (VB-Audio Virtual Cable)',
            'maxInputChannels': 2,
            'maxOutputChannels': 0,
            'defaultSampleRate': 48000.0
        }
        
        self.router._enumerate_devices()
        
        devices = self.router.list_available_devices()
        
        # Find virtual cable device
        virtual_devices = [d for d in devices if d.is_virtual]
        self.assertGreater(len(virtual_devices), 0)
        self.assertEqual(virtual_devices[0].device_type, DeviceType.VIRTUAL_CABLE_OUTPUT)
        
    def test_enumerate_detects_multiple_devices(self):
        """Test enumeration with multiple physical and virtual devices"""
        device_infos = [
            {
                'name': 'Microphone Array',
                'maxInputChannels': 2,
                'maxOutputChannels': 0,
                'defaultSampleRate': 16000.0
            },
            {
                'name': 'Speakers (Realtek)',
                'maxInputChannels': 0,
                'maxOutputChannels': 2,
                'defaultSampleRate': 48000.0
            },
            {
                'name': 'CABLE Input (VB-Audio Cable)',
                'maxInputChannels': 0,
                'maxOutputChannels': 2,
                'defaultSampleRate': 48000.0
            },
            {
                'name': 'CABLE Output (VB-Audio Cable)',
                'maxInputChannels': 2,
                'maxOutputChannels': 0,
                'defaultSampleRate': 48000.0
            }
        ]
        
        self.mock_audio.get_device_count.return_value = len(device_infos)
        self.mock_audio.get_device_info_by_index.side_effect = lambda i: device_infos[i]
        
        self.router._enumerate_devices()
        
        devices = self.router.list_available_devices()
        
        # Check we have both physical and virtual devices
        physical_devices = [d for d in devices if not d.is_virtual]
        virtual_devices = [d for d in devices if d.is_virtual]
        
        self.assertGreater(len(physical_devices), 0, "Should have physical devices")
        self.assertGreater(len(virtual_devices), 0, "Should have virtual devices")
        
    def test_enumerate_handles_device_error_gracefully(self):
        """Test that enumeration continues if one device fails"""
        self.mock_audio.get_device_count.return_value = 3
        
        def mock_get_device_info(index):
            if index == 1:
                raise Exception("Device not accessible")
            return {
                'name': f'Device {index}',
                'maxInputChannels': 1,
                'maxOutputChannels': 0,
                'defaultSampleRate': 16000.0
            }
        
        self.mock_audio.get_device_info_by_index.side_effect = mock_get_device_info
        
        # Should not raise exception
        self.router._enumerate_devices()
        
        devices = self.router.list_available_devices()
        # Should have 2 devices (indices 0 and 2, skipping 1)
        self.assertEqual(len(devices), 2)


class TestModeSwitching(unittest.TestCase):
    """Test mode switching between BASIC, FULL_AUTOMATION, and HYBRID - Requirement 16.4"""
    
    def setUp(self):
        """Set up router with mocked devices"""
        self.router = AudioRouter()
        self.mock_audio = MagicMock()
        self.router._audio = self.mock_audio
        
        # Mock devices
        self._setup_mock_devices()
        
    def _setup_mock_devices(self):
        """Set up mock device list"""
        self.router._available_devices = [
            AudioDevice(
                device_id=0,
                name='PC Microphone',
                device_type=DeviceType.MICROPHONE,
                is_virtual=False,
                sample_rate=16000,
                channels=1
            ),
            AudioDevice(
                device_id=1,
                name='PC Speakers',
                device_type=DeviceType.SPEAKER,
                is_virtual=False,
                sample_rate=44100,
                channels=2
            ),
            AudioDevice(
                device_id=2,
                name='CABLE Input',
                device_type=DeviceType.VIRTUAL_CABLE_INPUT,
                is_virtual=True,
                sample_rate=48000,
                channels=2
            ),
            AudioDevice(
                device_id=3,
                name='CABLE Output',
                device_type=DeviceType.VIRTUAL_CABLE_OUTPUT,
                is_virtual=True,
                sample_rate=48000,
                channels=2
            )
        ]
        self.router._devices_cached = True
        
    def test_set_mode_to_basic(self):
        """Test switching to BASIC_MODE"""
        result = self.router.set_mode(OperationMode.BASIC_MODE)
        
        self.assertTrue(result)
        self.assertEqual(self.router.config.operation_mode, OperationMode.BASIC_MODE)
        
    def test_set_mode_to_full_automation(self):
        """Test switching to FULL_AUTOMATION_MODE"""
        result = self.router.set_mode(OperationMode.FULL_AUTOMATION_MODE)
        
        self.assertTrue(result)
        self.assertEqual(self.router.config.operation_mode, OperationMode.FULL_AUTOMATION_MODE)
        
    def test_set_mode_to_hybrid(self):
        """Test switching to HYBRID_MODE"""
        result = self.router.set_mode(OperationMode.HYBRID_MODE)
        
        self.assertTrue(result)
        self.assertEqual(self.router.config.operation_mode, OperationMode.HYBRID_MODE)
        
    def test_set_mode_reverts_on_failure(self):
        """Test that mode reverts to previous value on failure"""
        # Start in BASIC_MODE
        self.router.config.operation_mode = OperationMode.BASIC_MODE
        self.router._configure_basic_mode()
        
        # Remove virtual devices to cause failure
        self.router._available_devices = [d for d in self.router._available_devices if not d.is_virtual]
        
        # Try to switch to FULL_AUTOMATION (should fail)
        result = self.router.set_mode(OperationMode.FULL_AUTOMATION_MODE)
        
        self.assertFalse(result)
        # Should revert to BASIC_MODE
        self.assertEqual(self.router.config.operation_mode, OperationMode.BASIC_MODE)
        
    def test_multiple_mode_switches(self):
        """Test multiple mode switches work correctly"""
        modes = [
            OperationMode.BASIC_MODE,
            OperationMode.HYBRID_MODE,
            OperationMode.FULL_AUTOMATION_MODE,
            OperationMode.BASIC_MODE
        ]
        
        for mode in modes:
            result = self.router.set_mode(mode)
            self.assertTrue(result, f"Failed to switch to {mode.value}")
            self.assertEqual(self.router.config.operation_mode, mode)


class TestBasicModeRouting(unittest.TestCase):
    """Test BASIC_MODE routes PC microphone to PC speakers - Requirement 16.5"""
    
    def setUp(self):
        """Set up router with mock devices"""
        self.router = AudioRouter(AudioConfig(operation_mode=OperationMode.BASIC_MODE))
        self.mock_audio = MagicMock()
        self.router._audio = self.mock_audio
        
        # Set up mock devices
        self.router._available_devices = [
            AudioDevice(0, 'PC Mic', DeviceType.MICROPHONE, False, 16000, 1),
            AudioDevice(1, 'PC Speaker', DeviceType.SPEAKER, False, 44100, 2)
        ]
        self.router._devices_cached = True
        
    def test_basic_mode_uses_pc_microphone(self):
        """Test that BASIC_MODE selects PC microphone as input"""
        success = self.router._configure_basic_mode()
        
        self.assertTrue(success)
        input_device = self.router.get_input_device()
        self.assertIsNotNone(input_device)
        self.assertEqual(input_device.device_type, DeviceType.MICROPHONE)
        self.assertFalse(input_device.is_virtual)
        
    def test_basic_mode_uses_pc_speakers(self):
        """Test that BASIC_MODE selects PC speakers as output"""
        success = self.router._configure_basic_mode()
        
        self.assertTrue(success)
        output_device = self.router.get_output_device()
        self.assertIsNotNone(output_device)
        self.assertEqual(output_device.device_type, DeviceType.SPEAKER)
        self.assertFalse(output_device.is_virtual)
        
    def test_basic_mode_fails_without_microphone(self):
        """Test that BASIC_MODE fails if no microphone available"""
        # Remove microphone
        self.router._available_devices = [d for d in self.router._available_devices 
                                          if d.device_type != DeviceType.MICROPHONE]
        
        success = self.router._configure_basic_mode()
        self.assertFalse(success)
        
    def test_basic_mode_fails_without_speaker(self):
        """Test that BASIC_MODE fails if no speaker available"""
        # Remove speaker
        self.router._available_devices = [d for d in self.router._available_devices 
                                          if d.device_type != DeviceType.SPEAKER]
        
        success = self.router._configure_basic_mode()
        self.assertFalse(success)


class TestFullAutomationModeRouting(unittest.TestCase):
    """Test FULL_AUTOMATION_MODE routes VB-Cable - Requirement 16.6"""
    
    def setUp(self):
        """Set up router with VB-Cable devices"""
        self.router = AudioRouter(AudioConfig(operation_mode=OperationMode.FULL_AUTOMATION_MODE))
        self.mock_audio = MagicMock()
        self.router._audio = self.mock_audio
        
        # Set up devices including VB-Cable
        self.router._available_devices = [
            AudioDevice(0, 'PC Mic', DeviceType.MICROPHONE, False, 16000, 1),
            AudioDevice(1, 'PC Speaker', DeviceType.SPEAKER, False, 44100, 2),
            AudioDevice(2, 'CABLE Input', DeviceType.VIRTUAL_CABLE_INPUT, True, 48000, 2),
            AudioDevice(3, 'CABLE Output', DeviceType.VIRTUAL_CABLE_OUTPUT, True, 48000, 2)
        ]
        self.router._devices_cached = True
        
    def test_full_automation_uses_vb_cable_output_as_input(self):
        """Test that FULL_AUTOMATION_MODE uses VB-Cable Output as input source"""
        success = self.router._configure_full_automation_mode()
        
        self.assertTrue(success)
        input_device = self.router.get_input_device()
        self.assertIsNotNone(input_device)
        self.assertEqual(input_device.device_type, DeviceType.VIRTUAL_CABLE_OUTPUT)
        self.assertTrue(input_device.is_virtual)
        
    def test_full_automation_uses_vb_cable_input_as_output(self):
        """Test that FULL_AUTOMATION_MODE uses VB-Cable Input as output destination"""
        success = self.router._configure_full_automation_mode()
        
        self.assertTrue(success)
        output_device = self.router.get_output_device()
        self.assertIsNotNone(output_device)
        self.assertEqual(output_device.device_type, DeviceType.VIRTUAL_CABLE_INPUT)
        self.assertTrue(output_device.is_virtual)
        
    def test_full_automation_enables_virtual_cable_flag(self):
        """Test that FULL_AUTOMATION_MODE sets virtual_cable_enabled flag"""
        success = self.router._configure_full_automation_mode()
        
        self.assertTrue(success)
        self.assertTrue(self.router.config.virtual_cable_enabled)
        
    def test_full_automation_fails_without_vb_cable(self):
        """Test that FULL_AUTOMATION_MODE fails if VB-Cable not installed"""
        # Remove virtual devices
        self.router._available_devices = [d for d in self.router._available_devices 
                                          if not d.is_virtual]
        
        success = self.router._configure_full_automation_mode()
        
        self.assertFalse(success)
        self.assertFalse(self.router.config.virtual_cable_enabled)
        
    def test_full_automation_fails_with_partial_vb_cable(self):
        """Test that mode fails if only partial VB-Cable is available"""
        # Keep only VB-Cable Input (remove Output)
        self.router._available_devices = [d for d in self.router._available_devices 
                                          if d.device_type != DeviceType.VIRTUAL_CABLE_OUTPUT]
        
        success = self.router._configure_full_automation_mode()
        self.assertFalse(success)


class TestHybridModeRouting(unittest.TestCase):
    """Test HYBRID_MODE routes PC mic + VB-Cable to both outputs - Requirement 16.7"""
    
    def setUp(self):
        """Set up router with all device types"""
        self.router = AudioRouter(AudioConfig(operation_mode=OperationMode.HYBRID_MODE))
        self.mock_audio = MagicMock()
        self.router._audio = self.mock_audio
        
        # Set up full device list
        self.router._available_devices = [
            AudioDevice(0, 'PC Mic', DeviceType.MICROPHONE, False, 16000, 1),
            AudioDevice(1, 'PC Speaker', DeviceType.SPEAKER, False, 44100, 2),
            AudioDevice(2, 'CABLE Input', DeviceType.VIRTUAL_CABLE_INPUT, True, 48000, 2),
            AudioDevice(3, 'CABLE Output', DeviceType.VIRTUAL_CABLE_OUTPUT, True, 48000, 2)
        ]
        self.router._devices_cached = True
        
    def test_hybrid_mode_uses_pc_microphone_as_primary(self):
        """Test that HYBRID_MODE uses PC microphone as primary input"""
        success = self.router._configure_hybrid_mode()
        
        self.assertTrue(success)
        input_device = self.router.get_input_device()
        self.assertIsNotNone(input_device)
        self.assertEqual(input_device.device_type, DeviceType.MICROPHONE)
        self.assertFalse(input_device.is_virtual)
        
    def test_hybrid_mode_uses_pc_speaker_as_primary_output(self):
        """Test that HYBRID_MODE uses PC speakers as primary output"""
        success = self.router._configure_hybrid_mode()
        
        self.assertTrue(success)
        output_device = self.router.get_output_device()
        self.assertIsNotNone(output_device)
        self.assertEqual(output_device.device_type, DeviceType.SPEAKER)
        self.assertFalse(output_device.is_virtual)
        
    def test_hybrid_mode_detects_vb_cable_availability(self):
        """Test that HYBRID_MODE detects if VB-Cable is available"""
        success = self.router._configure_hybrid_mode()
        
        self.assertTrue(success)
        # VB-Cable is available in our setup
        self.assertTrue(self.router.config.virtual_cable_enabled)
        
    def test_hybrid_mode_works_without_vb_cable(self):
        """Test that HYBRID_MODE works even without VB-Cable"""
        # Remove virtual devices
        self.router._available_devices = [d for d in self.router._available_devices 
                                          if not d.is_virtual]
        
        success = self.router._configure_hybrid_mode()
        
        self.assertTrue(success)
        self.assertFalse(self.router.config.virtual_cable_enabled)
        
        # Should still have PC devices configured
        self.assertIsNotNone(self.router.get_input_device())
        self.assertIsNotNone(self.router.get_output_device())


class TestAudioDeviceDetection(unittest.TestCase):
    """Test audio device detection - microphone, speaker, VB-Cable"""
    
    def setUp(self):
        """Set up router"""
        self.router = AudioRouter()
        
    def test_is_virtual_device_detects_vb_cable(self):
        """Test detection of VB-Cable virtual devices"""
        test_cases = [
            ('CABLE Output (VB-Audio Virtual Cable)', True),
            ('CABLE Input (VB-Audio Virtual Cable)', True),
            ('VB-Audio Virtual Cable', True),
            ('Loopback Capture', True),
            ('Built-in Microphone', False),
            ('Realtek Speakers', False)
        ]
        
        for name, expected in test_cases:
            result = self.router._is_virtual_device(name)
            self.assertEqual(result, expected, f"Failed for: {name}")
            
    def test_determine_device_type_for_microphone(self):
        """Test device type determination for microphones"""
        device_type = self.router._determine_device_type(
            name='Built-in Microphone',
            is_input=True,
            is_virtual=False
        )
        self.assertEqual(device_type, DeviceType.MICROPHONE)
        
    def test_determine_device_type_for_speaker(self):
        """Test device type determination for speakers"""
        device_type = self.router._determine_device_type(
            name='Built-in Speakers',
            is_input=False,
            is_virtual=False
        )
        self.assertEqual(device_type, DeviceType.SPEAKER)
        
    def test_determine_device_type_for_virtual_cable_input(self):
        """Test device type determination for VB-Cable Input"""
        device_type = self.router._determine_device_type(
            name='CABLE Input (VB-Audio Virtual Cable)',
            is_input=False,
            is_virtual=True
        )
        self.assertEqual(device_type, DeviceType.VIRTUAL_CABLE_INPUT)
        
    def test_determine_device_type_for_virtual_cable_output(self):
        """Test device type determination for VB-Cable Output"""
        device_type = self.router._determine_device_type(
            name='CABLE Output (VB-Audio Virtual Cable)',
            is_input=True,
            is_virtual=True
        )
        self.assertEqual(device_type, DeviceType.VIRTUAL_CABLE_OUTPUT)


class TestAudioPathValidation(unittest.TestCase):
    """Test audio path validation with test_audio_path()"""
    
    def setUp(self):
        """Set up router with devices"""
        self.router = AudioRouter()
        self.mock_audio = MagicMock()
        self.router._audio = self.mock_audio
        
        # Set up devices
        self.router._current_input_device = AudioDevice(
            0, 'Test Mic', DeviceType.MICROPHONE, False, 16000, 1
        )
        self.router._current_output_device = AudioDevice(
            1, 'Test Speaker', DeviceType.SPEAKER, False, 44100, 2
        )
        
    def test_audio_path_succeeds_with_valid_devices(self):
        """Test that audio path validation succeeds with valid devices"""
        # Mock successful device access
        mock_stream = MagicMock()
        self.mock_audio.open.return_value = mock_stream
        
        result = self.router.test_audio_path()
        
        self.assertTrue(result.success)
        self.assertIn('functional', result.message.lower())
        self.assertIsNotNone(result.input_device)
        self.assertIsNotNone(result.output_device)
        self.assertIsNotNone(result.latency_ms)
        
    def test_audio_path_fails_without_input_device(self):
        """Test that audio path validation fails if no input device"""
        self.router._current_input_device = None
        
        result = self.router.test_audio_path()
        
        self.assertFalse(result.success)
        self.assertIn('input', result.message.lower())
        
    def test_audio_path_fails_without_output_device(self):
        """Test that audio path validation fails if no output device"""
        self.router._current_output_device = None
        
        result = self.router.test_audio_path()
        
        self.assertFalse(result.success)
        self.assertIn('output', result.message.lower())
        
    def test_audio_path_fails_if_input_not_accessible(self):
        """Test that validation fails if input device cannot be opened"""
        # Mock input device access failure
        def mock_open(*args, **kwargs):
            if kwargs.get('input', False):
                raise Exception("Device not accessible")
            return MagicMock()
        
        self.mock_audio.open.side_effect = mock_open
        
        result = self.router.test_audio_path()
        
        self.assertFalse(result.success)
        self.assertIn('input', result.message.lower())
        
    def test_audio_path_fails_if_output_not_accessible(self):
        """Test that validation fails if output device cannot be opened"""
        # Mock successful input but failed output
        call_count = [0]
        
        def mock_open(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:  # First call (input) succeeds
                return MagicMock()
            else:  # Second call (output) fails
                raise Exception("Device not accessible")
        
        self.mock_audio.open.side_effect = mock_open
        
        result = self.router.test_audio_path()
        
        self.assertFalse(result.success)
        self.assertIn('output', result.message.lower())
        
    def test_audio_path_estimates_latency(self):
        """Test that audio path test estimates latency"""
        mock_stream = MagicMock()
        self.mock_audio.open.return_value = mock_stream
        
        result = self.router.test_audio_path()
        
        self.assertTrue(result.success)
        self.assertIsNotNone(result.latency_ms)
        self.assertGreater(result.latency_ms, 0)
        
    def test_latency_higher_with_virtual_cable(self):
        """Test that virtual cable adds latency to estimate"""
        mock_stream = MagicMock()
        self.mock_audio.open.return_value = mock_stream
        
        # Test without virtual cable
        self.router.config.virtual_cable_enabled = False
        result1 = self.router.test_audio_path()
        latency_without_vb = result1.latency_ms
        
        # Test with virtual cable
        self.router.config.virtual_cable_enabled = True
        result2 = self.router.test_audio_path()
        latency_with_vb = result2.latency_ms
        
        self.assertGreater(latency_with_vb, latency_without_vb)


class TestDeviceDisconnectionHandling(unittest.TestCase):
    """Test graceful handling of device disconnection - Requirement 16.14"""
    
    def setUp(self):
        """Set up router"""
        self.router = AudioRouter()
        self.mock_audio = MagicMock()
        self.router._audio = self.mock_audio
        
    def test_enumerate_handles_device_removal(self):
        """Test that enumeration handles device removal during scan"""
        # First call returns 3 devices, subsequent calls show device was removed
        call_count = [0]
        
        def mock_get_count():
            call_count[0] += 1
            return 3 if call_count[0] == 1 else 2
        
        self.mock_audio.get_device_count.side_effect = mock_get_count
        
        # Device 1 is removed during enumeration
        def mock_get_info(index):
            if index == 1:
                raise Exception("Device no longer exists")
            return {
                'name': f'Device {index}',
                'maxInputChannels': 1,
                'maxOutputChannels': 0,
                'defaultSampleRate': 16000.0
            }
        
        self.mock_audio.get_device_info_by_index.side_effect = mock_get_info
        
        # Should complete without crashing
        self.router._enumerate_devices()
        
        devices = self.router.list_available_devices()
        # Should have 2 devices (indices 0 and 2)
        self.assertEqual(len(devices), 2)
        
    def test_mode_switch_handles_missing_devices(self):
        """Test that mode switching handles missing devices gracefully"""
        # Start with devices
        self.router._available_devices = [
            AudioDevice(0, 'PC Mic', DeviceType.MICROPHONE, False, 16000, 1),
            AudioDevice(1, 'PC Speaker', DeviceType.SPEAKER, False, 44100, 2)
        ]
        self.router._devices_cached = True
        
        # Configure basic mode successfully
        success = self.router.set_mode(OperationMode.BASIC_MODE)
        self.assertTrue(success)
        
        # Simulate VB-Cable not available
        success = self.router.set_mode(OperationMode.FULL_AUTOMATION_MODE)
        
        # Should fail but not crash
        self.assertFalse(success)
        # Should revert to previous mode
        self.assertEqual(self.router.config.operation_mode, OperationMode.BASIC_MODE)
        
    def test_test_audio_path_detects_disconnected_device(self):
        """Test that test_audio_path detects when device is disconnected"""
        self.router._current_input_device = AudioDevice(
            0, 'Disconnected Mic', DeviceType.MICROPHONE, False, 16000, 1
        )
        self.router._current_output_device = AudioDevice(
            1, 'Speaker', DeviceType.SPEAKER, False, 44100, 2
        )
        
        # Mock device access failure
        self.mock_audio.open.side_effect = Exception("Device disconnected")
        
        result = self.router.test_audio_path()
        
        self.assertFalse(result.success)
        self.assertIn('cannot access', result.message.lower())
        
    def test_find_device_returns_none_when_not_found(self):
        """Test that _find_device returns None when device not found"""
        self.router._available_devices = []
        self.router._devices_cached = True
        
        device = self.router._find_device(
            device_type=DeviceType.MICROPHONE,
            is_virtual=False
        )
        
        self.assertIsNone(device)
        
    def test_list_devices_refreshes_cache_if_empty(self):
        """Test that list_available_devices re-enumerates if cache is empty"""
        self.router._available_devices = []
        self.router._devices_cached = False
        
        # Mock enumeration
        self.mock_audio.get_device_count.return_value = 1
        self.mock_audio.get_device_info_by_index.return_value = {
            'name': 'Test Device',
            'maxInputChannels': 1,
            'maxOutputChannels': 0,
            'defaultSampleRate': 16000.0
        }
        
        devices = self.router.list_available_devices()
        
        # Should have enumerated devices
        self.assertGreater(len(devices), 0)
        self.assertTrue(self.router._devices_cached)


class TestFactoryFunction(unittest.TestCase):
    """Test create_audio_router factory function"""
    
    def test_factory_creates_router_with_default_config(self):
        """Test factory creates router with default config"""
        router = create_audio_router()
        
        self.assertIsInstance(router, AudioRouter)
        self.assertEqual(router.config.operation_mode, OperationMode.BASIC_MODE)
        
    def test_factory_creates_router_with_custom_config(self):
        """Test factory creates router with custom config"""
        config = AudioConfig(
            operation_mode=OperationMode.FULL_AUTOMATION_MODE,
            sample_rate=44100,
            channels=2
        )
        
        router = create_audio_router(config)
        
        self.assertIsInstance(router, AudioRouter)
        self.assertEqual(router.config.operation_mode, OperationMode.FULL_AUTOMATION_MODE)
        self.assertEqual(router.config.sample_rate, 44100)
        self.assertEqual(router.config.channels, 2)


class TestAudioRouterInitialization(unittest.TestCase):
    """Test AudioRouter initialization"""
    
    def test_router_initializes_with_defaults(self):
        """Test router initialization with default configuration"""
        router = AudioRouter()
        
        self.assertIsNotNone(router.config)
        self.assertEqual(router.config.operation_mode, OperationMode.BASIC_MODE)
        self.assertIsNone(router._audio)
        self.assertIsNone(router._current_input_device)
        self.assertIsNone(router._current_output_device)
        self.assertEqual(len(router._available_devices), 0)
        self.assertFalse(router._devices_cached)
        
    def test_router_initializes_with_custom_config(self):
        """Test router initialization with custom configuration"""
        config = AudioConfig(
            operation_mode=OperationMode.HYBRID_MODE,
            sample_rate=48000,
            channels=2,
            buffer_size=2048,
            virtual_cable_enabled=True
        )
        
        router = AudioRouter(config)
        
        self.assertEqual(router.config.operation_mode, OperationMode.HYBRID_MODE)
        self.assertEqual(router.config.sample_rate, 48000)
        self.assertEqual(router.config.channels, 2)
        self.assertEqual(router.config.buffer_size, 2048)
        
    @patch('modules.audio_router.pyaudio.PyAudio')
    def test_initialize_creates_pyaudio_instance(self, mock_pyaudio_class):
        """Test that initialize() creates PyAudio instance"""
        mock_audio = MagicMock()
        mock_pyaudio_class.return_value = mock_audio
        
        router = AudioRouter()
        
        # Mock device enumeration
        mock_audio.get_device_count.return_value = 1
        mock_audio.get_device_info_by_index.return_value = {
            'name': 'Test Device',
            'maxInputChannels': 1,
            'maxOutputChannels': 1,
            'defaultSampleRate': 16000.0
        }
        
        success = router.initialize()
        
        self.assertTrue(success)
        mock_pyaudio_class.assert_called_once()
        
    def test_cleanup_terminates_pyaudio(self):
        """Test that cleanup() terminates PyAudio instance"""
        router = AudioRouter()
        mock_audio = MagicMock()
        router._audio = mock_audio
        
        router.cleanup()
        
        mock_audio.terminate.assert_called_once()
        self.assertIsNone(router._audio)


class TestAudioConfig(unittest.TestCase):
    """Test AudioConfig dataclass"""
    
    def test_audio_config_with_defaults(self):
        """Test AudioConfig with default values"""
        config = AudioConfig(operation_mode=OperationMode.BASIC_MODE)
        
        self.assertEqual(config.operation_mode, OperationMode.BASIC_MODE)
        self.assertEqual(config.sample_rate, 16000)
        self.assertEqual(config.channels, 1)
        self.assertEqual(config.buffer_size, 1024)
        self.assertFalse(config.virtual_cable_enabled)
        
    def test_audio_config_with_custom_values(self):
        """Test AudioConfig with custom values"""
        config = AudioConfig(
            operation_mode=OperationMode.FULL_AUTOMATION_MODE,
            sample_rate=48000,
            channels=2,
            buffer_size=2048,
            virtual_cable_enabled=True
        )
        
        self.assertEqual(config.operation_mode, OperationMode.FULL_AUTOMATION_MODE)
        self.assertEqual(config.sample_rate, 48000)
        self.assertEqual(config.channels, 2)
        self.assertEqual(config.buffer_size, 2048)
        self.assertTrue(config.virtual_cable_enabled)


class TestAudioDevice(unittest.TestCase):
    """Test AudioDevice dataclass"""
    
    def test_audio_device_creation(self):
        """Test AudioDevice creation"""
        device = AudioDevice(
            device_id=0,
            name='Test Microphone',
            device_type=DeviceType.MICROPHONE,
            is_virtual=False,
            sample_rate=16000,
            channels=1
        )
        
        self.assertEqual(device.device_id, 0)
        self.assertEqual(device.name, 'Test Microphone')
        self.assertEqual(device.device_type, DeviceType.MICROPHONE)
        self.assertFalse(device.is_virtual)
        self.assertEqual(device.sample_rate, 16000)
        self.assertEqual(device.channels, 1)
        
    def test_audio_device_string_representation(self):
        """Test AudioDevice string representation"""
        device = AudioDevice(
            device_id=0,
            name='Test Device',
            device_type=DeviceType.MICROPHONE,
            is_virtual=False,
            sample_rate=16000,
            channels=1
        )
        
        str_repr = str(device)
        self.assertIn('[PHYSICAL]', str_repr)
        self.assertIn('Test Device', str_repr)
        self.assertIn('microphone', str_repr)
        
    def test_virtual_device_string_representation(self):
        """Test virtual device string representation"""
        device = AudioDevice(
            device_id=2,
            name='CABLE Output',
            device_type=DeviceType.VIRTUAL_CABLE_OUTPUT,
            is_virtual=True,
            sample_rate=48000,
            channels=2
        )
        
        str_repr = str(device)
        self.assertIn('[VIRTUAL]', str_repr)
        self.assertIn('CABLE Output', str_repr)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
