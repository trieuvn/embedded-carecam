"""
Approach mới: Thay vì gọi SDK trực tiếp, ta sẽ:
1. Click mic button như bình thường (để nó gọi SDK đúng cách)
2. Nhưng IMMEDIATELY sau đó, bật lại speaker bằng cách click speaker button

Vì hai actions xảy ra gần như đồng thời, có thể tạo ra hiệu ứng full-duplex.

Hoặc: Hook/intercept message khi app cố tắt speaker, và block nó.
"""
import ctypes
from ctypes import wintypes
import time
import subprocess

# Windows API
user32 = ctypes.windll.user32
FindWindowW = user32.FindWindowW
FindWindowExW = user32.FindWindowExW
SendMessageW = user32.SendMessageW
PostMessageW = user32.PostMessageW
EnumChildWindows = user32.EnumChildWindows
GetClassNameW = user32.GetClassNameW
GetWindowTextW = user32.GetWindowTextW
GetWindowRect = user32.GetWindowRect

WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP = 0x0202

class RECT(ctypes.Structure):
    _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                ("right", ctypes.c_long), ("bottom", ctypes.c_long)]


def find_qianxin_window():
    """Find main QianXin window"""
    titles = ["QianXin", "CARE SMART CAMERA", "千心"]
    for title in titles:
        hwnd = FindWindowW(None, title)
        if hwnd:
            return hwnd
    return None


def click_at_position(hwnd, x, y):
    """Send click to window at position"""
    lparam = (y << 16) | (x & 0xFFFF)
    PostMessageW(hwnd, WM_LBUTTONDOWN, 1, lparam)
    time.sleep(0.05)
    PostMessageW(hwnd, WM_LBUTTONUP, 0, lparam)


def get_window_size(hwnd):
    """Get window dimensions"""
    rect = RECT()
    GetWindowRect(hwnd, ctypes.byref(rect))
    return rect.right - rect.left, rect.bottom - rect.top


def rapid_toggle_test():
    """
    Test rapid toggle: bật mic rồi NGAY LẬP TỨC bật lại speaker
    """
    print("=" * 60)
    print("Rapid Toggle Test")
    print("=" * 60)
    
    hwnd = find_qianxin_window()
    if not hwnd:
        print("❌ Không tìm thấy cửa sổ QianXin")
        return
    
    width, height = get_window_size(hwnd)
    print(f"Window size: {width}x{height}")
    
    # Button positions (relative)
    # Mic button: center-bottom
    mic_x = int(width * 0.5)
    mic_y = int(height * 0.94)
    
    # Speaker button: right side, near bottom
    speaker_x = int(width * 0.90)
    speaker_y = int(height * 0.94)
    
    print(f"Mic button: ({mic_x}, {mic_y})")
    print(f"Speaker button: ({speaker_x}, {speaker_y})")
    
    print("\n⚠️ QUAN TRỌNG:")
    print("   1. Đảm bảo SPEAKER đang BẬT trong app")
    print("   2. Cửa sổ app phải visible (không minimize)")
    print("\nNhấn Enter để test...")
    input()
    
    print("\n[1] Clicking mic button (sẽ tắt speaker)...")
    click_at_position(hwnd, mic_x, mic_y)
    
    # Wait a tiny bit
    time.sleep(0.05)
    
    print("[2] Immediately clicking speaker button (để bật lại)...")
    click_at_position(hwnd, speaker_x, speaker_y)
    
    print("\nKiểm tra app: cả mic VÀ speaker có đang bật không?")
    print("\n(Nếu không, thử tăng/giảm delay giữa 2 clicks)")
    

def continuous_reactivate_speaker():
    """
    Continuously monitor and reactivate speaker if it gets turned off
    This creates a pseudo full-duplex by rapidly toggling speaker back on
    """
    print("=" * 60)
    print("Continuous Speaker Re-activation")
    print("=" * 60)
    
    hwnd = find_qianxin_window()
    if not hwnd:
        print("❌ Không tìm thấy cửa sổ QianXin")
        return
    
    width, height = get_window_size(hwnd)
    
    # Speaker button position
    speaker_x = int(width * 0.90)
    speaker_y = int(height * 0.94)
    
    print("Chế độ này sẽ liên tục click speaker button mỗi 500ms")
    print("Điều này giúp duy trì speaker ON ngay cả khi mic được bật")
    print("\nNhấn Ctrl+C để dừng...")
    
    try:
        while True:
            click_at_position(hwnd, speaker_x, speaker_y)
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nĐã dừng.")


def main():
    print("\nChọn mode test:")
    print("1. Rapid Toggle (click mic rồi speaker liên tiếp)")
    print("2. Continuous Reactivate (liên tục bật lại speaker)")
    print("\nNhập 1 hoặc 2: ", end="")
    
    choice = input().strip()
    
    if choice == "1":
        rapid_toggle_test()
    elif choice == "2":
        continuous_reactivate_speaker()
    else:
        print("Invalid choice")


if __name__ == "__main__":
    main()
