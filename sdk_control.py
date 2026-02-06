"""
QianXin SDK Direct Control (Python 32-bit)
Gọi trực tiếp hàm Cfg_SetMicStatus trong sdk_client.dll để bật/tắt mic camera
"""

import ctypes
from ctypes import c_int, c_char_p, c_void_p, POINTER, byref
import os
import sys

# Path to SDK DLL
SDK_DLL_PATH = r"d:\carecam\QianXin\sdk_client.dll"

class QianXinSDK:
    """Interface trực tiếp với sdk_client.dll"""
    
    def __init__(self):
        self.dll = None
        self._load_dll()
    
    def _load_dll(self):
        """Load SDK DLL"""
        try:
            # Change to DLL directory for dependencies
            os.chdir(r"d:\carecam\QianXin")
            
            self.dll = ctypes.CDLL(SDK_DLL_PATH)
            print(f"✅ SDK DLL loaded successfully!")
            
            # List available functions
            self._find_functions()
            return True
            
        except Exception as e:
            print(f"❌ Error loading DLL: {e}")
            return False
    
    def _find_functions(self):
        """Find and setup exported functions"""
        functions_to_find = [
            'ZJ_Init',
            'ZJ_Start', 
            'ZJ_Stop',
            'ZJ_SetPeerMicPhoneStatus',  # Bật/tắt mic
            'ZJ_PushAudioStream',         # Gửi audio đến camera
            'ZJ_StopPushAudioStream',     # Dừng gửi audio
            'ZJ_WriteAudioFrame',         # Ghi audio frame
            'ZJ_SetAudioParam',
            'ZJ_GetAudioDescribe',
        ]
        
        print("\n🔍 Checking exported functions:")
        for func_name in functions_to_find:
            try:
                func = getattr(self.dll, func_name)
                print(f"   ✅ {func_name}")
            except AttributeError:
                print(f"   ❌ {func_name}")
    
    def set_mic_status(self, device_id=None, enabled=True):
        """
        Bật/tắt microphone camera
        
        Uses ZJ_SetPeerMicPhoneStatus
        Possible signature: int ZJ_SetPeerMicPhoneStatus(const char* deviceId, int status)
        """
        if not self.dll:
            print("❌ DLL not loaded")
            return False
        
        try:
            func = self.dll.ZJ_SetPeerMicPhoneStatus
            
            status = 1 if enabled else 0
            
            print(f"\n🎤 Calling ZJ_SetPeerMicPhoneStatus(status={status})...")
            
            # Try different signatures
            
            # Attempt 1: Just status (int)
            try:
                func.argtypes = [ctypes.c_int]
                func.restype = ctypes.c_int
                result = func(status)
                print(f"   Attempt 1 (int): result = {result}")
                if result == 0:
                    return True
            except Exception as e1:
                print(f"   Attempt 1 failed: {e1}")
            
            # Attempt 2: device_id (string) + status (int)
            try:
                func.argtypes = [ctypes.c_char_p, ctypes.c_int]
                func.restype = ctypes.c_int
                device_bytes = b"" if device_id is None else device_id.encode()
                result = func(device_bytes, status)
                print(f"   Attempt 2 (str, int): result = {result}")
                if result == 0:
                    return True
            except Exception as e2:
                print(f"   Attempt 2 failed: {e2}")
            
            # Attempt 3: void* handle + int status
            try:
                func.argtypes = [ctypes.c_void_p, ctypes.c_int]
                func.restype = ctypes.c_int
                result = func(None, status)
                print(f"   Attempt 3 (void*, int): result = {result}")
            except Exception as e3:
                print(f"   Attempt 3 failed: {e3}")
            
            return False
            
        except AttributeError:
            print("❌ Function ZJ_SetPeerMicPhoneStatus not found")
            return False
        except Exception as e:
            print(f"❌ Error calling function: {e}")
            return False
    
    def init_sdk(self):
        """Initialize SDK"""
        try:
            init_func = self.dll.ZJ_Init
            result = init_func()
            print(f"ZJ_Init() = {result}")
            return result == 0
        except Exception as e:
            print(f"ZJ_Init failed: {e}")
            return False
    
    def start_sdk(self):
        """Start SDK"""
        try:
            start_func = self.dll.ZJ_Start
            result = start_func()
            print(f"ZJ_Start() = {result}")
            return result == 0
        except Exception as e:
            print(f"ZJ_Start failed: {e}")
            return False


def main():
    print("=" * 60)
    print("🔧 QianXin SDK Direct Control (Python 32-bit)")
    print("=" * 60)
    
    # Check Python architecture
    import struct
    bits = struct.calcsize("P") * 8
    print(f"Python: {sys.version}")
    print(f"Architecture: {bits}-bit")
    
    if bits != 32:
        print("\n⚠️  WARNING: This script should run with Python 32-bit!")
        print("   Use: Python312-32\\python.exe sdk_control.py")
    
    print()
    
    # Initialize SDK
    sdk = QianXinSDK()
    
    if sdk.dll:
        # Try to enable mic
        print("\n" + "=" * 60)
        print("🎤 Testing Mic Control")
        print("=" * 60)
        
        sdk.set_mic_status(enabled=True)


if __name__ == "__main__":
    main()
