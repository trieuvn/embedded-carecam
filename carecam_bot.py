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
from modules.carecam_controller import get_controller as get_carecam_controller
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
        self.carecam_ctrl = None  # CareCam UI controller
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
            
            # Initialize CareCam controller for auto-mic/speaker control
            try:
                self.carecam_ctrl = get_carecam_controller()
                if self.carecam_ctrl.find_window():
                    print("\n🎮 CareCam app detected - Chế độ TỰ ĐỘNG MIC/SPEAKER enabled!")
                    
                    # QUAN TRỌNG: Mặc định BẬT LOA để nghe người từ camera nói
                    print("🔊 Đang bật loa để nghe người từ camera...")
                    if self.carecam_ctrl.click_speaker_button():
                        print("✅ Loa đã bật (mic tự động tắt do hardware constraint)")
                        time.sleep(1.0)  # Đợi 1 giây để loa kích hoạt hoàn toàn
                    else:
                        print("⚠️ Không thể bật loa, vui lòng bật thủ công")
                else:
                    print("\n⚠️ Không tìm thấy app CareCam - bạn cần điều khiển mic/speaker thủ công")
                    self.carecam_ctrl = None
            except Exception as e:
                print(f"⚠️ Không thể khởi tạo CareCam controller: {e}")
                self.carecam_ctrl = None
            
            # Chào mừng qua loa PC (không phát qua camera lúc khởi động)
            print("\n👋 Tỷ Tỷ đã sẵn sàng!")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Lỗi khởi tạo: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _say_to_camera(self, text: str):
        """
        Phát text qua camera speaker (qua Virtual Cable + auto-mic)
        
        QUAN TRỌNG: 
        - Trước khi nói: BẬT MIC (loa tự động tắt do hardware constraint)
        - Sau khi nói xong: BẬT LOA (mic tự động tắt) để tiếp tục nghe người dùng
        """
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
            
            # Calculate audio duration
            audio_duration = len(audio) / 1000.0  # milliseconds to seconds
            
            # BƯỚC 1: BẬT MIC (loa tự động tắt) để Tỷ Tỷ nói
            if self.carecam_ctrl:
                print(f"🎤 Bật MIC để Tỷ Tỷ nói (loa tự động tắt)...")
                if not self.carecam_ctrl.click_mic_button():
                    print("⚠️ Không thể bật mic, vui lòng bật thủ công")
                time.sleep(1.0)  # Đợi 1 giây để mic kích hoạt hoàn toàn (tăng từ 0.3s)
            
            # BƯỚC 2: Phát audio qua Virtual Cable (vào camera)
            print(f"🔊 Đang nói qua camera ({audio_duration:.1f}s)...")
            self.pipeline.play_to_virtual_cable(temp_file.name)
            
            # Also play to local speaker so user can hear
            self.pipeline.play_to_speakers(temp_file.name)
            
            # BƯỚC 3: Đợi audio phát xong
            time.sleep(audio_duration + 0.5)  # Thêm 0.5s buffer (tăng từ 0.2s)
            
            # BƯỚC 4: BẬT LOA (mic tự động tắt) để tiếp tục nghe người dùng
            if self.carecam_ctrl:
                print("🔊 Bật LOA để tiếp tục nghe người dùng (mic tự động tắt)...")
                if not self.carecam_ctrl.click_speaker_button():
                    print("⚠️ Không thể bật loa, vui lòng bật thủ công")
                time.sleep(1.0)  # Đợi 1 giây để loa kích hoạt hoàn toàn (tăng từ 0.3s)
            
            # Cleanup
            os.remove(mp3_file)
            os.remove(temp_file.name)
            
        except Exception as e:
            print(f"❌ Lỗi phát audio: {e}")
            import traceback
            traceback.print_exc()
            
            # Fallback: đảm bảo loa được bật lại
            if self.carecam_ctrl:
                print("🔄 Khôi phục: bật lại loa...")
                self.carecam_ctrl.click_speaker_button()
    
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
        """
        Main loop lắng nghe và phản hồi
        
        LOGIC MIC/SPEAKER (Hardware Constraint - bật cái này thì cái kia tự động tắt):
        1. MẶC ĐỊNH: LOA BẬT (để nghe người từ camera nói) - MIC TẮT
        2. Phát hiện "Tỷ Tỷ" → BẬT MIC (để nói "Dạ") → SAU ĐÓ BẬT LOA (để nghe câu hỏi)
        3. Sau khi xử lý → BẬT MIC (để nói câu trả lời) → SAU ĐÓ BẬT LOA (để tiếp tục nghe)
        """
        print("\n🎧 Đang lắng nghe qua PC microphone...")
        print("💡 Trong app CareCam, LOA đã được bật tự động để PC có thể nghe camera")
        print("   Nói 'Tỷ Tỷ' + câu hỏi vào camera")
        print("   Nhấn Ctrl+C để dừng\n")
        
        self.running = True
        
        # Đảm bảo loa đang bật ở trạng thái mặc định
        if self.carecam_ctrl:
            print("🔊 Kiểm tra loa đang bật...")
            self.carecam_ctrl.click_speaker_button()
            time.sleep(1.0)  # Đợi 1 giây để loa kích hoạt hoàn toàn (tăng từ 0.5s)
        
        while self.running:
            try:
                # Listen from default mic (should pick up app audio if speaker is on)
                print("👂 Đang nghe (loa đang bật)...")
                text = self.stt.listen_and_recognize()
                
                if not text:
                    continue
                
                # Check wake word
                detected, command = self.detector.check(text)
                
                if detected:
                    if command:
                        # Wake word + command trong cùng câu
                        # VD: "Tỷ Tỷ 1+1 bằng mấy?"
                        response = self.process_command(command)
                        
                        # Nói câu trả lời (tự động: bật mic → nói → bật loa)
                        if self.pipeline.has_virtual_cable():
                            self._say_to_camera(response)
                        else:
                            self._say_local(response)
                            print("💡 Giữ nút mic trong app để phát qua camera!")
                    
                    elif self.detector.is_just_wake_word(text):
                        # Chỉ có wake word, đợi câu hỏi tiếp theo
                        # Nói "Dạ" để xác nhận (tự động: bật mic → nói "Dạ" → bật loa)
                        if self.pipeline.has_virtual_cable():
                            self._say_to_camera("Dạ")
                        else:
                            self._say_local("Dạ, Tỷ Tỷ nghe đây!")
                        
                        # Sau khi nói "Dạ", loa đã được bật lại → có thể nghe người dùng
                        print("👂 Loa đã bật, đợi câu hỏi từ camera...")
                        command = self.stt.listen_and_recognize()
                        
                        if command:
                            response = self.process_command(command)
                            # Nói câu trả lời (tự động: bật mic → nói → bật loa)
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
                    print(f"👀 Nghe: '{text}' (không có wake word, tiếp tục nghe...)")
                    
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
