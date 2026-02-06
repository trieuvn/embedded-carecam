# Tỷ Tỷ - CareCam Voice Chatbot

## Giới thiệu
Chatbot AI điều khiển bằng giọng nói, tích hợp với camera CareCam.
Nói "Tỷ Tỷ" để kích hoạt và đặt câu hỏi.

## Cài đặt

### 1. Cài Python dependencies
```bash
cd "d:\carecam\Embeded system"
pip install -r requirements.txt
```

### 2. Lấy Google API Key (miễn phí)
1. Vào https://aistudio.google.com/app/apikey
2. Click "Create API Key"
3. Copy key và set environment variable:
```bash
$env:GOOGLE_API_KEY = "your-api-key-here"
```

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