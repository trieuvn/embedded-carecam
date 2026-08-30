# 🔧 Sửa Lỗi: Tự Động Điều Khiển Mic/Speaker Camera

**Vấn Đề:** Hệ thống chưa tự động click vào nút mic/speaker trên app CareCam

**Nguyên Nhân:** `ConversationManager` và `CareCamController` chưa được khởi tạo trong `main.py`

---

## 🎯 Giải Pháp

Có 2 cách:

### **Option 1: Sử Dụng Module Có Sẵn (Khuyến Nghị)**

Hệ thống đã có đầy đủ code để điều khiển camera, chỉ cần **kích hoạt**.

### **Option 2: Chạy Script Riêng**

Chạy `carecam_bot.py` thay vì `main.py` - file này có tích hợp sẵn camera control.

---

## 🚀 Option 1: Kích Hoạt Camera Control Trong Main.py

### Bước 1: Thêm Import CareCam Controller

Mở file `main.py`, tìm dòng import (khoảng dòng 46):

```python
from modules.conversation_manager import get_conversation_manager
```

Thêm dòng này ngay sau:

```python
from modules.carecam_controller import CareCamController
```

### Bước 2: Khởi Tạo CareCam Controller

Trong hàm `initialize()`, tìm dòng:

```python
# Initialize AI service
print(f"  🤖 Initializing AI Service ({config.AI_PROVIDER})...")
self.ai = get_ai_service()
```

Thêm đoạn code này **TRƯỚC** dòng trên:

```python
# Initialize CareCam Controller (if FULL_AUTOMATION or HYBRID mode)
if config.OPERATION_MODE in ["full_automation", "hybrid"]:
    print("  🎥 Initializing CareCam Controller...")
    try:
        self.carecam_controller = CareCamController()
        if not self.carecam_controller.find_window():
            print("  ⚠️  CareCam app window not found! Make sure QianXin.exe is running.")
            print("  💡 Falling back to BASIC mode (PC mic/speaker only)")
            config.OPERATION_MODE = "basic"
            self.carecam_controller = None
        else:
            print("  ✅ CareCam window found")
            
            # Initialize Conversation Manager with CareCam control
            print("  🎛️  Initializing Conversation Manager...")
            self.conversation_manager = get_conversation_manager(self.carecam_controller)
            print("  ✅ Conversation Manager ready (camera control enabled)")
            
            # Register health check
            self.error_handler.register_component(
                "carecam_controller",
                lambda: self.carecam_controller is not None
            )
            self.error_handler.register_component(
                "conversation_manager",
                lambda: self.conversation_manager is not None
            )
    except Exception as e:
        logger.warning(f"Failed to initialize CareCam controller: {e}")
        print(f"  ⚠️  CareCam controller failed: {e}")
        print("  💡 Falling back to BASIC mode")
        self.carecam_controller = None
        self.conversation_manager = None
else:
    print("  ⏭️  CareCam control disabled (BASIC mode)")
    self.carecam_controller = None
    self.conversation_manager = None
```

### Bước 3: Thêm Biến Instance

Trong hàm `__init__()`, tìm dòng:

```python
self.conversation_manager = None
```

Thêm dòng này ngay sau:

```python
self.carecam_controller = None
```

### Bước 4: Tích Hợp Vào Listen Loop

Tìm phần `listen_loop()` và sửa lại logic xử lý wake word để sử dụng `conversation_manager`.

**Thay thế phần xử lý hiện tại bằng:**

```python
# In listen loop, after detecting wake word
if self.conversation_manager:
    # Use conversation manager for state control
    print("🎤 Wake word detected!")
    
    # Transition to SPEAKING state (mic ON, speaker OFF)
    if self.conversation_manager.on_wake_word_detected():
        print("✅ Mic enabled for recording")
        
        # Record user command
        print("👂 Listening...")
        command_text = self.stt.listen()
        
        if command_text:
            # Process command
            response = self.process_command(command_text)
            
            # Transition to LISTENING state (speaker ON, mic OFF) for playback
            if self.conversation_manager.on_acknowledgment_end():
                self.speak(response)
                
                # Return to DEFAULT state after response
                self.conversation_manager.on_response_complete()
        else:
            print("⏰ Timeout - no speech detected")
            self.conversation_manager.force_default_state()
else:
    # Fallback to basic mode (no camera control)
    print("🎤 Wake word detected (basic mode)")
    command_text = self.stt.listen()
    if command_text:
        response = self.process_command(command_text)
        self.speak(response)
```

### Bước 5: Cấu Hình Operation Mode

Mở `config.py`, tìm dòng:

```python
OPERATION_MODE = "basic"
```

Đổi thành:

```python
OPERATION_MODE = "full_automation"  # hoặc "hybrid"
```

---

## 🚀 Option 2: Sử Dụng carecam_bot.py (Nhanh Hơn)

File `carecam_bot.py` đã có sẵn tích hợp đầy đủ camera control.

### Chạy Trực Tiếp

```bash
cd "d:\carecam\Embeded system"
python carecam_bot.py
```

### Ưu Điểm
- ✅ Đã tích hợp sẵn CareCam control
- ✅ Tự động click nút mic/speaker
- ✅ Không cần sửa code

### Nhược Điểm
- ⚠️ Thiếu một số tính năng mới (Ollama, dialogue controller)
- ⚠️ Kiến trúc cũ hơn

---

## 🎯 So Sánh 2 Options

| Tiêu chí | Option 1 (Sửa main.py) | Option 2 (carecam_bot.py) |
|----------|------------------------|---------------------------|
| **Camera Control** | ✅ Sau khi sửa | ✅ Có sẵn |
| **Ollama AI** | ✅ Có | ❌ Không |
| **Dialogue Controller** | ✅ Có | ❌ Không |
| **Context Manager** | ✅ Có | ❌ Không |
| **Effort** | ⚠️ Cần sửa code | ✅ Chạy ngay |
| **Kiến trúc** | ✅ Mới nhất | ⚠️ Cũ hơn |

---

## 📋 Khuyến Nghị

### Nếu Bạn Cần Nhanh:
👉 **Dùng Option 2** - `python carecam_bot.py`

### Nếu Muốn Đầy Đủ Tính Năng:
👉 **Dùng Option 1** - Sửa `main.py` theo hướng dẫn trên

---

## ✅ Test Sau Khi Sửa

### Test Camera Control

```bash
cd "d:\carecam\Embeded system"
python -c "from modules.carecam_controller import CareCamController; c = CareCamController(); print('Window found:', c.find_window())"
```

**Kỳ vọng:** `Window found: True`

### Test Conversation Manager

```bash
python -c "from modules.carecam_controller import CareCamController; from modules.conversation_manager import get_conversation_manager; c = CareCamController(); c.find_window(); m = get_conversation_manager(c); print('Manager ready:', m is not None)"
```

**Kỳ vọng:** `Manager ready: True`

### Test Full Flow

```bash
python main.py
```

**Kỳ vọng:**
```
🎥 Initializing CareCam Controller...
✅ CareCam window found
🎛️  Initializing Conversation Manager...
✅ Conversation Manager ready (camera control enabled)
```

---

## 🔧 Troubleshooting

### Lỗi: "CareCam window not found"

**Nguyên nhân:** App QianXin.exe chưa chạy

**Giải pháp:**
1. Mở QianXin.exe
2. Đợi cửa sổ camera hiện ra
3. Chạy lại `python main.py`

### Lỗi: Click sai vị trí

**Nguyên nhân:** Vị trí nút chưa được cấu hình

**Giải pháp:**
```bash
python ui_config_tool.py
```

Làm theo hướng dẫn để lưu vị trí nút mic/speaker.

### Lỗi: "Module 'pyautogui' not found"

**Giải pháp:**
```bash
pip install pyautogui pygetwindow pillow
```

---

## 📞 Tóm Tắt Nhanh

### Để Kích Hoạt Camera Control:

**Cách 1 (Nhanh):**
```bash
python carecam_bot.py
```

**Cách 2 (Đầy đủ tính năng):**
1. Sửa `main.py` theo hướng dẫn trên
2. Đổi `OPERATION_MODE = "full_automation"` trong `config.py`
3. Chạy `python ui_config_tool.py` để cấu hình vị trí nút
4. Chạy `python main.py`

---

**Trạng thái:** ⚠️ **CẦN SỬA** để kích hoạt camera control  
**Ưu tiên:** 🔥 **TRUNG BÌNH** (hệ thống vẫn chạy được với PC mic/speaker)  
**Thời gian sửa:** ~10-15 phút (Option 1) hoặc 1 phút (Option 2)

**Chúc bạn thành công! 🎉**
