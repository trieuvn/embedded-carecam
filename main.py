"""
Tỷ Tỷ - CareCam Voice Chatbot
=============================

Chatbot AI điều khiển bằng giọng nói cho camera CareCam.
Nói "Tỷ Tỷ" để kích hoạt, sau đó đặt câu hỏi.

Example:
    "Tỷ Tỷ 1+1 bằng mấy?" → "1 cộng 1 bằng 2!"
    "Tỷ Tỷ thời tiết hôm nay thế nào?" → AI trả lời
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.ai_service import get_ai_service
from modules.text_to_speech import get_tts
from modules.speech_to_text import get_stt
from modules.wake_word import get_wake_detector
from config import config


class TyTyChatbot:
    """Main chatbot controller"""
    
    def __init__(self):
        print("=" * 50)
        print("🤖 Tỷ Tỷ - CareCam Voice Chatbot")
        print("=" * 50)
        print()
        
        self.running = False
        self.ai = None
        self.tts = None
        self.stt = None
        self.detector = None
        
    def initialize(self) -> bool:
        """Initialize all components"""
        try:
            print("🔄 Initializing components...\n")
            
            # Initialize speech-to-text
            self.stt = get_stt()
            
            # Initialize wake word detector
            self.detector = get_wake_detector()
            
            # Initialize text-to-speech
            self.tts = get_tts()
            
            # Initialize AI service
            self.ai = get_ai_service()
            
            print("\n✅ All components initialized!")
            print("-" * 50)
            return True
            
        except Exception as e:
            print(f"\n❌ Initialization failed: {e}")
            return False
    
    def process_command(self, command: str) -> str:
        """Process user command and get AI response"""
        print(f"\n💭 Processing: '{command}'")
        response = self.ai.get_response(command)
        print(f"🤖 Tỷ Tỷ: {response}")
        return response
    
    def speak(self, text: str):
        """Speak the response"""
        print(f"🔊 Speaking...")
        self.tts.speak(text)
    
    def listen_loop(self):
        """Main listening loop"""
        print("\n🎧 Listening mode started!")
        print("💡 Say 'Tỷ Tỷ' followed by your question")
        print("   Example: 'Tỷ Tỷ 1+1 bằng mấy?'")
        print("   Press Ctrl+C to stop\n")
        
        self.running = True
        
        # Greeting
        self.speak("Xin chào! Tôi là Tỷ Tỷ. Bạn cần gì ạ?")
        
        while self.running:
            try:
                # Listen for speech
                text = self.stt.listen_and_recognize()
                
                if not text:
                    continue
                
                # Check for wake word
                detected, command = self.detector.check(text)
                
                if detected:
                    if command:
                        # Wake word + command
                        response = self.process_command(command)
                        self.speak(response)
                    elif self.detector.is_just_wake_word(text):
                        # Just wake word, wait for command
                        self.speak("Dạ, Tỷ Tỷ nghe đây!")
                        print("👂 Waiting for command...")
                        
                        # Listen for the actual command
                        command = self.stt.listen_and_recognize()
                        if command:
                            response = self.process_command(command)
                            self.speak(response)
                        else:
                            self.speak("Tỷ Tỷ không nghe rõ. Bạn nói lại được không?")
                else:
                    # No wake word detected
                    print(f"👀 Heard: '{text}' (no wake word)")
                    
            except KeyboardInterrupt:
                print("\n\n🛑 Stopping...")
                self.running = False
                self.speak("Tạm biệt nhé!")
                break
            except Exception as e:
                print(f"❌ Error in loop: {e}")
                continue
    
    def run(self):
        """Start the chatbot"""
        if self.initialize():
            self.listen_loop()
        else:
            print("\n❌ Failed to start chatbot")
            print("💡 Make sure you have set GOOGLE_API_KEY environment variable")
            print("   Get your free API key at: https://aistudio.google.com/app/apikey")


def main():
    """Entry point"""
    chatbot = TyTyChatbot()
    chatbot.run()


if __name__ == "__main__":
    main()
