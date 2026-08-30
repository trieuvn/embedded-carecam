# 🎤🔊 Logic Điều Khiển Mic/Speaker Camera

**Hardware Constraint:** Bật MIC → Speaker tự động TẮT | Bật SPEAKER → Mic tự động TẮT

---

## 🔄 Quy Trình Hoạt Động Đúng

### Trạng Thái Mặc Định
```
📢 SPEAKER: BẬT  (để nghe người từ camera nói)
🎤 MIC: TẮT      (tự động do hardware constraint)
```

**Mục đích:** PC có thể nghe người nói vào camera

---

### Khi Phát Hiện "Tỷ Tỷ"

#### Bước 1: Tỷ Tỷ Nói "Dạ"
```
🎤 MIC: BẬT      → Để phát "Dạ" qua camera speaker
📢 SPEAKER: TẮT  (tự động do hardware constraint)
```

**Code:**
```python
carecam_ctrl.click_mic_button()  # Bật mic
play_audio("Dạ")
```

#### Bước 2: Sau Khi Nói "Dạ" Xong
```
📢 SPEAKER: BẬT  → Để nghe câu hỏi từ camera
🎤 MIC: TẮT      (tự động do hardware constraint)
```

**Code:**
```python
carecam_ctrl.click_speaker_button()  # Bật loa
# Giờ có thể nghe người dùng hỏi
```

---

### Khi Xử Lý Câu Hỏi

#### Bước 3: Tỷ Tỷ Trả Lời
```
🎤 MIC: BẬT      → Để phát câu trả lời qua camera speaker
📢 SPEAKER: TẮT  (tự động do hardware constraint)
```

**Code:**
```python
carecam_ctrl.click_mic_button()  # Bật mic
play_audio("Câu trả lời...")
```

#### Bước 4: Sau Khi Trả Lời Xong
```
📢 SPEAKER: BẬT  → Quay lại trạng thái mặc định (nghe người dùng)
🎤 MIC: TẮT      (tự động do hardware constraint)
```

**Code:**
```python
carecam_ctrl.click_speaker_button()  # Bật loa
# Sẵn sàng nghe lệnh tiếp theo
```

---

## 🎯 Sơ Đồ Luồng Hoàn Chỉnh

```
[START] 
   ↓
[SPEAKER BẬT - Đang nghe người từ camera]
   ↓
[Phát hiện "Tỷ Tỷ"]
   ↓
[BẬT MIC] → Nói "Dạ" → [BẬT SPEAKER]
   ↓                         ↓
   ↓                    [Nghe câu hỏi]
   ↓                         ↓
   ↓                    [Xử lý AI]
   ↓                         ↓
   ↓                    [BẬT MIC] → Nói câu trả lời
   ↓                         ↓
   ↓                    [BẬT SPEAKER] ← Quay lại trạng thái mặc định
   ↓                         ↓
   └─────────────────────────┘
          ↓
   [Tiếp tục nghe...]
```

---

## ✅ Code Đã Sửa (carecam_bot.py)

### 1. Khởi Tạo - Bật Loa Mặc Định
```python
def initialize(self):
    # ...
    if self.carecam_ctrl.find_window():
        print("🔊 Đang bật loa để nghe người từ camera...")
        self.carecam_ctrl.click_speaker_button()  # ← BẬT LOA
        print("✅ Loa đã bật (mic tự động tắt)")
```

### 2. Hàm Nói Qua Camera
```python
def _say_to_camera(self, text: str):
    # BƯỚC 1: BẬT MIC (loa tự động tắt)
    self.carecam_ctrl.click_mic_button()
    time.sleep(0.3)
    
    # BƯỚC 2: Phát audio
    self.pipeline.play_to_virtual_cable(audio_file)
    time.sleep(audio_duration)
    
    # BƯỚC 3: BẬT LOA (mic tự động tắt)
    self.carecam_ctrl.click_speaker_button()
    time.sleep(0.3)
```

### 3. Main Loop
```python
def listen_loop(self):
    # Đảm bảo loa bật ở trạng thái mặc định
    self.carecam_ctrl.click_speaker_button()
    
    while True:
        print("👂 Đang nghe (loa đang bật)...")
        text = self.stt.listen_and_recognize()
        
        if detected_wake_word:
            # Nói "Dạ" → tự động: bật mic → nói → bật loa
            self._say_to_camera("Dạ")
            
            # Giờ loa đã bật, có thể nghe câu hỏi
            question = self.stt.listen_and_recognize()
            response = self.process_command(question)
            
            # Nói câu trả lời → tự động: bật mic → nói → bật loa
            self._say_to_camera(response)
            
            # Quay lại trạng thái mặc định (loa bật)
```

---

## 🐛 Lỗi Trước Đây

### ❌ Sai: Bật Mic Khi Khởi Động
```python
# SAI - Code cũ
if self.pipeline.has_virtual_cable():
    self._say_to_camera("Xin chào!")  # ← Bật mic ngay
```

**Vấn đề:** 
- Mic bật → Speaker tắt
- Không nghe được người từ camera nói gì!

### ✅ Đúng: Bật Loa Khi Khởi Động
```python
# ĐÚNG - Code mới
self.carecam_ctrl.click_speaker_button()  # ← Bật loa
print("✅ Loa đã bật, sẵn sàng nghe từ camera")
```

**Kết quả:**
- Loa bật → Mic tắt
- PC có thể nghe người nói vào camera!

---

## 🎯 Nguyên Tắc Quan Trọng

### 1. Luôn Biết Trạng Thái Hiện Tại
```
Đang ở trạng thái nào?
- Đang NGHE người dùng? → LOA BẬT
- Đang NÓI với người dùng? → MIC BẬT
```

### 2. Chuyển Đổi Trạng Thái Đúng Cách
```
NGHE → NÓI:
  1. Click MIC (loa tự động tắt)
  2. Phát audio
  3. Click SPEAKER (mic tự động tắt)

NÓI → NGHE:
  1. Click SPEAKER (mic tự động tắt)
  2. Sẵn sàng nhận audio
```

### 3. Luôn Về Trạng Thái Mặc Định
```
Sau mỗi tương tác:
→ BẬT LOA (để tiếp tục nghe người dùng)
```

---

## ✅ Checklist Kiểm Tra

Sau khi sửa, kiểm tra:

- [ ] **Khởi động:** Loa bật (không có tiếng click mic ngay lập tức)
- [ ] **Phát hiện "Tỷ Tỷ":** 
  - [ ] Mic bật → Nói "Dạ" → Loa bật lại
- [ ] **Nghe câu hỏi:** Loa đang bật (PC có thể nghe)
- [ ] **Trả lời:** Mic bật → Nói câu trả lời → Loa bật lại
- [ ] **Kết thúc:** Loa bật (sẵn sàng cho lần tiếp theo)

---

## 📊 Timeline Mẫu

```
00:00 - [START] Speaker BẬT (đang nghe...)
00:05 - Người dùng: "Tỷ Tỷ, 1+1 bằng mấy?"
00:06 - [Phát hiện wake word]
00:06 - Mic BẬT (speaker tự động TẮT)
00:07 - Tỷ Tỷ nói: "Dạ"
00:08 - Speaker BẬT (mic tự động TẮT)
00:09 - [AI xử lý: "1+1 bằng 2"]
00:10 - Mic BẬT (speaker tự động TẮT)
00:11 - Tỷ Tỷ nói: "1 cộng 1 bằng 2"
00:13 - Speaker BẬT (mic tự động TẮT)
00:14 - [Quay lại trạng thái mặc định - đang nghe...]
```

---

## 🚀 Test Sau Khi Sửa

```bash
cd "d:\carecam\Embeded system"
python carecam_bot.py
```

**Kỳ vọng:**
```
🎮 CareCam app detected - Chế độ TỰ ĐỘNG MIC/SPEAKER enabled!
🔊 Đang bật loa để nghe người từ camera...
✅ Loa đã bật (mic tự động tắt do hardware constraint)

👂 Đang nghe (loa đang bật)...
```

**Không thấy:**
```
🎤 Auto-hold mic for 2.0s...  ← KHÔNG CÓ dòng này lúc khởi động!
```

---

**Trạng thái:** ✅ **ĐÃ SỬA**  
**Ngày:** 30/08/2026  
**File:** `carecam_bot.py`  
**Nguyên tắc:** **Hardware Constraint - Bật cái này tắt cái kia**

**Chúc bạn thành công! 🎉**
