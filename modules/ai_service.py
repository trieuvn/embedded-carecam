"""
AI Service Module - Unified interface for AI providers (Gemini, Ollama)
Supports service selection with auto mode and fallback logic
"""

import google.generativeai as genai
from typing import Optional
from config import config, AIProvider
import ollama


class AIService:
    """
    Unified AI Service với support cho multiple providers
    Supports: Google Gemini, Ollama Local, Auto mode (Ollama first, then Gemini)
    """
    
    def __init__(self, provider: Optional[str] = None):
        """
        Initialize AI Service with specified provider
        
        Args:
            provider: AI provider ("gemini", "ollama", "auto"). 
                     If None, uses config.AI_PROVIDER
        """
        self.provider = provider or config.AI_PROVIDER
        self.system_prompt = config.SYSTEM_PROMPT
        
        # Provider-specific clients
        self.gemini_client = None
        self.ollama_client = None
        self.gemini_model = config.AI_MODEL
        self.ollama_model = config.OLLAMA_MODEL
        
        # Track current active provider for auto mode
        self.active_provider = None
        
        self._initialize()
    
    def _initialize(self):
        """Initialize AI provider(s) based on configuration"""
        provider_lower = self.provider.lower()
        
        if provider_lower == AIProvider.GEMINI.value:
            self._initialize_gemini()
            self.active_provider = AIProvider.GEMINI.value
            print(f"✅ AI Service initialized with Gemini ({self.gemini_model})")
            
        elif provider_lower == AIProvider.OLLAMA.value:
            self._initialize_ollama()
            self.active_provider = AIProvider.OLLAMA.value
            print(f"✅ AI Service initialized with Ollama ({self.ollama_model})")
            
        elif provider_lower == AIProvider.AUTO.value:
            # Auto mode: try Ollama first, fallback to Gemini
            print("🔄 AI Service in AUTO mode: trying Ollama first...")
            try:
                self._initialize_ollama()
                if self._test_ollama():
                    self.active_provider = AIProvider.OLLAMA.value
                    print(f"✅ AI Service using Ollama ({self.ollama_model})")
                else:
                    raise ConnectionError("Ollama not available")
            except Exception as e:
                print(f"⚠️ Ollama unavailable ({e}), falling back to Gemini...")
                self._initialize_gemini()
                self.active_provider = AIProvider.GEMINI.value
                print(f"✅ AI Service using Gemini ({self.gemini_model})")
        else:
            raise ValueError(
                f"Invalid AI_PROVIDER: {self.provider}\n"
                f"Valid options: gemini, ollama, auto"
            )
    
    def _initialize_gemini(self):
        """Initialize Google Gemini client"""
        if not config.GOOGLE_API_KEY:
            raise ValueError(
                "❌ Chưa có GOOGLE_API_KEY!\n"
                "Lấy API key miễn phí tại: https://aistudio.google.com/app/apikey\n"
                "Sau đó set environment variable: GOOGLE_API_KEY=your_key_here"
            )
        
        # Configure API key
        genai.configure(api_key=config.GOOGLE_API_KEY)
        # Initialize model
        self.gemini_client = genai.GenerativeModel(self.gemini_model)
    
    def _initialize_ollama(self):
        """Initialize Ollama client"""
        self.ollama_client = ollama.Client(host=config.OLLAMA_BASE_URL)
    
    def _test_ollama(self) -> bool:
        """
        Test Ollama connection and model availability
        
        Returns:
            True if Ollama is available and model exists
        """
        try:
            if not self.ollama_client:
                return False
            
            # Check if model is available
            models_response = self.ollama_client.list()
            available_models = [model['name'] for model in models_response.get('models', [])]
            return self.ollama_model in available_models
        except Exception:
            return False
    
    def get_response(self, user_message: str) -> str:
        """
        Get AI response with automatic fallback in auto mode
        
        Args:
            user_message: User's question/request
            
        Returns:
            AI response text
        """
        # Try current active provider
        if self.active_provider == AIProvider.OLLAMA.value:
            response = self._get_ollama_response(user_message)
            
            # In auto mode, fallback to Gemini if Ollama fails
            if response.startswith("Xin lỗi") and self.provider.lower() == AIProvider.AUTO.value:
                print("⚠️ Ollama failed, falling back to Gemini...")
                response = self._get_gemini_response(user_message)
                if not response.startswith("Xin lỗi"):
                    # Successful fallback, switch active provider
                    self.active_provider = AIProvider.GEMINI.value
            
            return response
            
        elif self.active_provider == AIProvider.GEMINI.value:
            return self._get_gemini_response(user_message)
        
        else:
            return "Xin lỗi, Tỷ Tỷ không xác định được AI service. Kiểm tra cấu hình nhé!"
    
    def _get_gemini_response(self, user_message: str) -> str:
        """
        Get response from Google Gemini
        
        Args:
            user_message: User's question
            
        Returns:
            Gemini response text
        """
        try:
            if not self.gemini_client:
                self._initialize_gemini()
            
            full_prompt = f"{self.system_prompt}\n\nNgười dùng hỏi: {user_message}"
            
            # Use generate_content method (correct API for google.generativeai)
            response = self.gemini_client.generate_content(full_prompt)
            return response.text.strip()
            
        except Exception as e:
            print(f"❌ Gemini Error: {e}")
            return "Xin lỗi, Tỷ Tỷ gặp lỗi khi xử lý với Gemini. Bạn thử hỏi lại nhé!"
    
    def _get_ollama_response(self, user_message: str) -> str:
        """
        Get response from Ollama
        
        Args:
            user_message: User's question
            
        Returns:
            Ollama response text
        """
        try:
            if not self.ollama_client:
                self._initialize_ollama()
            
            full_prompt = f"{self.system_prompt}\n\nNgười dùng hỏi: {user_message}"
            
            response = self.ollama_client.generate(
                model=self.ollama_model,
                prompt=full_prompt,
                options={
                    'temperature': 0.7,
                    'top_p': 0.9,
                    'top_k': 40,
                }
            )
            
            response_text = response.get('response', '').strip()
            
            if not response_text:
                return "Xin lỗi, Tỷ Tỷ không tạo được câu trả lời. Bạn thử hỏi lại nhé!"
            
            return response_text
            
        except ollama.ResponseError as e:
            print(f"❌ Ollama Response Error: {e}")
            return "Xin lỗi, Tỷ Tỷ gặp lỗi khi xử lý với Ollama. Bạn thử hỏi lại nhé!"
        except ollama.RequestError as e:
            print(f"❌ Ollama Request Error: {e}")
            return "Xin lỗi, Tỷ Tỷ không kết nối được đến Ollama. Kiểm tra Ollama service nhé!"
        except Exception as e:
            print(f"❌ Ollama Error: {e}")
            return "Xin lỗi, Tỷ Tỷ gặp lỗi không mong đợi với Ollama. Bạn thử hỏi lại nhé!"
    
    def get_active_provider(self) -> str:
        """
        Get currently active AI provider
        
        Returns:
            Active provider name ("gemini" or "ollama")
        """
        return self.active_provider or "unknown"
    
    def switch_provider(self, provider: str) -> bool:
        """
        Switch to different AI provider
        
        Args:
            provider: Target provider ("gemini" or "ollama")
            
        Returns:
            True if switch successful, False otherwise
        """
        try:
            provider_lower = provider.lower()
            
            if provider_lower == AIProvider.GEMINI.value:
                if not self.gemini_client:
                    self._initialize_gemini()
                self.active_provider = AIProvider.GEMINI.value
                print(f"✅ Switched to Gemini ({self.gemini_model})")
                return True
                
            elif provider_lower == AIProvider.OLLAMA.value:
                if not self.ollama_client:
                    self._initialize_ollama()
                if not self._test_ollama():
                    print("❌ Ollama not available, switch failed")
                    return False
                self.active_provider = AIProvider.OLLAMA.value
                print(f"✅ Switched to Ollama ({self.ollama_model})")
                return True
                
            else:
                print(f"❌ Invalid provider: {provider}")
                return False
                
        except Exception as e:
            print(f"❌ Switch failed: {e}")
            return False


# Singleton instance
_ai_service = None

def get_ai_service(provider: Optional[str] = None) -> AIService:
    """
    Get or create AI service instance
    
    Args:
        provider: Optional provider override ("gemini", "ollama", "auto")
        
    Returns:
        AIService instance
    """
    global _ai_service
    if _ai_service is None:
        _ai_service = AIService(provider=provider)
    return _ai_service


if __name__ == "__main__":
    """Test AI service with multiple providers"""
    import os
    
    print("=" * 70)
    print("🧪 Testing AI Service - Multi-Provider Support")
    print("=" * 70)
    
    # Test 1: Auto mode (default)
    print("\n" + "=" * 70)
    print("Test 1: AUTO Mode (Ollama → Gemini fallback)")
    print("=" * 70)
    try:
        ai_auto = AIService(provider="auto")
        print(f"Active provider: {ai_auto.get_active_provider()}")
        
        print("\n🧮 Question: 1+1 bằng mấy?")
        response = ai_auto.get_response("1+1 bằng mấy?")
        print(f"Tỷ Tỷ: {response}")
        print(f"Provider used: {ai_auto.get_active_provider()}")
    except Exception as e:
        print(f"❌ Auto mode test failed: {e}")
    
    # Test 2: Ollama mode
    print("\n" + "=" * 70)
    print("Test 2: OLLAMA Mode")
    print("=" * 70)
    try:
        ai_ollama = AIService(provider="ollama")
        print(f"Active provider: {ai_ollama.get_active_provider()}")
        
        print("\n🇻🇳 Question: Thủ đô Việt Nam là gì?")
        response = ai_ollama.get_response("Thủ đô Việt Nam là gì?")
        print(f"Tỷ Tỷ: {response}")
    except Exception as e:
        print(f"⚠️ Ollama mode test failed: {e}")
        print("Make sure Ollama is running: ollama serve")
        print(f"And model is installed: ollama pull {config.OLLAMA_MODEL}")
    
    # Test 3: Gemini mode
    print("\n" + "=" * 70)
    print("Test 3: GEMINI Mode")
    print("=" * 70)
    if os.getenv("GOOGLE_API_KEY") or config.GOOGLE_API_KEY:
        try:
            ai_gemini = AIService(provider="gemini")
            print(f"Active provider: {ai_gemini.get_active_provider()}")
            
            print("\n🌍 Question: Trái đất quay quanh mặt trời mất bao lâu?")
            response = ai_gemini.get_response("Trái đất quay quanh mặt trời mất bao lâu?")
            print(f"Tỷ Tỷ: {response}")
        except Exception as e:
            print(f"❌ Gemini mode test failed: {e}")
    else:
        print("⚠️ Set GOOGLE_API_KEY to test Gemini mode")
    
    # Test 4: Provider switching
    print("\n" + "=" * 70)
    print("Test 4: Dynamic Provider Switching")
    print("=" * 70)
    try:
        ai = get_ai_service(provider="auto")
        print(f"Initial provider: {ai.get_active_provider()}")
        
        # Try switching
        if ai.get_active_provider() == "ollama":
            print("\nAttempting switch to Gemini...")
            if ai.switch_provider("gemini"):
                print(f"Current provider: {ai.get_active_provider()}")
                response = ai.get_response("Xin chào")
                print(f"Tỷ Tỷ: {response}")
        elif ai.get_active_provider() == "gemini":
            print("\nAttempting switch to Ollama...")
            if ai.switch_provider("ollama"):
                print(f"Current provider: {ai.get_active_provider()}")
                response = ai.get_response("Xin chào")
                print(f"Tỷ Tỷ: {response}")
    except Exception as e:
        print(f"⚠️ Provider switching test failed: {e}")
    
    print("\n" + "=" * 70)
    print("✅ All tests completed!")
    print("=" * 70)
