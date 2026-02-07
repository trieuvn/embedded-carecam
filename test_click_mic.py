"""
Click Mic Button - Direct PyAutoGUI approach
"""
import ctypes
from ctypes import wintypes
import time

user32 = ctypes.windll.user32

SW_RESTORE = 9
SW_SHOW = 5

FindWindowW = user32.FindWindowW
FindWindowW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR]
FindWindowW.restype = wintypes.HWND

GetWindowRect = user32.GetWindowRect
GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]

ShowWindow = user32.ShowWindow
SetForegroundWindow = user32.SetForegroundWindow
IsIconic = user32.IsIconic


def main():
    print("=" * 60)
    print("Click Mic Button")
    print("=" * 60)
    
    # Find window
    hwnd = FindWindowW(None, "CARE SMART CAMERA")
    if not hwnd:
        print("CareCam window not found!")
        return
    
    print(f"Found window: hwnd=0x{hwnd:X}")
    
    # Check if minimized
    if IsIconic(hwnd):
        print("Window is minimized, restoring...")
        ShowWindow(hwnd, SW_RESTORE)
        time.sleep(0.5)
    
    # Bring to front
    SetForegroundWindow(hwnd)
    time.sleep(0.3)
    
    # Get window rect
    rect = wintypes.RECT()
    GetWindowRect(hwnd, ctypes.byref(rect))
    
    width = rect.right - rect.left
    height = rect.bottom - rect.top
    
    print(f"Window: ({rect.left}, {rect.top}) size={width}x{height}")
    
    if width < 100 or height < 100:
        print("Window still too small, may need manual restore")
        return
    
    # Use pyautogui for clicking
    try:
        import pyautogui
        
        # Mic button position - based on screenshot:
        # Camera panel is on right side, mic button in center-bottom of that panel
        # Try multiple positions
        
        positions = [
            (0.62, 0.65, "Center-bottom of camera"),
            (0.70, 0.65, "Further right"),
            (0.55, 0.60, "More centered"),
        ]
        
        for rel_x, rel_y, desc in positions:
            click_x = rect.left + int(width * rel_x)
            click_y = rect.top + int(height * rel_y)
            
            print(f"\nTrying: {desc}")
            print(f"  Position: ({click_x}, {click_y})")
            print(f"  Holding 5 seconds - noi vao mic PC!")
            
            pyautogui.click(click_x, click_y)
            time.sleep(0.2)
            pyautogui.mouseDown(click_x, click_y)
            time.sleep(5)
            pyautogui.mouseUp()
            
            print("  Released. Nut mic co sang len khong?")
            time.sleep(2)
            
    except ImportError:
        print("pyautogui not installed")
    
    print("\nDone!")


if __name__ == "__main__":
    main()
