# ⚠️ Vấn Đề API Key - Cần Hành Động Ngay

**Ngày:** 30/08/2026  
**Trạng thái:** ⚠️ **API KEY BỊ RÒ RỈ - CẦN THAY ĐỔI**

---

## 🚨 Vấn Đề Hiện Tại

```
403 Your API key was reported as leaked. 
Please use another API key.
```

### Nguyên Nhân
API key hiện tại trong `config.py` đã bị Google phát hiện **rò rỉ công khai** (có thể do commit lên GitHub, share code, hoặc log file).

Google đã **vô hiệu hóa** key này để bảo mật.

---

## ✅ Giải Pháp: Tạo API Key Mới

### Bước 1: Truy Cập Google AI Studio

Mở trình duyệt và truy cập:
```
https://aistudio.google.com/app/apikey
```

### Bước 2: Đăng Nhập

Đăng nhập bằng tài khoản Google của bạn

### Bước 3: Tạo API Key Mới

1. Click nút **"Create API Key"** hoặc **"Get API key"**
2. Chọn project (hoặc tạo project mới nếu chưa có)
3. Click **"Create API key in new project"** hoặc chọn project có sẵn
4. **Sao chép** API key vừa tạo (dạng: `AIzaSy...`)

### Bước 4: Cập Nhật Config

**Option 1: Sửa trực tiếp trong config.py (Nhanh nhất)**

Mở file `config.py`, tìm dòng ~41:
```python
GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "AIzaSy...")
```

Thay đổi thành:
```python
GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "API_KEY_MỚI_CỦA_BẠN")
```

**Option 2: Sử dụng file .env (An toàn hơn - KHUYẾN NGHỊ)**

1. Tạo/mở file `.env` trong thư mục `d:\carecam\Embeded system\`
2. Thêm dòng:
```
GOOGLE_API_KEY=API_KEY_MỚI_CỦA_BẠN
```

3. Trong `config.py`, đảm bảo dòng này không có giá trị mặc định:
```python
GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
```

### Bước 5: Test Lại

```bash
cd "d:\carecam\Embeded system"
python -c "from modules.ai_service import get_ai_service; service = get_ai_service('gemini'); print(service.get_response('Xin chào'))"
```

**Kết quả mong đợi:**
```
Xin chào! Tôi là Tỷ Tỷ, trợ lý ảo của bạn...
```

---

## 🔒 Bảo Mật API Key (Quan Trọng!)

### ❌ KHÔNG BAO GIỜ:
1. **Commit API key lên GitHub/GitLab** (public hoặc private)
2. **Share code có chứa API key** qua chat, email
3. **Đặt API key trong log file** hoặc output console
4. **Hardcode API key** trực tiếp trong code

### ✅ NÊN:
1. **Dùng file `.env`** và thêm vào `.gitignore`
2. **Dùng environment variables**
3. **Không commit file `.env`** lên version control
4. **Rotate (thay đổi) API key định kỳ** (3-6 tháng)

### File `.gitignore` Nên Có:

```gitignore
# Environment variables
.env
.env.local
.env.*.local

# Config với secrets
config.local.py

# Logs có thể chứa sensitive data
logs/*.log
*.log

# Position config (có thể chứa thông tin nhạy cảm)
position_config.json
```

---

## 🔄 Sau Khi Sửa

### Checklist

- [ ] Tạo API key mới tại Google AI Studio
- [ ] Cập nhật vào `.env` hoặc `config.py`
- [ ] Xóa API key cũ khỏi Google AI Studio
- [ ] Test lại: `python -c "..."`
- [ ] Đảm bảo `.env` có trong `.gitignore`
- [ ] Không commit API key mới lên git

### Test Commands

```bash
# Test AI Service
python -c "from modules.ai_service import get_ai_service; service = get_ai_service('gemini'); print('✅ OK')"

# Test với câu hỏi thật
python -c "from modules.ai_service import get_ai_service; service = get_ai_service('gemini'); print(service.get_response('2+2 bằng mấy?'))"
```

---

## 🎯 Alternative: Dùng Ollama (Không Cần API Key)

Nếu không muốn dùng API key hoặc lo ngại bảo mật, có thể dùng **Ollama** (AI cục bộ):

### Ưu Điểm Ollama
- ✅ **Không cần API key**
- ✅ **Chạy offline** (không cần internet)
- ✅ **Miễn phí hoàn toàn**
- ✅ **Bảo mật cao** (dữ liệu không ra ngoài)
- ✅ **Không có vấn đề quota hoặc rate limit**

### Cài Đặt Ollama

**Bước 1:** Tải Ollama
```
https://ollama.ai/download
```

**Bước 2:** Cài model
```bash
ollama pull qwen2.5:0.5b
```

**Bước 3:** Cấu hình
```python
# Trong config.py
AI_PROVIDER = "ollama"  # Hoặc "auto" để fallback Gemini
```

**Bước 4:** Chạy
```bash
python main.py
```

✅ **Không cần lo API key nữa!**

---

## 📊 So Sánh Gemini vs Ollama

| Tiêu chí | Gemini | Ollama |
|----------|--------|--------|
| **API Key** | ⚠️ Cần | ✅ Không cần |
| **Internet** | ⚠️ Cần | ✅ Không cần |
| **Bảo mật** | ⚠️ Dữ liệu ra ngoài | ✅ Dữ liệu local |
| **Chi phí** | ⚠️ Có quota | ✅ Miễn phí |
| **Cài đặt** | ✅ Dễ | ⚠️ Cần cài thêm |
| **Hiệu năng** | ✅ Rất tốt | ✅ Tốt |
| **Độ chính xác** | ✅ Rất cao | ✅ Cao |

---

## 🆘 Nếu Vẫn Gặp Lỗi

### Lỗi: "Invalid API key"

```
400 API key not valid
```

**Nguyên nhân:** API key sai format hoặc không hợp lệ

**Giải pháp:**
1. Kiểm tra API key có dạng: `AIzaSy...` (bắt đầu bằng AIzaSy)
2. Không có khoảng trắng ở đầu/cuối
3. Tạo lại API key mới

### Lỗi: "Quota exceeded"

```
429 Resource has been exhausted
```

**Nguyên nhân:** Vượt quá giới hạn miễn phí của Gemini

**Giải pháp:**
1. Đợi 1 phút rồi thử lại
2. Hoặc chuyển sang dùng Ollama (không giới hạn)

### Lỗi: "API key still reported as leaked"

**Nguyên nhân:** Dùng API key đã bị vô hiệu hóa

**Giải pháp:**
1. Xóa API key cũ trong Google Cloud Console
2. Tạo API key hoàn toàn mới
3. Cập nhật lại

---

## 📞 Tóm Tắt Nhanh

### Để Sửa Ngay:
1. ✅ Truy cập: https://aistudio.google.com/app/apikey
2. ✅ Tạo API key mới
3. ✅ Sao chép key
4. ✅ Mở `config.py` hoặc tạo file `.env`
5. ✅ Dán key vào: `GOOGLE_API_KEY = "key_mới"`
6. ✅ Test: `python main.py`

### Hoặc Dùng Ollama (Không Cần Key):
1. ✅ Tải: https://ollama.ai/download
2. ✅ Cài: `ollama pull qwen2.5:0.5b`
3. ✅ Config: `AI_PROVIDER = "ollama"`
4. ✅ Chạy: `python main.py`

---

**Trạng thái:** ⚠️ **CẦN HÀNH ĐỘNG** - Tạo API key mới hoặc chuyển sang Ollama  
**Ưu tiên:** 🔥 **CAO**  
**Thời gian sửa:** ~5 phút

**Chúc bạn thành công! 🎉**
