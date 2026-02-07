"""
QianXin SDK Direct Controller
Điều khiển mic camera trực tiếp qua DLL injection vào QianXin.exe

Function signature (verified):
    int ZJ_SetPeerMicPhoneStatus(int unknown, const char* deviceId, int status)
    - unknown: 0
    - deviceId: camera device ID from group.dat
    - status: 1 = enable, 0 = disable
    - returns: 0 on success
"""

import ctypes
from ctypes import wintypes
import struct
import subprocess
import json
import os


# Windows API constants
PROCESS_ALL_ACCESS = 0x1F0FFF
MEM_COMMIT = 0x1000
MEM_RESERVE = 0x2000
MEM_RELEASE = 0x8000
PAGE_EXECUTE_READWRITE = 0x40
INFINITE = 0xFFFFFFFF

# Windows API
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


class QianXinMicController:
    """Direct mic control via DLL injection"""
    
    QIANXIN_DIR = r"d:\carecam\QianXin"
    
    def __init__(self):
        self.device_id = self._get_device_id()
        self.process_handle = None
        self.func_addr = None
        
    def _get_device_id(self):
        """Read device ID from group.dat"""
        group_file = os.path.join(self.QIANXIN_DIR, "group.dat")
        
        try:
            with open(group_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Parse JSON-like content
            import re
            match = re.search(r'"dev_id"\s*:\s*"([^"]+)"', content)
            if match:
                device_id = match.group(1)
                print(f"Device ID: {device_id}")
                return device_id
        except Exception as e:
            print(f"Error reading device ID: {e}")
        
        return None
    
    def _find_process(self):
        """Find QianXin.exe PID"""
        result = subprocess.run(
            ['powershell', '-Command', 
             "Get-Process | Where-Object { $_.ProcessName -like '*QianXin*' } | Select-Object -ExpandProperty Id"],
            capture_output=True, text=True
        )
        if result.stdout.strip():
            return int(result.stdout.strip().split('\n')[0])
        return None
    
    def _find_module(self, name):
        """Find module base in process"""
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
            ctypes.windll.psapi.GetModuleBaseNameA(
                self.process_handle, hMods[i], mod_name, 260
            )
            if name.lower() in mod_name.value.decode('utf-8', errors='ignore').lower():
                return hMods[i]
        return None
    
    def _find_export(self, module_base, func_name):
        """Find exported function address"""
        dos = ctypes.create_string_buffer(64)
        br = ctypes.c_size_t()
        ReadProcessMemory(self.process_handle, module_base, dos, 64, ctypes.byref(br))
        
        if dos.raw[:2] != b'MZ':
            return None
        
        pe_offset = struct.unpack('<I', dos.raw[0x3C:0x40])[0]
        
        pe = ctypes.create_string_buffer(256)
        ReadProcessMemory(self.process_handle, module_base + pe_offset, pe, 256, ctypes.byref(br))
        
        export_rva = struct.unpack('<I', pe.raw[120:124])[0]
        
        exp = ctypes.create_string_buffer(40)
        ReadProcessMemory(self.process_handle, module_base + export_rva, exp, 40, ctypes.byref(br))
        
        num_names = struct.unpack('<I', exp.raw[24:28])[0]
        addr_rva = struct.unpack('<I', exp.raw[28:32])[0]
        name_rva = struct.unpack('<I', exp.raw[32:36])[0]
        ord_rva = struct.unpack('<I', exp.raw[36:40])[0]
        
        for i in range(num_names):
            np = ctypes.create_string_buffer(4)
            ReadProcessMemory(self.process_handle, module_base + name_rva + i*4, np, 4, ctypes.byref(br))
            name_ptr = struct.unpack('<I', np.raw)[0]
            
            name = ctypes.create_string_buffer(64)
            ReadProcessMemory(self.process_handle, module_base + name_ptr, name, 64, ctypes.byref(br))
            
            if name.value.decode('utf-8', errors='ignore') == func_name:
                op = ctypes.create_string_buffer(2)
                ReadProcessMemory(self.process_handle, module_base + ord_rva + i*2, op, 2, ctypes.byref(br))
                ordinal = struct.unpack('<H', op.raw)[0]
                
                ap = ctypes.create_string_buffer(4)
                ReadProcessMemory(self.process_handle, module_base + addr_rva + ordinal*4, ap, 4, ctypes.byref(br))
                func_rva = struct.unpack('<I', ap.raw)[0]
                
                return module_base + func_rva
        return None
    
    def _call_function(self, func_addr, param1, param2, param3):
        """Call function with 3 parameters using cdecl"""
        shellcode = bytearray()
        
        # push param3
        shellcode += b'\x68' + struct.pack('<I', param3)
        # push param2
        shellcode += b'\x68' + struct.pack('<I', param2)
        # push param1
        shellcode += b'\x68' + struct.pack('<I', param1)
        # mov eax, func_addr
        shellcode += b'\xB8' + struct.pack('<I', func_addr)
        # call eax
        shellcode += b'\xFF\xD0'
        # add esp, 12
        shellcode += b'\x83\xC4\x0C'
        # ret
        shellcode += b'\xC3'
        
        code_mem = VirtualAllocEx(
            self.process_handle, None, len(shellcode), 
            MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE
        )
        
        written = ctypes.c_size_t()
        WriteProcessMemory(
            self.process_handle, code_mem, 
            bytes(shellcode), len(shellcode), ctypes.byref(written)
        )
        
        thread_id = wintypes.DWORD()
        thread = CreateRemoteThread(
            self.process_handle, None, 0, code_mem, 
            None, 0, ctypes.byref(thread_id)
        )
        
        if not thread:
            VirtualFreeEx(self.process_handle, code_mem, 0, MEM_RELEASE)
            return None
        
        WaitForSingleObject(thread, INFINITE)
        
        exit_code = wintypes.DWORD()
        GetExitCodeThread(thread, ctypes.byref(exit_code))
        
        CloseHandle(thread)
        VirtualFreeEx(self.process_handle, code_mem, 0, MEM_RELEASE)
        
        return exit_code.value
    
    def connect(self):
        """Connect to QianXin process"""
        if not self.device_id:
            print("No device ID found")
            return False
        
        pid = self._find_process()
        if not pid:
            print("QianXin.exe not running")
            return False
        
        self.process_handle = OpenProcess(PROCESS_ALL_ACCESS, False, pid)
        if not self.process_handle:
            print("Failed to open process")
            return False
        
        sdk_base = self._find_module("sdk_client.dll")
        if not sdk_base:
            print("sdk_client.dll not found")
            self.close()
            return False
        
        self.func_addr = self._find_export(sdk_base, "ZJ_SetPeerMicPhoneStatus")
        if not self.func_addr:
            print("Function not found")
            self.close()
            return False
        
        print(f"Connected to QianXin (PID: {pid})")
        return True
    
    def set_mic_status(self, enabled: bool = True) -> bool:
        """
        Enable or disable microphone
        
        Args:
            enabled: True to enable mic, False to disable
            
        Returns:
            True on success
        """
        if not self.process_handle or not self.func_addr:
            if not self.connect():
                return False
        
        # Allocate device ID string
        dev_bytes = self.device_id.encode('utf-8') + b'\x00'
        str_mem = VirtualAllocEx(
            self.process_handle, None, len(dev_bytes),
            MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE
        )
        
        written = ctypes.c_size_t()
        WriteProcessMemory(
            self.process_handle, str_mem, 
            dev_bytes, len(dev_bytes), ctypes.byref(written)
        )
        
        status = 1 if enabled else 0
        
        # Call: ZJ_SetPeerMicPhoneStatus(0, deviceId, status)
        result = self._call_function(self.func_addr, 0, str_mem, status)
        
        VirtualFreeEx(self.process_handle, str_mem, 0, MEM_RELEASE)
        
        success = result == 0
        print(f"Mic {'enabled' if enabled else 'disabled'}: {'OK' if success else 'FAILED'}")
        
        return success
    
    def enable_mic(self) -> bool:
        """Enable microphone"""
        return self.set_mic_status(True)
    
    def disable_mic(self) -> bool:
        """Disable microphone"""
        return self.set_mic_status(False)
    
    def close(self):
        """Close process handle"""
        if self.process_handle:
            CloseHandle(self.process_handle)
            self.process_handle = None


# Singleton instance
_controller = None

def get_mic_controller() -> QianXinMicController:
    """Get singleton mic controller instance"""
    global _controller
    if _controller is None:
        _controller = QianXinMicController()
    return _controller


if __name__ == "__main__":
    print("=" * 60)
    print("QianXin Mic Controller Test")
    print("=" * 60)
    
    ctrl = get_mic_controller()
    
    if ctrl.connect():
        print("\nEnabling mic...")
        ctrl.enable_mic()
        
        import time
        time.sleep(3)
        
        print("\nDisabling mic...")
        ctrl.disable_mic()
        
        ctrl.close()
