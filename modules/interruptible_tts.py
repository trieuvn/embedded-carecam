"""
Interruptible TTS Controller
Cho phép phát TTS đến camera với khả năng bị ngắt bởi lệnh "Hủy".

APPROACH:
Vì không thể có full-duplex thực sự (SDK không cho phép), ta dùng polling:
1. Chia audio thành các chunks nhỏ (1-2 giây)
2. Sau mỗi chunk: tạm tắt mic, bật speaker, capture một chút, check "Hủy"
3. Nếu không có "Hủy", tiếp tục phát chunk tiếp theo
4. Nếu có "Hủy", dừng phát và return

Advantages:
- Không cần patch gì
- Response time ~ 1-2 giây (có thể chấp nhận được)
- Stable và reliable

Usage:
    controller = InterruptibleTTSController()
    was_interrupted = controller.play_tts_interruptible("response.wav")
"""
import time
import wave
import tempfile
import os
import pyaudio
import threading
from typing import Optional, Callable

# Import existing modules
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from modules.carecam_message import CareCamMessageController


class InterruptibleTTSController:
    """
    Controller để phát TTS với khả năng bị interrupt.
    
    Workflow:
    1. Bật mic, phát 1 chunk audio (1-2 giây)
    2. Tắt mic, bật speaker
    3. Capture audio trong 500ms
    4. Check xem có "Hủy" không (via callback)
    5. Nếu không, quay lại bước 1
    """
    
    def __init__(self, 
                 chunk_duration: float = 2.0,  # Độ dài mỗi chunk (giây)
                 check_duration: float = 0.5,  # Thời gian check "Hủy" (giây)
                 cancel_detector: Optional[Callable[[bytes], bool]] = None):
        """
        Args:
            chunk_duration: Thời gian phát audio trước khi check interrupt
            check_duration: Thời gian lắng nghe để detect "Hủy"
            cancel_detector: Callback function nhận audio bytes, return True nếu phát hiện "Hủy"
        """
        self.chunk_duration = chunk_duration
        self.check_duration = check_duration
        self.cancel_detector = cancel_detector
        
        self.ui_controller = CareCamMessageController()
        
        self._is_playing = False
        self._should_stop = False
    
    def enable_mic(self):
        """Bật mic (sẽ tắt speaker)"""
        return self.ui_controller.hold_mic(duration=0.1)  # Quick press to enable
    
    def enable_speaker(self):
        """Bật speaker"""
        return self.ui_controller.toggle_speaker()
    
    def _check_for_cancel(self) -> bool:
        """
        Capture audio và check xem có "Hủy" không.
        
        Returns:
            True nếu phát hiện "Hủy"
        """
        if not self.cancel_detector:
            return False
        
        # Capture audio via WASAPI loopback
        # (Simplified - in real implementation, use proper loopback capture)
        try:
            p = pyaudio.PyAudio()
            
            # Find WASAPI loopback device
            loopback_idx = None
            for i in range(p.get_device_count()):
                info = p.get_device_info_by_index(i)
                if 'loopback' in info['name'].lower() or 'stereo mix' in info['name'].lower():
                    loopback_idx = i
                    break
            
            if loopback_idx is None:
                p.terminate()
                return False
            
            # Capture
            stream = p.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                input_device_index=loopback_idx,
                frames_per_buffer=1024
            )
            
            frames = []
            for _ in range(int(16000 / 1024 * self.check_duration)):
                data = stream.read(1024, exception_on_overflow=False)
                frames.append(data)
            
            stream.stop_stream()
            stream.close()
            p.terminate()
            
            audio_data = b''.join(frames)
            return self.cancel_detector(audio_data)
            
        except Exception as e:
            print(f"Warning: Audio capture failed: {e}")
            return False
    
    def play_tts_interruptible(self, wav_path: str) -> bool:
        """
        Phát TTS file với khả năng bị interrupt bởi "Hủy".
        
        Args:
            wav_path: Path đến file WAV
            
        Returns:
            True nếu phát xong không bị interrupt, False nếu bị interrupt
        """
        if not os.path.exists(wav_path):
            print(f"❌ File not found: {wav_path}")
            return True  # No file = no interrupt
        
        print(f"🔊 Playing TTS: {os.path.basename(wav_path)}")
        
        # Read WAV file
        with wave.open(wav_path, 'rb') as wf:
            sample_rate = wf.getframerate()
            channels = wf.getnchannels()
            sample_width = wf.getsampwidth()
            total_frames = wf.getnframes()
            audio_data = wf.readframes(total_frames)
        
        # Calculate chunk size
        bytes_per_sec = sample_rate * channels * sample_width
        chunk_bytes = int(bytes_per_sec * self.chunk_duration)
        
        # Split into chunks
        chunks = []
        for i in range(0, len(audio_data), chunk_bytes):
            chunks.append(audio_data[i:i+chunk_bytes])
        
        print(f"   Split into {len(chunks)} chunks ({self.chunk_duration}s each)")
        
        self._is_playing = True
        self._should_stop = False
        
        try:
            for i, chunk in enumerate(chunks):
                if self._should_stop:
                    print("   ⛔ Stopped by external signal")
                    return False
                
                print(f"   Playing chunk {i+1}/{len(chunks)}...")
                
                # 1. Enable mic and play chunk via VB-Cable
                self.enable_mic()
                self._play_audio_chunk(chunk, sample_rate, channels, sample_width)
                
                # 2. Check for cancel (only if not last chunk)
                if i < len(chunks) - 1:
                    self.enable_speaker()
                    time.sleep(0.1)  # Let speaker stabilize
                    
                    if self._check_for_cancel():
                        print("   ⛔ Detected 'Hủy' - stopping playback")
                        return False
            
            print("   ✅ Playback complete")
            return True
            
        finally:
            self._is_playing = False
            self.enable_speaker()  # Ensure speaker is back on
    
    def _play_audio_chunk(self, audio_data: bytes, sample_rate: int, 
                          channels: int, sample_width: int):
        """Play audio chunk to VB-Cable"""
        try:
            p = pyaudio.PyAudio()
            
            # Find VB-Cable output device
            vbcable_idx = None
            for i in range(p.get_device_count()):
                info = p.get_device_info_by_index(i)
                if 'cable input' in info['name'].lower():
                    vbcable_idx = i
                    break
            
            if vbcable_idx is None:
                print("   ⚠️ VB-Cable not found, using default output")
                vbcable_idx = p.get_default_output_device_info()['index']
            
            # Play
            format_map = {1: pyaudio.paInt8, 2: pyaudio.paInt16, 4: pyaudio.paInt32}
            stream = p.open(
                format=format_map.get(sample_width, pyaudio.paInt16),
                channels=channels,
                rate=sample_rate,
                output=True,
                output_device_index=vbcable_idx
            )
            
            stream.write(audio_data)
            
            stream.stop_stream()
            stream.close()
            p.terminate()
            
        except Exception as e:
            print(f"   ⚠️ Playback error: {e}")
    
    def stop(self):
        """Stop current playback"""
        self._should_stop = True
    
    @property
    def is_playing(self) -> bool:
        return self._is_playing


def simple_cancel_detector(audio_data: bytes) -> bool:
    """
    Simple detector - always returns False.
    Replace with actual speech recognition for "Hủy" detection.
    """
    # TODO: Integrate with STT service to detect "Hủy"
    return False


def test():
    print("=" * 60)
    print("Interruptible TTS Controller Test")
    print("=" * 60)
    
    controller = InterruptibleTTSController(
        chunk_duration=1.5,
        check_duration=0.3,
        cancel_detector=simple_cancel_detector
    )
    
    test_wav = r"C:\Windows\Media\Windows Notify.wav"
    
    print(f"\nTest file: {test_wav}")
    print("\nNhấn Enter để bắt đầu...")
    input()
    
    result = controller.play_tts_interruptible(test_wav)
    
    if result:
        print("\n✅ Playback completed without interruption")
    else:
        print("\n⛔ Playback was interrupted")


if __name__ == "__main__":
    test()
