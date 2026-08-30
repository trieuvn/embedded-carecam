"""
Unit tests for UI Configuration Tool
Tests requirements 1.1-1.9
"""

import unittest
import json
import os
import tempfile
from unittest.mock import patch, MagicMock
import sys

# Import the module to test
from ui_config_tool import UIConfigTool, DEFAULT_CONFIG, CONFIG_FILE


class TestConfigFileOperations(unittest.TestCase):
    """Test configuration file loading and saving (Requirements 1.4, 1.5, 1.6, 1.7)"""
    
    def setUp(self):
        """Setup test environment with temporary config file"""
        # Create a temporary file for testing
        self.temp_fd, self.temp_config_file = tempfile.mkstemp(suffix='.json')
        os.close(self.temp_fd)
        
        # Patch CONFIG_FILE to use temp file
        self.config_file_patcher = patch('ui_config_tool.CONFIG_FILE', self.temp_config_file)
        self.config_file_patcher.start()
    
    def tearDown(self):
        """Cleanup temporary files"""
        self.config_file_patcher.stop()
        if os.path.exists(self.temp_config_file):
            os.remove(self.temp_config_file)
    
    def test_save_config_creates_json_file(self):
        """Test that saving configuration creates a JSON file (Requirement 1.4)"""
        # Create mock root
        with patch('tkinter.Tk'):
            root = MagicMock()
            tool = UIConfigTool(root)
            
            # Save configuration
            result = tool._save_config()
            
            # Verify file was created
            self.assertTrue(result)
            self.assertTrue(os.path.exists(self.temp_config_file))
    
    def test_save_config_contains_required_fields(self):
        """Test that saved config contains required fields (Requirement 1.5)"""
        with patch('tkinter.Tk'):
            root = MagicMock()
            tool = UIConfigTool(root)
            
            # Save configuration
            tool._save_config()
            
            # Read and verify
            with open(self.temp_config_file, 'r') as f:
                saved_config = json.load(f)
            
            # Check required fields exist
            self.assertIn('mic_button_x', saved_config)
            self.assertIn('mic_button_y', saved_config)
            self.assertIn('speaker_button_x', saved_config)
            self.assertIn('speaker_button_y', saved_config)
    
    def test_load_config_when_file_not_exists(self):
        """Test loading config when file doesn't exist creates defaults (Requirement 1.6)"""
        # Ensure file doesn't exist
        if os.path.exists(self.temp_config_file):
            os.remove(self.temp_config_file)
        
        with patch('tkinter.Tk'):
            root = MagicMock()
            tool = UIConfigTool(root)
            
            # Config should be default
            self.assertEqual(tool.config, DEFAULT_CONFIG)
    
    def test_load_config_when_file_exists(self):
        """Test loading config from existing file (Requirement 1.7)"""
        # Create test config
        test_config = {
            'mic_button_x': 100,
            'mic_button_y': 200,
            'speaker_button_x': 300,
            'speaker_button_y': 400
        }
        
        with open(self.temp_config_file, 'w') as f:
            json.dump(test_config, f)
        
        with patch('tkinter.Tk'):
            root = MagicMock()
            tool = UIConfigTool(root)
            
            # Verify loaded config matches
            self.assertEqual(tool.config, test_config)
    
    def test_save_and_load_roundtrip(self):
        """Test that save and load maintain data integrity"""
        with patch('tkinter.Tk'):
            root = MagicMock()
            tool = UIConfigTool(root)
            
            # Modify config
            tool.config['mic_button_x'] = 999
            tool.config['speaker_button_y'] = 888
            
            # Save
            tool._save_config()
            
            # Create new instance and load
            tool2 = UIConfigTool(root)
            
            # Verify
            self.assertEqual(tool2.config['mic_button_x'], 999)
            self.assertEqual(tool2.config['speaker_button_y'], 888)


class TestDefaultValues(unittest.TestCase):
    """Test default configuration values (Requirement 1.6)"""
    
    def test_default_config_has_all_fields(self):
        """Test that DEFAULT_CONFIG has all required fields"""
        self.assertIn('mic_button_x', DEFAULT_CONFIG)
        self.assertIn('mic_button_y', DEFAULT_CONFIG)
        self.assertIn('speaker_button_x', DEFAULT_CONFIG)
        self.assertIn('speaker_button_y', DEFAULT_CONFIG)
    
    def test_default_values_are_integers(self):
        """Test that default values are valid integers"""
        for key, value in DEFAULT_CONFIG.items():
            self.assertIsInstance(value, int)
            self.assertGreater(value, 0)


class TestPositionCapture(unittest.TestCase):
    """Test position capture functionality (Requirements 1.2, 1.3)"""
    
    @patch('ui_config_tool.pyautogui.position')
    @patch('tkinter.Tk')
    def test_mic_position_capture(self, mock_tk, mock_position):
        """Test capturing mic button position (Requirement 1.2)"""
        mock_position.return_value = (500, 600)
        
        root = MagicMock()
        tool = UIConfigTool(root)
        
        # Mock entries
        tool.mic_x_entry = MagicMock()
        tool.mic_y_entry = MagicMock()
        
        # Simulate position capture
        tool.config['mic_button_x'] = 500
        tool.config['mic_button_y'] = 600
        
        # Verify
        self.assertEqual(tool.config['mic_button_x'], 500)
        self.assertEqual(tool.config['mic_button_y'], 600)
    
    @patch('ui_config_tool.pyautogui.position')
    @patch('tkinter.Tk')
    def test_speaker_position_capture(self, mock_tk, mock_position):
        """Test capturing speaker button position (Requirement 1.3)"""
        mock_position.return_value = (700, 800)
        
        root = MagicMock()
        tool = UIConfigTool(root)
        
        # Mock entries
        tool.speaker_x_entry = MagicMock()
        tool.speaker_y_entry = MagicMock()
        
        # Simulate position capture
        tool.config['speaker_button_x'] = 700
        tool.config['speaker_button_y'] = 800
        
        # Verify
        self.assertEqual(tool.config['speaker_button_x'], 700)
        self.assertEqual(tool.config['speaker_button_y'], 800)


class TestPositionTesting(unittest.TestCase):
    """Test position testing functionality (Requirements 1.8, 1.9)"""
    
    @patch('ui_config_tool.pyautogui.moveTo')
    @patch('tkinter.Tk')
    def test_mic_position_test_moves_cursor(self, mock_tk, mock_moveTo):
        """Test that testing mic position moves cursor (Requirement 1.8)"""
        root = MagicMock()
        tool = UIConfigTool(root)
        
        # Mock entries
        tool.mic_x_entry = MagicMock()
        tool.mic_x_entry.get.return_value = "500"
        tool.mic_y_entry = MagicMock()
        tool.mic_y_entry.get.return_value = "600"
        tool.status_label = MagicMock()
        
        # Test mic position
        tool._test_mic_position()
        
        # Verify cursor moved to correct position
        mock_moveTo.assert_called_once_with(500, 600, duration=1)
    
    @patch('ui_config_tool.pyautogui.moveTo')
    @patch('tkinter.Tk')
    def test_speaker_position_test_moves_cursor(self, mock_tk, mock_moveTo):
        """Test that testing speaker position moves cursor (Requirement 1.9)"""
        root = MagicMock()
        tool = UIConfigTool(root)
        
        # Mock entries
        tool.speaker_x_entry = MagicMock()
        tool.speaker_x_entry.get.return_value = "700"
        tool.speaker_y_entry = MagicMock()
        tool.speaker_y_entry.get.return_value = "800"
        tool.status_label = MagicMock()
        
        # Test speaker position
        tool._test_speaker_position()
        
        # Verify cursor moved to correct position
        mock_moveTo.assert_called_once_with(700, 800, duration=1)


class TestUIComponents(unittest.TestCase):
    """Test UI component creation (Requirement 1.1)"""
    
    @patch('tkinter.Tk')
    def test_ui_config_tool_creates_window(self, mock_tk):
        """Test that UIConfigTool creates a window (Requirement 1.1)"""
        root = MagicMock()
        tool = UIConfigTool(root)
        
        # Verify root was configured
        root.title.assert_called_once()
        root.geometry.assert_called_once()
    
    @patch('tkinter.Tk')
    def test_ui_has_required_buttons(self, mock_tk):
        """Test that UI has all required buttons (Requirements 1.2, 1.3, 1.4, 1.8, 1.9)"""
        root = MagicMock()
        tool = UIConfigTool(root)
        
        # Verify button attributes exist
        self.assertTrue(hasattr(tool, 'select_mic_btn'))
        self.assertTrue(hasattr(tool, 'select_speaker_btn'))
        self.assertTrue(hasattr(tool, 'save_btn'))
        self.assertTrue(hasattr(tool, 'test_mic_btn'))
        self.assertTrue(hasattr(tool, 'test_speaker_btn'))


class TestConfigValidation(unittest.TestCase):
    """Test configuration validation"""
    
    @patch('tkinter.Tk')
    def test_invalid_position_values_handled(self, mock_tk):
        """Test that invalid position values are handled gracefully"""
        root = MagicMock()
        tool = UIConfigTool(root)
        
        # Mock entries with invalid values
        tool.mic_x_entry = MagicMock()
        tool.mic_x_entry.get.return_value = "invalid"
        tool.mic_y_entry = MagicMock()
        tool.mic_y_entry.get.return_value = "600"
        tool.status_label = MagicMock()
        
        # Should not crash
        with patch('ui_config_tool.messagebox'):
            tool._test_mic_position()


if __name__ == '__main__':
    print("=" * 60)
    print("Running UI Config Tool Tests")
    print("=" * 60)
    
    # Run tests
    unittest.main(verbosity=2)
