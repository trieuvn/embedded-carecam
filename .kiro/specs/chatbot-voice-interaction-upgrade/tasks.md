# Implementation Plan: Chatbot Voice Interaction Upgrade

## Overview

This implementation plan converts the design document into a series of actionable coding tasks for the "Tỷ Tỷ" Vietnamese voice chatbot upgrade. The plan focuses on enhancing voice interaction capabilities through VAD, enhanced wake word detection, multi-turn conversation support, improved audio pipeline, and robust error handling. All tasks build incrementally and integrate with existing modules (ai_service.py, wake_word.py, speech_to_text.py, text_to_speech.py, carecam_controller.py).

**Implementation Language**: Python

## Tasks

- [x] 1. Set up project foundation and configuration
  - Create new configuration options in config.py for VAD, wake word engine, multi-turn conversations, and error handling
  - Add new environment variables for Ollama service (optional local AI)
  - Update requirements.txt with new dependencies (pvporcupine, webrtcvad, vosk, ollama)
  - Create directory structure for models/ (wake word models) and logs/ (structured logging)
  - _Requirements: 8.3, 8.5, 6.6, 7.6_

- [x] 2. Implement Voice Activity Detection (VAD) module
  - [x] 2.1 Create modules/vad.py with VoiceActivityDetector class
    - Implement energy-based VAD using webrtcvad library
    - Create VADConfig dataclass (energy_threshold, silence_duration, min_speech_duration, sample_rate, frame_length_ms)
    - Implement initialize(), start_monitoring(), stop_monitoring(), is_voice_active(), get_audio_segment() methods
    - Implement adaptive thresholding based on ambient noise level
    - Add event callbacks: on_voice_start, on_voice_end
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7, 10.8, 10.9, 10.10_
  
  - [x] 2.2 Write unit tests for VAD module
    - Test energy calculation accuracy with synthetic audio
    - Test voice start/end detection timing with known audio samples
    - Test silence threshold sensitivity in different noise environments
    - Test adaptive thresholding with varying ambient noise
    - _Requirements: 10.1, 10.4, 10.5_

- [x] 3. Implement Enhanced Wake Word Detection Engine
  - [x] 3.1 Create modules/wake_word_engine.py with WakeWordEngine class
    - Implement Porcupine-based wake word detection using pvporcupine library
    - Create WakeWordResult dataclass (detected, keyword, confidence, timestamp, remaining_command)
    - Implement initialize() to load wake word model from models/ directory
    - Implement detect() method to process audio segments and return WakeWordResult
    - Implement is_wake_word_only() to check if text contains only wake word
    - Implement update_sensitivity() to adjust detection threshold
    - Add fallback to keyword matching (current implementation) if Porcupine unavailable
    - Support multiple wake word variations ("tỷ tỷ", "ty ty", "ti ti")
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 11.6, 11.7, 11.8, 11.9, 11.10_
  
  - [x] 3.2 Write unit tests for Wake Word Engine
    - Test true positive rate with various accents and pronunciations
    - Test false positive rate with similar-sounding words
    - Test command extraction accuracy (remaining_command field)
    - Test multi-variation support (all aliases detected correctly)
    - Test fallback mechanism when Porcupine unavailable
    - _Requirements: 11.4, 11.5, 11.8, 11.9_

- [x] 4. Checkpoint - Ensure VAD and Wake Word tests pass
  - Run all unit tests for VAD and Wake Word modules
  - Verify VAD detects voice activity in test audio samples
  - Verify Wake Word Engine detects "Tỷ Tỷ" with acceptable accuracy
  - Ask the user if questions arise

- [ ] 5. Implement Conversation Context Manager
  - [-] 5.1 Create modules/context_manager.py with ConversationContextManager class
    - Create ConversationContext dataclass (session_id, messages, user_preferences, session_start, last_activity, metadata)
    - Create Message dataclass (role, content, timestamp, metadata)
    - Implement create_session() to generate unique session ID and initialize context
    - Implement add_message() to append user/assistant messages to conversation history
    - Implement get_context() to retrieve conversation history with sliding window (last N turns)
    - Implement clear_context() to delete conversation history for privacy
    - Implement get_session_duration() to calculate active session time
    - Implement set_user_preference() and get_user_preference() for user settings
    - Implement automatic session cleanup (expire after 30 minutes inactivity)
    - Use in-memory storage with optional persistence to disk (JSON file in logs/)
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.6, 12.7, 12.8, 12.9, 12.10, 12.11, 12.12_
  
  - [-] 5.2 Write unit tests for Context Manager
    - Test session creation and unique ID generation
    - Test message storage and retrieval
    - Test sliding window with max_turns constraint
    - Test session expiration after inactivity timeout
    - Test user preference storage and retrieval
    - Test context clearing for privacy
    - _Requirements: 12.1, 12.4, 12.6, 12.7, 12.9_

- [ ] 6. Implement Multi-Turn Dialogue Controller
  - [-] 6.1 Create modules/dialogue_controller.py with DialogueController class
    - Create DialogueResponse dataclass (response_text, should_continue, intent, confidence, requires_clarification, suggested_followups)
    - Create DialogueState dataclass (current_intent, slot_values, confirmation_pending, clarification_needed, turn_count)
    - Implement initialize() accepting ConversationContextManager instance
    - Implement process_input() to parse user input, identify intent, extract entities
    - Support intents: QUESTION_ANSWERING, CALCULATION, WEATHER_QUERY, CAMERA_CONTROL, SMALL_TALK, CLARIFICATION_REQUEST, UNKNOWN
    - Implement dialogue pattern support: single-turn, multi-turn, slot-filling, clarification, confirmation
    - Implement should_continue_listening() to determine if conversation should continue
    - Implement reset_dialogue_state() to clear current dialogue state
    - Implement get_dialogue_state() to retrieve current dialogue state
    - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5, 13.6, 13.7, 13.8, 13.9, 13.10, 13.11, 13.12, 13.13, 13.14_
  
  - [-] 6.2 Write unit tests for Dialogue Controller
    - Test intent classification accuracy for different query types
    - Test multi-turn state management (follow-up questions without wake word)
    - Test slot-filling pattern (progressive information gathering)
    - Test clarification handling (missing/ambiguous information)
    - Test should_continue_listening() logic for different scenarios
    - _Requirements: 13.4, 13.5, 13.8, 13.9, 13.10, 13.12_

- [x] 7. Implement Context-Aware Prompt Builder
  - [x] 7.1 Create modules/prompt_builder.py with PromptBuilder class
    - Create ResponseMode enum (CONCISE, DETAILED, CONVERSATIONAL, TECHNICAL)
    - Implement initialize() accepting system_prompt string
    - Implement build_prompt() to combine system prompt, conversation history, user preferences, and current input
    - Format prompts according to Gemini API requirements
    - Implement set_response_mode() to adjust response style
    - Implement estimate_token_count() to estimate token usage (approximate)
    - Implement optimize_context_window() to truncate old messages when exceeding token limit
    - Preserve most recent messages when truncating
    - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5, 14.6, 14.7, 14.8, 14.9, 14.10, 14.11_
  
  - [x] 7.2 Write unit tests for Prompt Builder
    - Test prompt structure includes all required sections (system, context, input)
    - Test ResponseMode variations produce different prompt formats
    - Test token estimation accuracy (within 10% margin)
    - Test context window optimization preserves most recent messages
    - Test truncation logic when exceeding token limit
    - _Requirements: 14.3, 14.5, 14.7, 14.8, 14.9_

- [x] 8. Checkpoint - Ensure conversation management tests pass
  - Run all unit tests for Context Manager, Dialogue Controller, and Prompt Builder
  - Verify conversation context is maintained across multiple turns
  - Verify prompt builder generates valid prompts for Gemini API
  - Ask the user if questions arise

- [ ] 9. Implement Error Handler and Recovery System
  - [-] 9.1 Create modules/error_handler.py with ErrorHandler class
    - Create ErrorContext dataclass (component, operation, retry_count, session_id, timestamp)
    - Create RecoveryAction dataclass (action, fallback_component, retry_delay, user_message)
    - Create ErrorType enum (NETWORK_ERROR, API_ERROR, AUDIO_CAPTURE_ERROR, RECOGNITION_ERROR, TTS_ERROR, UNKNOWN_ERROR)
    - Create RecoveryActionType enum (RETRY, FALLBACK, SKIP, RESTART_COMPONENT, NOTIFY_USER)
    - Implement register_component() to register components with health checks
    - Implement handle_error() to categorize errors and return appropriate RecoveryAction
    - Implement error recovery strategies: retry with exponential backoff, fallback to alternative services
    - Implement log_error() with severity levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    - Implement get_fallback_response() for each error type
    - Implement notify_user() to generate user-friendly Vietnamese error messages
    - _Requirements: 15.1, 15.2, 15.3, 15.4, 15.5, 15.6, 15.7, 15.8, 15.9, 15.10, 15.11, 15.12, 15.13, 15.14, 15.15_
  
  - [-] 9.2 Write unit tests for Error Handler
    - Test error categorization for different error types
    - Test retry logic with exponential backoff timing
    - Test fallback activation when retries exhausted
    - Test user notification message generation in Vietnamese
    - Test recovery action selection for each error scenario
    - _Requirements: 15.5, 15.6, 15.7, 15.13, 15.14_

- [ ] 10. Implement Audio Router and Mode Controller
  - [x] 10.1 Create modules/audio_router.py with AudioRouter class
    - Create AudioConfig dataclass (operation_mode, sample_rate, channels, buffer_size, virtual_cable_enabled)
    - Create OperationMode enum (BASIC_MODE, FULL_AUTOMATION_MODE, HYBRID_MODE)
    - Create AudioDevice dataclass (device_id, name, device_type, is_virtual, sample_rate, channels)
    - Create DeviceType enum (MICROPHONE, SPEAKER, VIRTUAL_CABLE_INPUT, VIRTUAL_CABLE_OUTPUT, RTSP_STREAM)
    - Implement initialize() to detect and enumerate audio devices
    - Implement set_mode() to switch between operation modes
    - Implement get_input_device() and get_output_device() to return current devices
    - Implement list_available_devices() to enumerate all audio devices
    - Implement test_audio_path() to validate audio routing before conversation start
    - Handle device disconnection/reconnection gracefully
    - _Requirements: 16.1, 16.2, 16.3, 16.4, 16.5, 16.6, 16.7, 16.8, 16.9, 16.10, 16.11, 16.12, 16.13, 16.14, 16.15_
  
  - [-] 10.2 Write unit tests for Audio Router
    - Test device enumeration includes physical and virtual devices
    - Test mode switching between BASIC, FULL_AUTOMATION, and HYBRID
    - Test audio device detection (microphone, speaker, VB-Cable)
    - Test audio path validation with test_audio_path()
    - Test graceful handling of device disconnection
    - _Requirements: 16.4, 16.5, 16.6, 16.7, 16.13, 16.14_

- [ ] 11. Implement Ollama Local AI Service (optional enhancement)
  - [x] 11.1 Create modules/ollama_service.py with OllamaService class
    - Implement connection to Ollama server running locally
    - Use "qwen2.5:0.5b" model (lightweight for CPU)
    - Implement get_response() method matching ai_service interface
    - Implement test_connection() to verify Ollama availability
    - Implement timeout and connection error handling
    - Use same system prompt as Gemini for consistency
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.10, 6.11_
  
  - [-] 11.2 Update modules/ai_service.py to support service selection
    - Add configuration option to select AI service: "ollama", "gemini", or "auto"
    - Implement auto mode: try Ollama first, fallback to Gemini if unavailable
    - Maintain backward compatibility with existing Gemini integration
    - _Requirements: 6.1, 6.6, 6.7, 6.8, 6.9_
  
  - [-] 11.3 Write integration tests for AI service switching
    - Test Ollama service connection and response generation
    - Test fallback from Ollama to Gemini when Ollama unavailable
    - Test "auto" mode selects appropriate service
    - Test response consistency between Ollama and Gemini
    - _Requirements: 6.4, 6.9, 6.11_

- [x] 12. Checkpoint - Ensure error handling and audio routing tests pass
  - Run all unit tests for Error Handler and Audio Router
  - Verify error recovery strategies work correctly
  - Verify audio device enumeration detects physical and virtual devices
  - Ask the user if questions arise

- [ ] 13. Implement UI Configuration Tool for button positions
  - [x] 13.1 Create ui_config_tool.py with GUI for button position configuration
    - Create window with Tkinter displaying camera view overlay
    - Add "Select Mic Button Position" and "Select Speaker Button Position" buttons
    - Implement click-to-capture position functionality for mic and speaker buttons
    - Implement "Save Configuration" to write JSON file (position_config.json) with mic_button_x, mic_button_y, speaker_button_x, speaker_button_y
    - Implement "Test Mic Position" and "Test Speaker Position" buttons to validate saved positions
    - Load existing position_config.json if available and display saved values
    - Create default position values if config file doesn't exist
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9_
  
  - [-] 13.2 Integrate position config into CareCam controller
    - Update modules/carecam_controller.py to read position_config.json on initialization
    - Use loaded coordinates instead of calculated relative positions
    - Fallback to default/relative positions if position_config.json doesn't exist
    - Implement retry logic (up to 3 attempts) for button clicks
    - Log each button click and state transition
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 4.2, 4.3_
  
  - [-] 13.3 Write tests for UI config tool
    - Test position config file creation with default values
    - Test position config file loading when file exists
    - Test position validation (coordinates within screen bounds)
    - Test button click retry logic in CareCam controller
    - _Requirements: 1.4, 1.6, 2.1, 2.2, 4.5_

- [ ] 14. Implement CareCam SDK Integration Layer (advanced enhancement)
  - [x] 14.1 Create modules/carecam_sdk_adapter.py with CareCamSDKAdapter class
    - Create CameraConfig dataclass (ip_address, port, username, password, rtsp_enabled)
    - Create CameraStatus dataclass (connected, mic_active, speaker_active, signal_quality)
    - Implement initialize() to load qianxin_sdk.dll using ctypes
    - Implement connect_camera() to establish camera connection via SDK
    - Implement enable_microphone() and disable_microphone() for programmatic mic control
    - Implement is_microphone_active() to query mic status
    - Implement get_camera_status() to retrieve camera connection and device status
    - Implement play_audio_to_camera() to stream audio to camera speaker
    - Implement on_camera_audio_received() event callback for receiving audio from camera
    - Implement reconnection logic and SDK error handling
    - Fallback to UI automation (CareCam_Controller) if SDK unavailable
    - _Requirements: 17.1, 17.2, 17.3, 17.4, 17.5, 17.6, 17.7, 17.8, 17.9, 17.10, 17.11, 17.12, 17.13, 17.14, 17.15, 17.16_
  
  - [-] 14.2 Write integration tests for SDK adapter
    - Test SDK initialization and DLL loading
    - Test camera connection establishment
    - Test mic enable/disable programmatic control
    - Test audio streaming to camera speaker
    - Test fallback to UI automation when SDK unavailable
    - _Requirements: 17.2, 17.3, 17.5, 17.6, 17.10, 17.16_

- [ ] 15. Implement new Conversation Manager with state machine
  - [x] 15.1 Create modules/conversation_manager.py with ConversationManager class
    - Create ConversationState enum (DEFAULT_STATE, SPEAKING_STATE, LISTENING_STATE)
    - Implement state machine managing mic/speaker states respecting hardware constraint
    - Implement transition logic: DEFAULT → SPEAKING (wake word detected) → LISTENING (after "Dạ") → SPEAKING (after processing) → DEFAULT
    - Implement ensure_mic_speaker_exclusivity() to prevent mic and speaker being on simultaneously
    - Implement timeout logic for silence detection (3 seconds) during LISTENING_STATE
    - Implement get_current_state() and force_default_state() methods
    - Log all state transitions with timestamps
    - Integrate with CareCam_Controller for mic/speaker button clicks
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 3.10, 3.11, 3.12, 3.13, 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8_
  
  - [x] 15.2 Implement silence detection and timeout logic
    - Monitor audio level during LISTENING_STATE
    - Detect silence when audio energy below SILENCE_THRESHOLD for 3 seconds
    - Implement MAX_RECORDING_DURATION timeout (10 seconds) for safety
    - Send audio to STT when silence detected or timeout reached
    - Play timeout message if no audio detected: "Tỷ Tỷ không nghe rõ. Bạn nói lại được không?"
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.7_
  
  - [-] 15.3 Write unit tests for Conversation Manager
    - Test state transitions follow correct sequence
    - Test mic/speaker exclusivity constraint (never both on)
    - Test silence detection triggers after 3 seconds
    - Test timeout logic after 10 seconds of no audio
    - Test state reset to DEFAULT after errors
    - _Requirements: 3.11, 3.12, 3.13, 4.1, 5.2, 5.6_

- [x] 16. Checkpoint - Ensure conversation manager and UI tools work correctly
  - Run all unit tests for Conversation Manager and UI config tool
  - Test UI config tool manually to capture button positions
  - Verify Conversation Manager state transitions work correctly
  - Ask the user if questions arise

- [ ] 17. Integrate all components into main.py
  - [x] 17.1 Refactor main.py to use new architecture
    - Initialize VAD, WakeWordEngine, ContextManager, DialogueController, PromptBuilder, ErrorHandler, AudioRouter
    - Replace simple wake word detection with VAD + WakeWordEngine pipeline
    - Replace single-turn logic with multi-turn DialogueController
    - Integrate ConversationManager for state management
    - Use PromptBuilder to create context-aware prompts for AI
    - Implement error handling with ErrorHandler for all components
    - Configure AudioRouter based on operation mode (BASIC/FULL_AUTOMATION/HYBRID)
    - Maintain backward compatibility: allow disabling new features via config flags
    - _Requirements: 8.1, 8.2, 8.4, 8.6_
  
  - [-] 17.2 Update configuration in config.py with new options
    - Add VAD configuration (VAD_ENABLED, VAD_ENERGY_THRESHOLD, VAD_SILENCE_DURATION)
    - Add wake word configuration (WAKE_WORD_ENGINE, WAKE_WORD_SENSITIVITY)
    - Add conversation configuration (ENABLE_MULTI_TURN, MAX_CONTEXT_TURNS, SESSION_TIMEOUT_MINUTES)
    - Add response mode configuration (RESPONSE_MODE)
    - Add error handling configuration (MAX_RETRIES, ENABLE_FALLBACKS)
    - Add Ollama configuration (AI_SERVICE, OLLAMA_URL)
    - Set default values for all new features (disabled by default for safe migration)
    - _Requirements: 8.3, 8.5_
  
  - [x] 17.3 Implement graceful degradation and fallback mechanisms
    - If Porcupine unavailable, fallback to keyword-based wake word detection
    - If Ollama unavailable, fallback to Gemini
    - If VB-Cable not installed, switch to BASIC_MODE automatically
    - If CareCam SDK unavailable, use UI automation (CareCam_Controller)
    - Display informative messages when fallbacks are activated
    - _Requirements: 8.7, 11.9, 17.16_

- [ ] 18. Integration and end-to-end testing
  - [-] 18.1 Write end-to-end integration tests
    - Test complete voice pipeline: VAD → Wake Word → STT → Dialogue Controller → AI → TTS
    - Test multi-turn conversation: first turn with wake word, second turn without wake word
    - Test error recovery: disconnect network during AI call, verify retry and fallback
    - Test mode switching: switch from BASIC to FULL_AUTOMATION mode without dropping audio
    - Test CareCam SDK integration: send audio command to camera, verify mic activation
    - _Requirements: 8.4, 13.2, 13.3, 13.4, 13.5, 15.6, 15.7_
  
  - [x] 18.2 Perform manual testing with real audio devices
    - Test wake word detection with various pronunciations and accents
    - Test multi-turn conversations in noisy environments
    - Test timeout logic with long pauses between speech
    - Test error scenarios: network disconnection, API rate limiting
    - Test UI config tool to capture button positions on real CareCam app
    - Validate performance meets latency requirements (<4s end-to-end)
    - _Requirements: 9.1, 9.2, 18.1, 18.2, 18.3, 18.4, 18.5_

- [ ] 19. Documentation and deployment preparation
  - [-] 19.1 Update README.md with installation and setup instructions
    - Add section for installing Ollama (optional): "ollama pull qwen2.5:0.5b"
    - Add section for wake word model setup: download Vietnamese Porcupine model
    - Add section for VB-Cable installation (for full automation mode)
    - Add section for CareCam SDK setup (advanced users)
    - Add troubleshooting guide for common issues
    - Add configuration guide explaining all new config options
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6_
  
  - [-] 19.2 Create testing utilities and scripts
    - Create test script for VAD: python -m modules.vad --test
    - Create test script for Wake Word Engine: python -m modules.wake_word_engine --test
    - Create test script for Conversation Manager: python -m modules.conversation_manager --test
    - Create test script for Ollama connection: python -m modules.ollama_service --test
    - Create UI config tool test mode: python ui_config_tool.py --test
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7_
  
  - [x] 19.3 Set up logging and monitoring
    - Create structured logging configuration (logs/tyty_main.log, logs/tyty_errors.log, logs/tyty_audio.log)
    - Implement log rotation to prevent disk space issues
    - Add performance metrics logging: wake word accuracy, STT latency, AI response time
    - Add error rate tracking by component
    - Create log analysis scripts for debugging
    - _Requirements: 19.1, 19.2, 19.3_

- [x] 20. Final validation and checkpoint
  - Run complete test suite (unit + integration tests)
  - Verify all features work with default configuration
  - Verify backward compatibility: system works without enabling new features
  - Verify graceful degradation: system works when optional dependencies unavailable
  - Test performance meets requirements: <4s end-to-end latency, <200MB memory baseline
  - Ask the user for final review and approval

## Notes

- Tasks marked with `*` are optional testing tasks and can be skipped for faster MVP
- Each task references specific requirements from requirements.md for traceability
- Checkpoints ensure incremental validation and allow course correction
- All components maintain backward compatibility with existing modules
- Default configuration disables new features for safe migration
- Fallback mechanisms ensure system availability during partial failures
- Python is used as the implementation language throughout
- Property-based testing is not included as this is primarily an integration and orchestration system rather than pure algorithmic code

## Task Dependency Graph

```json
{
  "waves": [
    {
      "id": 0,
      "tasks": ["1"]
    },
    {
      "id": 1,
      "tasks": ["2.1", "3.1"]
    },
    {
      "id": 2,
      "tasks": ["2.2", "3.2"]
    },
    {
      "id": 3,
      "tasks": ["5.1", "6.1", "7.1"]
    },
    {
      "id": 4,
      "tasks": ["5.2", "6.2", "7.2"]
    },
    {
      "id": 5,
      "tasks": ["9.1", "10.1"]
    },
    {
      "id": 6,
      "tasks": ["9.2", "10.2", "11.1"]
    },
    {
      "id": 7,
      "tasks": ["11.2", "13.1"]
    },
    {
      "id": 8,
      "tasks": ["11.3", "13.2", "14.1"]
    },
    {
      "id": 9,
      "tasks": ["13.3", "14.2", "15.1"]
    },
    {
      "id": 10,
      "tasks": ["15.2"]
    },
    {
      "id": 11,
      "tasks": ["15.3", "17.1"]
    },
    {
      "id": 12,
      "tasks": ["17.2", "17.3"]
    },
    {
      "id": 13,
      "tasks": ["18.1", "18.2"]
    },
    {
      "id": 14,
      "tasks": ["19.1", "19.2", "19.3"]
    }
  ]
}
```
