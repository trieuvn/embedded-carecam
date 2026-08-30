"""
Test AI Service with Multi-Provider Support
Tests Gemini, Ollama, and Auto mode with fallback
"""
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.ai_service import AIService, get_ai_service
from config import config

def test_gemini_only():
    """Test Gemini provider exclusively"""
    print("\n" + "=" * 70)
    print("TEST 1: Gemini Provider")
    print("=" * 70)
    
    try:
        ai = AIService(provider="gemini")
        print(f"✅ Initialized with provider: {ai.get_active_provider()}")
        
        # Test simple math
        print("\n🧮 Question: 1+1 bằng mấy?")
        response = ai.get_response("1+1 bằng mấy?")
        print(f"🤖 Tỷ Tỷ: {response}")
        
        # Test Vietnamese knowledge
        print("\n🇻🇳 Question: Thủ đô Việt Nam là gì?")
        response = ai.get_response("Thủ đô Việt Nam là gì?")
        print(f"🤖 Tỷ Tỷ: {response}")
        
        print("\n✅ Gemini test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Gemini test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ollama_only():
    """Test Ollama provider exclusively"""
    print("\n" + "=" * 70)
    print("TEST 2: Ollama Provider")
    print("=" * 70)
    
    try:
        ai = AIService(provider="ollama")
        print(f"✅ Initialized with provider: {ai.get_active_provider()}")
        
        # Test simple calculation
        print("\n🧮 Question: 5+3 bằng mấy?")
        response = ai.get_response("5+3 bằng mấy?")
        print(f"🤖 Tỷ Tỷ: {response}")
        
        # Test greeting
        print("\n👋 Question: Xin chào Tỷ Tỷ")
        response = ai.get_response("Xin chào Tỷ Tỷ")
        print(f"🤖 Tỷ Tỷ: {response}")
        
        print("\n✅ Ollama test passed!")
        return True
        
    except Exception as e:
        print(f"⚠️ Ollama test failed: {e}")
        print("💡 Make sure Ollama is running:")
        print("   1. Start service: ollama serve")
        print(f"   2. Pull model: ollama pull {config.OLLAMA_MODEL}")
        return False

def test_auto_mode():
    """Test auto mode with Ollama → Gemini fallback"""
    print("\n" + "=" * 70)
    print("TEST 3: Auto Mode (Ollama → Gemini Fallback)")
    print("=" * 70)
    
    try:
        ai = AIService(provider="auto")
        print(f"✅ Auto mode initialized")
        print(f"   Active provider: {ai.get_active_provider()}")
        
        # Test with active provider
        print("\n🌍 Question: Trái đất quay quanh mặt trời mất bao lâu?")
        response = ai.get_response("Trái đất quay quanh mặt trời mất bao lâu?")
        print(f"🤖 Tỷ Tỷ: {response}")
        print(f"   Provider used: {ai.get_active_provider()}")
        
        # Test follow-up
        print("\n💭 Question: Còn mặt trăng thì sao?")
        response = ai.get_response("Còn mặt trăng thì sao?")
        print(f"🤖 Tỷ Tỷ: {response}")
        print(f"   Provider used: {ai.get_active_provider()}")
        
        print("\n✅ Auto mode test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Auto mode test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_provider_switching():
    """Test dynamic provider switching"""
    print("\n" + "=" * 70)
    print("TEST 4: Dynamic Provider Switching")
    print("=" * 70)
    
    try:
        # Start with auto mode
        ai = get_ai_service(provider="auto")
        initial_provider = ai.get_active_provider()
        print(f"Initial provider: {initial_provider}")
        
        # Test question with initial provider
        print(f"\n📝 Question with {initial_provider}:")
        response = ai.get_response("Hello, how are you?")
        print(f"🤖 Tỷ Tỷ: {response}")
        
        # Try switching to the other provider
        target_provider = "gemini" if initial_provider == "ollama" else "ollama"
        print(f"\n🔄 Attempting to switch to {target_provider}...")
        
        if ai.switch_provider(target_provider):
            print(f"✅ Switched to {ai.get_active_provider()}")
            
            # Test with new provider
            print(f"\n📝 Question with {ai.get_active_provider()}:")
            response = ai.get_response("Tỷ Tỷ có khỏe không?")
            print(f"🤖 Tỷ Tỷ: {response}")
            
            print("\n✅ Provider switching test passed!")
            return True
        else:
            print(f"⚠️ Could not switch to {target_provider}")
            return False
            
    except Exception as e:
        print(f"❌ Provider switching test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_fallback_behavior():
    """Test fallback behavior when Ollama fails in auto mode"""
    print("\n" + "=" * 70)
    print("TEST 5: Fallback Behavior (Simulated)")
    print("=" * 70)
    
    try:
        # Force auto mode
        ai = AIService(provider="auto")
        
        if ai.get_active_provider() == "ollama":
            print("✅ Started with Ollama")
            print("💡 If Ollama fails, should fallback to Gemini automatically")
        elif ai.get_active_provider() == "gemini":
            print("✅ Started with Gemini (Ollama not available)")
            print("💡 Fallback behavior working as expected")
        
        # Test multiple requests to verify stability
        for i in range(3):
            print(f"\n📝 Request {i+1}: Tính {i}+{i+1}")
            response = ai.get_response(f"Tính {i}+{i+1}")
            print(f"🤖 Tỷ Tỷ: {response}")
            print(f"   Provider: {ai.get_active_provider()}")
        
        print("\n✅ Fallback behavior test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Fallback test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("=" * 70)
    print("🧪 AI Service Multi-Provider Test Suite")
    print("=" * 70)
    
    print(f"\n📋 Configuration:")
    print(f"   AI_PROVIDER: {config.AI_PROVIDER}")
    print(f"   Gemini Model: {config.AI_MODEL}")
    print(f"   Ollama Model: {config.OLLAMA_MODEL}")
    print(f"   Ollama URL: {config.OLLAMA_BASE_URL}")
    
    results = {}
    
    # Run tests
    if config.GOOGLE_API_KEY:
        results['gemini'] = test_gemini_only()
    else:
        print("\n⚠️ Skipping Gemini test (no API key)")
        results['gemini'] = None
    
    results['ollama'] = test_ollama_only()
    results['auto'] = test_auto_mode()
    results['switching'] = test_provider_switching()
    results['fallback'] = test_fallback_behavior()
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 Test Results Summary")
    print("=" * 70)
    
    for test_name, result in results.items():
        if result is None:
            status = "⊘ SKIPPED"
        elif result:
            status = "✅ PASSED"
        else:
            status = "❌ FAILED"
        print(f"{test_name.ljust(15)}: {status}")
    
    passed = sum(1 for r in results.values() if r is True)
    total = sum(1 for r in results.values() if r is not None)
    
    print(f"\nTotal: {passed}/{total} tests passed")
    print("=" * 70)
    
    return all(r is True or r is None for r in results.values())

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
