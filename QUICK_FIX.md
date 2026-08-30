# Quick Fix - Sửa Lỗi Import và Cấu Hình

## ✅ Lỗi Import Đã Được Sửa

**Lỗi ban đầu:**
```
ImportError: cannot import name 'genai' from 'google'
```

**Đã sửa trong:** `modules\ai_service.py`
- Thay đổi: `from google import genai` → `import google.generativeai as genai`

---

## 🔧 Vấn Đề Hiện Tại: Ollama Chưa Cài Đặt

### Triệu chứng:
- Hệ thống khởi động nhưng bị treo ở bước "trying Ollama first..."
- Ollama chưa được cài đặt trên máy

### Giải pháp: Có 2 lựa chọn

---

## 🚀 OPTION 1: Sử Dụng Google Gemini (Đơn Giản Nhất - KHUYẾN NGHỊ)

**Ưu điểm:**
- ✅ Không cần cài thêm phần mềm
- ✅ Chỉ cần API key (đã có)
- ✅ Chạy ngay lập tức

**Cách làm:**

### Bước 1: Mở file `config.py`

Tìm dòng:
```python
AI_PROVIDER = "auto"  # auto, gemini, ollama
```

Sửa thành:
```python
AI_PROVIDER = "gemini"  # Chỉ dùng Gemini, không cần Ollama
```

### Bước 2: Chạy lại

```bash
cd "d:\carecam\Embeded system"
python main.py
```

**Xong!** Hệ thống sẽ chạy với Google Gemini.

---

## 🏠 OPTION 2: Cài Đặt Ollama (AI Cục Bộ - Nâng Cao)

**Ưu điểm:**
- ✅ Chạy offline (không cần internet)
- ✅ Nhanh hơn
- ✅ Miễn phí hoàn toàn
- ✅ Bảo mật hơn (dữ liệu không ra ngoài)

**Nhược điểm:**
- ⚠️ Cần cài đặt thêm phần mềm (~500MB)
- ⚠️ Tốn RAM (~2-4GB khi chạy)

**Cách làm:**

### Bước 1: Tải Ollama

Truy cập: **https://ollama.ai/download**

Tải phiên bản Windows và cài đặt.

### Bước 2: Cài Model Vietnamese

Mở Command Prompt/PowerShell và chạy:

```bash
# Khởi động Ollama (nếu chưa tự động chạy)
ollama serve

# Mở terminal khác và tải model tiếng Việt
ollama pull qwen2.5:0.5b
```

**Lưu ý:** Model ~320MB, cần internet để tải lần đầu.

### Bước 3: Kiểm Tra Ollama

```bash
ollama list
```

Bạn sẽ thấy:
```
NAME             ID          SIZE
qwen2.5:0.5b     abc123      320MB
```

### Bước 4: Cấu Hình

Mở `config.py`, đảm bảo:
```python
AI_PROVIDER = "auto"  # Hoặc "ollama"
OLLAMA_URL = "http://localhost:11434"
OLLAMA_MODEL = "qwen2.5:0.5b"
```

### Bước 5: Chạy lại

```bash
python main.py
```

Hệ thống sẽ dùng Ollama. Nếu Ollama không khả dụng, tự động fallback sang Gemini.

---

## 📊 So Sánh 2 Options

| Tiêu chí | Gemini (Option 1) | Ollama (Option 2) |
|----------|-------------------|-------------------|
| **Cài đặt** | ✅ Dễ (chỉ config) | ⚠️ Cần cài thêm |
| **Internet** | ⚠️ Cần | ✅ Không cần |
| **Tốc độ** | ⚠️ Trung bình | ✅ Nhanh |
| **Chi phí** | ⚠️ API quota | ✅ Miễn phí |
| **RAM** | ✅ Ít (~200MB) | ⚠️ Nhiều (~2-4GB) |
| **Độ chính xác** | ✅ Rất cao | ✅ Tốt |
| **Bảo mật** | ⚠️ Dữ liệu ra ngoài | ✅ Dữ liệu local |

---

## 🎯 Khuyến Nghị

### Cho người mới bắt đầu:
👉 **Chọn OPTION 1 (Gemini)**
- Đơn giản nhất
- Chỉ cần sửa 1 dòng config
- Chạy ngay

### Cho người dùng nâng cao:
👉 **Chọn OPTION 2 (Ollama)**
- Hiệu năng tốt hơn
- Không phụ thuộc internet
- Bảo mật cao hơn

### Lựa chọn linh hoạt:
👉 **Giữ AUTO mode**
- Dùng Ollama khi có
- Fallback Gemini khi cần
- Tốt nhất cả 2!

---

## ✅ Kiểm Tra Sau Khi Sửa

### Test 1: Chạy hệ thống

```bash
cd "d:\carecam\Embeded system"
python main.py
```

**Kết quả mong đợi:**
```
✅ AI Service initialized with Gemini (gemini-2.0-flash-exp)
```

Hoặc (nếu dùng Ollama):
```
✅ AI Service initialized with Ollama (qwen2.5:0.5b)
```

### Test 2: Thử hội thoại

Nói: **"Tỷ Tỷ"**

Chờ nghe: **"Dạ"**

Nói: **"Hôm nay thứ mấy?"**

Chờ phản hồi.

---

## 🆘 Nếu Vẫn Lỗi

### Lỗi: "API key invalid"

**Giải pháp:**
1. Mở file `.env`
2. Kiểm tra `GEMINI_API_KEY=...`
3. Lấy key mới tại: https://makersuite.google.com/app/apikey
4. Cập nhật vào `.env`

### Lỗi: "Connection timeout"

**Nguyên nhân:** Đang dùng AUTO mode nhưng Ollama chưa cài

**Giải pháp:** Chuyển sang Gemini (Option 1)

### Lỗi: "No module named 'google.generativeai'"

**Giải pháp:**
```bash
pip install google-generativeai --upgrade
```

### Lỗi khác

Xem chi tiết trong:
```bash
type logs\tyty_errors.log
```

---

## 📞 Liên Hệ

Nếu vẫn gặp vấn đề, cung cấp thông tin:

```bash
# Python version
python --version

# Dependencies
pip list | findstr google

# Log
type logs\tyty_errors.log
```

---

**Cập nhật:** 30/08/2026  
**Trạng thái:** ✅ Lỗi import đã được sửa  
**Khuyến nghị:** Chọn Option 1 (Gemini) để bắt đầu nhanh nhất
