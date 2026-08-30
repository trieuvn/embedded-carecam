# Tỷ Tỷ Chatbot Configuration
# Điền thông tin cần thiết vào file này

import os
from dataclasses import dataclass
from typing import Optional
from enum import Enum

class AIProvider(Enum):
    """AI Service Provider Options"""
    GEMINI = "gemini"
    OLLAMA = "ollama"
    AUTO = "auto"  # Try Ollama first, fallback to Gemini

class OperationMode(Enum):
    """Audio routing operation modes"""
    BASIC_MODE = "basic"  # PC mic to PC speakers
    FULL_AUTOMATION_MODE = "full_automation"  # VB-Cable routing
    HYBRID_MODE = "hybrid"  # PC mic + VB-Cable

class ResponseMode(Enum):
    """AI response style modes"""
    CONCISE = "concise"
    DETAILED = "detailed"
    CONVERSATIONAL = "conversational"
    TECHNICAL = "technical"

@dataclass
class Config:
    """Configuration for Tỷ Tỷ Chatbot"""
    
    # ===== AI Service =====
    # AI Provider Selection: "gemini", "ollama", or "auto"
    # Mặc định dùng "gemini" (đơn giản nhất, không cần cài Ollama)
    # Đổi sang "auto" nếu đã cài Ollama (tự động fallback)
    # Đổi sang "ollama" nếu chỉ muốn dùng Ollama
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "ollama")
    
    # Google Gemini Configuration
    # Lấy API key tại: https://aistudio.google.com/app/apikey
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "AIzaSyCmIhYgpbX2it0ssrA8VuTe6P8TPpydfHw")
    AI_MODEL: str = "gemini-flash-latest"
    
    # Ollama Configuration (Optional local AI)
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "qwen2.5:0.5b")
    OLLAMA_TIMEOUT: float = 30.0  # seconds
    
    # ===== Wake Word Configuration =====
    WAKE_WORD: str = "tỷ tỷ"
    WAKE_WORD_ALIASES: tuple = ("tỷ", "ty ty", "ti ti")
    
    # Wake Word Engine Settings
    WAKE_WORD_ENGINE_ENABLED: bool = True  # Use Porcupine if available
    WAKE_WORD_SENSITIVITY: float = 0.5  # 0.0 to 1.0 (higher = more sensitive)
    WAKE_WORD_MODEL_PATH: str = os.getenv("WAKE_WORD_MODEL_PATH", "./models/wake_word")
    
    # ===== Voice Activity Detection (VAD) Configuration =====
    VAD_ENABLED: bool = True
    VAD_ENERGY_THRESHOLD: float = 0.02  # Audio energy threshold
    VAD_SILENCE_DURATION: float = 1.5  # Seconds of silence to trigger voice_end
    VAD_MIN_SPEECH_DURATION: float = 0.3  # Minimum speech duration to register
    VAD_FRAME_LENGTH_MS: int = 30  # Frame length in milliseconds
    
    # ===== Multi-Turn Conversation Configuration =====
    CONVERSATION_ENABLED: bool = True
    MAX_CONTEXT_TURNS: int = 10  # Keep last N turns in context
    SESSION_TIMEOUT_MINUTES: int = 30  # Auto-expire sessions after inactivity
    DEFAULT_RESPONSE_MODE: str = ResponseMode.CONVERSATIONAL.value
    
    # ===== Error Handling Configuration =====
    # Retry settings
    MAX_RETRIES: int = 3
    RETRY_DELAY_MS: int = 1000  # Initial retry delay
    ENABLE_FALLBACKS: bool = True
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_DIR: str = "./logs"
    ENABLE_STRUCTURED_LOGGING: bool = True
    
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
    # Operation Mode
    OPERATION_MODE: str = os.getenv("OPERATION_MODE", OperationMode.BASIC_MODE.value)
    
    # Audio Processing
    USE_CAMERA_AUDIO: bool = False  # Bắt đầu với PC mic
    SAMPLE_RATE: int = 16000
    CHANNELS: int = 1  # Mono audio
    CHUNK_SIZE: int = 1024
    BUFFER_SIZE: int = 2048
    VIRTUAL_CABLE_ENABLED: bool = False
    
    # TTS Voice (Microsoft Edge TTS)
    TTS_VOICE: str = "vi-VN-HoaiMyNeural"  # Giọng nữ Việt Nam
    
    # ===== Chatbot Personality =====
    SYSTEM_PROMPT: str = """Bạn là Tỷ Tỷ, một trợ lý AI thông minh và thân thiện.
Bạn nói tiếng Việt tự nhiên và dễ thương.
Trả lời ngắn gọn, súc tích nhưng đầy đủ thông tin.
Nếu được hỏi toán, hãy tính toán chính xác.
Nếu không biết câu trả lời, hãy thành thật nói không biết."""

    # ===== Legacy Audio Processing (for backward compatibility) =====
    SILENCE_THRESHOLD: float = 0.02
    SILENCE_DURATION: float = 1.5  # Seconds of silence to end recording
    MAX_RECORDING_DURATION: float = 10.0  # Max seconds per command


config = Config()
