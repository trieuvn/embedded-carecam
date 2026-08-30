"""
Tỷ Tỷ - CareCam Voice Chatbot (Enhanced Architecture)
======================================================

Chatbot AI điều khiển bằng giọng nói cho camera CareCam với kiến trúc nâng cấp:
- Voice Activity Detection (VAD) để tối ưu xử lý âm thanh
- Enhanced Wake Word Detection với Porcupine acoustic model
- Multi-Turn Conversation Support với context management
- Context-Aware AI Prompts
- Error Handling và Recovery
- Flexible Audio Routing Management

Nói "Tỷ Tỷ" để kích hoạt, sau đó đặt câu hỏi.

Example:
    "Tỷ Tỷ 1+1 bằng mấy?" → "1 cộng 1 bằng 2!"
    "Tỷ Tỷ thời tiết hôm nay thế nào?" → AI trả lời
    
Requirements: 8.1, 8.2, 8.4, 8.6
"""

import sys
import os
import logging
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Core AI and Speech modules
from modules.ai_service import get_ai_service
from modules.text_to_speech import get_tts
from modules.speech_to_text import get_stt

# Legacy wake word detector (backward compatibility)
from modules.wake_word import get_wake_detector

# New architecture components
from modules.vad import create_vad, VADConfig
from modules.wake_word_engine import get_wake_word_engine
from modules.context_manager import ConversationContextManager, Role
from modules.dialogue_controller import get_dialogue_controller
from modules.prompt_builder import get_prompt_builder, ResponseMode
from modules.error_handler import ErrorHandler, ErrorContext, ErrorType, Severity
from modules.audio_router import create_audio_router, AudioConfig, OperationMode
from modules.conversation_manager import get_conversation_manager

from config import config

# Setup logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/main.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


class TyTyChatbot:
    """
    Main chatbot controller with enhanced architecture
    
    Integrates:
    - VAD for voice activity detection
    - Enhanced wake word engine (Porcupine or fallback)
    - Context manager for conversation history
    - Dialogue controller for multi-turn conversations
    - Prompt builder for context-aware AI prompts
    - Error handler for graceful error recovery
    - Audio router for flexible device management
    - Conversation manager for state management (optional)
    """
    
    def __init__(self):
        print("=" * 60)
        print("🤖 Tỷ Tỷ - CareCam Voice Chatbot (Enhanced)")
        print("=" * 60)
        print()
        
        self.running = False
        
        # Core components (always initialized)
        self.ai = None
        self.tts = None
        self.stt = None
        
        # New architecture components
        self.vad = None
        self.wake_word_engine = None
        self.context_manager = None
        self.dialogue_controller = None
        self.prompt_builder = None
        self.error_handler = None
        self.audio_router = None
        self.conversation_manager = None
        
        # Legacy components (fallback)
        self.legacy_detector = None
        
        # Session tracking
        self.current_session_id: Optional[str] = None
        
        # Feature flags (from config)
        self.use_vad = config.VAD_ENABLED
        self.use_enhanced_wake_word = config.WAKE_WORD_ENGINE_ENABLED
        self.use_conversation_context = config.CONVERSATION_ENABLED
        
    def initialize(self) -> bool:
        """Initialize all components with new architecture"""
        try:
            print("🔄 Initializing components...\n")
            
            # Initialize Error Handler first (for error recovery)
            print("  📋 Initializing Error Handler...")
            self.error_handler = ErrorHandler(log_file=f"{config.LOG_DIR}/error_handler.log")
            
            # Initialize Audio Router
            print(f"  🔊 Initializing Audio Router ({config.OPERATION_MODE})...")
            audio_config = AudioConfig(
                operation_mode=OperationMode(config.OPERATION_MODE),
                sample_rate=config.SAMPLE_RATE,
                channels=config.CHANNELS,
                buffer_size=config.BUFFER_SIZE,
                virtual_cable_enabled=config.VIRTUAL_CABLE_ENABLED
            )
            self.audio_router = create_audio_router(audio_config)
            
            if not self.audio_router.initialize():
                self.error_handler.notify_user(
                    "Không thể khởi tạo audio router, sử dụng cấu hình mặc định",
                    Severity.WARNING
                )
            
            # Initialize VAD (if enabled)
            if self.use_vad:
                print("  🎙️ Initializing Voice Activity Detection (VAD)...")
                vad_config = VADConfig(
                    energy_threshold=config.VAD_ENERGY_THRESHOLD,
                    silence_duration=config.VAD_SILENCE_DURATION,
                    min_speech_duration=config.VAD_MIN_SPEECH_DURATION,
                    sample_rate=config.SAMPLE_RATE,
                    frame_length_ms=config.VAD_FRAME_LENGTH_MS
                )
                self.vad = create_vad(vad_config)
                
                # Register health check
                self.error_handler.register_component(
                    "vad",
                    lambda: self.vad is not None
                )
            else:
                print("  ⏭️  VAD disabled (config.VAD_ENABLED=False)")
            
            # Initialize Wake Word Engine (enhanced or legacy)
            if self.use_enhanced_wake_word:
                print("  🔊 Initializing Enhanced Wake Word Engine...")
                try:
                    self.wake_word_engine = get_wake_word_engine(
                        model_path=config.WAKE_WORD_MODEL_PATH,
                        sensitivity=config.WAKE_WORD_SENSITIVITY
                    )
                    
                    # Register health check
                    self.error_handler.register_component(
                        "wake_word_engine",
                        lambda: self.wake_word_engine is not None
                    )
                except Exception as e:
                    logger.warning(f"Failed to initialize wake word engine: {e}")
                    print("  ⚠️  Falling back to legacy wake word detector...")
                    self.use_enhanced_wake_word = False
            
            if not self.use_enhanced_wake_word:
                print("  🔊 Initializing Legacy Wake Word Detector...")
                self.legacy_detector = get_wake_detector()
            
            # Initialize Speech-to-Text
            print("  🎤 Initializing Speech-to-Text...")
            self.stt = get_stt()
            self.error_handler.register_component(
                "speech_to_text",
                lambda: self.stt is not None
            )
            
            # Initialize Text-to-Speech
            print("  🔈 Initializing Text-to-Speech...")
            self.tts = get_tts()
            self.error_handler.register_component(
                "text_to_speech",
                lambda: self.tts is not None
            )
            
            # Initialize Context Manager (if conversation enabled)
            if self.use_conversation_context:
                print("  💾 Initializing Conversation Context Manager...")
                self.context_manager = ConversationContextManager(
                    max_context_turns=config.MAX_CONTEXT_TURNS,
                    session_timeout_minutes=config.SESSION_TIMEOUT_MINUTES,
                    persistence_enabled=True,
                    persistence_dir=f"{config.LOG_DIR}/sessions"
                )
                
                # Create initial session
                self.current_session_id = self.context_manager.create_session(user_id="default")
                logger.info(f"Created session: {self.current_session_id}")
                
                # Set user preferences
                self.context_manager.set_user_preference(
                    self.current_session_id,
                    "response_mode",
                    config.DEFAULT_RESPONSE_MODE
                )
                
                # Register health check
                self.error_handler.register_component(
                    "context_manager",
                    lambda: self.context_manager is not None
                )
            else:
                print("  ⏭️  Conversation context disabled (config.CONVERSATION_ENABLED=False)")
            
            # Initialize Dialogue Controller (if conversation enabled)
            if self.use_conversation_context and self.context_manager:
                print("  🎯 Initializing Dialogue Controller...")
                self.dialogue_controller = get_dialogue_controller()
                self.dialogue_controller.initialize(self.context_manager)
                
                # Register health check
                self.error_handler.register_component(
                    "dialogue_controller",
                    lambda: self.dialogue_controller is not None
                )
            
            # Initialize Prompt Builder
            print("  📝 Initializing Prompt Builder...")
            self.prompt_builder = get_prompt_builder()
            self.prompt_builder.initialize(config.SYSTEM_PROMPT)
            self.prompt_builder.set_response_mode(ResponseMode(config.DEFAULT_RESPONSE_MODE))
            
            # Initialize AI service
            print(f"  🤖 Initializing AI Service ({config.AI_PROVIDER})...")
            self.ai = get_ai_service()
            self.error_handler.register_component(
                "ai_service",
                lambda: self.ai is not None
            )
            
            print("\n✅ All components initialized successfully!")
            print("-" * 60)
            self._print_configuration()
            return True
            
        except Exception as e:
            logger.error(f"Initialization failed: {e}", exc_info=True)
            print(f"\n❌ Initialization failed: {e}")
            
            # Try to provide helpful error message
            context = ErrorContext(
                component="main",
                operation="initialization",
                retry_count=0
            )
            recovery_action = self.error_handler.handle_error(e, context)
            self.error_handler.notify_user(recovery_action.user_message, Severity.ERROR)
            
            return False
    
    def _print_configuration(self):
        """Print current configuration"""
        print("\n⚙️  Configuration:")
        print(f"  - Operation Mode: {config.OPERATION_MODE}")
        print(f"  - AI Provider: {config.AI_PROVIDER}")
        print(f"  - VAD Enabled: {self.use_vad}")
        print(f"  - Enhanced Wake Word: {self.use_enhanced_wake_word}")
        print(f"  - Conversation Context: {self.use_conversation_context}")
        print(f"  - Audio Sample Rate: {config.SAMPLE_RATE} Hz")
        print(f"  - Max Context Turns: {config.MAX_CONTEXT_TURNS if self.use_conversation_context else 'N/A'}")
    
    def process_command(self, command: str) -> str:
        """
        Process user command with context-aware prompting
        
        Args:
            command: User command text
            
        Returns:
            AI response text
        """
        try:
            print(f"\n💭 Processing: '{command}'")
            
            # Add user message to context (if enabled)
            if self.use_conversation_context and self.current_session_id:
                self.context_manager.add_message(
                    self.current_session_id,
                    Role.USER,
                    command
                )
            
            # Use dialogue controller for intent parsing (if enabled)
            if self.dialogue_controller and self.current_session_id:
                dialogue_response = self.dialogue_controller.process_input(
                    self.current_session_id,
                    command
                )
                
                logger.info(f"Intent: {dialogue_response.intent.value}, Confidence: {dialogue_response.confidence}")
                
                # Check if clarification is needed
                if dialogue_response.requires_clarification:
                    response = dialogue_response.response_text
                    print(f"🤖 Tỷ Tỷ (clarification): {response}")
                    return response
            
            # Build context-aware prompt
            if self.use_conversation_context and self.current_session_id:
                context = self.context_manager.get_context(self.current_session_id)
                context_dict = {
                    "session_id": context.session_id,
                    "messages": [msg.to_dict() for msg in context.messages],
                    "user_preferences": context.user_preferences
                }
                prompt = self.prompt_builder.build_prompt(context_dict, command)
            else:
                # No context, use simple prompt
                prompt = self.prompt_builder.build_prompt(None, command)
            
            # Get AI response
            response = self.ai.get_response(prompt)
            print(f"🤖 Tỷ Tỷ: {response}")
            
            # Add assistant message to context (if enabled)
            if self.use_conversation_context and self.current_session_id:
                self.context_manager.add_message(
                    self.current_session_id,
                    Role.ASSISTANT,
                    response
                )
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing command: {e}", exc_info=True)
            
            # Handle error with recovery
            context = ErrorContext(
                component="ai_service",
                operation="process_command",
                retry_count=0,
                session_id=self.current_session_id
            )
            recovery_action = self.error_handler.handle_error(e, context)
            
            # Return fallback response
            fallback_response = self.error_handler.get_fallback_response(ErrorType.API_ERROR)
            self.error_handler.notify_user(fallback_response, Severity.ERROR)
            
            return fallback_response
    
    def speak(self, text: str):
        """
        Speak the response with error handling
        
        Args:
            text: Text to speak
        """
        try:
            print(f"🔊 Speaking...")
            self.tts.speak(text)
        except Exception as e:
            logger.error(f"TTS error: {e}")
            
            context = ErrorContext(
                component="text_to_speech",
                operation="speak",
                retry_count=0
            )
            recovery_action = self.error_handler.handle_error(e, context)
            self.error_handler.notify_user(recovery_action.user_message, Severity.WARNING)
    
    def listen_loop(self):
        """Main listening loop with enhanced wake word detection"""
        print("\n🎧 Listening mode started!")
        print("💡 Say 'Tỷ Tỷ' followed by your question")
        print("   Example: 'Tỷ Tỷ 1+1 bằng mấy?'")
        print("   Press Ctrl+C to stop\n")
        
        self.running = True
        
        # Greeting
        greeting = "Xin chào!"
        self.speak(greeting)
        
        # Add greeting to context (if enabled)
        if self.use_conversation_context and self.current_session_id:
            self.context_manager.add_message(
                self.current_session_id,
                Role.ASSISTANT,
                greeting
            )
        
        while self.running:
            try:
                # Listen for speech
                text = self.stt.listen_and_recognize()
                
                if not text:
                    continue
                
                # Detect wake word using enhanced engine or legacy detector
                wake_word_detected = False
                command = None
                
                if self.use_enhanced_wake_word and self.wake_word_engine:
                    # Use enhanced wake word engine
                    result = self.wake_word_engine.detect(text=text)
                    wake_word_detected = result.detected
                    command = result.remaining_command
                    
                    if wake_word_detected:
                        logger.info(f"Wake word detected: {result.keyword}, confidence: {result.confidence}")
                else:
                    # Use legacy detector
                    wake_word_detected, command = self.legacy_detector.check(text)
                
                # Process if wake word detected
                if wake_word_detected:
                    if command:
                        # Wake word + command in same utterance
                        response = self.process_command(command)
                        self.speak(response)
                    else:
                        # Just wake word - check if it's only the wake word
                        is_only_wake_word = False
                        
                        if self.use_enhanced_wake_word and self.wake_word_engine:
                            is_only_wake_word = self.wake_word_engine.is_wake_word_only(text)
                        else:
                            is_only_wake_word = self.legacy_detector.is_just_wake_word(text)
                        
                        if is_only_wake_word:
                            # Just wake word, acknowledge and wait for command
                            ack_response = "Dạ, Tỷ Tỷ nghe đây!"
                            self.speak(ack_response)
                            print("👂 Waiting for command...")
                            
                            # Add acknowledgment to context
                            if self.use_conversation_context and self.current_session_id:
                                self.context_manager.add_message(
                                    self.current_session_id,
                                    Role.ASSISTANT,
                                    ack_response
                                )
                            
                            # Listen for the actual command
                            command = self.stt.listen_and_recognize()
                            if command:
                                response = self.process_command(command)
                                self.speak(response)
                            else:
                                error_msg = "Tỷ Tỷ không nghe rõ. Bạn nói lại được không?"
                                self.speak(error_msg)
                else:
                    # No wake word detected
                    print(f"👀 Heard: '{text}' (no wake word)")
                    
            except KeyboardInterrupt:
                print("\n\n🛑 Stopping...")
                self.running = False
                farewell = "Tạm biệt nhé!"
                self.speak(farewell)
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}", exc_info=True)
                
                context = ErrorContext(
                    component="main_loop",
                    operation="listen_and_process",
                    retry_count=0
                )
                recovery_action = self.error_handler.handle_error(e, context)
                
                # Continue running unless critical error
                if recovery_action.action.value != "skip":
                    self.error_handler.notify_user(
                        "Gặp lỗi, nhưng Tỷ Tỷ vẫn đang nghe...",
                        Severity.WARNING
                    )
                continue
    
    def cleanup(self):
        """Cleanup resources"""
        try:
            print("\n🧹 Cleaning up resources...")
            
            # End conversation session
            if self.use_conversation_context and self.current_session_id:
                try:
                    duration = self.context_manager.get_session_duration(self.current_session_id)
                    logger.info(f"Session duration: {duration:.2f}s")
                    # Note: We don't end the session here to allow persistence
                except Exception as e:
                    logger.error(f"Error getting session duration: {e}")
            
            # Cleanup audio router
            if self.audio_router:
                self.audio_router.cleanup()
            
            # Cleanup VAD if active
            if self.vad and hasattr(self.vad, 'stop_monitoring'):
                try:
                    self.vad.stop_monitoring()
                except:
                    pass
            
            print("✅ Cleanup complete")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def run(self):
        """Start the chatbot"""
        try:
            if self.initialize():
                self.listen_loop()
            else:
                print("\n❌ Failed to start chatbot")
                print("💡 Make sure you have configured the environment properly")
                print("   Check config.py for required settings")
        finally:
            self.cleanup()


def main():
    """Entry point"""
    chatbot = TyTyChatbot()
    chatbot.run()


if __name__ == "__main__":
    main()
