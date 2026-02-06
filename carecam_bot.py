"""
Tỷ Tỷ CareCam - Full Automation Mode
=====================================

Chế độ tự động hoàn toàn:
1. Camera mic thu âm → App CareCam phát qua speaker → PC capture (WASAPI loopback)
2. AI xử lý → TTS → Phát qua Virtual Cable
3. App CareCam nhận từ Virtual Cable (như mic) → Camera speaker phát

YÊU CẦU:
- VB-Audio Virtual Cable: https://vb-audio.com/Cable/
- Cài đặt VB-Cable, sau đó:
  1. Trong app CareCam: Settings → Đổi Microphone thành "CABLE Output"
  2. Chạy script này
"""

import sys
import os
import time
import threading
import tempfile
import wave
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import pyaudio
    import numpy as np
except ImportError:
    print("Cần cài đặt: pip install pyaudio numpy")
    sys.exit(1)

from modules.ai_service import get_ai_service
from modules.text_to_speech import get_tts
from modules.speech_to_text import get_stt
from modules.wake_word import get_wake_detector
from config import config


class VirtualAudioPipeline:
    """Pipeline xử lý audio tự động với Virtual Cable"""
    
    def __init__(self):
        self.audio = pyaudio.PyAudio()
        self.virtual_cable_input = None  # Index của "CABLE Input" (để phát TTS)
        self.virtual_cable_output = None  # Index của "CABLE Output" (app dùng làm mic)
        self.default_output = None  # Default speaker
        
        self._find_devices()
    
    def _find_devices(self):
        """Tìm các audio devices"""
        print("🔍 Đang tìm audio devices...")
        
        for i in range(self.audio.get_device_count()):
            dev = self.audio.get_device_info_by_index(i)
            name = dev['name'].lower()
            
            # Tìm VB-Cable
            if 'cable input' in name and dev['maxOutputChannels'] > 0:
                self.virtual_cable_input = i
                print(f"   ✅ Found CABLE Input (output device): [{i}] {dev['name']}")
            
            if 'cable output' in name and dev['maxInputChannels'] > 0:
                self.virtual_cable_output = i
                print(f"   ✅ Found CABLE Output (input device): [{i}] {dev['name']}")
        
        # Default output
        try:
            self.default_output = self.audio.get_default_output_device_info()['index']
        except:
            self.default_output = 0
        
        if self.virtual_cable_input is None:
            print("\n⚠️  VB-Cable không được tìm thấy!")
            print("   Tải tại: https://vb-audio.com/Cable/")
            print("   Cài đặt xong, chạy lại script này.")
    
    def play_to_virtual_cable(self, audio_file: str) -> bool:
        """Phát audio file qua Virtual Cable (để app CareCam nhận)"""
        if self.virtual_cable_input is None:
            print("❌ VB-Cable chưa được cài đặt")
            return False
        
        try:
            wf = wave.open(audio_file, 'rb')
            
            stream = self.audio.open(
                format=self.audio.get_format_from_width(wf.getsampwidth()),
                channels=wf.getnchannels(),
                rate=wf.getframerate(),
                output=True,
                output_device_index=self.virtual_cable_input
            )
            
            print(f"📤 Phát qua Virtual Cable → Camera speaker...")
            chunk = 1024
            data = wf.readframes(chunk)
            
            while data:
                stream.write(data)
                data = wf.readframes(chunk)
            
            stream.stop_stream()
            stream.close()
            wf.close()
            
            return True
            
        except Exception as e:
            print(f"❌ Lỗi phát Virtual Cable: {e}")
            return False
    
    def play_to_speakers(self, audio_file: str) -> bool:
        """Phát audio qua loa PC (để user nghe)"""
        try:
            wf = wave.open(audio_file, 'rb')
            
            stream = self.audio.open(
                format=self.audio.get_format_from_width(wf.getsampwidth()),
                channels=wf.getnchannels(),
                rate=wf.getframerate(),
                output=True,
                output_device_index=self.default_output
            )
            
            chunk = 1024
            data = wf.readframes(chunk)
            
            while data:
                stream.write(data)
                data = wf.readframes(chunk)
            
            stream.stop_stream()
            stream.close()
            wf.close()
            
            return True
            
        except Exception as e:
            print(f"❌ Lỗi phát speaker: {e}")
            return False
    
    def has_virtual_cable(self) -> bool:
        """Kiểm tra VB-Cable đã được cài chưa"""
        return self.virtual_cable_input is not None
    
    def close(self):
        self.audio.terminate()


class TyTyFullAutoBot:
    """Tỷ Tỷ chatbot với full automation qua CareCam"""
    
    def __init__(self):
        print("=" * 60)
        print("🤖 Tỷ Tỷ - CareCam Full Automation")
        print("=" * 60)
        print()
        
        self.pipeline = None
        self.ai = None
        self.tts = None
        self.stt = None
        self.detector = None
        self.running = False
    
    def initialize(self) -> bool:
        """Khởi tạo tất cả components"""
        try:
            print("🔄 Đang khởi tạo...\n")
            
            # Virtual Audio Pipeline
            self.pipeline = VirtualAudioPipeline()
            
            if not self.pipeline.has_virtual_cable():
                print("\n" + "=" * 60)
                print("⚠️  CẦN CÀI ĐẶT VB-CABLE!")
                print("=" * 60)
                print("\n1. Tải VB-Cable: https://vb-audio.com/Cable/")
                print("2. Cài đặt (chạy VBCABLE_Setup_x64.exe với admin)")
                print("3. Trong app CareCam:")
                print("   - Click phải vào icon loa (taskbar)")
                print("   - Chọn 'Open Sound settings'")
                print("   - App input: chọn 'CABLE Output'")
                print("4. Chạy lại script này")
                print()
                
                # Vẫn cho chạy với chế độ manual
                print("💡 Tiếp tục với chế độ MANUAL (không tự động phát qua camera)")
                input("   Nhấn Enter để tiếp tục...")
            
            # Speech-to-Text (từ default mic NẾU bật speaker trong app)
            self.stt = get_stt()
            
            # Wake word detector
            self.detector = get_wake_detector()
            
            # Text-to-Speech
            self.tts = get_tts()
            
            # AI service
            self.ai = get_ai_service()
            
            print("\n" + "=" * 60)
            print("✅ Sẵn sàng! Nói 'Tỷ Tỷ' vào camera để bắt đầu")
            print("=" * 60)
            
            # Test connection - phát "xin chào" qua camera
            if self.pipeline.has_virtual_cable():
                self._say_to_camera("Xin chào! Tỷ Tỷ đã kết nối với camera.")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Lỗi khởi tạo: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _say_to_camera(self, text: str):
        """Phát text qua camera speaker (qua Virtual Cable)"""
        try:
            # Generate TTS to file
            import asyncio
            import edge_tts
            
            temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            mp3_file = temp_file.name.replace(".wav", ".mp3")
            
            async def generate():
                communicate = edge_tts.Communicate(text, config.TTS_VOICE)
                await communicate.save(mp3_file)
            
            asyncio.run(generate())
            
            # Convert MP3 to WAV (for pyaudio)
            from pydub import AudioSegment
            audio = AudioSegment.from_mp3(mp3_file)
            audio.export(temp_file.name, format="wav")
            
            # Play to Virtual Cable
            self.pipeline.play_to_virtual_cable(temp_file.name)
            
            # Also play to local speaker so user can hear
            self.pipeline.play_to_speakers(temp_file.name)
            
            # Cleanup
            os.remove(mp3_file)
            os.remove(temp_file.name)
            
        except Exception as e:
            print(f"❌ Lỗi phát audio: {e}")
    
    def _say_local(self, text: str):
        """Phát text qua loa PC (không qua camera)"""
        self.tts.speak(text)
    
    def process_command(self, command: str) -> str:
        """Xử lý command và trả về response"""
        print(f"\n💭 Đang xử lý: '{command}'")
        response = self.ai.get_response(command)
        print(f"🤖 Tỷ Tỷ: {response}")
        return response
    
    def listen_loop(self):
        """Main loop lắng nghe và phản hồi"""
        print("\n🎧 Đang lắng nghe qua PC microphone...")
        print("💡 Trong app CareCam, bật loa (speaker) để PC có thể nghe camera")
        print("   Nói 'Tỷ Tỷ' + câu hỏi vào camera")
        print("   Nhấn Ctrl+C để dừng\n")
        
        self.running = True
        
        while self.running:
            try:
                # Listen from default mic (should pick up app audio if speaker is on)
                text = self.stt.listen_and_recognize()
                
                if not text:
                    continue
                
                # Check wake word
                detected, command = self.detector.check(text)
                
                if detected:
                    if command:
                        response = self.process_command(command)
                        
                        if self.pipeline.has_virtual_cable():
                            self._say_to_camera(response)
                        else:
                            self._say_local(response)
                            print("💡 Giữ nút mic trong app để phát qua camera!")
                    
                    elif self.detector.is_just_wake_word(text):
                        if self.pipeline.has_virtual_cable():
                            self._say_to_camera("Dạ, Tỷ Tỷ nghe đây!")
                        else:
                            self._say_local("Dạ, Tỷ Tỷ nghe đây!")
                        
                        print("👂 Đợi câu hỏi...")
                        command = self.stt.listen_and_recognize()
                        
                        if command:
                            response = self.process_command(command)
                            if self.pipeline.has_virtual_cable():
                                self._say_to_camera(response)
                            else:
                                self._say_local(response)
                        else:
                            msg = "Tỷ Tỷ không nghe rõ. Bạn nói lại nhé!"
                            if self.pipeline.has_virtual_cable():
                                self._say_to_camera(msg)
                            else:
                                self._say_local(msg)
                else:
                    print(f"👀 Nghe: '{text}' (không có wake word)")
                    
            except KeyboardInterrupt:
                print("\n\n🛑 Đang dừng...")
                self.running = False
                break
            except Exception as e:
                print(f"❌ Lỗi: {e}")
                continue
        
        if self.pipeline:
            self.pipeline.close()
    
    def run(self):
        """Start the bot"""
        if self.initialize():
            self.listen_loop()
        else:
            print("\n❌ Không thể khởi động")


def main():
    bot = TyTyFullAutoBot()
    bot.run()


if __name__ == "__main__":
    main()
