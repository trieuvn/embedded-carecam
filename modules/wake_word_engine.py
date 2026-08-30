"""
Enhanced Wake Word Detection Engine - Phát hiện "Tỷ Tỷ" sử dụng Porcupine acoustic model
Với fallback sang keyword matching nếu Porcupine không khả dụng

Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6, 11.7, 11.8, 11.9, 11.10
"""

import os
import struct
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Tuple
import numpy as np

# Try to import Porcupine
try:
    import pvporcupine
    PORCUPINE_AVAILABLE = True
except ImportError:
    PORCUPINE_AVAILABLE = False
    print("⚠️  pvporcupine not available - will use fallback keyword matching")

import sys
import os
# Add parent directory to path for config import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import config


@dataclass
class WakeWordResult:
    """
    Result from wake word detection
    
    Attributes:
        detected: Boolean indicating if wake word was found
        keyword: The wake word variant that was detected
        confidence: Confidence score (0.0 to 1.0)
        timestamp: When the detection occurred
        remaining_command: Command text after the wake word (if any)
    """
    detected: bool
    keyword: Optional[str] = None
    confidence: float = 0.0
    timestamp: datetime = None
    remaining_command: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class WakeWordEngine:
    """
    Enhanced wake word detection using Porcupine acoustic model
    Falls back to keyword matching if Porcupine unavailable
    
    Supports multiple wake word variations: "tỷ tỷ", "ty ty", "ti ti"
    """
    
    def __init__(self, model_path: Optional[str] = None, sensitivity: float = 0.5):
        """
        Initialize wake word engine
        
        Args:
            model_path: Path to wake word model directory (optional)
            sensitivity: Detection sensitivity 0.0 to 1.0 (higher = more sensitive)
        """
        self.model_path = model_path or config.WAKE_WORD_MODEL_PATH
        self.sensitivity = max(0.0, min(1.0, sensitivity))  # Clamp to [0, 1]
        self.porcupine = None
        self.use_porcupine = False
        
        # Wake word variations
        self.wake_word = config.WAKE_WORD.lower()
        self.variations = [self.wake_word] + [alias.lower() for alias in config.WAKE_WORD_ALIASES]
        
        # Initialize the engine
        self.initialize()
    
    def initialize(self) -> bool:
        """
        Initialize wake word detection engine
        Tries Porcupine first, falls back to keyword matching
        
        Returns:
            Boolean indicating successful initialization
        """
        # Try to initialize Porcupine if available
        if PORCUPINE_AVAILABLE and config.WAKE_WORD_ENGINE_ENABLED:
            try:
                success = self._initialize_porcupine()
                if success:
                    print("✅ Wake Word Engine initialized with Porcupine acoustic model")
                    print(f"   Sensitivity: {self.sensitivity}")
                    print(f"   Model path: {self.model_path}")
                    return True
            except Exception as e:
                print(f"⚠️  Failed to initialize Porcupine: {e}")
                print("   Falling back to keyword matching...")
        
        # Fallback to keyword matching
        self.use_porcupine = False
        print("✅ Wake Word Engine initialized with keyword matching (fallback)")
        print(f"   Wake word: '{self.wake_word}'")
        print(f"   Variations: {self.variations}")
        return True
    
    def _initialize_porcupine(self) -> bool:
        """
        Initialize Porcupine wake word engine
        
        Returns:
            Boolean indicating success
        """
        try:
            # Look for custom keyword model files in model_path
            keyword_paths = self._find_keyword_models()
            
            if keyword_paths:
                # Use custom trained models
                self.porcupine = pvporcupine.create(
                    keyword_paths=keyword_paths,
                    sensitivities=[self.sensitivity] * len(keyword_paths)
                )
                print(f"   Loaded {len(keyword_paths)} custom keyword model(s)")
            else:
                # Use built-in keywords if available
                # Note: Porcupine has limited built-in Vietnamese keywords
                # For production, custom models should be trained
                print("   No custom models found in:", self.model_path)
                print("   Custom wake word models are recommended for Vietnamese")
                return False
            
            self.use_porcupine = True
            return True
            
        except Exception as e:
            print(f"   Porcupine initialization error: {e}")
            return False
    
    def _find_keyword_models(self) -> List[str]:
        """
        Find .ppn keyword model files in model directory
        
        Returns:
            List of paths to keyword model files
        """
        if not os.path.exists(self.model_path):
            return []
        
        model_files = []
        for filename in os.listdir(self.model_path):
            if filename.endswith('.ppn'):
                model_files.append(os.path.join(self.model_path, filename))
        
        return model_files
    
    def detect(self, audio_segment: Optional[bytes] = None, 
               text: Optional[str] = None) -> WakeWordResult:
        """
        Detect wake word in audio segment or text
        
        Args:
            audio_segment: Raw audio data (16-bit PCM, 16kHz, mono)
            text: Transcribed text (if already available)
        
        Returns:
            WakeWordResult with detection information
        """
        if self.use_porcupine and audio_segment is not None:
            return self._detect_porcupine(audio_segment)
        elif text is not None:
            return self._detect_keyword(text)
        else:
            # No valid input
            return WakeWordResult(detected=False)
    
    def _detect_porcupine(self, audio_segment: bytes) -> WakeWordResult:
        """
        Detect wake word using Porcupine acoustic model
        
        Args:
            audio_segment: Raw audio data (16-bit PCM)
        
        Returns:
            WakeWordResult
        """
        try:
            # Convert bytes to int16 array
            audio_data = np.frombuffer(audio_segment, dtype=np.int16)
            
            # Porcupine processes fixed-size frames
            frame_length = self.porcupine.frame_length
            
            # Process audio in frames
            for i in range(0, len(audio_data) - frame_length, frame_length):
                frame = audio_data[i:i + frame_length]
                keyword_index = self.porcupine.process(frame)
                
                if keyword_index >= 0:
                    # Wake word detected!
                    detected_keyword = self.variations[keyword_index] if keyword_index < len(self.variations) else self.wake_word
                    
                    return WakeWordResult(
                        detected=True,
                        keyword=detected_keyword,
                        confidence=self.sensitivity,  # Porcupine doesn't provide confidence, use sensitivity as proxy
                        timestamp=datetime.now(),
                        remaining_command=None  # Audio-based detection can't extract command
                    )
            
            # No wake word detected in this segment
            return WakeWordResult(detected=False)
            
        except Exception as e:
            print(f"⚠️  Porcupine detection error: {e}")
            # Fallback to keyword matching if we have text
            return WakeWordResult(detected=False)
    
    def _detect_keyword(self, text: str) -> WakeWordResult:
        """
        Detect wake word using keyword matching (fallback method)
        
        Args:
            text: Transcribed text
        
        Returns:
            WakeWordResult
        """
        if not text:
            return WakeWordResult(detected=False)
        
        text_lower = text.lower().strip()
        
        # Check each variation
        for variation in self.variations:
            if variation in text_lower:
                command = self._extract_command(text_lower, variation)
                return WakeWordResult(
                    detected=True,
                    keyword=variation,
                    confidence=0.8,  # Keyword matching has lower confidence
                    timestamp=datetime.now(),
                    remaining_command=command
                )
        
        return WakeWordResult(detected=False)
    
    def _extract_command(self, text: str, wake_word: str) -> Optional[str]:
        """
        Extract command text after wake word
        
        Args:
            text: Full text
            wake_word: The wake word found
        
        Returns:
            Command text after wake word, or None
        """
        # Split by wake word and get the part after it
        parts = text.split(wake_word, 1)
        if len(parts) > 1:
            command = parts[1].strip()
            
            # Clean up common Vietnamese filler words
            fillers = ["ơi", "à", "này", "nè", "đi", "nhé", "nha", ",", "."]
            for filler in fillers:
                if command.startswith(filler):
                    command = command[len(filler):].strip()
            
            return command if command else None
        
        return None
    
    def is_wake_word_only(self, text: str) -> bool:
        """
        Check if text contains ONLY the wake word (no command)
        
        Args:
            text: Text to check
        
        Returns:
            Boolean indicating if text is just the wake word
        """
        if not text:
            return False
        
        text_clean = text.lower().strip()
        
        # Remove common filler words
        fillers = ["ơi", "à", "này", "nè", "đi", "nhé", "nha", ",", "."]
        for filler in fillers:
            text_clean = text_clean.replace(filler, "").strip()
        
        # Check if cleaned text matches any wake word variation
        return text_clean in self.variations
    
    def update_sensitivity(self, sensitivity: float) -> None:
        """
        Update detection sensitivity threshold
        
        Args:
            sensitivity: New sensitivity value 0.0 to 1.0
        """
        old_sensitivity = self.sensitivity
        self.sensitivity = max(0.0, min(1.0, sensitivity))  # Clamp to [0, 1]
        
        # If using Porcupine, need to reinitialize with new sensitivity
        if self.use_porcupine and self.sensitivity != old_sensitivity:
            print(f"🔄 Updating sensitivity: {old_sensitivity:.2f} → {self.sensitivity:.2f}")
            self._cleanup_porcupine()
            self._initialize_porcupine()
    
    def _cleanup_porcupine(self) -> None:
        """Cleanup Porcupine resources"""
        if self.porcupine is not None:
            try:
                self.porcupine.delete()
            except Exception as e:
                print(f"⚠️  Error cleaning up Porcupine: {e}")
            finally:
                self.porcupine = None
    
    def __del__(self):
        """Cleanup on deletion"""
        self._cleanup_porcupine()


# Singleton instance
_engine = None


def get_wake_word_engine(model_path: Optional[str] = None, 
                         sensitivity: Optional[float] = None) -> WakeWordEngine:
    """
    Get or create wake word engine instance (singleton pattern)
    
    Args:
        model_path: Path to model directory (optional)
        sensitivity: Detection sensitivity (optional)
    
    Returns:
        WakeWordEngine instance
    """
    global _engine
    if _engine is None:
        sens = sensitivity if sensitivity is not None else config.WAKE_WORD_SENSITIVITY
        _engine = WakeWordEngine(model_path=model_path, sensitivity=sens)
    return _engine


if __name__ == "__main__":
    """Test wake word engine"""
    print("🔊 Testing Wake Word Engine...\n")
    
    # Initialize engine
    engine = get_wake_word_engine()
    
    # Test cases for keyword matching
    test_cases = [
        "Tỷ Tỷ 1 cộng 1 bằng mấy",
        "tỷ tỷ ơi thời tiết hôm nay thế nào",
        "Ty Ty bạn là ai",
        "ti ti giúp tôi với",
        "Xin chào bạn",  # No wake word
        "Tỷ Tỷ",  # Just wake word
        "Tỷ Tỷ à",  # Wake word with filler
    ]
    
    print("Testing keyword matching (text input):")
    print("=" * 60)
    for test in test_cases:
        result = engine.detect(text=test)
        is_only = engine.is_wake_word_only(test)
        
        print(f"\nInput: '{test}'")
        print(f"  Detected: {result.detected}")
        if result.detected:
            print(f"  Keyword: '{result.keyword}'")
            print(f"  Confidence: {result.confidence:.2f}")
            print(f"  Command: '{result.remaining_command}'")
            print(f"  Just wake word: {is_only}")
    
    print("\n" + "=" * 60)
    print("\n✅ Wake word engine test complete!")
    print(f"Using Porcupine: {engine.use_porcupine}")
    print(f"Sensitivity: {engine.sensitivity}")
    
    # Test sensitivity update
    print("\n🔄 Testing sensitivity update...")
    engine.update_sensitivity(0.7)
    print(f"New sensitivity: {engine.sensitivity}")
    
    # Note about audio testing
    if not engine.use_porcupine:
        print("\n📝 Note: Audio-based detection requires Porcupine with custom models")
        print("   Place .ppn model files in:", config.WAKE_WORD_MODEL_PATH)
        print("   Currently using keyword matching fallback")
