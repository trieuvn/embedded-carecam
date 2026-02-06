"""
AI Service Module - Xử lý hội thoại với Google Gemini
Sử dụng package google-genai mới (thay thế google-generativeai)
"""

from google import genai
from config import config


class AIService:
    """Service để xử lý câu hỏi và tạo câu trả lời từ AI"""
    
    def __init__(self):
        self.client = None
        self.model = config.AI_MODEL
        self.system_prompt = config.SYSTEM_PROMPT
        self._initialize()
    
    def _initialize(self):
        """Khởi tạo Google Gemini"""
        if not config.GOOGLE_API_KEY:
            raise ValueError(
                "❌ Chưa có GOOGLE_API_KEY!\n"
                "Lấy API key miễn phí tại: https://aistudio.google.com/app/apikey\n"
                "Sau đó set environment variable: GOOGLE_API_KEY=your_key_here"
            )
        
        self.client = genai.Client(api_key=config.GOOGLE_API_KEY)
        print(f"✅ AI Service initialized with {self.model}")
    
    def get_response(self, user_message: str) -> str:
        """
        Gửi tin nhắn và nhận phản hồi từ AI
        
        Args:
            user_message: Câu hỏi/yêu cầu từ người dùng
            
        Returns:
            Câu trả lời từ AI
        """
        try:
            # Thêm context từ system prompt
            full_prompt = f"{self.system_prompt}\n\nNgười dùng hỏi: {user_message}"
            
            response = self.client.models.generate_content(
                model=self.model,
                contents=full_prompt
            )
            return response.text.strip()
        except Exception as e:
            print(f"❌ AI Error: {e}")
            return "Xin lỗi, Tỷ Tỷ gặp lỗi khi xử lý. Bạn thử hỏi lại nhé!"


# Singleton instance
_ai_service = None

def get_ai_service() -> AIService:
    """Get or create AI service instance"""
    global _ai_service
    if _ai_service is None:
        _ai_service = AIService()
    return _ai_service


if __name__ == "__main__":
    # Test AI service
    import os
    
    # Demo với API key (nếu có)
    if os.getenv("GOOGLE_API_KEY"):
        ai = get_ai_service()
        
        # Test toán
        print("\n🧮 Test: 1+1 bằng mấy?")
        response = ai.get_response("1+1 bằng mấy?")
        print(f"Tỷ Tỷ: {response}")
        
        # Test tiếng Việt
        print("\n🇻🇳 Test: Thủ đô Việt Nam là gì?")
        response = ai.get_response("Thủ đô Việt Nam là gì?")
        print(f"Tỷ Tỷ: {response}")
    else:
        print("⚠️ Set GOOGLE_API_KEY để test AI service")
