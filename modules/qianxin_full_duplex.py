"""
QianXin Full-Duplex Audio Controller
Cho phép mở mic và speaker cùng lúc bằng cách bypass UI logic.

Thay vì click nút mic trong UI (sẽ tắt speaker), ta sử dụng SDK injection
để stream audio trực tiếp đến camera.

VERIFIED WORKING FUNCTIONS:
- ZJ_PushSoundFile(deviceId, filePath) -> returns 0 on success
- ZJ_PlayPeerSoundFile(filePath, deviceId) -> returns 0 on success

APPROACH:
Thay vì dùng ZJ_PushAudioStream (trả error), ta dùng ZJ_PushSoundFile
đã verified hoạt động tốt. Điều này cho phép gửi audio files đến camera
mà KHÔNG ảnh hưởng đến trạng thái speaker trong app.
"""

import ctypes
from ctypes import wintypes
import struct
import subprocess
import os
import re
import tempfile


# Windows API constants
PROCESS_ALL_ACCESS = 0x1F0FFF
MEM_COMMIT = 0x1000
MEM_RESERVE = 0x2000
MEM_RELEASE = 0x8000
PAGE_EXECUTE_READWRITE = 0x40
INFINITE = 0xFFFFFFFF

kernel32 = ctypes.windll.kernel32

OpenProcess = kernel32.OpenProcess
OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
OpenProcess.restype = wintypes.HANDLE
CloseHandle = kernel32.CloseHandle
VirtualAllocEx = kernel32.VirtualAllocEx
VirtualAllocEx.argtypes = [wintypes.HANDLE, wintypes.LPVOID, ctypes.c_size_t, wintypes.DWORD, wintypes.DWORD]
VirtualAllocEx.restype = wintypes.LPVOID
VirtualFreeEx = kernel32.VirtualFreeEx
WriteProcessMemory = kernel32.WriteProcessMemory
WriteProcessMemory.argtypes = [wintypes.HANDLE, wintypes.LPVOID, wintypes.LPCVOID, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
ReadProcessMemory = kernel32.ReadProcessMemory
CreateRemoteThread = kernel32.CreateRemoteThread
CreateRemoteThread.argtypes = [wintypes.HANDLE, wintypes.LPVOID, ctypes.c_size_t, wintypes.LPVOID, wintypes.LPVOID, wintypes.DWORD, wintypes.LPDWORD]
CreateRemoteThread.restype = wintypes.HANDLE
WaitForSingleObject = kernel32.WaitForSingleObject
GetExitCodeThread = kernel32.GetExitCodeThread


class QianXinFullDuplexController:
    """
    Full-duplex audio controller cho QianXin camera.
    
    Cho phép MỞ MIC VÀ SPEAKER CÙNG LÚC bằng cách:
    1. Giữ speaker trong app luôn mở (để nghe camera mic)
    2. Sử dụng ZJ_PushSoundFile để gửi audio files đến camera speaker
       (thay vì click nút mic trong UI sẽ tự động tắt speaker)
    
    Workflow cho Chatbot:
    1. User bật speaker trong app (click icon loa) để nghe camera
    2. Khi cần phát TTS response:
       a. Save TTS audio to temp WAV file
       b. Gọi push_sound_file() để gửi đến camera
    3. Speaker VẪN MỞ trong suốt quá trình!
    """
    
    QIANXIN_DIR = r"d:\carecam\QianXin"
    
    def __init__(self):
        self.device_id = self._get_device_id()
        self.process_handle = None
        self.sdk_base = None
        self.funcs = {}
        
    def _get_device_id(self):
        """Read device ID from group.dat"""
        group_file = os.path.join(self.QIANXIN_DIR, "group.dat")
        try:
            with open(group_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            match = re.search(r'"dev_id"\s*:\s*"([^"]+)"', content)
            if match:
                return match.group(1)
        except Exception as e:
            print(f"Error reading device ID: {e}")
        return None
    
    def _find_pid(self):
        result = subprocess.run(
            ['powershell', '-Command', 
             "Get-Process | Where-Object { $_.ProcessName -like '*QianXin*' } | Select-Object -ExpandProperty Id"],
            capture_output=True, text=True
        )
        if result.stdout.strip():
            return int(result.stdout.strip().split('\n')[0])
        return None
    
    def _find_module(self, name):
        if not self.process_handle:
            return None
        hMods = (wintypes.HMODULE * 1024)()
        cbNeeded = wintypes.DWORD()
        ctypes.windll.psapi.EnumProcessModulesEx(
            self.process_handle, ctypes.byref(hMods), 
            ctypes.sizeof(hMods), ctypes.byref(cbNeeded), 0x03
        )
        count = cbNeeded.value // ctypes.sizeof(wintypes.HMODULE)
        for i in range(count):
            mod_name = ctypes.create_string_buffer(260)
            ctypes.windll.psapi.GetModuleBaseNameA(self.process_handle, hMods[i], mod_name, 260)
            if name.lower() in mod_name.value.decode('utf-8', errors='ignore').lower():
                return hMods[i]
        return None
    
    def _find_export(self, func_name):
        if not self.process_handle or not self.sdk_base:
            return None
            
        dos = ctypes.create_string_buffer(64)
        br = ctypes.c_size_t()
        ReadProcessMemory(self.process_handle, self.sdk_base, dos, 64, ctypes.byref(br))
        if dos.raw[:2] != b'MZ':
            return None
            
        pe_offset = struct.unpack('<I', dos.raw[0x3C:0x40])[0]
        pe = ctypes.create_string_buffer(256)
        ReadProcessMemory(self.process_handle, self.sdk_base + pe_offset, pe, 256, ctypes.byref(br))
        export_rva = struct.unpack('<I', pe.raw[120:124])[0]
        exp = ctypes.create_string_buffer(40)
        ReadProcessMemory(self.process_handle, self.sdk_base + export_rva, exp, 40, ctypes.byref(br))
        
        num_names = struct.unpack('<I', exp.raw[24:28])[0]
        addr_rva = struct.unpack('<I', exp.raw[28:32])[0]
        name_rva = struct.unpack('<I', exp.raw[32:36])[0]
        ord_rva = struct.unpack('<I', exp.raw[36:40])[0]
        
        for i in range(num_names):
            np = ctypes.create_string_buffer(4)
            ReadProcessMemory(self.process_handle, self.sdk_base + name_rva + i*4, np, 4, ctypes.byref(br))
            name_ptr = struct.unpack('<I', np.raw)[0]
            name = ctypes.create_string_buffer(64)
            ReadProcessMemory(self.process_handle, self.sdk_base + name_ptr, name, 64, ctypes.byref(br))
            if name.value.decode('utf-8', errors='ignore') == func_name:
                op = ctypes.create_string_buffer(2)
                ReadProcessMemory(self.process_handle, self.sdk_base + ord_rva + i*2, op, 2, ctypes.byref(br))
                ordinal = struct.unpack('<H', op.raw)[0]
                ap = ctypes.create_string_buffer(4)
                ReadProcessMemory(self.process_handle, self.sdk_base + addr_rva + ordinal*4, ap, 4, ctypes.byref(br))
                func_rva = struct.unpack('<I', ap.raw)[0]
                return self.sdk_base + func_rva
        return None
    
    def _call_func(self, func_addr, *params):
        """Call function with variable params (cdecl)"""
        shellcode = bytearray()
        for p in reversed(params):
            shellcode += b'\x68' + struct.pack('<I', p & 0xFFFFFFFF)
        shellcode += b'\xB8' + struct.pack('<I', func_addr)
        shellcode += b'\xFF\xD0'
        stack_size = len(params) * 4
        if stack_size > 0:
            shellcode += b'\x83\xC4' + bytes([stack_size])
        shellcode += b'\xC3'
        
        code_mem = VirtualAllocEx(self.process_handle, None, len(shellcode), MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE)
        written = ctypes.c_size_t()
        WriteProcessMemory(self.process_handle, code_mem, bytes(shellcode), len(shellcode), ctypes.byref(written))
        
        tid = wintypes.DWORD()
        thread = CreateRemoteThread(self.process_handle, None, 0, code_mem, None, 0, ctypes.byref(tid))
        if not thread:
            VirtualFreeEx(self.process_handle, code_mem, 0, MEM_RELEASE)
            return None
        
        WaitForSingleObject(thread, INFINITE)
        exit_code = wintypes.DWORD()
        GetExitCodeThread(thread, ctypes.byref(exit_code))
        CloseHandle(thread)
        VirtualFreeEx(self.process_handle, code_mem, 0, MEM_RELEASE)
        
        return exit_code.value
    
    def _alloc_string(self, s):
        data = s.encode('utf-8') + b'\x00'
        mem = VirtualAllocEx(self.process_handle, None, len(data), MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE)
        written = ctypes.c_size_t()
        WriteProcessMemory(self.process_handle, mem, data, len(data), ctypes.byref(written))
        return mem
    
    def connect(self) -> bool:
        """Connect to QianXin process"""
        if not self.device_id:
            print("❌ No device ID found")
            return False
        
        pid = self._find_pid()
        if not pid:
            print("❌ QianXin.exe not running")
            return False
        
        self.process_handle = OpenProcess(PROCESS_ALL_ACCESS, False, pid)
        if not self.process_handle:
            print("❌ Failed to open process")
            return False
        
        self.sdk_base = self._find_module("sdk_client.dll")
        if not self.sdk_base:
            print("❌ sdk_client.dll not found")
            self.close()
            return False
        
        # Find required functions
        func_names = [
            "ZJ_PushSoundFile",
            "ZJ_PlayPeerSoundFile",
            "ZJ_SetAudioParameter",
        ]
        
        for name in func_names:
            addr = self._find_export(name)
            if addr:
                self.funcs[name] = addr
        
        print(f"✅ Full-Duplex Controller connected (PID: {pid})")
        print(f"   Device: {self.device_id}")
        print(f"   Functions: {list(self.funcs.keys())}")
        return True
    
    def push_sound_file(self, file_path: str) -> bool:
        """
        Gửi audio file đến camera speaker.
        
        ĐÂY LÀ CÁCH BYPASS CHÍNH:
        - Thay vì click nút mic (sẽ tắt speaker)
        - Ta gọi SDK function trực tiếp để phát audio
        - Speaker trong app VẪN MỞ!
        
        Args:
            file_path: Path đến file audio (WAV recommended)
            
        Returns:
            True on success
        """
        if not self.process_handle:
            if not self.connect():
                return False
        
        if "ZJ_PushSoundFile" not in self.funcs:
            print("❌ ZJ_PushSoundFile not found")
            return False
        
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            return False
        
        # Allocate strings in remote process
        dev_mem = self._alloc_string(self.device_id)
        file_mem = self._alloc_string(file_path)
        
        # Call: ZJ_PushSoundFile(deviceId, filePath)
        result = self._call_func(self.funcs["ZJ_PushSoundFile"], dev_mem, file_mem)
        
        # Cleanup
        VirtualFreeEx(self.process_handle, dev_mem, 0, MEM_RELEASE)
        VirtualFreeEx(self.process_handle, file_mem, 0, MEM_RELEASE)
        
        success = result == 0
        if success:
            print(f"✅ Audio sent to camera: {os.path.basename(file_path)}")
        else:
            print(f"❌ Push failed (error: {result})")
        
        return success
    
    def send_tts_to_camera(self, wav_path: str) -> bool:
        """
        Gửi TTS audio đến camera speaker.
        
        Dùng cho chatbot: khi có response từ AI, convert to WAV rồi gọi function này.
        Speaker trong app sẽ VẪN MỞ để tiếp tục nghe camera mic.
        
        Args:
            wav_path: Path đến file WAV chứa TTS audio
            
        Returns:
            True on success
        """
        return self.push_sound_file(wav_path)
    
    def close(self):
        """Close connection"""
        if self.process_handle:
            CloseHandle(self.process_handle)
            self.process_handle = None
    
    def test_full_duplex(self):
        """
        Test full-duplex mode.
        
        Instructions:
        1. Mở app QianXin và bật speaker (click icon loa để nghe camera)
        2. Chạy function này
        3. Verify: speaker vẫn hoạt động VÀ âm thanh test phát qua camera
        """
        print("=" * 60)
        print("🔊 Full-Duplex Test")
        print("=" * 60)
        print("\n⚠️  QUAN TRỌNG: Hãy bật SPEAKER trong app QianXin trước khi test!")
        print("   (Click icon loa ở góc dưới bên phải app)")
        print("\n   Nhấn Enter để tiếp tục...")
        input()
        
        if not self.connect():
            return False
        
        # Test with Windows notification sound
        test_wav = r"C:\Windows\Media\Windows Notify.wav"
        
        print(f"\n[1] Đang gửi audio test: {test_wav}")
        result = self.push_sound_file(test_wav)
        
        import time
        time.sleep(2)
        
        print("\n" + "=" * 60)
        if result:
            print("✅ Test hoàn tất!")
            print("\nKết quả mong đợi:")
            print("  - Speaker trong app VẪN hoạt động (nghe được camera)")
            print("  - Âm thanh test đã phát qua camera speaker")
            print("  - Không có crash hoặc lỗi")
        else:
            print("❌ Test thất bại - xem log ở trên")
        print("=" * 60)
        
        self.close()
        return result


# Singleton instance
_controller = None

def get_full_duplex_controller() -> QianXinFullDuplexController:
    """Get singleton full-duplex controller"""
    global _controller
    if _controller is None:
        _controller = QianXinFullDuplexController()
    return _controller


if __name__ == "__main__":
    ctrl = QianXinFullDuplexController()
    ctrl.test_full_duplex()
