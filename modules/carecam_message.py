"""
CareCam Window Message Controller
Gửi Windows Messages trực tiếp đến nút mic mà không cần di chuyển chuột
"""

import ctypes
from ctypes import wintypes
import time

# Windows API
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

# Constants
WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP = 0x0202
WM_MOUSEMOVE = 0x0200
MK_LBUTTON = 0x0001
BM_CLICK = 0x00F5

# FindWindow
FindWindowW = user32.FindWindowW
FindWindowW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR]
FindWindowW.restype = wintypes.HWND

# FindWindowEx
FindWindowExW = user32.FindWindowExW
FindWindowExW.argtypes = [wintypes.HWND, wintypes.HWND, wintypes.LPCWSTR, wintypes.LPCWSTR]
FindWindowExW.restype = wintypes.HWND

# EnumChildWindows
WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
EnumChildWindows = user32.EnumChildWindows
EnumChildWindows.argtypes = [wintypes.HWND, WNDENUMPROC, wintypes.LPARAM]

# GetWindowRect
GetWindowRect = user32.GetWindowRect
GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]

# SendMessage
SendMessageW = user32.SendMessageW
SendMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
SendMessageW.restype = wintypes.LPARAM

# PostMessage
PostMessageW = user32.PostMessageW
PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
PostMessageW.restype = wintypes.BOOL

# GetClassName
GetClassNameW = user32.GetClassNameW
GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
GetClassNameW.restype = ctypes.c_int

# GetWindowText
GetWindowTextW = user32.GetWindowTextW
GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
GetWindowTextW.restype = ctypes.c_int

# ScreenToClient
ScreenToClient = user32.ScreenToClient
ScreenToClient.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.POINT)]


def MAKELPARAM(low, high):
    """Create LPARAM from low and high words"""
    return (high << 16) | (low & 0xFFFF)


class CareCamMessageController:
    """Điều khiển CareCam qua Windows Messages"""
    
    WINDOW_TITLES = ["CARE SMART CAMERA", "Care Smart Camera", "QianXin"]
    
    def __init__(self):
        self.hwnd = None
        self.child_windows = []
        
    def find_window(self) -> bool:
        """Tìm cửa sổ CareCam"""
        for title in self.WINDOW_TITLES:
            self.hwnd = FindWindowW(None, title)
            if self.hwnd:
                print(f"✅ Found window: '{title}' (hwnd=0x{self.hwnd:X})")
                return True
        
        print("❌ Không tìm thấy cửa sổ CareCam")
        return False
    
    def enumerate_children(self):
        """Liệt kê tất cả child windows"""
        if not self.hwnd:
            return
        
        self.child_windows = []
        
        def callback(hwnd, lparam):
            # Get class name
            class_name = ctypes.create_unicode_buffer(256)
            GetClassNameW(hwnd, class_name, 256)
            
            # Get window text
            text = ctypes.create_unicode_buffer(256)
            GetWindowTextW(hwnd, text, 256)
            
            # Get rect
            rect = wintypes.RECT()
            GetWindowRect(hwnd, ctypes.byref(rect))
            
            self.child_windows.append({
                'hwnd': hwnd,
                'class': class_name.value,
                'text': text.value,
                'rect': (rect.left, rect.top, rect.right, rect.bottom)
            })
            return True
        
        EnumChildWindows(self.hwnd, WNDENUMPROC(callback), 0)
        
        print(f"\n📋 Found {len(self.child_windows)} child windows:")
        for i, w in enumerate(self.child_windows[:20]):
            print(f"  [{i}] hwnd=0x{w['hwnd']:X} class='{w['class']}' text='{w['text'][:30]}' rect={w['rect']}")
    
    def find_button_by_position(self, rel_x: float, rel_y: float):
        """Tìm button gần vị trí tương đối trong cửa sổ"""
        if not self.hwnd:
            return None
        
        # Get main window rect
        rect = wintypes.RECT()
        GetWindowRect(self.hwnd, ctypes.byref(rect))
        
        target_x = rect.left + int((rect.right - rect.left) * rel_x)
        target_y = rect.top + int((rect.bottom - rect.top) * rel_y)
        
        print(f"🎯 Target position: ({target_x}, {target_y})")
        
        # Find closest button
        for w in self.child_windows:
            if 'button' in w['class'].lower():
                r = w['rect']
                if r[0] <= target_x <= r[2] and r[1] <= target_y <= r[3]:
                    print(f"   Found button: hwnd=0x{w['hwnd']:X}")
                    return w['hwnd']
        
        return None
    
    def send_click_to_position(self, rel_x: float = 0.50, rel_y: float = 0.94, hold_duration: float = 0):
        """
        Gửi click message đến vị trí trong cửa sổ
        
        Args:
            rel_x: Vị trí X tương đối (0.0-1.0)
            rel_y: Vị trí Y tương đối (0.0-1.0)  
            hold_duration: Thời gian giữ (giây), 0 = click thường
        """
        if not self.hwnd:
            if not self.find_window():
                return False
        
        # Get window rect
        rect = wintypes.RECT()
        GetWindowRect(self.hwnd, ctypes.byref(rect))
        
        # Calculate screen coordinates
        screen_x = rect.left + int((rect.right - rect.left) * rel_x)
        screen_y = rect.top + int((rect.bottom - rect.top) * rel_y)
        
        # Convert to client coordinates
        point = wintypes.POINT(screen_x, screen_y)
        ScreenToClient(self.hwnd, ctypes.byref(point))
        
        lparam = MAKELPARAM(point.x, point.y)
        
        print(f"🖱️ Sending click to ({point.x}, {point.y}) in window")
        
        # Send mouse down
        PostMessageW(self.hwnd, WM_LBUTTONDOWN, MK_LBUTTON, lparam)
        
        if hold_duration > 0:
            print(f"   Holding for {hold_duration:.1f}s...")
            time.sleep(hold_duration)
        
        # Send mouse up
        PostMessageW(self.hwnd, WM_LBUTTONUP, 0, lparam)
        
        print("✅ Click sent!")
        return True
    
    def hold_mic(self, duration: float = 5.0):
        """Giữ nút mic trong duration giây"""
        # Mic button at center-bottom: x=50%, y=94%
        return self.send_click_to_position(0.50, 0.94, hold_duration=duration)
    
    def toggle_speaker(self):
        """Click vào nút speaker"""
        # Speaker button: right side, near bottom
        return self.send_click_to_position(0.90, 0.94, hold_duration=0)


if __name__ == "__main__":
    print("=" * 60)
    print("🎮 CareCam Message Controller Test")
    print("=" * 60)
    
    ctrl = CareCamMessageController()
    
    if ctrl.find_window():
        # Enumerate children
        ctrl.enumerate_children()
        
        # Test hold mic for 3 seconds
        print("\n🎤 Test giữ nút mic 3 giây...")
        print("   (Script sẽ gửi message trực tiếp, không di chuột)")
        time.sleep(2)
        
        ctrl.hold_mic(duration=3)
