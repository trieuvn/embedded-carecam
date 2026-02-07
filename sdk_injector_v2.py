"""
SDK Injector v2 - With 3 parameters
Based on disassembly analysis:
- Function uses cdecl calling convention
- Takes 3 parameters accessed at [esp+8], [esp+0C], [esp+10]
- Likely: ZJ_SetPeerMicPhoneStatus(deviceId, sessionHandle?, status)
"""

import ctypes
from ctypes import wintypes
import struct
import subprocess

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


def find_pid():
    result = subprocess.run(
        ['powershell', '-Command', 
         "Get-Process | Where-Object { $_.ProcessName -like '*QianXin*' } | Select-Object -ExpandProperty Id"],
        capture_output=True, text=True
    )
    if result.stdout.strip():
        return int(result.stdout.strip().split('\n')[0])
    return None


def find_module(process_handle, name):
    hMods = (wintypes.HMODULE * 1024)()
    cbNeeded = wintypes.DWORD()
    ctypes.windll.psapi.EnumProcessModulesEx(process_handle, ctypes.byref(hMods), ctypes.sizeof(hMods), ctypes.byref(cbNeeded), 0x03)
    
    count = cbNeeded.value // ctypes.sizeof(wintypes.HMODULE)
    for i in range(count):
        mod_name = ctypes.create_string_buffer(260)
        ctypes.windll.psapi.GetModuleBaseNameA(process_handle, hMods[i], mod_name, 260)
        if name.lower() in mod_name.value.decode('utf-8', errors='ignore').lower():
            return hMods[i]
    return None


def find_export(process_handle, module_base, func_name):
    """Find exported function address"""
    # Read DOS header
    dos = ctypes.create_string_buffer(64)
    br = ctypes.c_size_t()
    ReadProcessMemory(process_handle, module_base, dos, 64, ctypes.byref(br))
    
    if dos.raw[:2] != b'MZ':
        return None
    
    pe_offset = struct.unpack('<I', dos.raw[0x3C:0x40])[0]
    
    # Read PE header
    pe = ctypes.create_string_buffer(256)
    ReadProcessMemory(process_handle, module_base + pe_offset, pe, 256, ctypes.byref(br))
    
    export_rva = struct.unpack('<I', pe.raw[120:124])[0]
    
    # Read export directory
    exp = ctypes.create_string_buffer(40)
    ReadProcessMemory(process_handle, module_base + export_rva, exp, 40, ctypes.byref(br))
    
    num_names = struct.unpack('<I', exp.raw[24:28])[0]
    addr_rva = struct.unpack('<I', exp.raw[28:32])[0]
    name_rva = struct.unpack('<I', exp.raw[32:36])[0]
    ord_rva = struct.unpack('<I', exp.raw[36:40])[0]
    
    # Search for function
    for i in range(num_names):
        # Read name pointer
        np = ctypes.create_string_buffer(4)
        ReadProcessMemory(process_handle, module_base + name_rva + i*4, np, 4, ctypes.byref(br))
        name_ptr = struct.unpack('<I', np.raw)[0]
        
        # Read name
        name = ctypes.create_string_buffer(64)
        ReadProcessMemory(process_handle, module_base + name_ptr, name, 64, ctypes.byref(br))
        
        if name.value.decode('utf-8', errors='ignore') == func_name:
            # Get ordinal
            op = ctypes.create_string_buffer(2)
            ReadProcessMemory(process_handle, module_base + ord_rva + i*2, op, 2, ctypes.byref(br))
            ordinal = struct.unpack('<H', op.raw)[0]
            
            # Get address
            ap = ctypes.create_string_buffer(4)
            ReadProcessMemory(process_handle, module_base + addr_rva + ordinal*4, ap, 4, ctypes.byref(br))
            func_rva = struct.unpack('<I', ap.raw)[0]
            
            return module_base + func_rva
    
    return None


def call_function_3_params(process_handle, func_addr, param1, param2, param3):
    """Call function with 3 parameters using cdecl"""
    
    # x86 shellcode: call func(param1, param2, param3)
    # cdecl: caller cleans up stack
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
    
    # add esp, 12 (cleanup 3 params * 4 bytes)
    shellcode += b'\x83\xC4\x0C'
    
    # ret
    shellcode += b'\xC3'
    
    # Allocate and execute
    code_mem = VirtualAllocEx(process_handle, None, len(shellcode), MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE)
    
    written = ctypes.c_size_t()
    WriteProcessMemory(process_handle, code_mem, bytes(shellcode), len(shellcode), ctypes.byref(written))
    
    thread_id = wintypes.DWORD()
    thread = CreateRemoteThread(process_handle, None, 0, code_mem, None, 0, ctypes.byref(thread_id))
    
    if not thread:
        VirtualFreeEx(process_handle, code_mem, 0, MEM_RELEASE)
        return None
    
    WaitForSingleObject(thread, INFINITE)
    
    exit_code = wintypes.DWORD()
    GetExitCodeThread(thread, ctypes.byref(exit_code))
    
    CloseHandle(thread)
    VirtualFreeEx(process_handle, code_mem, 0, MEM_RELEASE)
    
    return exit_code.value


def set_mic(enabled=True, device_id="12000101402e36d5"):
    print("=" * 60)
    print("SDK Mic Control - 3 Parameter Version")
    print("=" * 60)
    
    pid = find_pid()
    if not pid:
        print("QianXin.exe not found")
        return False
    
    print(f"PID: {pid}")
    
    handle = OpenProcess(PROCESS_ALL_ACCESS, False, pid)
    if not handle:
        print("Failed to open process")
        return False
    
    try:
        sdk_base = find_module(handle, "sdk_client.dll")
        if not sdk_base:
            print("sdk_client.dll not found")
            return False
        print(f"SDK base: 0x{sdk_base:08X}")
        
        func_addr = find_export(handle, sdk_base, "ZJ_SetPeerMicPhoneStatus")
        if not func_addr:
            print("Function not found")
            return False
        print(f"Function: 0x{func_addr:08X}")
        
        # Allocate device ID string
        dev_bytes = device_id.encode('utf-8') + b'\x00'
        str_mem = VirtualAllocEx(handle, None, len(dev_bytes), MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE)
        written = ctypes.c_size_t()
        WriteProcessMemory(handle, str_mem, dev_bytes, len(dev_bytes), ctypes.byref(written))
        print(f"Device ID: 0x{str_mem:08X}")
        
        status = 1 if enabled else 0
        
        # Try different parameter combinations
        param_combos = [
            # (deviceId, 0, status) - deviceId first
            (str_mem, 0, status, "deviceId, 0, status"),
            # (0, deviceId, status) - handle first
            (0, str_mem, status, "0, deviceId, status"),
            # (deviceId, status, 0)
            (str_mem, status, 0, "deviceId, status, 0"),
            # Try with -1 as "all devices"
            (-1 & 0xFFFFFFFF, 0, status, "-1, 0, status"),
        ]
        
        for p1, p2, p3, desc in param_combos:
            print(f"\nTrying: {desc}")
            result = call_function_3_params(handle, func_addr, p1, p2, p3)
            
            if result is not None:
                if result == 0:
                    print(f"  SUCCESS! Result: {result}")
                    VirtualFreeEx(handle, str_mem, 0, MEM_RELEASE)
                    return True
                elif result == 0xC0000005:
                    print(f"  Access violation")
                else:
                    print(f"  Result: {result} (0x{result:08X})")
        
        VirtualFreeEx(handle, str_mem, 0, MEM_RELEASE)
        return False
        
    finally:
        CloseHandle(handle)


if __name__ == "__main__":
    set_mic(enabled=True)
