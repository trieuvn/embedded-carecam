"""Test Google Gemini AI với API key - Using new google-genai package"""
import os

API_KEY = "AIzaSyCmIhYgpbX2it0ssrA8VuTe6P8TPpydfHw"

print("🔄 Connecting to Google Gemini...")

try:
    from google import genai
    
    client = genai.Client(api_key=API_KEY)
    
    print("✅ Connected!")
    print("\n🧮 Question: 1+1 bằng mấy?")
    
    response = client.models.generate_content(
        model="gemini-flash-latest",
        contents="1+1 bằng mấy? Trả lời ngắn gọn bằng tiếng Việt."
    )
    
    print(f"🤖 Tỷ Tỷ: {response.text}")
    print("\n✅ Test passed!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
