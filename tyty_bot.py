"""
Tỷ Tỷ Bot - Half-Duplex Mode
=============================

Workflow đơn giản:
1. Mặc định: LÒA BẬT → lắng nghe từ camera
2. Khi nghe "Tỷ tỷ + câu hỏi":
   - Tắt loa
   - Bật mic + phát TTS qua VB-Cable
   - Bật lại loa
3. KHÔNG phản hồi nếu không có wake word "Tỷ tỷ"

Cài đặt:
1. pip install -r requirements.txt
2. Cấu hình .env (GOOGLE_API_KEY)
3. Cài VB-Cable và set app CareCam dùng "CABLE Output" làm mic
4. Mở app CareCam, bật loa (speaker)
5. Chạy: python tyty_bot.py
"""

import sys
import os
import time
import tempfile
import asyncio
from typing import Optional, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import pyaudio
    import numpy as np
    import edge_tts
    from pydub import AudioSegment
except ImportError as e:
    print(f"❌ Thiếu thư viện: {e}")
    print("   Chạy: pip install -r requirements.txt")
    sys.exit(1)

from dotenv import load_dotenv
load_dotenv()

# Config
WAKE_WORD = "tỷ tỷ"  # Có thể thêm các biến thể: ["tỷ tỷ", "ty ty", "chị chị"]
WAKE_WORD_VARIANTS = ["tỷ tỷ", "ty ty", "chị", "ti ti", "titi"]
TTS_VOICE = "vi-VN-HoaiMyNeural"
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")


class TyTyBot:
    """Tỷ Tỷ Chatbot - Half-Duplex Mode"""
    
    def __init__(self):
        print("=" * 60)
        print("🤖 Tỷ Tỷ Bot - Half-Duplex Mode")
        print("=" * 60)
        
        self.audio = pyaudio.PyAudio()
        self.vbcable_idx = None
        self.ui_controller = None
        self.ai_service = None
        self.stt_service = None
        
        self.running = False
        self.speaker_on = False  # Track speaker state
        
    def initialize(self) -> bool:
        """Khởi tạo tất cả components"""
        print("\n🔄 Đang khởi tạo...\n")
        
        # 1. Find VB-Cable
        self._find_vbcable()
        
        # 2. Initialize UI controller
        self._init_ui_controller()
        
        # 3. Initialize AI service
        self._init_ai_service()
        
        # 4. Initialize STT
        self._init_stt_service()
        
        if not self.vbcable_idx:
            print("\n⚠️  VB-Cable chưa cài đặt!")
            print("   Tải tại: https://vb-audio.com/Cable/")
            return False
        
        if not self.ui_controller:
            print("\n⚠️  Không thể điều khiển app - cần chạy CareCam")
            return False
        
        print("\n✅ Khởi tạo hoàn tất!")
        return True
    
    def _find_vbcable(self):
        """Tìm VB-Cable output device"""
        for i in range(self.audio.get_device_count()):
            info = self.audio.get_device_info_by_index(i)
            if 'cable input' in info['name'].lower() and info['maxOutputChannels'] > 0:
                self.vbcable_idx = i
                print(f"✅ VB-Cable: [{i}] {info['name']}")
                return
        print("❌ VB-Cable không tìm thấy")
    
    def _init_ui_controller(self):
        """Khởi tạo UI controller cho CareCam"""
        try:
            from modules.carecam_message import CareCamMessageController
            self.ui_controller = CareCamMessageController()
            if self.ui_controller.find_window():
                print("✅ CareCam app detected")
            else:
                self.ui_controller = None
        except Exception as e:
            print(f"❌ UI Controller error: {e}")
            self.ui_controller = None
    
    def _init_ai_service(self):
        """Khởi tạo AI service"""
        if not GOOGLE_API_KEY:
            print("⚠️  GOOGLE_API_KEY chưa được cấu hình trong .env")
            print("   Bot sẽ hoạt động ở chế độ echo")
            return
        
        try:
            import google.generativeai as genai
            genai.configure(api_key=GOOGLE_API_KEY)
            self.ai_service = genai.GenerativeModel('gemini-1.5-flash')
            print("✅ AI Service: Gemini 1.5 Flash")
        except Exception as e:
            print(f"❌ AI Service error: {e}")
    
    def _init_stt_service(self):
        """Khởi tạo Speech-to-Text"""
        try:
            import speech_recognition as sr
            self.stt_service = sr.Recognizer()
            self.stt_service.energy_threshold = 300
            self.stt_service.dynamic_energy_threshold = True
            print("✅ Speech Recognition ready")
        except Exception as e:
            print(f"❌ STT error: {e}")
    
    def enable_speaker(self):
        """Bật loa trong app"""
        if self.ui_controller and not self.speaker_on:
            print("🔊 Bật loa...")
            self.ui_controller.toggle_speaker()
            self.speaker_on = True
            time.sleep(0.3)
    
    def disable_speaker(self):
        """Tắt loa trong app"""
        if self.ui_controller and self.speaker_on:
            print("🔇 Tắt loa...")
            self.ui_controller.toggle_speaker()
            self.speaker_on = False
            time.sleep(0.3)
    
    def hold_mic_and_speak(self, text: str):
        """Giữ mic và phát TTS"""
        if not self.ui_controller:
            print("⚠️  Không có UI controller")
            return
        
        try:
            # 1. Generate TTS
            print(f"🗣️ Generating TTS: '{text[:50]}...'")
            temp_mp3 = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False).name
            temp_wav = temp_mp3.replace(".mp3", ".wav")
            
            async def generate():
                communicate = edge_tts.Communicate(text, TTS_VOICE)
                await communicate.save(temp_mp3)
            
            asyncio.run(generate())
            
            # Convert to WAV
            audio_segment = AudioSegment.from_mp3(temp_mp3)
            audio_segment.export(temp_wav, format="wav")
            audio_duration = len(audio_segment) / 1000.0
            
            # 2. Hold mic
            print(f"🎤 Giữ mic {audio_duration:.1f}s...")
            import threading
            mic_thread = threading.Thread(
                target=self.ui_controller.hold_mic,
                args=(audio_duration + 1.0,)
            )
            mic_thread.start()
            time.sleep(0.5)  # Wait for mic to be held
            
            # 3. Play to VB-Cable
            self._play_wav_to_vbcable(temp_wav)
            
            # 4. Wait for mic release
            mic_thread.join()
            
            # Cleanup
            os.remove(temp_mp3)
            os.remove(temp_wav)
            
        except Exception as e:
            print(f"❌ TTS error: {e}")
            import traceback
            traceback.print_exc()
    
    def _play_wav_to_vbcable(self, wav_path: str):
        """Phát WAV file qua VB-Cable"""
        import wave
        
        wf = wave.open(wav_path, 'rb')
        stream = self.audio.open(
            format=self.audio.get_format_from_width(wf.getsampwidth()),
            channels=wf.getnchannels(),
            rate=wf.getframerate(),
            output=True,
            output_device_index=self.vbcable_idx
        )
        
        print("📤 Phát qua VB-Cable...")
        data = wf.readframes(1024)
        while data:
            stream.write(data)
            data = wf.readframes(1024)
        
        stream.stop_stream()
        stream.close()
        wf.close()
    
    def listen_for_speech(self) -> Optional[str]:
        """Lắng nghe và nhận dạng giọng nói"""
        if not self.stt_service:
            return None
        
        import speech_recognition as sr
        
        with sr.Microphone() as source:
            try:
                print("👂 Đang nghe...", end=" ", flush=True)
                audio = self.stt_service.listen(source, timeout=5, phrase_time_limit=10)
                text = self.stt_service.recognize_google(audio, language="vi-VN")
                print(f"'{text}'")
                return text.lower()
            except sr.WaitTimeoutError:
                print("(timeout)")
                return None
            except sr.UnknownValueError:
                print("(không nhận dạng được)")
                return None
            except Exception as e:
                print(f"(error: {e})")
                return None
    
    def check_wake_word(self, text: str) -> Tuple[bool, str]:
        """
        Kiểm tra wake word và trích xuất câu hỏi
        
        Returns:
            (has_wake_word, question)
        """
        if not text:
            return False, ""
        
        text_lower = text.lower()
        
        for variant in WAKE_WORD_VARIANTS:
            if variant in text_lower:
                # Trích xuất phần sau wake word
                idx = text_lower.find(variant)
                question = text[idx + len(variant):].strip()
                return True, question
        
        return False, ""
    
    def get_ai_response(self, question: str) -> str:
        """Lấy response từ AI"""
        if not self.ai_service:
            # Echo mode if no AI
            return f"Bạn hỏi: {question}"
        
        try:
            # System prompt cho Tỷ Tỷ
            prompt = f"""Bạn là Tỷ Tỷ, một trợ lý AI thân thiện, nói tiếng Việt tự nhiên.
Trả lời ngắn gọn, dễ hiểu, thân thiện như một người chị gái.
Không dùng markdown hay format đặc biệt.

User hỏi: {question}"""
            
            response = self.ai_service.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"❌ AI error: {e}")
            return "Xin lỗi, Tỷ Tỷ không xử lý được câu hỏi này."
    
    def respond_to_camera(self, text: str):
        """
        Phản hồi đến camera:
        1. Tắt loa
        2. Bật mic + phát TTS
        3. Bật lại loa
        """
        print("\n" + "=" * 40)
        print(f"🤖 Tỷ Tỷ: {text}")
        print("=" * 40)
        
        # 1. Tắt loa
        self.disable_speaker()
        
        # 2. Bật mic và phát TTS
        self.hold_mic_and_speak(text)
        
        # 3. Bật lại loa
        time.sleep(0.5)
        self.enable_speaker()
        
        print("\n👂 Tiếp tục lắng nghe...")
    
    def run(self):
        """Main loop"""
        if not self.initialize():
            return
        
        print("\n" + "=" * 60)
        print("🎧 Đang lắng nghe...")
        print(f"   Nói '{WAKE_WORD.upper()} + câu hỏi' để tương tác")
        print("   Ví dụ: 'Tỷ tỷ 1+1 bằng mấy?'")
        print("   Nhấn Ctrl+C để dừng")
        print("=" * 60 + "\n")
        
        # Bật loa mặc định
        self.enable_speaker()
        
        self.running = True
        
        while self.running:
            try:
                # Lắng nghe
                text = self.listen_for_speech()
                
                if not text:
                    continue
                
                # Kiểm tra wake word
                has_wake, question = self.check_wake_word(text)
                
                if has_wake:
                    if question:
                        # Có wake word + câu hỏi → phản hồi
                        print(f"\n🎯 Phát hiện: '{WAKE_WORD}' + '{question}'")
                        response = self.get_ai_response(question)
                        self.respond_to_camera(response)
                    else:
                        # Chỉ có wake word → chờ câu hỏi
                        print(f"\n🎯 Phát hiện: '{WAKE_WORD}' (chờ câu hỏi...)")
                        self.respond_to_camera("Dạ, Tỷ Tỷ nghe đây!")
                        
                        # Lắng nghe câu hỏi
                        follow_up = self.listen_for_speech()
                        if follow_up:
                            response = self.get_ai_response(follow_up)
                            self.respond_to_camera(response)
                else:
                    # Không có wake word → bỏ qua
                    print(f"   (Bỏ qua - không có wake word)")
                
            except KeyboardInterrupt:
                print("\n\n🛑 Đang dừng...")
                self.running = False
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        self.audio.terminate()
        print("\n👋 Tạm biệt!")
    
    def test_tts(self, text: str = "Xin chào! Tỷ Tỷ đã sẵn sàng."):
        """Test TTS output"""
        if not self.initialize():
            return
        
        print(f"\n🔊 Test TTS: '{text}'")
        self.respond_to_camera(text)


def main():
    bot = TyTyBot()
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # Test mode
        bot.test_tts()
    else:
        # Main mode
        bot.run()


if __name__ == "__main__":
    main()
