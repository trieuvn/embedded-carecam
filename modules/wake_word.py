"""
Wake Word Detection Module - Phát hiện khi người dùng gọi "Tỷ Tỷ"
Sử dụng keyword matching đơn giản trên text đã được nhận dạng
"""

from typing import Tuple, Optional
from config import config


class WakeWordDetector:
    """Detect wake word "Tỷ Tỷ" from recognized text"""
    
    def __init__(self):
        self.wake_word = config.WAKE_WORD.lower()
        self.aliases = tuple(alias.lower() for alias in config.WAKE_WORD_ALIASES)
        print(f"✅ Wake word detector initialized: '{self.wake_word}'")
        print(f"   Aliases: {self.aliases}")
    
    def check(self, text: str) -> Tuple[bool, Optional[str]]:
        """
        Kiểm tra xem text có chứa wake word không
        
        Args:
            text: Text đã được nhận dạng từ giọng nói
        
        Returns:
            Tuple (is_wake_word_detected, remaining_command)
            - is_wake_word_detected: True nếu phát hiện wake word
            - remaining_command: Phần còn lại sau wake word (câu lệnh)
        """
        if not text:
            return False, None
        
        text_lower = text.lower().strip()
        
        # Check main wake word
        if self.wake_word in text_lower:
            command = self._extract_command(text_lower, self.wake_word)
            return True, command
        
        # Check aliases
        for alias in self.aliases:
            if alias in text_lower:
                command = self._extract_command(text_lower, alias)
                return True, command
        
        return False, None
    
    def _extract_command(self, text: str, wake_word: str) -> Optional[str]:
        """Extract command after wake word"""
        # Split by wake word and get the part after it
        parts = text.split(wake_word, 1)
        if len(parts) > 1:
            command = parts[1].strip()
            # Clean up common filler words
            for filler in ["ơi", "à", "này", "nè", "đi", ","]:
                if command.startswith(filler):
                    command = command[len(filler):].strip()
            return command if command else None
        return None
    
    def is_just_wake_word(self, text: str) -> bool:
        """Check if text is ONLY the wake word (no command)"""
        if not text:
            return False
        
        text_clean = text.lower().strip()
        
        # Remove common filler words
        for filler in ["ơi", "à", "này", "nè", ","]:
            text_clean = text_clean.replace(filler, "").strip()
        
        return text_clean == self.wake_word or text_clean in self.aliases


# Singleton instance
_detector = None

def get_wake_detector() -> WakeWordDetector:
    """Get or create wake word detector instance"""
    global _detector
    if _detector is None:
        _detector = WakeWordDetector()
    return _detector


if __name__ == "__main__":
    # Test wake word detection
    print("🔊 Testing Wake Word Detection...\n")
    
    detector = get_wake_detector()
    
    test_cases = [
        "Tỷ Tỷ 1 cộng 1 bằng mấy",
        "tỷ tỷ ơi thời tiết hôm nay thế nào",
        "Ty Ty bạn là ai",
        "ti ti giúp tôi với",
        "Xin chào bạn",  # No wake word
        "Tỷ Tỷ",  # Just wake word
    ]
    
    for test in test_cases:
        detected, command = detector.check(test)
        just_wake = detector.is_just_wake_word(test)
        
        print(f"Input: '{test}'")
        print(f"  → Detected: {detected}, Command: '{command}', Just wake word: {just_wake}")
        print()
