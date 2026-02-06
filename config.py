# Tỷ Tỷ Chatbot Configuration
# Điền thông tin cần thiết vào file này

import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class Config:
    """Configuration for Tỷ Tỷ Chatbot"""
    
    # ===== AI Service =====
    # Sử dụng Google Gemini (miễn phí)
    # Lấy API key tại: https://aistudio.google.com/app/apikey
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "AIzaSyCmIhYgpbX2it0ssrA8VuTe6P8TPpydfHw")
    AI_MODEL: str = "gemini-flash-latest"
    
    # ===== Wake Word =====
    WAKE_WORD: str = "tỷ tỷ"
    WAKE_WORD_ALIASES: tuple = ("tỷ", "ty ty", "ti ti")
    
    # ===== Camera Settings =====
    # Điền IP camera của bạn (ví dụ: 192.168.1.100)
    CAMERA_IP: str = os.getenv("CAMERA_IP", "192.168.1.8")
    CAMERA_PORT: int = 8554  # CareCam RTSP port
    CAMERA_USERNAME: str = os.getenv("CAMERA_USERNAME", "admin")
    CAMERA_PASSWORD: str = os.getenv("CAMERA_PASSWORD", "")
    
    # RTSP URL (sẽ được tự động tạo)
    @property
    def rtsp_url(self) -> str:
        if self.CAMERA_IP:
            auth = f"{self.CAMERA_USERNAME}:{self.CAMERA_PASSWORD}@" if self.CAMERA_PASSWORD else ""
            return f"rtsp://{auth}{self.CAMERA_IP}:{self.CAMERA_PORT}/stream1"
        return ""
    
    # ===== Audio Settings =====
    # True = capture từ camera RTSP, False = capture từ PC microphone
    USE_CAMERA_AUDIO: bool = False  # Bắt đầu với PC mic
    
    # TTS Voice (Microsoft Edge TTS)
    TTS_VOICE: str = "vi-VN-HoaiMyNeural"  # Giọng nữ Việt Nam
    
    # ===== Chatbot Personality =====
    SYSTEM_PROMPT: str = """Bạn là Tỷ Tỷ, một trợ lý AI thông minh và thân thiện.
Bạn nói tiếng Việt tự nhiên và dễ thương.
Trả lời ngắn gọn, súc tích nhưng đầy đủ thông tin.
Nếu được hỏi toán, hãy tính toán chính xác.
Nếu không biết câu trả lời, hãy thành thật nói không biết."""

    # ===== Audio Processing =====
    SAMPLE_RATE: int = 16000
    CHUNK_SIZE: int = 1024
    SILENCE_THRESHOLD: float = 0.02
    SILENCE_DURATION: float = 1.5  # Seconds of silence to end recording
    MAX_RECORDING_DURATION: float = 10.0  # Max seconds per command


config = Config()
