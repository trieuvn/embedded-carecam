# 🚀 Khởi Động Nhanh - Điều Khiển Camera

**Vấn Đề:** Hệ thống chưa tự động click nút mic/speaker trên camera

**Giải Pháp Nhanh:** Dùng `carecam_bot.py` thay vì `main.py`

---

## ⚡ Cách Nhanh Nhất (2 Phút)

### Bước 1: Đảm Bảo QianXin.exe Đang Chạy

Mở ứng dụng CareCam QianXin và đảm bảo cửa sổ camera hiển thị.

### Bước 2: Chạy carecam_bot.py

```bash
cd "d:\carecam\Embeded system"
python carecam_bot.py
```

**XONG!** Hệ thống sẽ tự động điều khiển mic/speaker của camera! 🎉

---

## 📊 So Sánh 2 File

| Tính Năng | main.py (Hiện tại) | carecam_bot.py (Khuyến nghị) |
|-----------|-------------------|------------------------------|
| **Camera Control** | ❌ Chưa có | ✅ Tự động |
| **Ollama AI** | ✅ Có | ⚠️ Cần config |
| **Auto Click Mic/Speaker** | ❌ Không | ✅ Có |
| **VB-Cable Support** | ⚠️ Cần sửa | ✅ Có sẵn |
| **Kiến trúc** | ✅ Mới nhất | ⚠️ Cũ hơn |

---

## 🎯 Khuyến Nghị

### Nếu Cần Camera Control Ngay:
👉 **Dùng `python carecam_bot.py`**

### Nếu Muốn Cả Ollama + Camera Control:
👉 Xem file **`CAMERA_CONTROL_FIX.md`** để tích hợp vào `main.py`

---

## ✅ Kết Quả Mong Đợi

Khi chạy `carecam_bot.py`, bạn sẽ thấy:

```
🎥 Finding CareCam window...
✅ Found window: QianXin
🎯 Initializing components...
✅ All components ready!

🎤 Say "Tỷ Tỷ" to start...
```

Khi nói "Tỷ Tỷ":
1. ✅ Hệ thống tự động **click nút MIC** trên camera
2. ✅ Camera thu âm câu hỏi của bạn
3. ✅ AI xử lý và trả lời
4. ✅ Hệ thống tự động **click nút SPEAKER**
5. ✅ Camera phát câu trả lời

---

## 🔧 Nếu Gặp Vấn Đề

### Lỗi: "CareCam window not found"

**Giải pháp:**
1. Mở QianXin.exe
2. Đợi cửa sổ camera xuất hiện
3. Chạy lại script

### Lỗi: Click sai vị trí

**Giải pháp:**
```bash
python ui_config_tool.py
```

Làm theo hướng dẫn để cấu hình lại vị trí nút.

### Lỗi: "Module not found"

**Giải pháp:**
```bash
pip install pyaudio numpy pyautogui pygetwindow pillow
```

---

## 🎓 Nâng Cao

### Cấu Hình Ollama Trong carecam_bot.py

Mở file `carecam_bot.py` và tìm dòng:

```python
from modules.ai_service import get_ai_service
```

AI service sẽ tự động dùng config từ `config.py`. Nếu bạn đã cấu hình:

```python
AI_PROVIDER = "ollama"
```

Thì `carecam_bot.py` cũng sẽ dùng Ollama!

---

## 📞 Tóm Tắt

**Để có camera control ngay:**

```bash
cd "d:\carecam\Embeded system"
python carecam_bot.py
```

**Để có cả Ollama + Camera control:**

Xem file `CAMERA_CONTROL_FIX.md` để tích hợp vào `main.py`

---

**Trạng thái:** ✅ **GIẢI PHÁP SẴN SÀNG**  
**Thời gian:** ⚡ **2 phút**  
**Độ khó:** 🟢 **Rất dễ**

**Chúc bạn thành công! 🎉**
