# Tỷ Tỷ - CareCam Voice Chatbot

## Giới thiệu
Chatbot AI điều khiển bằng giọng nói, tích hợp với camera CareCam.
Nói "Tỷ Tỷ" để kích hoạt và đặt câu hỏi.

**Tính năng chính:**
- 🎙️ Wake word detection với acoustic model (Porcupine)
- 🧠 Hỗ trợ AI local (Ollama) và cloud (Google Gemini)
- 💬 Multi-turn conversation với context memory
- 🔊 Voice Activity Detection (VAD) thông minh
- 🎯 Nhiều operation modes (Basic, Full Automation, Hybrid)
- 🛡️ Error handling và recovery tự động

## Cài đặt cơ bản

### 1. Cài Python dependencies
```bash
cd "d:\carecam\Embeded system"
pip install -r requirements.txt
```

### 2. Cấu hình AI Service

#### Option A: Sử dụng Google Gemini (Cloud - Khuyên dùng cho người mới)
1. Vào https://aistudio.google.com/app/apikey
2. Click "Create API Key"
3. Tạo file `.env` từ template:
   ```bash
   copy .env.example .env
   ```
4. Mở file `.env` và điền API key:
   ```
   AI_PROVIDER=gemini
   GOOGLE_API_KEY=your-api-key-here
   ```

#### Option B: Sử dụng Ollama (Local AI - Cho người dùng nâng cao)
Xem phần [Cài đặt Ollama](#cài-đặt-ollama-optional) bên dưới.

#### Option C: Auto mode (Thử Ollama trước, fallback sang Gemini)
```
AI_PROVIDER=auto
GOOGLE_API_KEY=your-api-key-here
```

### 3. Chạy chatbot
```bash
python main.py
```

## Cài đặt Ollama (Optional)

Ollama cho phép chạy AI model local, không cần internet và không tốn API quota.

### Cài đặt Ollama

**Windows:**
1. Tải Ollama installer từ https://ollama.com/download
2. Chạy installer và làm theo hướng dẫn
3. Ollama service sẽ tự động khởi động

**Hoặc dùng PowerShell:**
```powershell
# Download và cài đặt
winget install Ollama.Ollama
```

### Tải model AI

Sau khi cài Ollama, tải model lightweight cho CPU:

```bash
ollama pull qwen2.5:0.5b
```

**Model recommendations:**
- `qwen2.5:0.5b` - Nhẹ nhất, chạy tốt trên CPU (khuyên dùng)
- `qwen2.5:1.5b` - Cân bằng tốc độ và chất lượng
- `qwen2.5:3b` - Chất lượng cao hơn, cần RAM nhiều hơn

### Kiểm tra cài đặt

```bash
# Liệt kê models đã cài
ollama list

# Test model
ollama run qwen2.5:0.5b "Xin chào"
```

### Cấu hình trong .env

```
AI_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:0.5b
```

### Khởi động Ollama service

**Windows:**
Ollama service tự động chạy khi khởi động máy. Nếu cần start thủ công:

```powershell
# Kiểm tra service
Get-Service Ollama

# Start service nếu cần
Start-Service Ollama
```

## Cài đặt Wake Word Model (Vietnamese Porcupine)

Wake word model giúp phát hiện "Tỷ Tỷ" chính xác hơn so với keyword matching đơn giản.

### Tải Vietnamese Porcupine Model

1. **Tạo thư mục models:**
   ```bash
   mkdir -p "./models/wake_word"
   ```

2. **Tải model từ Picovoice Console:**
   - Vào https://console.picovoice.ai/
   - Đăng ký tài khoản miễn phí (Free tier có sẵn)
   - Vào "Porcupine Wake Word" → "Create New Wake Word"
   - Nhập wake word: "tỷ tỷ" (hoặc variations: "ty ty", "ti ti")
   - Chọn platform: Windows
   - Download file `.ppn`

3. **Copy model vào thư mục:**
   ```bash
   copy ty-ty_vi_windows.ppn "./models/wake_word/"
   ```

4. **Cấu hình trong .env:**
   ```
   WAKE_WORD_MODEL_PATH=./models/wake_word
   ```

### Fallback Mode

Nếu không có Porcupine model, hệ thống tự động fallback về keyword matching với phonetic matching. Hệ thống vẫn hoạt động bình thường nhưng độ chính xác thấp hơn.

## Cài đặt VB-Cable (For Full Automation Mode)

VB-Cable là virtual audio cable cho phép routing audio giữa CareCam app và chatbot.

### Khi nào cần VB-Cable?

- **Basic Mode** (PC mic → PC speakers): **KHÔNG** cần VB-Cable
- **Full Automation Mode** (Camera ↔ Chatbot): **CẦN** VB-Cable
- **Hybrid Mode** (PC + Camera): **CẦN** VB-Cable

### Cài đặt VB-Cable

1. **Tải VB-Audio Virtual Cable:**
   - Vào https://vb-audio.com/Cable/
   - Download "VB-CABLE Virtual Audio Device"
   - Extract file zip

2. **Cài đặt driver:**
   - Right-click `VBCABLE_Setup_x64.exe`
   - Chọn "Run as Administrator"
   - Click "Install Driver"
   - Restart máy tính nếu được yêu cầu

3. **Kiểm tra cài đặt:**
   - Mở "Settings" → "Sound"
   - Kiểm tra có device: "CABLE Input" và "CABLE Output"

### Cấu hình CareCam App với VB-Cable

1. **Trong CareCam/QianXin app:**
   - Vào Settings → Audio
   - Set Microphone: **CABLE Output** (VB-Cable Output)
   - Set Speaker: **CABLE Input** (VB-Cable Input)

2. **Trong .env file:**
   ```
   OPERATION_MODE=full_automation
   VIRTUAL_CABLE_ENABLED=true
   ```

3. **Test audio routing:**
   ```bash
   python -m modules.audio_router --test
   ```

### VB-Cable Alternatives

- **VoiceMeeter** - Advanced audio mixer (free)
- **Virtual Audio Cable** (VAC) - Commercial alternative

## Cài đặt CareCam SDK (Advanced Users)

CareCam SDK cho phép điều khiển camera programmatically thay vì UI automation.

### Lấy SDK

1. **Liên hệ nhà cung cấp camera:**
   - Email: support@qianxin.com (hoặc nhà cung cấp của bạn)
   - Yêu cầu "CareCam SDK for Windows" hoặc "QianXin SDK"

2. **Hoặc extract từ QianXin app:**
   - Tìm file `qianxin_sdk.dll` trong thư mục cài đặt
   - Thường ở: `C:\Program Files\QianXin\` hoặc `C:\Program Files (x86)\QianXin\`

### Cài đặt SDK

1. **Copy SDK files:**
   ```bash
   mkdir -p "./sdk/carecam"
   copy qianxin_sdk.dll "./sdk/carecam/"
   copy libvrcam.dll "./sdk/carecam/"  # Nếu có
   ```

2. **Cấu hình trong config.py:**
   ```python
   # CareCam SDK Settings
   CARECAM_SDK_ENABLED = True
   CARECAM_SDK_PATH = "./sdk/carecam/qianxin_sdk.dll"
   ```

3. **Cấu hình camera credentials trong .env:**
   ```
   CAMERA_IP=192.168.1.100
   CAMERA_USERNAME=admin
   CAMERA_PASSWORD=your-password
   ```

### Fallback khi không có SDK

Nếu không có SDK, hệ thống tự động dùng **UI automation** (PyAutoGUI) để click nút mic/speaker. Chức năng vẫn hoạt động nhưng:
- Cần cửa sổ CareCam app visible
- Phụ thuộc vào vị trí button (dùng UI Config Tool)
- Chậm hơn SDK approach

### 3. Chạy chatbot
```bash
python main.py
```

## Sử dụng

| Lệnh | Kết quả |
|------|---------|
| "Tỷ Tỷ 1+1 bằng mấy?" | AI trả lời toán |
| "Tỷ Tỷ ơi thời tiết thế nào?" | AI trả lời thời tiết |
| "Tỷ Tỷ" (chờ) + "câu hỏi" | Hai bước kích hoạt |

## Cấu hình (config.py)

| Setting | Mô tả | Mặc định |
|---------|-------|----------|
| `GOOGLE_API_KEY` | API key cho Gemini | Từ env |
| `TTS_VOICE` | Giọng đọc | vi-VN-HoaiMyNeural |
| `WAKE_WORD` | Từ kích hoạt | "tỷ tỷ" |
| `USE_CAMERA_AUDIO` | Dùng mic camera | False |

## Cấu trúc project

```
Embeded system/
├── main.py              # Entry point
├── config.py            # Cấu hình
├── requirements.txt     # Dependencies
└── modules/
    ├── ai_service.py    # Google Gemini AI
    ├── text_to_speech.py # Edge TTS (giọng Việt)
    ├── speech_to_text.py # Google Speech Recognition
    ├── wake_word.py      # Phát hiện "Tỷ Tỷ"
    └── audio_capture.py  # Capture audio (RTSP/mic)
```