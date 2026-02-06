"""
Audio Capture Module - Capture audio từ camera RTSP hoặc PC microphone
"""

import subprocess
import numpy as np
import tempfile
import os
from typing import Optional, Generator
from config import config


class AudioCapture:
    """Capture audio from RTSP stream or local microphone"""
    
    def __init__(self, use_camera: bool = None):
        self.use_camera = use_camera if use_camera is not None else config.USE_CAMERA_AUDIO
        print(f"✅ Audio capture initialized (source: {'Camera RTSP' if self.use_camera else 'PC Microphone'})")
    
    def capture_from_rtsp(self, duration: float = 5.0) -> Optional[str]:
        """
        Capture audio từ RTSP stream
        
        Args:
            duration: Thời gian capture (seconds)
        
        Returns:
            Path to audio file hoặc None nếu lỗi
        """
        if not config.CAMERA_IP:
            print("❌ Camera IP not configured")
            return None
        
        rtsp_url = config.rtsp_url
        print(f"📡 Connecting to RTSP: {rtsp_url}")
        
        try:
            # Create temp file for audio
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                output_path = f.name
            
            # Use FFmpeg to capture audio from RTSP
            cmd = [
                "ffmpeg",
                "-y",  # Overwrite output
                "-rtsp_transport", "tcp",  # Use TCP for more reliable streaming
                "-i", rtsp_url,
                "-t", str(duration),  # Duration
                "-vn",  # No video
                "-acodec", "pcm_s16le",  # PCM audio
                "-ar", str(config.SAMPLE_RATE),  # Sample rate
                "-ac", "1",  # Mono
                output_path
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=duration + 10
            )
            
            if result.returncode == 0 and os.path.exists(output_path):
                print(f"✅ Captured {duration}s audio from RTSP")
                return output_path
            else:
                print(f"❌ FFmpeg error: {result.stderr.decode()[:200]}")
                return None
                
        except subprocess.TimeoutExpired:
            print("❌ RTSP capture timeout")
            return None
        except FileNotFoundError:
            print("❌ FFmpeg not found. Install FFmpeg and add to PATH")
            return None
        except Exception as e:
            print(f"❌ RTSP Capture Error: {e}")
            return None
    
    def check_ffmpeg(self) -> bool:
        """Check if FFmpeg is installed"""
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False
    
    def check_rtsp_connection(self) -> bool:
        """Test RTSP connection"""
        if not config.CAMERA_IP:
            print("❌ Camera IP not configured")
            return False
        
        try:
            rtsp_url = config.rtsp_url
            print(f"🔍 Testing RTSP connection: {rtsp_url}")
            
            cmd = [
                "ffprobe",
                "-v", "error",
                "-rtsp_transport", "tcp",
                "-i", rtsp_url,
                "-show_entries", "stream=codec_type",
                "-of", "default=noprint_wrappers=1"
            ]
            
            result = subprocess.run(cmd, capture_output=True, timeout=10)
            
            if result.returncode == 0:
                output = result.stdout.decode()
                has_video = "video" in output
                has_audio = "audio" in output
                print(f"✅ RTSP connected - Video: {has_video}, Audio: {has_audio}")
                return has_audio
            else:
                print(f"❌ RTSP connection failed: {result.stderr.decode()[:200]}")
                return False
                
        except subprocess.TimeoutExpired:
            print("❌ RTSP connection timeout")
            return False
        except Exception as e:
            print(f"❌ RTSP Error: {e}")
            return False


# Singleton instance
_capture = None

def get_audio_capture() -> AudioCapture:
    """Get or create audio capture instance"""
    global _capture
    if _capture is None:
        _capture = AudioCapture()
    return _capture


if __name__ == "__main__":
    # Test audio capture
    print("🎤 Testing Audio Capture...\n")
    
    capture = get_audio_capture()
    
    # Check FFmpeg
    print(f"FFmpeg installed: {capture.check_ffmpeg()}")
    
    # Check RTSP (if camera IP is configured)
    if config.CAMERA_IP:
        print(f"\nTesting RTSP connection to {config.CAMERA_IP}...")
        capture.check_rtsp_connection()
    else:
        print("\n⚠️ Camera IP not configured. Set CAMERA_IP environment variable.")
        print("   Using PC microphone as fallback.")
