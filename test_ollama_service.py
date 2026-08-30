"""
Unit tests for Ollama Service Module
Tests connection, error handling, and response generation
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
from modules.ollama_service import OllamaService, get_ollama_service
from config import config


class TestOllamaService(unittest.TestCase):
    """Test cases for OllamaService class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_client = Mock()
    
    @patch('modules.ollama_service.ollama.Client')
    def test_initialization_success(self, mock_client_class):
        """Test successful initialization with available model"""
        # Mock the client and its methods
        mock_instance = Mock()
        mock_client_class.return_value = mock_instance
        mock_instance.list.return_value = {
            'models': [
                {'name': 'qwen2.5:0.5b'},
                {'name': 'llama2:7b'}
            ]
        }
        
        # Create service
        service = OllamaService()
        
        # Verify initialization
        self.assertIsNotNone(service.client)
        self.assertEqual(service.model, config.OLLAMA_MODEL)
        self.assertEqual(service.system_prompt, config.SYSTEM_PROMPT)
        mock_client_class.assert_called_once_with(host=config.OLLAMA_BASE_URL)
    
    @patch('modules.ollama_service.ollama.Client')
    def test_initialization_model_not_available(self, mock_client_class):
        """Test initialization when model is not available"""
        # Mock the client with no matching model
        mock_instance = Mock()
        mock_client_class.return_value = mock_instance
        mock_instance.list.return_value = {
            'models': [
                {'name': 'llama2:7b'}
            ]
        }
        
        # Should raise ConnectionError
        with self.assertRaises(ConnectionError):
            service = OllamaService()
    
    @patch('modules.ollama_service.ollama.Client')
    def test_test_connection_success(self, mock_client_class):
        """Test connection test when model is available"""
        # Mock successful connection
        mock_instance = Mock()
        mock_client_class.return_value = mock_instance
        mock_instance.list.return_value = {
            'models': [
                {'name': 'qwen2.5:0.5b'}
            ]
        }
        
        service = OllamaService()
        result = service.test_connection()
        
        self.assertTrue(result)
    
    @patch('modules.ollama_service.ollama.Client')
    def test_test_connection_failure(self, mock_client_class):
        """Test connection test when server is not available"""
        # Mock connection failure
        mock_instance = Mock()
        mock_client_class.return_value = mock_instance
        mock_instance.list.side_effect = Exception("Connection refused")
        
        # Create service (will fail on init, so we patch test_connection to return False initially)
        with patch.object(OllamaService, 'test_connection', return_value=False):
            with self.assertRaises(ConnectionError):
                service = OllamaService()
    
    @patch('modules.ollama_service.ollama.Client')
    def test_get_response_success(self, mock_client_class):
        """Test successful response generation"""
        # Mock successful response
        mock_instance = Mock()
        mock_client_class.return_value = mock_instance
        mock_instance.list.return_value = {
            'models': [{'name': 'qwen2.5:0.5b'}]
        }
        mock_instance.generate.return_value = {
            'response': '1 + 1 = 2'
        }
        
        service = OllamaService()
        response = service.get_response("1+1 bằng mấy?")
        
        self.assertEqual(response, "1 + 1 = 2")
        mock_instance.generate.assert_called_once()
    
    @patch('modules.ollama_service.ollama.Client')
    def test_get_response_empty_response(self, mock_client_class):
        """Test handling of empty response from Ollama"""
        # Mock empty response
        mock_instance = Mock()
        mock_client_class.return_value = mock_instance
        mock_instance.list.return_value = {
            'models': [{'name': 'qwen2.5:0.5b'}]
        }
        mock_instance.generate.return_value = {
            'response': ''
        }
        
        service = OllamaService()
        response = service.get_response("Test question")
        
        self.assertIn("không tạo được câu trả lời", response)
    
    @patch('modules.ollama_service.ollama.Client')
    @patch('modules.ollama_service.ollama.ResponseError', Exception)
    def test_get_response_response_error(self, mock_client_class):
        """Test handling of Ollama response error"""
        # Mock response error
        mock_instance = Mock()
        mock_client_class.return_value = mock_instance
        mock_instance.list.return_value = {
            'models': [{'name': 'qwen2.5:0.5b'}]
        }
        
        # Import the actual exception
        import ollama
        mock_instance.generate.side_effect = ollama.ResponseError("API Error")
        
        service = OllamaService()
        response = service.get_response("Test question")
        
        self.assertIn("gặp lỗi khi xử lý", response)
    
    @patch('modules.ollama_service.ollama.Client')
    def test_get_response_request_error(self, mock_client_class):
        """Test handling of Ollama request/connection error"""
        # Mock request error
        mock_instance = Mock()
        mock_client_class.return_value = mock_instance
        mock_instance.list.return_value = {
            'models': [{'name': 'qwen2.5:0.5b'}]
        }
        
        # Import the actual exception
        import ollama
        mock_instance.generate.side_effect = ollama.RequestError("Connection refused")
        
        service = OllamaService()
        response = service.get_response("Test question")
        
        self.assertIn("không kết nối được", response)
    
    @patch('modules.ollama_service.ollama.Client')
    def test_get_response_timeout_error(self, mock_client_class):
        """Test handling of timeout error"""
        # Mock timeout error
        mock_instance = Mock()
        mock_client_class.return_value = mock_instance
        mock_instance.list.return_value = {
            'models': [{'name': 'qwen2.5:0.5b'}]
        }
        mock_instance.generate.side_effect = TimeoutError("Request timeout")
        
        service = OllamaService()
        response = service.get_response("Test question")
        
        self.assertIn("xử lý hơi lâu", response)
    
    @patch('modules.ollama_service.ollama.Client')
    def test_system_prompt_included(self, mock_client_class):
        """Test that system prompt is included in requests"""
        # Mock successful response
        mock_instance = Mock()
        mock_client_class.return_value = mock_instance
        mock_instance.list.return_value = {
            'models': [{'name': 'qwen2.5:0.5b'}]
        }
        mock_instance.generate.return_value = {
            'response': 'Test response'
        }
        
        service = OllamaService()
        service.get_response("Test question")
        
        # Check that generate was called with prompt containing system prompt
        call_args = mock_instance.generate.call_args
        self.assertIn('prompt', call_args.kwargs)
        prompt = call_args.kwargs['prompt']
        self.assertIn(config.SYSTEM_PROMPT, prompt)
        self.assertIn("Test question", prompt)
    
    @patch('modules.ollama_service.ollama.Client')
    def test_singleton_get_ollama_service(self, mock_client_class):
        """Test singleton pattern for get_ollama_service"""
        # Mock successful initialization
        mock_instance = Mock()
        mock_client_class.return_value = mock_instance
        mock_instance.list.return_value = {
            'models': [{'name': 'qwen2.5:0.5b'}]
        }
        
        # Reset singleton
        import modules.ollama_service as om
        om._ollama_service = None
        
        # Get service twice
        service1 = get_ollama_service()
        service2 = get_ollama_service()
        
        # Should be the same instance
        self.assertIs(service1, service2)


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 Running Ollama Service Unit Tests")
    print("=" * 60)
    unittest.main(verbosity=2)
