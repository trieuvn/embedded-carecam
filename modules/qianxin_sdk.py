"""
QianXin SDK Interface
Giao tiếp trực tiếp với sdk_client.dll để điều khiển camera
"""

import ctypes
from ctypes import c_int, c_char_p, c_void_p, POINTER, byref
import os
import time

# Path to SDK DLL
SDK_DLL_PATH = r"d:\carecam\QianXin\sdk_client.dll"


class QianXinSDK:
    """
    Interface để gọi trực tiếp functions trong sdk_client.dll
    
    Các function đã tìm thấy:
    - Cfg_SetMicStatus: Bật/tắt mic
    - Cfg_SetMicVolume: Điều chỉnh âm lượng
    - Cfg_SetAudioParam: Thiết lập tham số audio
    """
    
    def __init__(self, dll_path: str = SDK_DLL_PATH):
        self.dll = None
        self.dll_path = dll_path
        self._load_dll()
    
    def _load_dll(self):
        """Load SDK DLL"""
        if not os.path.exists(self.dll_path):
            print(f"❌ Không tìm thấy DLL: {self.dll_path}")
            return False
        
        try:
            # Load DLL
            self.dll = ctypes.CDLL(self.dll_path)
            print(f"✅ Loaded: {os.path.basename(self.dll_path)}")
            
            # Try to find exported functions
            self._find_exports()
            return True
            
        except Exception as e:
            print(f"❌ Lỗi load DLL: {e}")
            return False
    
    def _find_exports(self):
        """Tìm các function exported từ DLL"""
        if not self.dll:
            return
        
        print("\n🔍 Tìm các functions...")
        
        # List of functions to look for
        functions = [
            'Cfg_SetMicStatus',
            'Cfg_SetMicVolume', 
            'Cfg_SetAudioParam',
            'Cfg_StartAddDevice',
            'Cfg_SetInIotOpenFlag',
        ]
        
        for func_name in functions:
            try:
                func = getattr(self.dll, func_name)
                print(f"   ✅ Found: {func_name}")
            except AttributeError:
                print(f"   ❌ Not found: {func_name}")
    
    def set_mic_status(self, enabled: bool = True) -> bool:
        """
        Bật/tắt mic camera
        
        Args:
            enabled: True = bật mic, False = tắt mic
        
        Returns:
            True nếu thành công
        """
        if not self.dll:
            print("❌ DLL chưa được load")
            return False
        
        try:
            # Try to call Cfg_SetMicStatus
            # Note: Chưa biết chính xác signature của function
            # Có thể cần thử nhiều cách
            
            func = self.dll.Cfg_SetMicStatus
            
            # Thử với int parameter (1 = on, 0 = off)
            status = 1 if enabled else 0
            result = func(status)
            
            print(f"🎤 SetMicStatus({status}) = {result}")
            return result == 0  # Giả sử 0 = success
            
        except Exception as e:
            print(f"❌ Lỗi gọi Cfg_SetMicStatus: {e}")
            return False
    
    def set_mic_volume(self, volume: int = 100) -> bool:
        """
        Điều chỉnh âm lượng mic
        
        Args:
            volume: 0-100
        """
        if not self.dll:
            return False
        
        try:
            func = self.dll.Cfg_SetMicVolume
            result = func(volume)
            print(f"🔊 SetMicVolume({volume}) = {result}")
            return result == 0
        except Exception as e:
            print(f"❌ Lỗi gọi Cfg_SetMicVolume: {e}")
            return False


def analyze_dll_exports():
    """Phân tích chi tiết DLL exports sử dụng PE format"""
    import struct
    
    with open(SDK_DLL_PATH, 'rb') as f:
        data = f.read()
    
    # Tìm DOS header
    if data[:2] != b'MZ':
        print("Not a valid PE file")
        return
    
    # PE offset
    pe_offset = struct.unpack('<I', data[0x3C:0x40])[0]
    
    print(f"PE header at: 0x{pe_offset:X}")
    
    # Check PE signature
    if data[pe_offset:pe_offset+4] != b'PE\x00\x00':
        print("Invalid PE signature")
        return
    
    # Number of sections
    num_sections = struct.unpack('<H', data[pe_offset+6:pe_offset+8])[0]
    print(f"Number of sections: {num_sections}")
    
    # Optional header size
    opt_header_size = struct.unpack('<H', data[pe_offset+20:pe_offset+22])[0]
    print(f"Optional header size: {opt_header_size}")
    
    # Data directories start
    opt_header_start = pe_offset + 24
    
    # Export table RVA (first data directory)
    # For 32-bit: at offset 96 from optional header
    # For 64-bit: at offset 112 from optional header
    
    # Check if 32 or 64 bit
    magic = struct.unpack('<H', data[opt_header_start:opt_header_start+2])[0]
    if magic == 0x10b:  # PE32
        export_rva_offset = opt_header_start + 96
    else:  # PE32+
        export_rva_offset = opt_header_start + 112
    
    export_rva = struct.unpack('<I', data[export_rva_offset:export_rva_offset+4])[0]
    export_size = struct.unpack('<I', data[export_rva_offset+4:export_rva_offset+8])[0]
    
    print(f"Export table RVA: 0x{export_rva:X}, Size: {export_size}")
    
    if export_rva == 0:
        print("No exports found")
        return
    
    print("\n📋 DLL có export table - có thể gọi functions trực tiếp!")


if __name__ == "__main__":
    print("=" * 60)
    print("🔧 QianXin SDK Analyzer")
    print("=" * 60)
    
    # Analyze exports
    print("\n📊 Analyzing DLL structure...")
    analyze_dll_exports()
    
    # Try to load SDK
    print("\n📦 Loading SDK...")
    sdk = QianXinSDK()
    
    if sdk.dll:
        print("\n💡 SDK loaded successfully!")
        print("   Có thể thử gọi sdk.set_mic_status(True) để bật mic")
