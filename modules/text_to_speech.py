"""
Text-to-Speech Module - Chuyển văn bản thành giọng nói
Sử dụng Microsoft Edge TTS (miễn phí, chất lượng cao)
"""

import asyncio
import edge_tts
import tempfile
import os
from typing import Optional
from pydub import AudioSegment
from pydub.playback import play

from config import config


class TextToSpeech:
    """Convert text to speech using Edge TTS"""
    
    def __init__(self, voice: str = None):
        self.voice = voice or config.TTS_VOICE
        print(f"✅ TTS initialized with voice: {self.voice}")
    
    async def _generate_audio(self, text: str, output_path: str) -> bool:
        """Generate audio file from text"""
        try:
            communicate = edge_tts.Communicate(text, self.voice)
            await communicate.save(output_path)
            return True
        except Exception as e:
            print(f"❌ TTS Error: {e}")
            return False
    
    def speak(self, text: str) -> bool:
        """
        Nói văn bản qua loa PC
        
        Args:
            text: Văn bản cần đọc
            
        Returns:
            True nếu thành công
        """
        try:
            # Tạo file tạm
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                temp_path = f.name
            
            # Generate audio
            asyncio.run(self._generate_audio(text, temp_path))
            
            # Play audio
            if os.path.exists(temp_path):
                audio = AudioSegment.from_mp3(temp_path)
                play(audio)
                os.remove(temp_path)
                return True
            
            return False
            
        except Exception as e:
            print(f"❌ Playback Error: {e}")
            return False
    
    async def speak_async(self, text: str) -> bool:
        """Async version of speak"""
        try:
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
                temp_path = f.name
            
            await self._generate_audio(text, temp_path)
            
            if os.path.exists(temp_path):
                audio = AudioSegment.from_mp3(temp_path)
                play(audio)
                os.remove(temp_path)
                return True
            
            return False
            
        except Exception as e:
            print(f"❌ Async Playback Error: {e}")
            return False
    
    @staticmethod
    def list_vietnamese_voices():
        """List available Vietnamese voices"""
        voices = [
            ("vi-VN-HoaiMyNeural", "Nữ - HoaiMy (khuyến nghị)"),
            ("vi-VN-NamMinhNeural", "Nam - NamMinh"),
        ]
        return voices


# Singleton instance
_tts = None

def get_tts() -> TextToSpeech:
    """Get or create TTS instance"""
    global _tts
    if _tts is None:
        _tts = TextToSpeech()
    return _tts


if __name__ == "__main__":
    # Test TTS
    print("🔊 Testing Text-to-Speech...")
    print("\nAvailable Vietnamese voices:")
    for voice_id, name in TextToSpeech.list_vietnamese_voices():
        print(f"  - {voice_id}: {name}")
    
    tts = get_tts()
    tts.speak("Xin chào! Tôi là Tỷ Tỷ, trợ lý AI của bạn. 1 cộng 1 bằng 2!")
