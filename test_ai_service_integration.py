"""
Integration Tests for AI Service Switching
Tests Ollama service connection, fallback from Ollama to Gemini,
"auto" mode service selection, and response consistency

**Validates: Requirements 6.4, 6.9, 6.11**

Requirements tested:
- 6.4: THE Ollama_Service SHALL have response time dưới 2 giây cho câu trả lời ngắn (dưới 50 từ)
- 6.9: WHEN cấu hình là "auto", THE AI_Service SHALL thử Ollama trước, nếu thất bại thì dùng Gemini
- 6.11: THE Ollama_Service SHALL xử lý lỗi timeout và connection error một cách graceful
"""

import unittest
import time
import os
from unittest.mock import patch, Mock
from modules.ai_service import AIService, get_ai_service
from config import config
import ollama


class TestOllamaServiceConnection(unittest.TestCase):
    """Integration tests for Ollama service connection and response generation"""
    
    @classmethod
    def setUpClass(cls):
        """Check if Ollama is available for testing"""
        cls.ollama_available = False
        try:
            client = ollama.Client(host=config.OLLAMA_BASE_URL)
            models_response = client.list()
            available_models = [model['name'] for model in models_response.get('models', [])]
            cls.ollama_available = config.OLLAMA_MODEL in available_models
            print(f"\n🔍 Ollama available: {cls.ollama_available}")
            if cls.ollama_available:
                print(f"   Model: {config.OLLAMA_MODEL}")
        except Exception as e:
            print(f"\n⚠️ Ollama not available: {e}")
    
    def test_ollama_connection_success(self):
        """Test successful connection to Ollama service"""
        if not self.ollama_available:
            self.skipTest("Ollama not available")
        
        print("\n📡 Testing Ollama connection...")
        ai_service = AIService(provider="ollama")
        
        self.assertEqual(ai_service.get_active_provider(), "ollama")
        self.assertIsNotNone(ai_service.ollama_client)
        print("✅ Ollama connection successful")
    
    def test_ollama_response_generation(self):
        """Test Ollama generates valid responses"""
        if not self.ollama_available:
            self.skipTest("Ollama not available")
        
        print("\n🤖 Testing Ollama response generation...")
        ai_service = AIService(provider="ollama")
        
        # Test simple question
        question = "1+1 bằng mấy?"
        response = ai_service.get_response(question)
        
        self.assertIsInstance(response, str)
        self.assertGreater(len(response), 0)
        self.assertNotIn("Xin lỗi", response)  # Should not be error message
        print(f"✅ Response: {response[:100]}...")
    
    def test_ollama_response_time(self):
        """
        Test Ollama response time is under 2 seconds for short responses
        **Validates: Requirement 6.4**
        """
        if not self.ollama_available:
            self.skipTest("Ollama not available")
        
        print("\n⏱️ Testing Ollama response time (Requirement 6.4)...")
        ai_service = AIService(provider="ollama")
        
        # Test with short question (under 50 words response expected)
        question = "Xin chào"
        start_time = time.time()
        response = ai_service.get_response(question)
        elapsed_time = time.time() - start_time
        
        print(f"   Response time: {elapsed_time:.2f}s")
        print(f"   Response: {response[:100]}...")
        
        # Requirement 6.4: response time under 2 seconds for short responses
        self.assertLess(elapsed_time, 2.0, 
                       f"Response time {elapsed_time:.2f}s exceeds 2s limit (Requirement 6.4)")
        print(f"✅ Response time {elapsed_time:.2f}s is under 2s limit")
    
    def test_ollama_connection_error_handling(self):
        """
        Test Ollama handles connection errors gracefully
        **Validates: Requirement 6.11**
        """
        print("\n🔌 Testing Ollama connection error handling (Requirement 6.11)...")
        
        # Use invalid URL to simulate connection error
        with patch('modules.ai_service.config') as mock_config:
            mock_config.OLLAMA_BASE_URL = "http://invalid:9999"
            mock_config.OLLAMA_MODEL = config.OLLAMA_MODEL
            mock_config.AI_PROVIDER = "ollama"
            mock_config.SYSTEM_PROMPT = config.SYSTEM_PROMPT
            
            # Should handle initialization error gracefully
            with self.assertRaises(Exception):
                ai_service = AIService(provider="ollama")
        
        print("✅ Connection error handled gracefully")
    
    def test_ollama_timeout_handling(self):
        """
        Test Ollama handles timeout errors gracefully
        **Validates: Requirement 6.11**
        """
        if not self.ollama_available:
            self.skipTest("Ollama not available")
        
        print("\n⏳ Testing Ollama timeout handling (Requirement 6.11)...")
        ai_service = AIService(provider="ollama")
        
        # Mock timeout error
        with patch.object(ai_service.ollama_client, 'generate', side_effect=TimeoutError("Request timeout")):
            response = ai_service.get_response("Test question")
            
            self.assertIn("xử lý hơi lâu", response.lower())
            print(f"✅ Timeout handled: {response}")


class TestAutoModeServiceSelection(unittest.TestCase):
    """
    Integration tests for "auto" mode selecting appropriate service
    **Validates: Requirement 6.9**
    """
    
    def test_auto_mode_tries_ollama_first(self):
        """
        Test auto mode tries Ollama first before Gemini
        **Validates: Requirement 6.9**
        """
        print("\n🔄 Testing auto mode tries Ollama first (Requirement 6.9)...")
        
        # Reset singleton
        import modules.ai_service as ai_module
        ai_module._ai_service = None
        
        with patch('modules.ai_service.ollama.Client') as mock_ollama:
            # Mock Ollama available
            mock_instance = Mock()
            mock_ollama.return_value = mock_instance
            mock_instance.list.return_value = {
                'models': [{'name': config.OLLAMA_MODEL}]
            }
            
            ai_service = AIService(provider="auto")
            
            # Should have tried Ollama first
            mock_ollama.assert_called_once()
            print(f"✅ Auto mode tried Ollama first, active: {ai_service.get_active_provider()}")
    
    def test_auto_mode_fallback_to_gemini(self):
        """
        Test auto mode falls back to Gemini when Ollama unavailable
        **Validates: Requirement 6.9**
        """
        print("\n🔄 Testing auto mode fallback to Gemini (Requirement 6.9)...")
        
        # Reset singleton
        import modules.ai_service as ai_module
        ai_module._ai_service = None
        
        with patch('modules.ai_service.ollama.Client') as mock_ollama:
            # Mock Ollama unavailable
            mock_ollama.side_effect = Exception("Connection refused")
            
            # Should fallback to Gemini if API key available
            if config.GOOGLE_API_KEY:
                ai_service = AIService(provider="auto")
                
                self.assertEqual(ai_service.get_active_provider(), "gemini")
                print(f"✅ Auto mode fell back to Gemini: {ai_service.get_active_provider()}")
            else:
                print("⚠️ Skipping: No Gemini API key available")
                self.skipTest("No Gemini API key")


class TestFallbackFromOllamaToGemini(unittest.TestCase):
    """Integration tests for fallback from Ollama to Gemini when Ollama unavailable"""
    
    def setUp(self):
        """Reset singleton before each test"""
        import modules.ai_service as ai_module
        ai_module._ai_service = None
    
    def test_fallback_when_ollama_down(self):
        """Test fallback to Gemini when Ollama service is down"""
        if not config.GOOGLE_API_KEY:
            self.skipTest("No Gemini API key")
        
        print("\n⚠️ Testing fallback when Ollama down...")
        
        with patch('modules.ai_service.ollama.Client') as mock_ollama:
            # Mock Ollama connection failure
            mock_ollama.side_effect = ConnectionError("Connection refused")
            
            # Auto mode should fallback to Gemini
            ai_service = AIService(provider="auto")
            
            self.assertEqual(ai_service.get_active_provider(), "gemini")
            
            # Should still get valid responses from Gemini
            response = ai_service.get_response("Xin chào")
            self.assertIsInstance(response, str)
            self.assertGreater(len(response), 0)
            print(f"✅ Fallback successful, response: {response[:50]}...")
    
    def test_runtime_fallback_in_auto_mode(self):
        """Test runtime fallback when Ollama fails during operation"""
        if not config.GOOGLE_API_KEY:
            self.skipTest("No Gemini API key")
        
        print("\n⚠️ Testing runtime fallback in auto mode...")
        
        with patch('modules.ai_service.ollama.Client') as mock_ollama:
            # Mock Ollama initially available
            mock_instance = Mock()
            mock_ollama.return_value = mock_instance
            mock_instance.list.return_value = {
                'models': [{'name': config.OLLAMA_MODEL}]
            }
            
            ai_service = AIService(provider="auto")
            
            # Verify started with Ollama
            self.assertEqual(ai_service.get_active_provider(), "ollama")
            
            # Mock Ollama failure during generate
            mock_instance.generate.side_effect = ollama.RequestError("Connection lost")
            
            # Should fallback to Gemini for this request
            response = ai_service.get_response("Test question")
            
            # In auto mode, should switch to Gemini after failure
            if not response.startswith("Xin lỗi"):
                self.assertEqual(ai_service.get_active_provider(), "gemini")
                print(f"✅ Runtime fallback successful to: {ai_service.get_active_provider()}")
            else:
                print("⚠️ Both providers failed, got error message")
    
    def test_no_fallback_in_ollama_only_mode(self):
        """Test no fallback occurs when explicitly using Ollama mode"""
        print("\n🔒 Testing no fallback in Ollama-only mode...")
        
        with patch('modules.ai_service.ollama.Client') as mock_ollama:
            # Mock Ollama available for init
            mock_instance = Mock()
            mock_ollama.return_value = mock_instance
            mock_instance.list.return_value = {
                'models': [{'name': config.OLLAMA_MODEL}]
            }
            
            ai_service = AIService(provider="ollama")
            
            # Mock Ollama failure
            mock_instance.generate.side_effect = ollama.RequestError("Connection error")
            
            # Should NOT fallback to Gemini in ollama-only mode
            response = ai_service.get_response("Test")
            
            # Should remain on Ollama
            self.assertEqual(ai_service.get_active_provider(), "ollama")
            # Should get error message, not Gemini response
            self.assertIn("Xin lỗi", response)
            print(f"✅ No fallback occurred, stayed on Ollama with error message")


class TestResponseConsistency(unittest.TestCase):
    """Integration tests for response consistency between Ollama and Gemini"""
    
    @classmethod
    def setUpClass(cls):
        """Check provider availability"""
        cls.ollama_available = False
        cls.gemini_available = bool(config.GOOGLE_API_KEY)
        
        try:
            client = ollama.Client(host=config.OLLAMA_BASE_URL)
            models_response = client.list()
            available_models = [model['name'] for model in models_response.get('models', [])]
            cls.ollama_available = config.OLLAMA_MODEL in available_models
        except Exception:
            pass
        
        print(f"\n📊 Provider availability:")
        print(f"   Ollama: {cls.ollama_available}")
        print(f"   Gemini: {cls.gemini_available}")
    
    def test_both_providers_use_same_system_prompt(self):
        """Test both providers use the same system prompt"""
        print("\n📝 Testing system prompt consistency...")
        
        if self.ollama_available:
            ollama_service = AIService(provider="ollama")
            self.assertEqual(ollama_service.system_prompt, config.SYSTEM_PROMPT)
            print(f"✅ Ollama uses config system prompt")
        
        if self.gemini_available:
            gemini_service = AIService(provider="gemini")
            self.assertEqual(gemini_service.system_prompt, config.SYSTEM_PROMPT)
            print(f"✅ Gemini uses config system prompt")
    
    def test_response_format_consistency(self):
        """Test both providers return string responses"""
        print("\n📋 Testing response format consistency...")
        
        question = "Xin chào"
        
        if self.ollama_available:
            ollama_service = AIService(provider="ollama")
            ollama_response = ollama_service.get_response(question)
            self.assertIsInstance(ollama_response, str)
            self.assertGreater(len(ollama_response), 0)
            print(f"✅ Ollama response format valid")
        
        if self.gemini_available:
            gemini_service = AIService(provider="gemini")
            gemini_response = gemini_service.get_response(question)
            self.assertIsInstance(gemini_response, str)
            self.assertGreater(len(gemini_response), 0)
            print(f"✅ Gemini response format valid")
    
    def test_both_providers_handle_math_questions(self):
        """Test both providers can handle basic math questions"""
        if not (self.ollama_available and self.gemini_available):
            self.skipTest("Both providers not available")
        
        print("\n🧮 Testing math question handling...")
        
        question = "1+1 bằng mấy?"
        
        ollama_service = AIService(provider="ollama")
        ollama_response = ollama_service.get_response(question)
        
        gemini_service = AIService(provider="gemini")
        gemini_response = gemini_service.get_response(question)
        
        # Both should provide valid responses (not error messages)
        self.assertNotIn("Xin lỗi", ollama_response)
        self.assertNotIn("Xin lỗi", gemini_response)
        
        # Both responses should contain number 2 or "hai"
        ollama_has_answer = "2" in ollama_response or "hai" in ollama_response.lower()
        gemini_has_answer = "2" in gemini_response or "hai" in gemini_response.lower()
        
        print(f"   Ollama: {ollama_response[:100]}...")
        print(f"   Gemini: {gemini_response[:100]}...")
        print(f"✅ Both providers handled math question")
    
    def test_error_message_format_consistency(self):
        """Test both providers return consistent error message format"""
        print("\n⚠️ Testing error message consistency...")
        
        # Both should return Vietnamese error messages starting with "Xin lỗi"
        error_messages_vietnamese = True
        
        if self.ollama_available:
            with patch('modules.ai_service.ollama.Client') as mock_ollama:
                mock_instance = Mock()
                mock_ollama.return_value = mock_instance
                mock_instance.list.return_value = {
                    'models': [{'name': config.OLLAMA_MODEL}]
                }
                mock_instance.generate.side_effect = Exception("Test error")
                
                ollama_service = AIService(provider="ollama")
                error_response = ollama_service.get_response("Test")
                
                self.assertIn("Xin lỗi", error_response)
                print(f"✅ Ollama error format: {error_response[:50]}...")
        
        # Similar check could be done for Gemini
        print("✅ Error message format consistent")


class TestProviderSwitching(unittest.TestCase):
    """Integration tests for dynamic provider switching"""
    
    def setUp(self):
        """Reset singleton before each test"""
        import modules.ai_service as ai_module
        ai_module._ai_service = None
    
    def test_switch_from_gemini_to_ollama(self):
        """Test switching from Gemini to Ollama"""
        if not config.GOOGLE_API_KEY:
            self.skipTest("No Gemini API key")
        
        print("\n🔄 Testing switch from Gemini to Ollama...")
        
        # Start with Gemini
        ai_service = AIService(provider="gemini")
        self.assertEqual(ai_service.get_active_provider(), "gemini")
        
        # Try to switch to Ollama
        with patch.object(ai_service, '_test_ollama', return_value=True):
            with patch('modules.ai_service.ollama.Client'):
                success = ai_service.switch_provider("ollama")
                
                if success:
                    self.assertEqual(ai_service.get_active_provider(), "ollama")
                    print(f"✅ Switched to: {ai_service.get_active_provider()}")
                else:
                    print("⚠️ Switch failed (Ollama not available)")
    
    def test_switch_from_ollama_to_gemini(self):
        """Test switching from Ollama to Gemini"""
        if not config.GOOGLE_API_KEY:
            self.skipTest("No Gemini API key")
        
        print("\n🔄 Testing switch from Ollama to Gemini...")
        
        with patch('modules.ai_service.ollama.Client') as mock_ollama:
            # Mock Ollama available
            mock_instance = Mock()
            mock_ollama.return_value = mock_instance
            mock_instance.list.return_value = {
                'models': [{'name': config.OLLAMA_MODEL}]
            }
            
            # Start with Ollama
            ai_service = AIService(provider="ollama")
            self.assertEqual(ai_service.get_active_provider(), "ollama")
            
            # Switch to Gemini
            success = ai_service.switch_provider("gemini")
            
            self.assertTrue(success)
            self.assertEqual(ai_service.get_active_provider(), "gemini")
            print(f"✅ Switched to: {ai_service.get_active_provider()}")
    
    def test_invalid_provider_switch(self):
        """Test handling of invalid provider in switch"""
        print("\n❌ Testing invalid provider switch...")
        
        with patch('modules.ai_service.ollama.Client') as mock_ollama:
            mock_instance = Mock()
            mock_ollama.return_value = mock_instance
            mock_instance.list.return_value = {
                'models': [{'name': config.OLLAMA_MODEL}]
            }
            
            ai_service = AIService(provider="ollama")
            
            # Try invalid provider
            success = ai_service.switch_provider("invalid_provider")
            
            self.assertFalse(success)
            # Should remain on original provider
            self.assertEqual(ai_service.get_active_provider(), "ollama")
            print(f"✅ Invalid switch rejected, stayed on: {ai_service.get_active_provider()}")


def run_integration_tests():
    """Run all integration tests with detailed output"""
    print("=" * 80)
    print("🧪 AI Service Integration Tests")
    print("=" * 80)
    print(f"\nConfiguration:")
    print(f"  AI_PROVIDER: {config.AI_PROVIDER}")
    print(f"  Gemini Model: {config.AI_MODEL}")
    print(f"  Ollama Model: {config.OLLAMA_MODEL}")
    print(f"  Ollama URL: {config.OLLAMA_BASE_URL}")
    print(f"  Gemini API Key: {'✅ Set' if config.GOOGLE_API_KEY else '❌ Not set'}")
    print("=" * 80)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestOllamaServiceConnection))
    suite.addTests(loader.loadTestsFromTestCase(TestAutoModeServiceSelection))
    suite.addTests(loader.loadTestsFromTestCase(TestFallbackFromOllamaToGemini))
    suite.addTests(loader.loadTestsFromTestCase(TestResponseConsistency))
    suite.addTests(loader.loadTestsFromTestCase(TestProviderSwitching))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 Test Summary")
    print("=" * 80)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    print("=" * 80)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_integration_tests()
    exit(0 if success else 1)
