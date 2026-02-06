"""
Speech-to-Text Module - Chuyển giọng nói thành văn bản
Sử dụng Google Speech Recognition (miễn phí) hoặc Vosk (offline)
"""

import speech_recognition as sr
from typing import Optional, Tuple
from config import config


class SpeechToText:
    """Convert speech to text using various engines"""
    
    def __init__(self, use_vosk: bool = False):
        self.recognizer = sr.Recognizer()
        self.microphone = None
        self.use_vosk = use_vosk
        self._setup_microphone()
    
    def _setup_microphone(self):
        """Setup microphone for capturing audio"""
        try:
            self.microphone = sr.Microphone(sample_rate=config.SAMPLE_RATE)
            # Adjust for ambient noise
            with self.microphone as source:
                print("🎤 Calibrating microphone for ambient noise...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
            print("✅ Microphone ready!")
        except Exception as e:
            print(f"❌ Microphone Error: {e}")
            print("💡 Tip: Make sure you have a microphone connected")
            self.microphone = None
    
    def listen(self, timeout: float = None, phrase_time_limit: float = None) -> Optional[sr.AudioData]:
        """
        Lắng nghe và capture audio từ microphone
        
        Args:
            timeout: Thời gian chờ bắt đầu nói (seconds)
            phrase_time_limit: Thời gian tối đa cho mỗi câu nói (seconds)
        
        Returns:
            AudioData object hoặc None nếu lỗi
        """
        if not self.microphone:
            print("❌ No microphone available")
            return None
        
        try:
            with self.microphone as source:
                print("👂 Listening...")
                audio = self.recognizer.listen(
                    source,
                    timeout=timeout or 5,
                    phrase_time_limit=phrase_time_limit or config.MAX_RECORDING_DURATION
                )
                return audio
        except sr.WaitTimeoutError:
            print("⏰ Timeout - no speech detected")
            return None
        except Exception as e:
            print(f"❌ Listen Error: {e}")
            return None
    
    def recognize(self, audio: sr.AudioData) -> Tuple[Optional[str], float]:
        """
        Nhận dạng văn bản từ audio
        
        Args:
            audio: AudioData object từ listen()
        
        Returns:
            Tuple (text, confidence) hoặc (None, 0) nếu lỗi
        """
        try:
            # Sử dụng Google Speech Recognition (miễn phí, online)
            text = self.recognizer.recognize_google(audio, language="vi-VN")
            return text.lower(), 0.9  # Google không trả về confidence
        except sr.UnknownValueError:
            print("🤷 Could not understand audio")
            return None, 0
        except sr.RequestError as e:
            print(f"❌ Google Speech API Error: {e}")
            # Fallback to Vosk if available
            return self._recognize_vosk(audio) if self.use_vosk else (None, 0)
        except Exception as e:
            print(f"❌ Recognition Error: {e}")
            return None, 0
    
    def _recognize_vosk(self, audio: sr.AudioData) -> Tuple[Optional[str], float]:
        """Fallback recognition using Vosk (offline)"""
        try:
            from vosk import Model, KaldiRecognizer
            import json
            
            # Note: Requires downloading Vietnamese model
            model = Model("models/vosk-model-small-vn-0.4")
            rec = KaldiRecognizer(model, config.SAMPLE_RATE)
            
            raw_data = audio.get_raw_data(convert_rate=config.SAMPLE_RATE)
            rec.AcceptWaveform(raw_data)
            
            result = json.loads(rec.FinalResult())
            return result.get("text", "").lower(), result.get("confidence", 0.5)
        except Exception as e:
            print(f"❌ Vosk Error: {e}")
            return None, 0
    
    def listen_and_recognize(self) -> Optional[str]:
        """
        Convenient method: Listen and recognize in one call
        
        Returns:
            Recognized text hoặc None
        """
        audio = self.listen()
        if audio:
            text, confidence = self.recognize(audio)
            if text:
                print(f"📝 Recognized: '{text}' (confidence: {confidence:.0%})")
            return text
        return None


# Singleton instance
_stt = None

def get_stt() -> SpeechToText:
    """Get or create STT instance"""
    global _stt
    if _stt is None:
        _stt = SpeechToText()
    return _stt


if __name__ == "__main__":
    # Test STT
    print("🎤 Testing Speech-to-Text...")
    print("Speak something in Vietnamese!\n")
    
    stt = get_stt()
    text = stt.listen_and_recognize()
    
    if text:
        print(f"\n✅ You said: {text}")
    else:
        print("\n❌ No speech recognized")
