"""
Unit Tests for System Initializer - Graceful Degradation

Tests for Task 17.3: Implement graceful degradation and fallback mechanisms

Requirements tested:
- 8.7: If Ollama unavailable, fallback to Gemini
- 11.9: If Porcupine unavailable, fallback to keyword-based wake word detection
- 17.16: If VB-Cable not installed, switch to BASIC_MODE automatically
- 17.16: If CareCam SDK unavailable, use UI automation (CareCam_Controller)
- Display informative messages when fallbacks are activated
"""

import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.system_initializer import (
    SystemInitializer,
    ComponentStatus,
    ComponentInfo,
    initialize_system_with_fallbacks
)
from config import config


class TestSystemInitializer(unittest.TestCase):
    """Test cases for SystemInitializer graceful degradation"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.initializer = SystemInitializer()
    
    def test_component_info_creation(self):
        """Test ComponentInfo dataclass creation"""
        component = ComponentInfo(
            name="Test Component",
            status=ComponentStatus.AVAILABLE,
            message="Test message"
        )
        
        self.assertEqual(component.name, "Test Component")
        self.assertEqual(component.status, ComponentStatus.AVAILABLE)
        self.assertEqual(component.message, "Test message")
        self.assertIsNone(component.fallback_name)
        self.assertFalse(component.is_critical)
    
    def test_component_info_with_fallback(self):
        """Test ComponentInfo with fallback information"""
        component = ComponentInfo(
            name="Test Component",
            status=ComponentStatus.FALLBACK_ACTIVE,
            fallback_name="Fallback Service",
            message="Using fallback"
        )
        
        self.assertEqual(component.status, ComponentStatus.FALLBACK_ACTIVE)
        self.assertEqual(component.fallback_name, "Fallback Service")
    
    @patch('modules.system_initializer.logger')
    def test_initializer_creation(self, mock_logger):
        """Test SystemInitializer initialization"""
        init = SystemInitializer()
        
        self.assertIsInstance(init.components, dict)
        self.assertIsInstance(init.warnings, list)
        self.assertIsInstance(init.errors, list)
        self.assertIsInstance(init.fallbacks_activated, list)
        
        self.assertEqual(len(init.components), 0)
        self.assertEqual(len(init.warnings), 0)
        self.assertEqual(len(init.errors), 0)
    
    def test_wake_word_engine_porcupine_available(self):
        """Test wake word engine when Porcupine is available"""
        # Simulate Porcupine being available by importing pvporcupine
        # If it's not actually installed, this test will verify fallback works
        self.initializer._check_wake_word_engine(config)
        
        self.assertIn("wake_word_engine", self.initializer.components)
        component = self.initializer.components["wake_word_engine"]
        
        # Should use Porcupine if available and enabled, otherwise fallback
        self.assertIn(component.status, [ComponentStatus.AVAILABLE, ComponentStatus.FALLBACK_ACTIVE])
    
    def test_wake_word_engine_porcupine_unavailable(self):
        """Test wake word engine fallback when Porcupine unavailable"""
        # Ensure pvporcupine is not importable
        with patch.dict('sys.modules', {'pvporcupine': None}):
            self.initializer._check_wake_word_engine(config)
        
        self.assertIn("wake_word_engine", self.initializer.components)
        component = self.initializer.components["wake_word_engine"]
        
        # Should fallback to keyword matching
        self.assertEqual(component.status, ComponentStatus.FALLBACK_ACTIVE)
        self.assertEqual(component.fallback_name, "Keyword Matching")
        self.assertIn("Wake Word Detection", self.initializer.fallbacks_activated)
    
    @patch('modules.system_initializer.SystemInitializer._test_ollama_connection')
    @patch('modules.system_initializer.SystemInitializer._test_gemini_connection')
    def test_ai_service_ollama_available(self, mock_gemini, mock_ollama):
        """Test AI service when Ollama is available"""
        mock_ollama.return_value = True
        mock_gemini.return_value = True
        
        # Test with AUTO mode
        test_config = Mock()
        test_config.AI_PROVIDER = "auto"
        test_config.OLLAMA_BASE_URL = "http://localhost:11434"
        test_config.OLLAMA_MODEL = "qwen2.5:0.5b"
        test_config.AI_MODEL = "gemini-flash-latest"
        
        self.initializer._check_ai_service(test_config)
        
        self.assertIn("ai_service", self.initializer.components)
        component = self.initializer.components["ai_service"]
        
        # Should use Ollama as primary
        self.assertEqual(component.status, ComponentStatus.AVAILABLE)
        self.assertIn("Ollama", component.message)
    
    @patch('modules.system_initializer.SystemInitializer._test_ollama_connection')
    @patch('modules.system_initializer.SystemInitializer._test_gemini_connection')
    def test_ai_service_ollama_unavailable_gemini_fallback(self, mock_gemini, mock_ollama):
        """Test AI service fallback to Gemini when Ollama unavailable"""
        mock_ollama.return_value = False
        mock_gemini.return_value = True
        
        # Test with AUTO mode
        test_config = Mock()
        test_config.AI_PROVIDER = "auto"
        test_config.OLLAMA_BASE_URL = "http://localhost:11434"
        test_config.OLLAMA_MODEL = "qwen2.5:0.5b"
        test_config.AI_MODEL = "gemini-flash-latest"
        
        self.initializer._check_ai_service(test_config)
        
        self.assertIn("ai_service", self.initializer.components)
        component = self.initializer.components["ai_service"]
        
        # Should fallback to Gemini
        self.assertEqual(component.status, ComponentStatus.FALLBACK_ACTIVE)
        self.assertEqual(component.fallback_name, "Google Gemini")
        self.assertIn("AI Service", self.initializer.fallbacks_activated)
    
    @patch('modules.system_initializer.SystemInitializer._test_ollama_connection')
    @patch('modules.system_initializer.SystemInitializer._test_gemini_connection')
    def test_ai_service_both_unavailable(self, mock_gemini, mock_ollama):
        """Test AI service when both Ollama and Gemini unavailable"""
        mock_ollama.return_value = False
        mock_gemini.return_value = False
        
        test_config = Mock()
        test_config.AI_PROVIDER = "auto"
        test_config.OLLAMA_BASE_URL = "http://localhost:11434"
        test_config.OLLAMA_MODEL = "qwen2.5:0.5b"
        test_config.AI_MODEL = "gemini-flash-latest"
        
        self.initializer._check_ai_service(test_config)
        
        self.assertIn("ai_service", self.initializer.components)
        component = self.initializer.components["ai_service"]
        
        # Should be unavailable and critical
        self.assertEqual(component.status, ComponentStatus.UNAVAILABLE)
        self.assertTrue(component.is_critical)
        self.assertGreater(len(self.initializer.errors), 0)
    
    @patch('modules.system_initializer.SystemInitializer._detect_vb_cable')
    def test_vb_cable_available(self, mock_detect):
        """Test VB-Cable detection when installed"""
        mock_detect.return_value = True
        
        test_config = Mock()
        test_config.OPERATION_MODE = "full_automation"
        
        self.initializer._check_vb_cable(test_config)
        
        self.assertIn("vb_cable", self.initializer.components)
        component = self.initializer.components["vb_cable"]
        
        self.assertEqual(component.status, ComponentStatus.AVAILABLE)
    
    @patch('modules.system_initializer.SystemInitializer._detect_vb_cable')
    @patch('modules.audio_router.OperationMode')
    def test_vb_cable_unavailable_basic_mode_fallback(self, mock_mode, mock_detect):
        """Test fallback to BASIC_MODE when VB-Cable not installed"""
        mock_detect.return_value = False
        
        test_config = Mock()
        test_config.OPERATION_MODE = "full_automation"
        test_config.VIRTUAL_CABLE_ENABLED = True
        
        self.initializer._check_vb_cable(test_config)
        
        self.assertIn("vb_cable", self.initializer.components)
        component = self.initializer.components["vb_cable"]
        
        # Should fallback to BASIC_MODE
        self.assertEqual(component.status, ComponentStatus.FALLBACK_ACTIVE)
        self.assertEqual(component.fallback_name, "BASIC_MODE")
        self.assertIn("Audio Routing", self.initializer.fallbacks_activated)
        
        # Config should be updated
        self.assertFalse(test_config.VIRTUAL_CABLE_ENABLED)
    
    @patch('modules.system_initializer.SystemInitializer._detect_carecam_sdk')
    def test_carecam_sdk_available(self, mock_detect):
        """Test CareCam SDK detection when available"""
        mock_detect.return_value = True
        
        self.initializer._check_carecam_sdk(config)
        
        self.assertIn("carecam_sdk", self.initializer.components)
        component = self.initializer.components["carecam_sdk"]
        
        self.assertEqual(component.status, ComponentStatus.AVAILABLE)
        self.assertIn("Native SDK", component.message)
    
    @patch('modules.system_initializer.SystemInitializer._detect_carecam_sdk')
    def test_carecam_sdk_unavailable_ui_automation_fallback(self, mock_detect):
        """Test fallback to UI automation when SDK unavailable"""
        mock_detect.return_value = False
        
        self.initializer._check_carecam_sdk(config)
        
        self.assertIn("carecam_sdk", self.initializer.components)
        component = self.initializer.components["carecam_sdk"]
        
        # Should fallback to UI automation
        self.assertEqual(component.status, ComponentStatus.FALLBACK_ACTIVE)
        self.assertEqual(component.fallback_name, "UI Automation")
        self.assertIn("Camera Control", self.initializer.fallbacks_activated)
    
    def test_can_start_system_all_available(self):
        """Test system can start when all components available"""
        # Add non-critical components
        self.initializer.components["test1"] = ComponentInfo(
            name="Test1",
            status=ComponentStatus.AVAILABLE,
            message="Available"
        )
        self.initializer.components["test2"] = ComponentInfo(
            name="Test2",
            status=ComponentStatus.FALLBACK_ACTIVE,
            message="Fallback"
        )
        
        can_start = self.initializer._can_start_system()
        self.assertTrue(can_start)
    
    def test_can_start_system_critical_unavailable(self):
        """Test system cannot start when critical component unavailable"""
        # Add critical unavailable component
        self.initializer.components["critical"] = ComponentInfo(
            name="Critical",
            status=ComponentStatus.UNAVAILABLE,
            message="Unavailable",
            is_critical=True
        )
        
        can_start = self.initializer._can_start_system()
        self.assertFalse(can_start)
    
    def test_get_status_report(self):
        """Test status report generation"""
        # Add some components
        self.initializer.components["test"] = ComponentInfo(
            name="Test Component",
            status=ComponentStatus.AVAILABLE,
            message="Working"
        )
        self.initializer.fallbacks_activated = ["Test Fallback"]
        self.initializer.warnings = ["Test warning"]
        
        report = self.initializer.get_status_report()
        
        self.assertIsInstance(report, str)
        self.assertIn("Test Component", report)
        self.assertIn("AVAILABLE", report)
        self.assertIn("Test Fallback", report)
        self.assertIn("Test warning", report)
    
    def test_ollama_connection_test(self):
        """Test Ollama connection testing"""
        test_config = Mock()
        test_config.OLLAMA_BASE_URL = "http://localhost:11434"
        test_config.OLLAMA_MODEL = "qwen2.5:0.5b"
        
        # Test with mocked ollama - patch at import location
        with patch('ollama.Client') as mock_client_class:
            mock_client = Mock()
            mock_client.list.return_value = {
                'models': [{'name': 'qwen2.5:0.5b'}]
            }
            mock_client_class.return_value = mock_client
            
            result = self.initializer._test_ollama_connection(test_config)
            self.assertTrue(result)
    
    def test_gemini_connection_test(self):
        """Test Gemini connection testing"""
        test_config = Mock()
        
        # Valid API key
        test_config.GOOGLE_API_KEY = "AIzaSyDummyKeyForTesting123456789"
        result = self.initializer._test_gemini_connection(test_config)
        self.assertTrue(result)
        
        # Invalid API key
        test_config.GOOGLE_API_KEY = ""
        result = self.initializer._test_gemini_connection(test_config)
        self.assertFalse(result)
        
        # Short API key
        test_config.GOOGLE_API_KEY = "short"
        result = self.initializer._test_gemini_connection(test_config)
        self.assertFalse(result)
    
    def test_detect_vb_cable(self):
        """Test VB-Cable detection logic"""
        with patch('pyaudio.PyAudio') as mock_audio_class:
            mock_audio = Mock()
            mock_audio_class.return_value = mock_audio
            
            # Simulate device with "cable" in name
            mock_audio.get_device_count.return_value = 2
            mock_audio.get_device_info_by_index.side_effect = [
                {'name': 'Microphone'},
                {'name': 'CABLE Input (VB-Audio)'}
            ]
            
            result = self.initializer._detect_vb_cable()
            self.assertTrue(result)
    
    def test_detect_carecam_sdk(self):
        """Test CareCam SDK detection"""
        with patch('os.path.exists') as mock_exists:
            # SDK file exists
            mock_exists.return_value = True
            result = self.initializer._detect_carecam_sdk()
            self.assertTrue(result)
            
            # SDK file doesn't exist
            mock_exists.return_value = False
            result = self.initializer._detect_carecam_sdk()
            self.assertFalse(result)


class TestSystemInitializationIntegration(unittest.TestCase):
    """Integration tests for full system initialization"""
    
    @patch('modules.system_initializer.SystemInitializer._check_wake_word_engine')
    @patch('modules.system_initializer.SystemInitializer._check_ai_service')
    @patch('modules.system_initializer.SystemInitializer._check_vb_cable')
    @patch('modules.system_initializer.SystemInitializer._check_carecam_sdk')
    def test_initialize_system_calls_all_checks(self, mock_sdk, mock_vb, mock_ai, mock_ww):
        """Test that initialize_system calls all component checks"""
        test_config = Mock()
        
        initializer = SystemInitializer()
        status = initializer.initialize_system(test_config)
        
        # All checks should be called
        mock_ww.assert_called_once_with(test_config)
        mock_ai.assert_called_once_with(test_config)
        mock_vb.assert_called_once_with(test_config)
        mock_sdk.assert_called_once_with(test_config)
        
        # Status should be returned
        self.assertIsNotNone(status)
        self.assertIsInstance(status.components, dict)
        self.assertIsInstance(status.warnings, list)
        self.assertIsInstance(status.errors, list)
    
    def test_initialize_system_with_fallbacks_convenience_function(self):
        """Test convenience function for system initialization"""
        with patch('modules.system_initializer.SystemInitializer.initialize_system') as mock_init:
            mock_status = Mock()
            mock_init.return_value = mock_status
            
            result = initialize_system_with_fallbacks(config)
            
            self.assertEqual(result, mock_status)
            mock_init.assert_called_once()


class TestComponentStatus(unittest.TestCase):
    """Test ComponentStatus enum"""
    
    def test_component_status_values(self):
        """Test ComponentStatus enum values"""
        self.assertEqual(ComponentStatus.AVAILABLE.value, "available")
        self.assertEqual(ComponentStatus.UNAVAILABLE.value, "unavailable")
        self.assertEqual(ComponentStatus.FALLBACK_ACTIVE.value, "fallback_active")
        self.assertEqual(ComponentStatus.NOT_CHECKED.value, "not_checked")


def run_tests():
    """Run all unit tests"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestSystemInitializer))
    suite.addTests(loader.loadTestsFromTestCase(TestSystemInitializationIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestComponentStatus))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    """Run unit tests"""
    print("=" * 80)
    print("Unit Tests for System Initializer - Graceful Degradation")
    print("Task 17.3: Implement graceful degradation and fallback mechanisms")
    print("=" * 80)
    print()
    
    success = run_tests()
    
    print("\n" + "=" * 80)
    if success:
        print("✅ All unit tests passed!")
    else:
        print("❌ Some unit tests failed!")
    print("=" * 80)
    
    sys.exit(0 if success else 1)
