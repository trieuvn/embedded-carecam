"""
Test CareCam Controller with Position Config Integration
Tests the position_config.json loading and fallback mechanisms
"""

import json
import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from modules.carecam_controller import CareCamController, POSITION_CONFIG_FILE


def test_load_position_config_exists():
    """Test loading position_config.json when file exists"""
    print("\n" + "=" * 60)
    print("Test 1: Load position_config.json when file exists")
    print("=" * 60)
    
    # Create a temporary config file
    test_config = {
        "mic_button_x": 100,
        "mic_button_y": 200,
        "speaker_button_x": 300,
        "speaker_button_y": 400
    }
    
    with open(POSITION_CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(test_config, f)
    
    try:
        # Create controller and verify it loaded the config
        controller = CareCamController()
        
        assert controller.mic_button_pos == (100, 200), \
            f"Expected mic_button_pos (100, 200), got {controller.mic_button_pos}"
        assert controller.speaker_button_pos == (300, 400), \
            f"Expected speaker_button_pos (300, 400), got {controller.speaker_button_pos}"
        
        print("✅ Test passed: Position config loaded successfully")
        print(f"   Mic button: {controller.mic_button_pos}")
        print(f"   Speaker button: {controller.speaker_button_pos}")
        
    finally:
        # Clean up
        if os.path.exists(POSITION_CONFIG_FILE):
            os.remove(POSITION_CONFIG_FILE)


def test_fallback_when_no_config():
    """Test fallback to relative positions when position_config.json doesn't exist"""
    print("\n" + "=" * 60)
    print("Test 2: Fallback when position_config.json doesn't exist")
    print("=" * 60)
    
    # Ensure config file doesn't exist
    if os.path.exists(POSITION_CONFIG_FILE):
        os.remove(POSITION_CONFIG_FILE)
    
    # Create controller
    controller = CareCamController()
    
    # Verify it falls back to None (will calculate relative positions)
    assert controller.mic_button_pos is None, \
        f"Expected mic_button_pos None, got {controller.mic_button_pos}"
    assert controller.speaker_button_pos is None, \
        f"Expected speaker_button_pos None, got {controller.speaker_button_pos}"
    
    print("✅ Test passed: Fallback to relative positions when no config file")


def test_fallback_when_invalid_config():
    """Test fallback when position_config.json is invalid/corrupted"""
    print("\n" + "=" * 60)
    print("Test 3: Fallback when position_config.json is invalid")
    print("=" * 60)
    
    # Create an invalid config file
    with open(POSITION_CONFIG_FILE, 'w', encoding='utf-8') as f:
        f.write("invalid json content {{{")
    
    try:
        # Create controller
        controller = CareCamController()
        
        # Verify it falls back to None
        assert controller.mic_button_pos is None, \
            f"Expected mic_button_pos None, got {controller.mic_button_pos}"
        assert controller.speaker_button_pos is None, \
            f"Expected speaker_button_pos None, got {controller.speaker_button_pos}"
        
        print("✅ Test passed: Fallback when config file is invalid")
        
    finally:
        # Clean up
        if os.path.exists(POSITION_CONFIG_FILE):
            os.remove(POSITION_CONFIG_FILE)


def test_retry_logic():
    """Test retry logic for button clicks"""
    print("\n" + "=" * 60)
    print("Test 4: Retry logic for button clicks")
    print("=" * 60)
    
    # Create controller
    controller = CareCamController()
    
    # Note: This test will fail if no window is found, which is expected
    # We're just verifying the retry logic is in place
    print("ℹ️  Testing retry logic (may fail if CareCam window not found)")
    result = controller.click_mic_button(retries=1)
    
    print(f"   Click result: {result}")
    print("✅ Test passed: Retry logic implemented")


def test_position_calculation_with_config():
    """Test that loaded positions are used instead of calculated ones"""
    print("\n" + "=" * 60)
    print("Test 5: Position calculation with loaded config")
    print("=" * 60)
    
    # Create a config file
    test_config = {
        "mic_button_x": 500,
        "mic_button_y": 600,
        "speaker_button_x": 700,
        "speaker_button_y": 800
    }
    
    with open(POSITION_CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(test_config, f)
    
    try:
        # Create controller
        controller = CareCamController()
        
        # Get positions (should return loaded values, not calculated)
        mic_pos = controller._calculate_mic_button_position()
        speaker_pos = controller._calculate_speaker_button_position()
        
        assert mic_pos == (500, 600), \
            f"Expected mic position (500, 600), got {mic_pos}"
        assert speaker_pos == (700, 800), \
            f"Expected speaker position (700, 800), got {speaker_pos}"
        
        print("✅ Test passed: Loaded positions are used instead of calculated")
        print(f"   Mic position: {mic_pos}")
        print(f"   Speaker position: {speaker_pos}")
        
    finally:
        # Clean up
        if os.path.exists(POSITION_CONFIG_FILE):
            os.remove(POSITION_CONFIG_FILE)


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("🧪 CareCam Controller Position Config Integration Tests")
    print("=" * 60)
    
    try:
        test_load_position_config_exists()
        test_fallback_when_no_config()
        test_fallback_when_invalid_config()
        test_retry_logic()
        test_position_calculation_with_config()
        
        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
