# Requirements Document

## Introduction

Hệ thống chatbot CareCam hiện tại sử dụng AI service bên ngoài (Google Gemini) và có luồng hội thoại đơn giản. Dự án nâng cấp này nhằm cải thiện trải nghiệm người dùng thông qua các tính năng chính sau:

1. **Công cụ cấu hình vị trí nút UI** - Cho phép người dùng tùy chỉnh vị trí các nút điều khiển mic/loa trên giao diện camera
2. **Logic conversation flow mới** - Cải tiến luồng hội thoại với wake word detection, timeout logic và quản lý trạng thái mic/loa phù hợp với ràng buộc phần cứng camera
3. **Chuyển đổi AI Model** - Thay thế Google Gemini bằng Ollama local để xử lý offline và giảm độ trễ
4. **Voice Activity Detection (VAD)** - Phát hiện voice activity để tối ưu hóa processing và giảm false wake word triggers
5. **Enhanced Wake Word Detection** - Sử dụng Porcupine acoustic model thay vì keyword matching đơn giản
6. **Multi-Turn Conversation Support** - Hỗ trợ hội thoại nhiều lượt với conversation context management
7. **Context-Aware AI Prompts** - Xây dựng prompts thông minh dựa trên conversation history và user preferences
8. **Error Handling và Recovery** - Xử lý lỗi gracefully với fallback strategies và recovery mechanisms
9. **Audio Routing Management** - Quản lý flexible audio routing giữa các devices và operation modes
10. **CareCam SDK Integration** - Tích hợp trực tiếp với CareCam SDK thay vì UI automation

**Ràng buộc phần cứng quan trọng**: Camera QianXin có ràng buộc phần cứng đặc biệt - khi loa bật thì mic tự động tắt, khi mic bật thì loa tự động tắt. Logic conversation flow phải tuân thủ ràng buộc này.

**Mục tiêu nâng cấp**: Hệ thống mới sẽ cung cấp trải nghiệm conversation tự nhiên hơn với khả năng nhớ context, xử lý multi-turn dialogues, phát hiện wake word chính xác hơn, và error recovery robust. Đồng thời duy trì backward compatibility với các modules hiện có.

## Glossary

- **Chatbot**: Hệ thống trợ lý AI điều khiển bằng giọng nói cho camera CareCam
- **Camera**: Camera QianXin được điều khiển qua app CareCam (QianXin.exe)
- **UI_Config_Tool**: Công cụ Python với giao diện cửa sổ cho phép cấu hình vị trí nút mic/loa
- **Position_Config_File**: File JSON lưu trữ tọa độ vị trí nút mic và loa
- **Conversation_Manager**: Module quản lý luồng hội thoại và trạng thái mic/loa
- **Wake_Word_Detector**: Module phát hiện từ kích hoạt "Tỷ Tỷ" (legacy keyword matching)
- **Wake_Word_Engine**: Module nâng cao phát hiện wake word sử dụng acoustic model (Porcupine)
- **VAD_Module**: Voice Activity Detection module phát hiện voice vs. silence
- **Context_Manager**: Module quản lý conversation history và context across multiple turns
- **Dialogue_Controller**: Module orchestrating multi-turn conversations với state management
- **Prompt_Builder**: Module xây dựng context-aware prompts cho AI
- **Error_Handler**: Module xử lý errors với fallback strategies và recovery mechanisms
- **Audio_Router**: Module quản lý audio routing giữa các devices và operation modes
- **CareCam_SDK_Adapter**: Module tích hợp CareCam SDK để điều khiển camera programmatically
- **Ollama_Service**: Service AI chạy local thay thế Google Gemini
- **AI_Service**: Interface tổng quát cho các AI service (Gemini hoặc Ollama)
- **Mic_Button**: Nút trong app CareCam để bật mic (chatbot nói với camera)
- **Speaker_Button**: Nút trong app CareCam để bật loa (chatbot nghe từ camera)
- **Default_State**: Trạng thái mặc định của hệ thống (loa bật, mic tắt - đang nghe)
- **Speaking_State**: Trạng thái khi chatbot đang trả lời (mic bật, loa tắt)
- **Listening_State**: Trạng thái khi chatbot đang thu giọng nói người dùng (loa bật, mic tắt)
- **Silence_Timeout**: Khoảng thời gian im lặng (3 giây) để kết thúc việc thu âm và xử lý yêu cầu
- **CareCam_Controller**: Module hiện có điều khiển app CareCam qua pyautogui (UI automation)
- **SessionID**: Unique identifier cho conversation session
- **ConversationContext**: Object chứa conversation history, preferences, và metadata
- **DialogueState**: Object chứa current intent, slot values, và dialogue flow state
- **AudioSegment**: Object chứa audio data với timestamp và metadata
- **WakeWordResult**: Object chứa kết quả wake word detection với confidence score
- **RecoveryAction**: Object định nghĩa action để recover from errors
- **AudioDevice**: Object representing physical hoặc virtual audio device
- **CameraStatus**: Object chứa camera connection và device status
- **OperationMode**: Mode hoạt động của hệ thống (BASIC_MODE, FULL_AUTOMATION_MODE, HYBRID_MODE)
- **ResponseMode**: Style của AI response (CONCISE, DETAILED, CONVERSATIONAL, TECHNICAL)

## Requirements

### Requirement 1: Công cụ cấu hình vị trí nút UI

**User Story:** As a người dùng hệ thống, I want công cụ để cấu hình vị trí nút mic và loa trên màn hình camera, so that hệ thống có thể điều khiển chính xác các nút này trên các thiết bị khác nhau

#### Acceptance Criteria

1. THE UI_Config_Tool SHALL hiển thị cửa sổ với giao diện cho phép chọn vị trí nút
2. WHEN người dùng click "Select Mic Button Position", THE UI_Config_Tool SHALL cho phép người dùng click vào vị trí nút mic trên màn hình
3. WHEN người dùng click "Select Speaker Button Position", THE UI_Config_Tool SHALL cho phép người dùng click vào vị trí nút loa trên màn hình
4. WHEN người dùng click "Save Configuration", THE UI_Config_Tool SHALL lưu tọa độ vị trí vào Position_Config_File dưới định dạng JSON
5. THE Position_Config_File SHALL chứa các trường: mic_button_x, mic_button_y, speaker_button_x, speaker_button_y
6. WHEN Position_Config_File không tồn tại, THE UI_Config_Tool SHALL tạo file mới với giá trị mặc định
7. WHEN Position_Config_File tồn tại, THE UI_Config_Tool SHALL hiển thị các giá trị đã lưu
8. THE UI_Config_Tool SHALL cung cấp nút "Test Mic Position" để kiểm tra vị trí nút mic
9. THE UI_Config_Tool SHALL cung cấp nút "Test Speaker Position" để kiểm tra vị trí nút loa

### Requirement 2: Tích hợp Position Config vào hệ thống chính

**User Story:** As a hệ thống chatbot, I want nạp cấu hình vị trí nút từ Position_Config_File khi khởi động, so that có thể điều khiển đúng vị trí nút mic và loa

#### Acceptance Criteria

1. WHEN Chatbot khởi động, THE Chatbot SHALL đọc Position_Config_File
2. IF Position_Config_File không tồn tại, THEN THE Chatbot SHALL sử dụng giá trị mặc định từ CareCam_Controller
3. WHEN Position_Config_File được đọc thành công, THE Chatbot SHALL cập nhật tọa độ nút trong CareCam_Controller
4. THE CareCam_Controller SHALL sử dụng tọa độ từ Position_Config_File thay vì tính toán tương đối
5. WHEN CareCam_Controller click nút mic, THE CareCam_Controller SHALL click đúng tọa độ mic_button_x và mic_button_y
6. WHEN CareCam_Controller click nút loa, THE CareCam_Controller SHALL click đúng tọa độ speaker_button_x và speaker_button_y

### Requirement 3: Logic Conversation Flow mới

**User Story:** As a người dùng, I want hệ thống hoạt động với luồng hội thoại tự nhiên tuân thủ ràng buộc phần cứng camera, so that có thể tương tác dễ dàng với chatbot

#### Acceptance Criteria

1. THE Conversation_Manager SHALL duy trì Default_State với loa bật và mic tắt
2. WHEN Wake_Word_Detector phát hiện "Tỷ Tỷ", THE Conversation_Manager SHALL chuyển sang Speaking_State
3. WHILE Conversation_Manager ở Speaking_State, THE Conversation_Manager SHALL bật mic và tắt loa
4. WHEN Conversation_Manager ở Speaking_State, THE Chatbot SHALL phát câu trả lời "Dạ"
5. WHEN câu trả lời "Dạ" kết thúc, THE Conversation_Manager SHALL chuyển sang Listening_State
6. WHILE Conversation_Manager ở Listening_State, THE Conversation_Manager SHALL bật loa và tắt mic
7. WHEN Conversation_Manager ở Listening_State, THE Chatbot SHALL thu âm giọng nói người dùng
8. WHEN im lặng trong Silence_Timeout (3 giây) ở Listening_State, THE Conversation_Manager SHALL xử lý yêu cầu đã thu được
9. WHEN xử lý yêu cầu hoàn tất, THE Conversation_Manager SHALL chuyển sang Speaking_State để phát câu trả lời
10. WHEN phát câu trả lời hoàn tất, THE Conversation_Manager SHALL quay về Default_State
11. THE Conversation_Manager SHALL đảm bảo mic và loa không bật đồng thời
12. WHEN chuyển từ Speaking_State sang Listening_State, THE Conversation_Manager SHALL tắt mic trước khi bật loa
13. WHEN chuyển từ Listening_State sang Speaking_State, THE Conversation_Manager SHALL tắt loa trước khi bật mic

### Requirement 4: Quản lý trạng thái Mic và Loa

**User Story:** As a Conversation_Manager, I want quản lý trạng thái mic và loa tuân thủ ràng buộc phần cứng, so that tránh xung đột phần cứng camera

#### Acceptance Criteria

1. THE Conversation_Manager SHALL duy trì biến trạng thái hiện tại (Default_State, Speaking_State, Listening_State)
2. WHEN bật mic, THE Conversation_Manager SHALL gọi CareCam_Controller để click Mic_Button
3. WHEN bật loa, THE Conversation_Manager SHALL gọi CareCam_Controller để click Speaker_Button
4. THE Conversation_Manager SHALL ghi log mỗi lần chuyển trạng thái
5. IF CareCam_Controller thất bại khi click nút, THEN THE Conversation_Manager SHALL thử lại tối đa 3 lần
6. IF thử lại 3 lần thất bại, THEN THE Conversation_Manager SHALL ghi log lỗi và quay về Default_State
7. THE Conversation_Manager SHALL cung cấp method get_current_state() trả về trạng thái hiện tại
8. THE Conversation_Manager SHALL cung cấp method force_default_state() để reset về Default_State

### Requirement 5: Timeout Logic cho việc thu âm

**User Story:** As a Chatbot, I want phát hiện khi người dùng ngừng nói, so that có thể xử lý yêu cầu kịp thời

#### Acceptance Criteria

1. THE Conversation_Manager SHALL theo dõi mức âm thanh trong Listening_State
2. WHEN mức âm thanh dưới SILENCE_THRESHOLD trong Silence_Timeout (3 giây), THE Conversation_Manager SHALL kết thúc thu âm
3. THE Conversation_Manager SHALL sử dụng thuật toán phát hiện im lặng từ audio stream
4. WHEN thu âm kết thúc, THE Conversation_Manager SHALL gửi audio đến Speech_To_Text service
5. WHEN Speech_To_Text trả về text, THE Conversation_Manager SHALL gửi text đến AI_Service
6. IF không có âm thanh trong MAX_RECORDING_DURATION (10 giây), THEN THE Conversation_Manager SHALL timeout và quay về Default_State
7. WHEN timeout xảy ra, THE Chatbot SHALL phát câu "Tỷ Tỷ không nghe rõ. Bạn nói lại được không?"

### Requirement 6: Chuyển đổi sang Ollama Local AI

**User Story:** As a hệ thống, I want sử dụng Ollama local thay vì Google Gemini, so that có thể xử lý offline và giảm độ trễ

#### Acceptance Criteria

1. THE AI_Service SHALL cung cấp interface chung cho cả Google Gemini và Ollama_Service
2. THE Ollama_Service SHALL kết nối đến Ollama server chạy local
3. THE Ollama_Service SHALL sử dụng model "qwen2.5:0.5b" (lightest model for CPU)
4. WHEN Ollama_Service không thể kết nối, THE AI_Service SHALL fallback sang Google Gemini
5. THE Ollama_Service SHALL có response time dưới 2 giây cho câu trả lời ngắn (dưới 50 từ)
6. THE AI_Service SHALL cho phép cấu hình chọn service (Ollama hoặc Gemini) trong config.py
7. WHEN cấu hình là "ollama", THE AI_Service SHALL sử dụng Ollama_Service
8. WHEN cấu hình là "gemini", THE AI_Service SHALL sử dụng Google Gemini
9. WHEN cấu hình là "auto", THE AI_Service SHALL thử Ollama trước, nếu thất bại thì dùng Gemini
10. THE Ollama_Service SHALL sử dụng cùng system prompt với Gemini để đảm bảo tính nhất quán
11. THE Ollama_Service SHALL xử lý lỗi timeout và connection error một cách graceful

### Requirement 7: Cài đặt và cấu hình Ollama

**User Story:** As a người cài đặt hệ thống, I want hướng dẫn cài đặt Ollama, so that có thể chạy AI local

#### Acceptance Criteria

1. THE README.md SHALL chứa hướng dẫn cài đặt Ollama
2. THE README.md SHALL chứa lệnh tải model: "ollama pull qwen2.5:0.5b"
3. THE README.md SHALL chứa lệnh kiểm tra Ollama: "ollama list"
4. THE README.md SHALL chứa hướng dẫn khởi động Ollama service
5. THE README.md SHALL giải thích cách chọn giữa Ollama và Gemini trong config.py
6. THE requirements.txt SHALL chứa package "ollama" để tích hợp với Ollama API

### Requirement 8: Tương thích ngược với hệ thống hiện tại

**User Story:** As a developer, I want hệ thống mới tương thích với code hiện có, so that không phá vỡ chức năng đã có

#### Acceptance Criteria

1. THE Conversation_Manager SHALL sử dụng các module hiện có: Wake_Word_Detector, Speech_To_Text, Text_To_Speech
2. THE CareCam_Controller SHALL mở rộng class hiện có thay vì tạo class mới
3. WHEN Position_Config_File không tồn tại, THE CareCam_Controller SHALL hoạt động như cũ với tính toán tương đối
4. THE main.py SHALL tích hợp Conversation_Manager thay vì logic đơn giản hiện tại
5. THE config.py SHALL giữ nguyên các cấu hình hiện có và thêm cấu hình mới
6. THE AI_Service interface SHALL cho phép thay thế implementation mà không ảnh hưởng code khác
7. WHEN Ollama không khả dụng, THE Chatbot SHALL hoạt động bình thường với Gemini

### Requirement 9: Testing và Validation

**User Story:** As a developer, I want công cụ test các thành phần, so that đảm bảo hệ thống hoạt động đúng

#### Acceptance Criteria

1. THE UI_Config_Tool SHALL cung cấp chế độ test để kiểm tra vị trí nút
2. THE Conversation_Manager SHALL cung cấp method test_state_transitions() để test chuyển trạng thái
3. THE Ollama_Service SHALL cung cấp method test_connection() để kiểm tra kết nối
4. WHEN chạy "python ui_config_tool.py --test", THE UI_Config_Tool SHALL hiển thị vị trí nút hiện tại
5. WHEN chạy "python -m modules.conversation_manager", THE Conversation_Manager SHALL chạy test state machine
6. WHEN chạy "python -m modules.ollama_service", THE Ollama_Service SHALL test kết nối và tạo response mẫu
7. THE test scripts SHALL ghi log chi tiết để debug

### Requirement 10: Voice Activity Detection (VAD)

**User Story:** As a hệ thống chatbot, I want phát hiện khi người dùng đang nói hay im lặng, so that giảm false wake word triggers và tối ưu hóa xử lý âm thanh

#### Acceptance Criteria

1. THE VAD_Module SHALL khởi tạo với cấu hình energy_threshold, silence_duration, min_speech_duration, sample_rate
2. WHEN VAD_Module bắt đầu monitoring, THE VAD_Module SHALL nhận audio stream từ audio source
3. THE VAD_Module SHALL tính short-term energy của audio frames
4. WHEN audio energy vượt threshold, THE VAD_Module SHALL phát event on_voice_start
5. WHEN audio energy dưới threshold trong silence_duration, THE VAD_Module SHALL phát event on_voice_end
6. THE VAD_Module SHALL áp dụng adaptive thresholding dựa trên ambient noise level
7. THE VAD_Module SHALL cung cấp method is_voice_active() trả về trạng thái hiện tại
8. WHEN voice detected, THE VAD_Module SHALL cung cấp audio segment qua method get_audio_segment()
9. THE VAD_Module SHALL lọc non-speech audio để giảm false wake word triggers
10. THE VAD_Module SHALL support configurable thresholds cho các môi trường noise khác nhau

### Requirement 11: Enhanced Wake Word Detection với Porcupine

**User Story:** As a hệ thống chatbot, I want phát hiện "Tỷ Tỷ" wake word chính xác bằng acoustic model, so that cải thiện độ chính xác và giảm false positives

#### Acceptance Criteria

1. THE Wake_Word_Engine SHALL khởi tạo với model_path và sensitivity parameter
2. THE Wake_Word_Engine SHALL load Porcupine acoustic model từ model_path
3. THE Wake_Word_Engine SHALL support multiple wake word variations: "tỷ tỷ", "ty ty", "ti ti"
4. WHEN Wake_Word_Engine nhận audio segment, THE Wake_Word_Engine SHALL detect wake word và trả về WakeWordResult
5. THE WakeWordResult SHALL chứa: detected (Boolean), keyword (String), confidence (Float), timestamp, remaining_command
6. WHEN wake word detected, THE Wake_Word_Engine SHALL extract command text sau wake word
7. THE Wake_Word_Engine SHALL cung cấp method update_sensitivity() để điều chỉnh sensitivity
8. THE Wake_Word_Engine SHALL cung cấp method is_wake_word_only() để kiểm tra nếu text chỉ chứa wake word
9. IF Porcupine không khả dụng, THEN THE Wake_Word_Engine SHALL fallback sang keyword matching với phonetic matching
10. THE Wake_Word_Engine SHALL có false positive rate thấp hơn current keyword matching implementation

### Requirement 12: Conversation Context Manager

**User Story:** As a hệ thống chatbot, I want duy trì conversation history và context, so that có thể hỗ trợ multi-turn dialogues tự nhiên

#### Acceptance Criteria

1. THE Context_Manager SHALL cung cấp method create_session(user_id) trả về SessionID
2. THE Context_Manager SHALL lưu trữ conversation history với user và assistant messages
3. WHEN thêm message, THE Context_Manager SHALL gọi add_message(session_id, role, content)
4. THE Context_Manager SHALL cung cấp method get_context(session_id, max_turns) trả về ConversationContext
5. THE ConversationContext SHALL chứa: session_id, messages, user_preferences, session_start, last_activity, metadata
6. THE Context_Manager SHALL implement sliding window để giữ last N turns (configurable, default 10 turns)
7. THE Context_Manager SHALL tự động cleanup expired sessions sau 30 phút inactivity
8. THE Context_Manager SHALL cung cấp method clear_context(session_id) để xóa context vì privacy
9. THE Context_Manager SHALL support user preferences: response_mode, voice_name, language, max_context_turns
10. THE Context_Manager SHALL lưu trữ in-memory với optional persistence to disk cho session recovery
11. WHEN session inactive quá timeout, THE Context_Manager SHALL đánh dấu session state là EXPIRED
12. THE Context_Manager SHALL cung cấp method get_session_duration(session_id) trả về thời gian session

### Requirement 13: Multi-Turn Dialogue Controller

**User Story:** As a hệ thống chatbot, I want quản lý multi-turn conversations với state management, so that có thể xử lý follow-up questions và complex commands

#### Acceptance Criteria

1. THE Dialogue_Controller SHALL khởi tạo với ConversationContextManager instance
2. THE Dialogue_Controller SHALL cung cấp method process_input(session_id, user_input) trả về DialogueResponse
3. THE DialogueResponse SHALL chứa: response_text, should_continue, intent, confidence, requires_clarification, suggested_followups
4. THE Dialogue_Controller SHALL parse user input để identify intent và extract entities
5. THE Dialogue_Controller SHALL support intents: QUESTION_ANSWERING, CALCULATION, WEATHER_QUERY, CAMERA_CONTROL, SMALL_TALK, CLARIFICATION_REQUEST, UNKNOWN
6. THE Dialogue_Controller SHALL duy trì DialogueState với: current_intent, slot_values, confirmation_pending, clarification_needed, turn_count
7. THE Dialogue_Controller SHALL support single-turn pattern: simple Q&A
8. THE Dialogue_Controller SHALL support multi-turn pattern: follow-up questions without wake word
9. THE Dialogue_Controller SHALL support slot-filling pattern: progressive information gathering
10. THE Dialogue_Controller SHALL support clarification pattern: ask for missing/ambiguous information
11. THE Dialogue_Controller SHALL support confirmation pattern: verify before executing actions
12. THE Dialogue_Controller SHALL cung cấp method should_continue_listening() để determine nếu cần continuation
13. THE Dialogue_Controller SHALL cung cấp method reset_dialogue_state(session_id) để reset state
14. THE Dialogue_Controller SHALL cung cấp method get_dialogue_state(session_id) để query current state

### Requirement 14: Context-Aware Prompt Builder

**User Story:** As a hệ thống chatbot, I want xây dựng prompts tối ưu cho Gemini AI với conversation context, so that AI responses có chất lượng cao và coherent

#### Acceptance Criteria

1. THE Prompt_Builder SHALL khởi tạo với system_prompt
2. THE Prompt_Builder SHALL cung cấp method build_prompt(context, user_input) trả về formatted prompt string
3. THE formatted prompt SHALL bao gồm: system instructions, user preferences, conversation history, current user input
4. THE Prompt_Builder SHALL format prompts theo Gemini API requirements
5. THE Prompt_Builder SHALL support ResponseMode: CONCISE, DETAILED, CONVERSATIONAL, TECHNICAL
6. THE Prompt_Builder SHALL cung cấp method set_response_mode(mode) để thay đổi response mode
7. THE Prompt_Builder SHALL cung cấp method estimate_token_count(prompt) để estimate token usage
8. THE Prompt_Builder SHALL cung cấp method optimize_context_window(messages, max_tokens) để truncate old messages nếu vượt token limit
9. WHEN token count vượt limit, THE Prompt_Builder SHALL truncate oldest messages first nhưng preserve most recent messages
10. THE Prompt_Builder SHALL include user preferences trong prompt: response style, language formality
11. THE Prompt_Builder SHALL optimize prompt structure cho cost và quality

### Requirement 15: Error Handler và Recovery System

**User Story:** As a hệ thống chatbot, I want xử lý errors gracefully với fallback strategies, so that hệ thống vẫn available khi có partial failures

#### Acceptance Criteria

1. THE Error_Handler SHALL cung cấp method register_component(component_name, health_check) để register components
2. THE Error_Handler SHALL cung cấp method handle_error(error, context) trả về RecoveryAction
3. THE RecoveryAction SHALL chứa: action type, fallback_component, retry_delay, user_message
4. THE Error_Handler SHALL support RecoveryActionType: RETRY, FALLBACK, SKIP, RESTART_COMPONENT, NOTIFY_USER
5. THE Error_Handler SHALL categorize errors: NETWORK_ERROR, API_ERROR, AUDIO_CAPTURE_ERROR, RECOGNITION_ERROR, TTS_ERROR, UNKNOWN_ERROR
6. WHEN Google STT network error, THE Error_Handler SHALL retry 3 lần với exponential backoff, sau đó fallback to Vosk
7. WHEN Gemini API error, THE Error_Handler SHALL retry 2 lần với exponential backoff, sau đó use cached response hoặc apologize message
8. WHEN TTS generation error, THE Error_Handler SHALL retry 1 lần, sau đó use simple text response
9. WHEN wake word detection failure, THE Error_Handler SHALL re-initialize detector, reduce sensitivity, và log error
10. WHEN audio capture timeout, THE Error_Handler SHALL restart audio stream, check device, và notify user
11. WHEN VB-Cable not found, THE Error_Handler SHALL switch to PC mic/speaker mode và warn user
12. THE Error_Handler SHALL log errors với severity levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
13. THE Error_Handler SHALL generate user-friendly error messages in Vietnamese
14. THE Error_Handler SHALL cung cấp method get_fallback_response(error_type) để get appropriate fallback
15. THE Error_Handler SHALL cung cấp method notify_user(message, severity) để notify user về errors

### Requirement 16: Audio Router và Mode Controller

**User Story:** As a hệ thống chatbot, I want quản lý audio routing giữa các devices và modes, so that support flexible deployment scenarios

#### Acceptance Criteria

1. THE Audio_Router SHALL khởi tạo với AudioConfig: operation_mode, sample_rate, channels, buffer_size, virtual_cable_enabled
2. THE Audio_Router SHALL support OperationMode: BASIC_MODE, FULL_AUTOMATION_MODE, HYBRID_MODE
3. THE Audio_Router SHALL cung cấp method set_mode(mode) để switch between modes
4. WHEN ở BASIC_MODE, THE Audio_Router SHALL route PC microphone to PC speakers
5. WHEN ở FULL_AUTOMATION_MODE, THE Audio_Router SHALL route VB-Cable Output to VB-Cable Input
6. WHEN ở HYBRID_MODE, THE Audio_Router SHALL route PC mic + VB-Cable to both PC speakers và VB-Cable
7. THE Audio_Router SHALL cung cấp method get_input_device() trả về current input AudioDevice
8. THE Audio_Router SHALL cung cấp method get_output_device() trả về current output AudioDevice
9. THE Audio_Router SHALL cung cấp method list_available_devices() trả về list tất cả audio devices
10. THE AudioDevice SHALL chứa: device_id, name, device_type, is_virtual, sample_rate, channels
11. THE Audio_Router SHALL support DeviceType: MICROPHONE, SPEAKER, VIRTUAL_CABLE_INPUT, VIRTUAL_CABLE_OUTPUT, RTSP_STREAM
12. THE Audio_Router SHALL cung cấp method test_audio_path() để test audio routing trước khi start conversation
13. THE Audio_Router SHALL detect và enumerate audio devices (physical và virtual)
14. THE Audio_Router SHALL handle device disconnection/reconnection gracefully
15. WHEN switching modes, THE Audio_Router SHALL không drop audio đang processing

### Requirement 17: CareCam SDK Integration Layer

**User Story:** As a hệ thống chatbot, I want tích hợp trực tiếp với CareCam SDK, so that điều khiển camera mic/speaker reliable hơn UI automation

#### Acceptance Criteria

1. THE CareCam_SDK_Adapter SHALL khởi tạo với sdk_path và CameraConfig: ip_address, port, username, password, rtsp_enabled
2. THE CareCam_SDK_Adapter SHALL load qianxin_sdk.dll từ sdk_path
3. THE CareCam_SDK_Adapter SHALL cung cấp method connect_camera(camera_id) để establish camera connection
4. WHEN connected, THE CareCam_SDK_Adapter SHALL trả về Boolean success status
5. THE CareCam_SDK_Adapter SHALL cung cấp method enable_microphone(duration) để bật mic programmatically
6. THE CareCam_SDK_Adapter SHALL cung cấp method disable_microphone() để tắt mic
7. THE CareCam_SDK_Adapter SHALL cung cấp method is_microphone_active() trả về mic status
8. THE CareCam_SDK_Adapter SHALL cung cấp method get_camera_status() trả về CameraStatus
9. THE CameraStatus SHALL chứa: connected, mic_active, speaker_active, signal_quality
10. THE CareCam_SDK_Adapter SHALL cung cấp method play_audio_to_camera(audio_data) để stream audio to camera speaker
11. THE CareCam_SDK_Adapter SHALL support event on_camera_audio_received(callback) để receive audio from camera
12. THE CareCam_SDK_Adapter SHALL handle SDK errors và implement reconnection logic
13. THE CareCam_SDK_Adapter SHALL work với minimized/background CareCam app
14. THE CareCam_SDK_Adapter SHALL có faster response time than UI automation approach
15. THE CareCam_SDK_Adapter SHALL không depend on window position or button coordinates
16. IF CareCam SDK không khả dụng, THEN THE system SHALL fallback to UI automation approach với CareCam_Controller

### Requirement 18: Performance và Latency Requirements

**User Story:** As a người dùng, I want hệ thống response nhanh, so that trải nghiệm conversation tự nhiên và mượt mà

#### Acceptance Criteria

1. THE Wake_Word_Engine SHALL có detection latency dưới 300ms từ audio start
2. THE Speech_To_Text SHALL process audio trong dưới 1 giây cho 5-second audio clip
3. THE AI_Service SHALL generate response trong dưới 2 giây cho typical queries
4. THE Text_To_Speech SHALL synthesize speech trong dưới 500ms cho 50-word response
5. THE entire end-to-end latency SHALL dưới 4 giây từ user finishing speech đến TTS playback start
6. THE VAD_Module SHALL use circular buffers để minimize memory allocation
7. THE system SHALL preload wake word và TTS models at startup để avoid loading delays
8. THE Prompt_Builder SHALL minimize prompt tokens while preserving context quality
9. THE TTS_Service SHALL support streaming playback để start audio while still generating
10. THE system SHALL run parallel processing: VAD, wake word detection, và STT in parallel threads

### Requirement 19: Memory Management

**User Story:** As a hệ thống chatbot, I want quản lý memory hiệu quả, so that system stable với multiple concurrent sessions

#### Acceptance Criteria

1. THE VAD_Module SHALL use tối đa 5MB cho audio buffers (30 seconds of 16kHz mono audio)
2. THE Context_Manager SHALL use tối đa 1MB per active session
3. THE Context_Manager SHALL support tối đa 100 concurrent sessions
4. THE Wake_Word_Engine SHALL load compressed model dưới 2MB
5. THE Audio_Router SHALL use tối đa 10MB cho audio routing buffers
6. THE total baseline memory SHALL dưới 200MB + 1MB per active session
7. THE Context_Manager SHALL implement sliding window để discard old messages
8. THE system SHALL compress audio data after transcription
9. THE Context_Manager SHALL automatically cleanup expired sessions sau 30 phút inactivity
10. THE system SHALL lazy load TTS models only when needed
11. IF sử dụng local AI models, THE system SHALL release GPU memory after inference
