# Hướng Dẫn Sử Dụng Hệ Thống Chatbot "Tỷ Tỷ"

## 📋 Mục Lục

1. [Giới Thiệu](#giới-thiệu)
2. [Yêu Cầu Hệ Thống](#yêu-cầu-hệ-thống)
3. [Cài Đặt](#cài-đặt)
4. [Cấu Hình](#cấu-hình)
5. [Sử Dụng Cơ Bản](#sử-dụng-cơ-bản)
6. [Tính Năng Nâng Cao](#tính-năng-nâng-cao)
7. [Xử Lý Sự Cố](#xử-lý-sự-cố)
8. [Câu Hỏi Thường Gặp](#câu-hỏi-thường-gặp)

---

## 🎯 Giới Thiệu

Hệ thống Chatbot "Tỷ Tỷ" là trợ lý giọng nói tiếng Việt thông minh, giúp bạn tương tác với camera CareCam QianXin thông qua giọng nói. Hệ thống hỗ trợ:

- ✅ Nhận diện giọng nói tiếng Việt
- ✅ Trả lời câu hỏi thông minh
- ✅ Điều khiển camera (bật/tắt mic, speaker)
- ✅ Hội thoại nhiều lượt (multi-turn conversation)
- ✅ Phát hiện từ đánh thức "Tỷ Tỷ"
- ✅ Xử lý lỗi tự động và dự phòng

---

## 💻 Yêu Cầu Hệ Thống

### Phần Cứng
- **Hệ điều hành:** Windows 10/11
- **RAM:** Tối thiểu 4GB (khuyến nghị 8GB)
- **Bộ xử lý:** Intel i3 hoặc tương đương trở lên
- **Microphone:** Bất kỳ (tích hợp hoặc rời)
- **Loa:** Bất kỳ (tích hợp hoặc rời)
- **Camera:** CareCam QianXin (với phần mềm QianXin.exe)

### Phần Mềm
- **Python:** 3.8 trở lên (khuyến nghị 3.10+)
- **Internet:** Kết nối ổn định (cho Google Gemini API)
- **Ứng dụng CareCam:** QianXin.exe đang chạy

### Tùy Chọn (Không Bắt Buộc)
- **VB-Cable:** Để chế độ tự động hóa hoàn toàn
- **Ollama:** Để chạy AI cục bộ (không cần internet)

---

## 🔧 Cài Đặt

### Bước 1: Cài Đặt Python

Nếu chưa có Python, tải và cài đặt từ: https://www.python.org/downloads/

```bash
# Kiểm tra Python đã cài đặt
python --version
```

### Bước 2: Clone Hoặc Tải Mã Nguồn

```bash
# Di chuyển đến thư mục dự án
cd "d:\carecam\Embeded system"
```

### Bước 3: Cài Đặt Dependencies

```bash
# Cài đặt các thư viện cần thiết
pip install -r requirements.txt
```

### Bước 4: Cấu Hình API Key

1. Sao chép file mẫu cấu hình:
```bash
copy .env.example .env
```

2. Mở file `.env` và thêm Google Gemini API key của bạn:
```
GEMINI_API_KEY=your_api_key_here
```

**Lấy API Key:**
- Truy cập: https://makersuite.google.com/app/apikey
- Đăng nhập bằng tài khoản Google
- Tạo API key mới
- Sao chép và dán vào file `.env`

### Bước 5: Cài Đặt VB-Cable (Tùy Chọn)

**Chỉ cần nếu muốn chế độ tự động hóa hoàn toàn**

1. Tải VB-Cable từ: https://vb-audio.com/Cable/
2. Giải nén và chạy `VBCABLE_Setup_x64.exe`
3. Cài đặt và khởi động lại máy tính

---

## ⚙️ Cấu Hình

### Cấu Hình Cơ Bản

File `config.py` chứa tất cả các cài đặt. Các tham số quan trọng:

```python
# Chế độ hoạt động
OPERATION_MODE = "basic"  # basic / full_automation / hybrid

# AI Service
AI_PROVIDER = "auto"  # auto / gemini / ollama

# Wake Word Detection
WAKE_WORD_ENGINE_ENABLED = True
WAKE_WORD = "tỷ tỷ"

# Conversation
CONVERSATION_ENABLED = True
MAX_CONTEXT_TURNS = 5  # Số lượt hội thoại lưu trữ

# Timeouts
SILENCE_TIMEOUT = 3.0  # Giây im lặng trước khi xử lý
MAX_RECORDING_DURATION = 10.0  # Thời gian ghi âm tối đa
```

### Chế Độ Hoạt Động

#### 1. **BASIC Mode (Mặc Định)**
- Sử dụng microphone và loa của máy tính
- Không cần VB-Cable
- Phù hợp cho sử dụng thử nghiệm

```python
OPERATION_MODE = "basic"
```

#### 2. **FULL_AUTOMATION Mode**
- Sử dụng VB-Cable để điều khiển camera tự động
- Cần cài đặt VB-Cable
- Phù hợp cho tích hợp hoàn toàn với camera

```python
OPERATION_MODE = "full_automation"
```

#### 3. **HYBRID Mode**
- Kết hợp cả hai chế độ
- Linh hoạt nhất

```python
OPERATION_MODE = "hybrid"
```

### Cấu Hình Vị Trí Nút (Quan Trọng!)

Trước khi sử dụng, bạn cần cấu hình vị trí nút mic và speaker trong ứng dụng QianXin.

#### Chạy Công Cụ Cấu Hình UI

```bash
cd "d:\carecam\Embeded system"
python ui_config_tool.py
```

#### Các Bước Cấu Hình:

1. **Đảm bảo QianXin.exe đang chạy** và bạn thấy cửa sổ camera

2. **Chọn vị trí nút Mic:**
   - Click "Select Mic Button Position"
   - Di chuột đến nút microphone trong QianXin
   - Click vào nút đó
   - Tọa độ sẽ được ghi lại tự động

3. **Chọn vị trí nút Speaker:**
   - Click "Select Speaker Button Position"
   - Di chuột đến nút speaker trong QianXin
   - Click vào nút đó
   - Tọa độ sẽ được ghi lại tự động

4. **Kiểm tra vị trí:**
   - Click "Test Mic Position" - con trỏ chuột sẽ di chuyển đến nút mic
   - Click "Test Speaker Position" - con trỏ chuột sẽ di chuyển đến nút speaker
   - Đảm bảo vị trí chính xác

5. **Lưu cấu hình:**
   - Click "Save Configuration"
   - File `position_config.json` sẽ được tạo

**Lưu ý:** Nếu bạn thay đổi độ phân giải màn hình hoặc vị trí cửa sổ QianXin, cần chạy lại công cụ này.

---

## 🚀 Sử Dụng Cơ Bản

### Khởi Động Hệ Thống

#### Bước 1: Mở QianXin

Đảm bảo ứng dụng CareCam QianXin.exe đang chạy và đã kết nối camera.

#### Bước 2: Chạy Chatbot

```bash
cd "d:\carecam\Embeded system"
python main.py
```

Bạn sẽ thấy màn hình khởi động:

```
======================================================================
🚀 Khởi Tạo Hệ Thống Chatbot Tỷ Tỷ
======================================================================

🔊 [1/4] Kiểm Tra Wake Word Engine...
   ✅ Porcupine sẵn sàng
   📍 Độ nhạy: 0.5

🧠 [2/4] Kiểm Tra AI Services...
   ✅ Google Gemini sẵn sàng
   📦 Model: gemini-flash-latest

🔌 [3/4] Kiểm Tra VB-Cable...
   ✅ VB-Cable phát hiện
   📍 Chế độ: FULL_AUTOMATION

🎥 [4/4] Kiểm Tra CareCam SDK...
   ✅ Fallback: UI Automation

======================================================================
✅ Hệ thống sẵn sàng!
======================================================================
```

### Sử Dụng Lần Đầu

#### 1. **Gọi Từ Đánh Thức**

Nói: **"Tỷ Tỷ"** hoặc các biến thể:
- "Tỷ" (ngắn gọn)
- "Ty ty" (latinh hóa)
- "Ti ti" (phát âm khác)

Hệ thống sẽ trả lời: **"Dạ"** (xác nhận đã nghe)

#### 2. **Đặt Câu Hỏi**

Sau khi nghe "Dạ", hãy nói câu hỏi của bạn:

**Ví dụ:**
```
Bạn: "Tỷ Tỷ"
Tỷ Tỷ: "Dạ"
Bạn: "Hôm nay thời tiết Hà Nội thế nào?"
Tỷ Tỷ: "Hôm nay Hà Nội trời nắng, nhiệt độ khoảng 28 độ C..."
```

#### 3. **Im Lặng = Kết Thúc**

Sau khi nói xong, im lặng **3 giây**. Hệ thống sẽ tự động xử lý câu hỏi của bạn.

### Các Lệnh Cơ Bản

#### Câu Hỏi Thông Tin
```
"Tỷ Tỷ, hôm nay là thứ mấy?"
"Tỷ Tỷ, mấy giờ rồi?"
"Tỷ Tỷ, thủ đô của Việt Nam là gì?"
```

#### Tính Toán
```
"Tỷ Tỷ, 15 cộng 27 bằng bao nhiêu?"
"Tỷ Tỷ, 100 chia 4 bằng mấy?"
```

#### Trò Chuyện
```
"Tỷ Tỷ, chào buổi sáng"
"Tỷ Tỷ, cảm ơn bạn"
"Tỷ Tỷ, tạm biệt"
```

#### Điều Khiển Camera
```
"Tỷ Tỷ, bật microphone"
"Tỷ Tỷ, tắt loa"
"Tỷ Tỷ, kiểm tra trạng thái camera"
```

---

## 🎨 Tính Năng Nâng Cao

### 1. Hội Thoại Nhiều Lượt

Hệ thống hỗ trợ hội thoại liên tục mà không cần gọi "Tỷ Tỷ" nhiều lần:

```
Bạn: "Tỷ Tỷ, thời tiết hôm nay thế nào?"
Tỷ Tỷ: "Hôm nay trời nắng, nhiệt độ 28 độ."

Bạn: "Còn ngày mai thì sao?" (không cần gọi "Tỷ Tỷ" lại)
Tỷ Tỷ: "Ngày mai dự báo có mưa nhỏ..."
```

**Cấu hình:**
```python
# Trong config.py
CONVERSATION_ENABLED = True
MAX_CONTEXT_TURNS = 5  # Lưu 5 lượt hội thoại gần nhất
```

### 2. Sử Dụng Ollama (AI Cục Bộ)

Nếu muốn chạy AI trên máy tính của bạn (không cần internet):

#### Cài Đặt Ollama

1. Tải Ollama: https://ollama.ai/download
2. Cài đặt và khởi động Ollama
3. Tải model:

```bash
ollama pull qwen2.5:0.5b
```

#### Cấu Hình

```python
# Trong config.py
AI_PROVIDER = "ollama"  # Hoặc "auto" để tự động
OLLAMA_URL = "http://localhost:11434"
OLLAMA_MODEL = "qwen2.5:0.5b"
```

**Lợi ích:**
- ✅ Không cần internet
- ✅ Nhanh hơn (không có độ trễ mạng)
- ✅ Miễn phí hoàn toàn
- ✅ Quyền riêng tư cao hơn

### 3. Chế Độ Phản Hồi

Hệ thống hỗ trợ 4 chế độ phản hồi:

```python
# CONCISE: Ngắn gọn, súc tích
# DETAILED: Chi tiết, đầy đủ
# CONVERSATIONAL: Tự nhiên, thân thiện (mặc định)
# TECHNICAL: Kỹ thuật, chính xác

RESPONSE_MODE = "CONVERSATIONAL"
```

### 4. Điều Chỉnh Độ Nhạy Wake Word

Nếu "Tỷ Tỷ" nhận diện quá nhạy hoặc không đủ nhạy:

```python
# Trong config.py
WAKE_WORD_SENSITIVITY = 0.5  # Từ 0.0 đến 1.0

# 0.3 - 0.4: Ít nhạy hơn (ít false positive)
# 0.5 - 0.6: Cân bằng (khuyến nghị)
# 0.7 - 0.8: Nhạy hơn (dễ kích hoạt)
```

### 5. Timeout và Thời Gian Chờ

```python
# Trong config.py

# Thời gian im lặng trước khi xử lý
SILENCE_TIMEOUT = 3.0  # giây

# Thời gian ghi âm tối đa
MAX_RECORDING_DURATION = 10.0  # giây

# Thời gian session hết hạn
SESSION_TIMEOUT_MINUTES = 30  # phút
```

---

## 🔧 Xử Lý Sự Cố

### Vấn Đề 1: "Tỷ Tỷ" Không Nghe Thấy Tôi

**Triệu chứng:** Hệ thống không phản hồi khi gọi "Tỷ Tỷ"

**Giải pháp:**

1. **Kiểm tra microphone:**
   ```bash
   # Chạy test microphone
   python -c "import pyaudio; p = pyaudio.PyAudio(); print(p.get_default_input_device_info())"
   ```

2. **Tăng độ nhạy wake word:**
   ```python
   WAKE_WORD_SENSITIVITY = 0.7  # Tăng từ 0.5 lên 0.7
   ```

3. **Kiểm tra âm lượng:**
   - Mở Settings → Sound → Input
   - Đảm bảo microphone không bị tắt tiếng
   - Tăng âm lượng input lên 80-100%

4. **Nói rõ hơn:**
   - Nói to và rõ ràng
   - Khoảng cách 30-50cm từ microphone
   - Giảm tiếng ồn xung quanh

### Vấn Đề 2: Lỗi "API Key Invalid"

**Triệu chứng:** 
```
❌ Google Gemini not available (missing/invalid API key)
```

**Giải pháp:**

1. Kiểm tra file `.env`:
   ```bash
   type .env
   ```

2. Đảm bảo API key đúng format:
   ```
   GEMINI_API_KEY=AIzaSy...
   ```

3. Tạo API key mới nếu cần:
   - Truy cập: https://makersuite.google.com/app/apikey
   - Tạo key mới
   - Cập nhật vào `.env`

4. Khởi động lại hệ thống:
   ```bash
   python main.py
   ```

### Vấn Đề 3: Nút Mic/Speaker Click Sai Vị Trí

**Triệu chứng:** Hệ thống click sai vị trí trong QianXin

**Giải pháp:**

1. **Chạy lại UI Config Tool:**
   ```bash
   python ui_config_tool.py
   ```

2. **Cấu hình lại vị trí:**
   - Select Mic Button Position
   - Select Speaker Button Position
   - Test để đảm bảo chính xác
   - Save Configuration

3. **Kiểm tra độ phân giải màn hình:**
   - Nếu đã thay đổi độ phân giải, cần cấu hình lại
   - Nếu di chuyển cửa sổ QianXin, cần cấu hình lại

4. **Xóa config cũ và tạo mới:**
   ```bash
   del position_config.json
   python ui_config_tool.py
   ```

### Vấn Đề 4: "Connection refused" hoặc "Timeout"

**Triệu chứng:** Lỗi kết nối mạng

**Giải pháp:**

1. **Kiểm tra internet:**
   ```bash
   ping google.com
   ```

2. **Sử dụng Ollama (không cần internet):**
   ```bash
   ollama serve
   ollama pull qwen2.5:0.5b
   ```
   
   Cập nhật config:
   ```python
   AI_PROVIDER = "ollama"
   ```

3. **Kiểm tra firewall:**
   - Cho phép Python qua firewall
   - Cho phép kết nối đến api.google.com

4. **Thử lại với timeout dài hơn:**
   ```python
   REQUEST_TIMEOUT = 30  # Tăng từ 10 lên 30 giây
   ```

### Vấn Đề 5: Hệ Thống Chậm / Lag

**Triệu chứng:** Phản hồi mất > 5 giây

**Giải pháp:**

1. **Sử dụng Ollama thay vì Gemini:**
   ```python
   AI_PROVIDER = "ollama"  # Nhanh hơn Gemini
   ```

2. **Giảm context turns:**
   ```python
   MAX_CONTEXT_TURNS = 3  # Giảm từ 5 xuống 3
   ```

3. **Sử dụng CONCISE mode:**
   ```python
   RESPONSE_MODE = "CONCISE"  # Phản hồi ngắn gọn hơn
   ```

4. **Kiểm tra tài nguyên hệ thống:**
   ```bash
   # Mở Task Manager (Ctrl+Shift+Esc)
   # Kiểm tra CPU và RAM usage
   ```

### Vấn Đề 6: VB-Cable Không Hoạt Động

**Triệu chứng:**
```
⚠️  VB-Cable not detected
```

**Giải pháp:**

1. **Cài đặt VB-Cable:**
   - Tải từ: https://vb-audio.com/Cable/
   - Chạy installer với quyền Administrator
   - Khởi động lại máy tính

2. **Kiểm tra VB-Cable trong Windows:**
   - Mở Settings → Sound
   - Tìm "CABLE Input" và "CABLE Output"
   - Nếu không thấy, cài đặt lại VB-Cable

3. **Sử dụng BASIC mode thay thế:**
   ```python
   OPERATION_MODE = "basic"  # Không cần VB-Cable
   ```

### Vấn Đề 7: Lỗi Import Module

**Triệu chứng:**
```
ImportError: No module named 'xxx'
```

**Giải pháp:**

1. **Cài đặt lại dependencies:**
   ```bash
   pip install -r requirements.txt --force-reinstall
   ```

2. **Kiểm tra Python version:**
   ```bash
   python --version  # Phải >= 3.8
   ```

3. **Sử dụng virtual environment:**
   ```bash
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```

---

## ❓ Câu Hỏi Thường Gặp

### Q1: Tôi có thể sử dụng mà không cần internet không?

**Có!** Cài đặt Ollama và chạy AI cục bộ:

```bash
# Cài đặt Ollama từ https://ollama.ai/download
ollama serve
ollama pull qwen2.5:0.5b
```

Cập nhật config:
```python
AI_PROVIDER = "ollama"
```

### Q2: Tỷ Tỷ có hiểu giọng miền Nam/Bắc/Trung không?

**Có!** Hệ thống sử dụng Google Speech-to-Text hỗ trợ tất cả giọng địa phương Việt Nam. Tuy nhiên:
- Giọng miền Bắc: Độ chính xác cao nhất
- Giọng miền Nam/Trung: Vẫn hoạt động tốt nhưng có thể cần nói rõ hơn

### Q3: Làm sao để Tỷ Tỷ phản hồi nhanh hơn?

**3 cách:**

1. **Sử dụng Ollama** (AI cục bộ - nhanh nhất)
2. **Giảm context turns:** `MAX_CONTEXT_TURNS = 3`
3. **Dùng CONCISE mode:** `RESPONSE_MODE = "CONCISE"`

### Q4: Tôi có thể thay đổi tên "Tỷ Tỷ" thành tên khác không?

**Có!** Sửa trong `config.py`:

```python
WAKE_WORD = "tên bạn muốn"
WAKE_WORD_VARIATIONS = ["biến thể 1", "biến thể 2"]
```

**Lưu ý:** Porcupine chỉ hỗ trợ một số từ có sẵn. Nếu dùng từ tùy chỉnh, hệ thống sẽ dùng keyword matching (kém chính xác hơn).

### Q5: Làm sao để xem log khi có lỗi?

Mở file log trong thư mục `logs/`:

```bash
# Log chính
type logs\tyty_main.log

# Log lỗi
type logs\tyty_errors.log

# Log audio
type logs\tyty_audio.log
```

### Q6: Tỷ Tỷ có lưu lại hội thoại của tôi không?

**Có và Không:**
- Session trong RAM sẽ **tự động xóa sau 30 phút** không hoạt động
- Log file chỉ ghi **metadata** (không ghi nội dung hội thoại)
- Bạn có thể xóa thủ công: `del logs\sessions\*.json`

### Q7: Tôi có thể dùng nhiều camera cùng lúc không?

**Hiện tại chưa hỗ trợ.** Mỗi instance của hệ thống chỉ điều khiển 1 camera. Để điều khiển nhiều camera, cần chạy nhiều instance riêng biệt.

### Q8: VB-Cable là gì và tại sao cần nó?

**VB-Cable** là virtual audio cable - dây audio ảo:
- Cho phép chuyển audio từ máy tính sang camera
- Cần thiết cho **FULL_AUTOMATION mode**
- Không bắt buộc nếu dùng **BASIC mode**

**Download:** https://vb-audio.com/Cable/

### Q9: Làm sao để backup cấu hình của tôi?

Backup các file sau:

```bash
# Backup
copy .env .env.backup
copy config.py config.py.backup
copy position_config.json position_config.json.backup

# Restore
copy .env.backup .env
copy config.py.backup config.py
copy position_config.json.backup position_config.json
```

### Q10: Tỷ Tỷ có thể làm gì?

**Tỷ Tỷ có thể:**
- ✅ Trả lời câu hỏi (kiến thức chung)
- ✅ Tính toán đơn giản
- ✅ Cho biết thời gian, ngày tháng
- ✅ Trò chuyện, small talk
- ✅ Điều khiển camera (mic, speaker)
- ✅ Nhớ ngữ cảnh hội thoại (5 lượt gần nhất)

**Tỷ Tỷ KHÔNG thể:**
- ❌ Truy cập internet để tìm kiếm real-time (trừ khi được cấu hình)
- ❌ Điều khiển các thiết bị smart home khác
- ❌ Gọi điện hoặc gửi tin nhắn
- ❌ Truy cập dữ liệu cá nhân (trừ trong session hiện tại)

---

## 📞 Hỗ Trợ Kỹ Thuật

### Khi Cần Trợ Giúp

1. **Xem log lỗi:**
   ```bash
   type logs\tyty_errors.log
   ```

2. **Chạy chế độ debug:**
   ```bash
   python main.py --debug
   ```

3. **Chạy test suite:**
   ```bash
   python run_all_tests.py
   ```

4. **Xem system status:**
   ```bash
   python -m modules.system_initializer
   ```

### Thông Tin Hệ Thống

Để báo cáo lỗi, cung cấp thông tin:

```bash
# Version
python --version

# Dependencies
pip list

# System info
systeminfo | findstr /C:"OS" /C:"System"

# Log files
type logs\tyty_errors.log
```

---

## 🎓 Tips & Tricks

### 1. Nói Tự Nhiên

Bạn không cần nói từng từ rõ ràng. Hãy nói tự nhiên như với người thật:

**Good:**
```
"Tỷ Tỷ, hôm nay thời tiết Hà Nội thế nào?"
```

**Also Good:**
```
"Tỷ Tỷ, thời tiết Hà Nội hôm nay ra sao?"
```

### 2. Sử Dụng Ngữ Cảnh

Trong hội thoại nhiều lượt, bạn không cần nhắc lại thông tin:

```
Bạn: "Tỷ Tỷ, thời tiết Hà Nội hôm nay thế nào?"
Tỷ Tỷ: "Hôm nay Hà Nội trời nắng..."

Bạn: "Còn ngày mai thì sao?"  # Tỷ Tỷ hiểu "Hà Nội"
Tỷ Tỷ: "Ngày mai Hà Nội có mưa..."

Bạn: "Nhiệt độ bao nhiêu?"  # Tỷ Tỷ hiểu "ngày mai" và "Hà Nội"
```

### 3. Pause Là Quan Trọng

- **Pause 1 giây** sau "Tỷ Tỷ" - đợi "Dạ"
- **Pause 3 giây** sau câu hỏi - để hệ thống xử lý

### 4. Tối Ưu Performance

```python
# config.py - Cấu hình cho tốc độ cao
AI_PROVIDER = "ollama"  # Nhanh nhất
RESPONSE_MODE = "CONCISE"  # Phản hồi ngắn
MAX_CONTEXT_TURNS = 3  # Giảm context
SILENCE_TIMEOUT = 2.0  # Timeout ngắn hơn
```

### 5. Tối Ưu Độ Chính Xác

```python
# config.py - Cấu hình cho độ chính xác cao
AI_PROVIDER = "gemini"  # Chính xác nhất
RESPONSE_MODE = "DETAILED"  # Phản hồi chi tiết
MAX_CONTEXT_TURNS = 10  # Nhiều context hơn
WAKE_WORD_SENSITIVITY = 0.7  # Nhạy hơn
```

---

## 📚 Tài Liệu Tham Khảo

### File Quan Trọng

- `README.md` - Tổng quan dự án
- `config.py` - Cấu hình hệ thống
- `.env` - API keys và secrets
- `requirements.txt` - Dependencies
- `TASK_20_FINAL_VALIDATION_REPORT.md` - Báo cáo validation

### Thư Mục Quan Trọng

- `modules/` - Mã nguồn các module
- `logs/` - Log files
- `models/` - Wake word models
- `.kiro/specs/` - Tài liệu kỹ thuật

### Links Hữu Ích

- **Google Gemini API:** https://makersuite.google.com/
- **Ollama:** https://ollama.ai/
- **VB-Cable:** https://vb-audio.com/Cable/
- **Python:** https://www.python.org/

---

## ✅ Checklist Bắt Đầu

Trước khi sử dụng, đảm bảo:

- [ ] Python 3.8+ đã cài đặt
- [ ] Dependencies đã cài (`pip install -r requirements.txt`)
- [ ] Google Gemini API key đã cấu hình trong `.env`
- [ ] QianXin.exe đang chạy
- [ ] Đã chạy `ui_config_tool.py` và lưu vị trí nút
- [ ] File `position_config.json` đã tồn tại
- [ ] Microphone và speaker hoạt động bình thường
- [ ] Đã test với `python main.py`

**Chúc bạn sử dụng vui vẻ! 🎉**

---

**Phiên bản:** 1.0  
**Ngày cập nhật:** 30/08/2026  
**Người viết:** Kiro AI Agent
