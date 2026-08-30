"""
Ollama Service Module - Local AI xử lý hội thoại offline
Sử dụng Ollama với model qwen2.5:0.5b cho CPU performance
"""

import ollama
from typing import Optional
from config import config


class OllamaService:
    """Service để xử lý câu hỏi và tạo câu trả lời từ Ollama Local AI"""
    
    def __init__(self):
        self.base_url = config.OLLAMA_BASE_URL
        self.model = config.OLLAMA_MODEL
        self.timeout = config.OLLAMA_TIMEOUT
        self.system_prompt = config.SYSTEM_PROMPT
        self.client = None
        self._initialize()
    
    def _initialize(self):
        """Khởi tạo Ollama client"""
        try:
            # Initialize Ollama client with custom base URL
            self.client = ollama.Client(host=self.base_url)
            
            # Test connection by checking if model exists
            if not self.test_connection():
                raise ConnectionError(f"Model {self.model} not available")
            
            print(f"✅ Ollama Service initialized with {self.model} at {self.base_url}")
        except Exception as e:
            print(f"❌ Ollama initialization failed: {e}")
            raise
    
    def test_connection(self) -> bool:
        """
        Kiểm tra kết nối đến Ollama server và model availability
        
        Returns:
            True nếu kết nối thành công và model có sẵn, False nếu không
        """
        try:
            # List available models
            models_response = self.client.list()
            available_models = [model['name'] for model in models_response.get('models', [])]
            
            # Check if our model is available
            if self.model in available_models:
                print(f"✅ Model {self.model} is available")
                return True
            else:
                print(f"⚠️ Model {self.model} not found. Available models: {available_models}")
                print(f"💡 Run: ollama pull {self.model}")
                return False
        except Exception as e:
            print(f"❌ Connection test failed: {e}")
            print(f"💡 Make sure Ollama is running: ollama serve")
            return False
    
    def get_response(self, user_message: str) -> str:
        """
        Gửi tin nhắn và nhận phản hồi từ Ollama AI
        
        Args:
            user_message: Câu hỏi/yêu cầu từ người dùng
            
        Returns:
            Câu trả lời từ AI
        """
        try:
            # Combine system prompt with user message
            full_prompt = f"{self.system_prompt}\n\nNgười dùng hỏi: {user_message}"
            
            # Call Ollama API with timeout
            response = self.client.generate(
                model=self.model,
                prompt=full_prompt,
                options={
                    'temperature': 0.7,
                    'top_p': 0.9,
                    'top_k': 40,
                }
            )
            
            # Extract response text
            response_text = response.get('response', '').strip()
            
            if not response_text:
                return "Xin lỗi, Tỷ Tỷ không tạo được câu trả lời. Bạn thử hỏi lại nhé!"
            
            return response_text
            
        except ollama.ResponseError as e:
            print(f"❌ Ollama Response Error: {e}")
            return "Xin lỗi, Tỷ Tỷ gặp lỗi khi xử lý. Bạn thử hỏi lại nhé!"
        except ollama.RequestError as e:
            print(f"❌ Ollama Request Error (connection issue): {e}")
            return "Xin lỗi, Tỷ Tỷ không kết nối được đến AI. Kiểm tra Ollama service nhé!"
        except TimeoutError as e:
            print(f"❌ Ollama Timeout: {e}")
            return "Xin lỗi, Tỷ Tỷ xử lý hơi lâu. Bạn thử câu hỏi ngắn hơn nhé!"
        except Exception as e:
            print(f"❌ Ollama Unexpected Error: {e}")
            return "Xin lỗi, Tỷ Tỷ gặp lỗi không mong đợi. Bạn thử hỏi lại nhé!"


# Singleton instance
_ollama_service: Optional[OllamaService] = None


def get_ollama_service() -> OllamaService:
    """Get or create Ollama service instance"""
    global _ollama_service
    if _ollama_service is None:
        _ollama_service = OllamaService()
    return _ollama_service


if __name__ == "__main__":
    """Test Ollama service"""
    print("=" * 60)
    print("🧪 Testing Ollama Service")
    print("=" * 60)
    
    try:
        # Initialize service
        print("\n📡 Initializing Ollama service...")
        ollama_svc = get_ollama_service()
        
        # Test connection
        print("\n🔍 Testing connection...")
        if not ollama_svc.test_connection():
            print("\n⚠️ Connection test failed!")
            print("Make sure:")
            print("  1. Ollama is running: ollama serve")
            print(f"  2. Model is installed: ollama pull {config.OLLAMA_MODEL}")
            exit(1)
        
        # Test simple math
        print("\n" + "=" * 60)
        print("🧮 Test 1: Simple Math")
        print("=" * 60)
        question1 = "1+1 bằng mấy?"
        print(f"Người dùng: {question1}")
        response1 = ollama_svc.get_response(question1)
        print(f"Tỷ Tỷ: {response1}")
        
        # Test Vietnamese knowledge
        print("\n" + "=" * 60)
        print("🇻🇳 Test 2: Vietnamese Knowledge")
        print("=" * 60)
        question2 = "Thủ đô Việt Nam là gì?"
        print(f"Người dùng: {question2}")
        response2 = ollama_svc.get_response(question2)
        print(f"Tỷ Tỷ: {response2}")
        
        # Test general knowledge
        print("\n" + "=" * 60)
        print("🌍 Test 3: General Knowledge")
        print("=" * 60)
        question3 = "Trái đất quay quanh mặt trời mất bao lâu?"
        print(f"Người dùng: {question3}")
        response3 = ollama_svc.get_response(question3)
        print(f"Tỷ Tỷ: {response3}")
        
        print("\n" + "=" * 60)
        print("✅ All tests completed!")
        print("=" * 60)
        
    except ConnectionError as e:
        print(f"\n❌ Connection Error: {e}")
        print("\n💡 Troubleshooting:")
        print("  1. Start Ollama server: ollama serve")
        print(f"  2. Pull model: ollama pull {config.OLLAMA_MODEL}")
        print("  3. Check if Ollama is running: ollama list")
        exit(1)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
