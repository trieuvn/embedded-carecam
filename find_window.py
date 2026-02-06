"""Find CareCam window"""
import ctypes
from ctypes import wintypes

user32 = ctypes.windll.user32

# EnumWindows callback
WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

windows = []

def enum_callback(hwnd, lparam):
    if user32.IsWindowVisible(hwnd):
        length = user32.GetWindowTextLengthW(hwnd)
        if length > 0:
            buff = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buff, length + 1)
            title = buff.value
            windows.append((hwnd, title))
    return True

# Enumerate all windows
user32.EnumWindows(WNDENUMPROC(enum_callback), 0)

print(f"Found {len(windows)} visible windows\n")
print("Windows with 'care', 'cam', 'qian', 'smart' in title:")
print("-" * 60)

for hwnd, title in windows:
    lower = title.lower()
    if any(k in lower for k in ['care', 'cam', 'qian', 'smart']):
        print(f"hwnd=0x{hwnd:08X} title='{title}'")

print("\n" + "-" * 60)
print("All visible windows:")
for hwnd, title in windows[:30]:
    print(f"  0x{hwnd:08X}: {title[:50]}")
