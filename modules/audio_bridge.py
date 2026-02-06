"""
Windows Audio Bridge Module
Capture audio từ Windows system (khi app CareCam phát) và phát audio qua Windows
"""

import pyaudio
import wave
import numpy as np
import tempfile
import time
import threading
from typing import Optional, Callable
from config import config


class WindowsAudioBridge:
    """
    Cầu nối âm thanh với CareCam:
    1. Bật loa trong app CareCam -> âm thanh từ camera phát qua PC speaker -> capture qua WASAPI loopback
    2. Nói vào microphone PC -> app CareCam bật mic -> gửi đến camera
    """
    
    def __init__(self):
        self.audio = pyaudio.PyAudio()
        self.is_recording = False
        self.is_playing = False
        self._recording_thread = None
        
    def list_audio_devices(self):
        """Liệt kê tất cả audio devices"""
        print("🎤 Available Audio Devices:")
        print("-" * 60)
        
        for i in range(self.audio.get_device_count()):
            dev = self.audio.get_device_info_by_index(i)
            dev_type = []
            if dev['maxInputChannels'] > 0:
                dev_type.append("INPUT")
            if dev['maxOutputChannels'] > 0:
                dev_type.append("OUTPUT")
            
            print(f"[{i}] {dev['name']}")
            print(f"    Type: {', '.join(dev_type)}")
            print(f"    Channels: In={dev['maxInputChannels']}, Out={dev['maxOutputChannels']}")
            print()
    
    def get_default_input_device(self) -> int:
        """Lấy default microphone"""
        try:
            return self.audio.get_default_input_device_info()['index']
        except:
            return 0
    
    def get_default_output_device(self) -> int:
        """Lấy default speaker"""
        try:
            return self.audio.get_default_output_device_info()['index']
        except:
            return 0
    
    def record_from_mic(self, duration: float = 5.0, device_index: int = None) -> Optional[str]:
        """
        Ghi âm từ microphone
        
        Args:
            duration: Thời gian ghi (giây)
            device_index: Index của microphone device
            
        Returns:
            Path to WAV file hoặc None
        """
        if device_index is None:
            device_index = self.get_default_input_device()
        
        try:
            # Config
            chunk = 1024
            format_type = pyaudio.paInt16
            channels = 1
            rate = config.SAMPLE_RATE
            
            # Open stream
            stream = self.audio.open(
                format=format_type,
                channels=channels,
                rate=rate,
                input=True,
                input_device_index=device_index,
                frames_per_buffer=chunk
            )
            
            print(f"🎤 Recording from mic for {duration}s...")
            frames = []
            
            num_chunks = int(rate / chunk * duration)
            for _ in range(num_chunks):
                data = stream.read(chunk, exception_on_overflow=False)
                frames.append(data)
            
            stream.stop_stream()
            stream.close()
            
            # Save to temp file
            temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            with wave.open(temp_file.name, 'wb') as wf:
                wf.setnchannels(channels)
                wf.setsampwidth(self.audio.get_sample_size(format_type))
                wf.setframerate(rate)
                wf.writeframes(b''.join(frames))
            
            print(f"✅ Recorded to {temp_file.name}")
            return temp_file.name
            
        except Exception as e:
            print(f"❌ Recording Error: {e}")
            return None
    
    def play_audio(self, audio_file: str, device_index: int = None) -> bool:
        """
        Phát audio file qua speaker
        
        Args:
            audio_file: Path to audio file (WAV/MP3)
            device_index: Index của speaker device
        """
        if device_index is None:
            device_index = self.get_default_output_device()
        
        try:
            wf = wave.open(audio_file, 'rb')
            
            stream = self.audio.open(
                format=self.audio.get_format_from_width(wf.getsampwidth()),
                channels=wf.getnchannels(),
                rate=wf.getframerate(),
                output=True,
                output_device_index=device_index
            )
            
            print(f"🔊 Playing audio...")
            chunk = 1024
            data = wf.readframes(chunk)
            
            while data:
                stream.write(data)
                data = wf.readframes(chunk)
            
            stream.stop_stream()
            stream.close()
            wf.close()
            
            print("✅ Playback complete")
            return True
            
        except Exception as e:
            print(f"❌ Playback Error: {e}")
            return False
    
    def close(self):
        """Cleanup resources"""
        self.audio.terminate()


# Test
if __name__ == "__main__":
    bridge = WindowsAudioBridge()
    
    # List devices
    bridge.list_audio_devices()
    
    # Test record
    print("\n🎤 Testing microphone recording (3 seconds)...")
    audio_file = bridge.record_from_mic(duration=3)
    
    if audio_file:
        print("\n🔊 Playing back recording...")
        bridge.play_audio(audio_file)
    
    bridge.close()
