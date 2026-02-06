"""
CareCam App Controller - Tự động điều khiển app CareCam
Chức năng: Tự động click và giữ nút mic khi phát audio
"""

import time
import threading
from typing import Optional, Tuple

try:
    import pyautogui
    import pygetwindow as gw
except ImportError:
    print("Cần cài đặt: pip install pyautogui pygetwindow pillow")
    raise


class CareCamController:
    """Điều khiển tự động app CareCam"""
    
    # Tên cửa sổ app CareCam
    WINDOW_TITLES = ["CARE SMART CAMERA", "Care Smart Camera", "QianXin"]
    
    # Vị trí tương đối của nút mic (% từ góc trái-dưới của cửa sổ)
    # Dựa trên screenshot: nút mic ở giữa dưới, khoảng 50% width, 95% height
    MIC_BUTTON_RELATIVE_X = 0.50  # 50% từ trái
    MIC_BUTTON_RELATIVE_Y = 0.94  # 94% từ trên (gần dưới cùng)
    
    def __init__(self):
        self.window = None
        self.mic_button_pos = None
        self._holding_mic = False
        self._hold_thread = None
        
        # Tắt fail-safe của pyautogui (di chuột góc màn hình sẽ không dừng)
        pyautogui.FAILSAFE = False
        pyautogui.PAUSE = 0.1
    
    def find_window(self) -> bool:
        """Tìm cửa sổ app CareCam"""
        for title in self.WINDOW_TITLES:
            windows = gw.getWindowsWithTitle(title)
            if windows:
                self.window = windows[0]
                print(f"✅ Tìm thấy cửa sổ: '{self.window.title}'")
                print(f"   Vị trí: ({self.window.left}, {self.window.top})")
                print(f"   Kích thước: {self.window.width}x{self.window.height}")
                return True
        
        print("❌ Không tìm thấy cửa sổ CareCam!")
        print(f"   Đang tìm: {self.WINDOW_TITLES}")
        return False
    
    def _calculate_mic_button_position(self) -> Optional[Tuple[int, int]]:
        """Tính vị trí nút mic dựa trên vị trí cửa sổ"""
        if not self.window:
            return None
        
        # Refresh window info
        try:
            self.window = gw.getWindowsWithTitle(self.window.title)[0]
        except:
            return None
        
        x = self.window.left + int(self.window.width * self.MIC_BUTTON_RELATIVE_X)
        y = self.window.top + int(self.window.height * self.MIC_BUTTON_RELATIVE_Y)
        
        return (x, y)
    
    def activate_window(self) -> bool:
        """Đưa cửa sổ CareCam lên foreground"""
        if not self.window:
            return False
        
        try:
            self.window.activate()
            time.sleep(0.3)
            return True
        except Exception as e:
            print(f"⚠️ Không thể activate window: {e}")
            return False
    
    def hold_mic_button(self, duration: float = 5.0):
        """
        Giữ nút mic trong một khoảng thời gian
        
        Args:
            duration: Thời gian giữ (giây)
        """
        if not self.window:
            if not self.find_window():
                print("❌ Không thể giữ mic - không tìm thấy cửa sổ")
                return
        
        pos = self._calculate_mic_button_position()
        if not pos:
            print("❌ Không thể tính vị trí nút mic")
            return
        
        print(f"🎤 Giữ nút mic tại ({pos[0]}, {pos[1]}) trong {duration:.1f}s...")
        
        # Di chuột đến nút mic
        pyautogui.moveTo(pos[0], pos[1], duration=0.2)
        
        # Nhấn và giữ
        pyautogui.mouseDown(button='left')
        self._holding_mic = True
        
        # Giữ trong duration giây
        time.sleep(duration)
        
        # Thả
        pyautogui.mouseUp(button='left')
        self._holding_mic = False
        
        print("✅ Đã thả nút mic")
    
    def hold_mic_async(self, duration: float = 5.0):
        """Giữ mic trong background thread"""
        self._hold_thread = threading.Thread(
            target=self.hold_mic_button, 
            args=(duration,)
        )
        self._hold_thread.start()
    
    def release_mic(self):
        """Thả nút mic ngay lập tức"""
        if self._holding_mic:
            pyautogui.mouseUp(button='left')
            self._holding_mic = False
            print("🔇 Thả nút mic")
    
    def click_mic_button(self):
        """Click vào nút mic (không giữ)"""
        if not self.window:
            if not self.find_window():
                return
        
        pos = self._calculate_mic_button_position()
        if pos:
            pyautogui.click(pos[0], pos[1])
            print(f"🎤 Click nút mic tại ({pos[0]}, {pos[1]})")
    
    def calibrate_mic_button(self):
        """
        Hiệu chỉnh vị trí nút mic
        Di chuột đến vị trí hiện tại để kiểm tra
        """
        if not self.find_window():
            return
        
        pos = self._calculate_mic_button_position()
        if pos:
            print(f"\n📍 Di chuột đến vị trí nút mic dự đoán: ({pos[0]}, {pos[1]})")
            print("   Kiểm tra xem con trỏ có đúng vào nút mic không...")
            
            pyautogui.moveTo(pos[0], pos[1], duration=1)
            
            print("\n💡 Nếu vị trí không đúng, điều chỉnh:")
            print(f"   MIC_BUTTON_RELATIVE_X = {self.MIC_BUTTON_RELATIVE_X}")
            print(f"   MIC_BUTTON_RELATIVE_Y = {self.MIC_BUTTON_RELATIVE_Y}")
            print("   Trong file carecam_controller.py")


# Singleton
_controller = None

def get_controller() -> CareCamController:
    global _controller
    if _controller is None:
        _controller = CareCamController()
    return _controller


if __name__ == "__main__":
    print("=" * 50)
    print("🎮 CareCam Controller Test")
    print("=" * 50)
    
    controller = get_controller()
    
    # Tìm cửa sổ
    if controller.find_window():
        print("\n🔧 Calibrating mic button position...")
        print("   Con trỏ sẽ di chuyển đến vị trí nút mic")
        print("   Nhấn Ctrl+C để hủy\n")
        
        time.sleep(2)
        controller.calibrate_mic_button()
        
        print("\n" + "=" * 50)
        print("💡 Test giữ nút mic 3 giây...")
        print("=" * 50)
        
        time.sleep(2)
        controller.hold_mic_button(duration=3)
