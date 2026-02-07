"""
Test Sound File Functions - Play audio to camera via SDK
Try ZJ_PlayPeerSoundFile and ZJ_PushSoundFile
"""

import ctypes
from ctypes import wintypes
import struct
import subprocess
import os
import time

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


def find_pid():
    result = subprocess.run(
        ['powershell', '-Command', 
         "Get-Process | Where-Object { $_.ProcessName -like '*QianXin*' } | Select-Object -ExpandProperty Id"],
        capture_output=True, text=True
    )
    if result.stdout.strip():
        return int(result.stdout.strip().split('\n')[0])
    return None


def find_module(handle, name):
    hMods = (wintypes.HMODULE * 1024)()
    cbNeeded = wintypes.DWORD()
    ctypes.windll.psapi.EnumProcessModulesEx(handle, ctypes.byref(hMods), ctypes.sizeof(hMods), ctypes.byref(cbNeeded), 0x03)
    count = cbNeeded.value // ctypes.sizeof(wintypes.HMODULE)
    for i in range(count):
        mod_name = ctypes.create_string_buffer(260)
        ctypes.windll.psapi.GetModuleBaseNameA(handle, hMods[i], mod_name, 260)
        if name.lower() in mod_name.value.decode('utf-8', errors='ignore').lower():
            return hMods[i]
    return None


def find_export(handle, module_base, func_name):
    dos = ctypes.create_string_buffer(64)
    br = ctypes.c_size_t()
    ReadProcessMemory(handle, module_base, dos, 64, ctypes.byref(br))
    if dos.raw[:2] != b'MZ':
        return None
    pe_offset = struct.unpack('<I', dos.raw[0x3C:0x40])[0]
    pe = ctypes.create_string_buffer(256)
    ReadProcessMemory(handle, module_base + pe_offset, pe, 256, ctypes.byref(br))
    export_rva = struct.unpack('<I', pe.raw[120:124])[0]
    exp = ctypes.create_string_buffer(40)
    ReadProcessMemory(handle, module_base + export_rva, exp, 40, ctypes.byref(br))
    num_names = struct.unpack('<I', exp.raw[24:28])[0]
    addr_rva = struct.unpack('<I', exp.raw[28:32])[0]
    name_rva = struct.unpack('<I', exp.raw[32:36])[0]
    ord_rva = struct.unpack('<I', exp.raw[36:40])[0]
    
    for i in range(num_names):
        np = ctypes.create_string_buffer(4)
        ReadProcessMemory(handle, module_base + name_rva + i*4, np, 4, ctypes.byref(br))
        name_ptr = struct.unpack('<I', np.raw)[0]
        name = ctypes.create_string_buffer(64)
        ReadProcessMemory(handle, module_base + name_ptr, name, 64, ctypes.byref(br))
        if name.value.decode('utf-8', errors='ignore') == func_name:
            op = ctypes.create_string_buffer(2)
            ReadProcessMemory(handle, module_base + ord_rva + i*2, op, 2, ctypes.byref(br))
            ordinal = struct.unpack('<H', op.raw)[0]
            ap = ctypes.create_string_buffer(4)
            ReadProcessMemory(handle, module_base + addr_rva + ordinal*4, ap, 4, ctypes.byref(br))
            func_rva = struct.unpack('<I', ap.raw)[0]
            return module_base + func_rva
    return None


def call_func(handle, func_addr, *params):
    """Call function with variable params (cdecl)"""
    shellcode = bytearray()
    for p in reversed(params):
        shellcode += b'\x68' + struct.pack('<I', p & 0xFFFFFFFF)
    shellcode += b'\xB8' + struct.pack('<I', func_addr)
    shellcode += b'\xFF\xD0'
    stack_size = len(params) * 4
    shellcode += b'\x83\xC4' + bytes([stack_size])
    shellcode += b'\xC3'
    
    code_mem = VirtualAllocEx(handle, None, len(shellcode), MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE)
    written = ctypes.c_size_t()
    WriteProcessMemory(handle, code_mem, bytes(shellcode), len(shellcode), ctypes.byref(written))
    
    tid = wintypes.DWORD()
    thread = CreateRemoteThread(handle, None, 0, code_mem, None, 0, ctypes.byref(tid))
    if not thread:
        VirtualFreeEx(handle, code_mem, 0, MEM_RELEASE)
        return None
    
    WaitForSingleObject(thread, INFINITE)
    exit_code = wintypes.DWORD()
    GetExitCodeThread(thread, ctypes.byref(exit_code))
    CloseHandle(thread)
    VirtualFreeEx(handle, code_mem, 0, MEM_RELEASE)
    
    return exit_code.value


def alloc_string(handle, s):
    data = s.encode('utf-8') + b'\x00'
    mem = VirtualAllocEx(handle, None, len(data), MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE)
    written = ctypes.c_size_t()
    WriteProcessMemory(handle, mem, data, len(data), ctypes.byref(written))
    return mem


def main():
    print("=" * 60)
    print("Testing Sound File Functions")
    print("=" * 60)
    
    device_id = "12000101402e36d5"
    
    # Create a simple test WAV path (doesn't need to exist for this test)
    test_file = r"C:\Windows\Media\Windows Notify.wav"
    
    pid = find_pid()
    if not pid:
        print("QianXin.exe not found")
        return
    
    print(f"PID: {pid}")
    
    handle = OpenProcess(PROCESS_ALL_ACCESS, False, pid)
    if not handle:
        print("Failed to open process")
        return
    
    try:
        sdk_base = find_module(handle, "sdk_client.dll")
        if not sdk_base:
            print("sdk_client.dll not found")
            return
        print(f"SDK base: 0x{sdk_base:08X}")
        
        # Find functions
        funcs = {}
        func_names = [
            "ZJ_PlayPeerSoundFile",
            "ZJ_PushSoundFile",
            "ZJ_PushAudioStream",
            "ZJ_SetAudioParam",
            "ZJ_SetAudioParameter",
        ]
        
        for name in func_names:
            addr = find_export(handle, sdk_base, name)
            if addr:
                funcs[name] = addr
                print(f"  {name}: 0x{addr:08X}")
        
        # Allocate strings
        dev_mem = alloc_string(handle, device_id)
        file_mem = alloc_string(handle, test_file)
        
        print(f"\nDevice ID at: 0x{dev_mem:08X}")
        print(f"File path at: 0x{file_mem:08X}")
        
        # Test ZJ_SetAudioParameter first
        if "ZJ_SetAudioParameter" in funcs:
            print("\n--- Testing ZJ_SetAudioParameter ---")
            # Try setting audio params: format=1 (PCM?), rate=8000, channels=1
            for params in [
                (dev_mem,),
                (dev_mem, 1),
                (dev_mem, 1, 8000),
                (dev_mem, 1, 8000, 1),
            ]:
                result = call_func(handle, funcs["ZJ_SetAudioParameter"], *params)
                print(f"  ZJ_SetAudioParameter{params}: result={result}")
                if result == 0:
                    break
        
        # Test ZJ_PushAudioStream again after setting parameters
        if "ZJ_PushAudioStream" in funcs:
            print("\n--- Testing ZJ_PushAudioStream (after SetAudioParameter) ---")
            result = call_func(handle, funcs["ZJ_PushAudioStream"], dev_mem)
            print(f"  Result: {result} (0x{result:08X})")
            
            if result == 0:
                print("  SUCCESS! Audio stream started.")
                print("  Sleeping 3 seconds...")
                time.sleep(3)
        
        # Test ZJ_PlayPeerSoundFile
        if "ZJ_PlayPeerSoundFile" in funcs:
            print("\n--- Testing ZJ_PlayPeerSoundFile ---")
            
            # Try different param combinations
            tests = [
                ((dev_mem, file_mem), "deviceId, filePath"),
                ((file_mem, dev_mem), "filePath, deviceId"),
                ((0, dev_mem, file_mem), "0, deviceId, filePath"),
            ]
            
            for params, desc in tests:
                result = call_func(handle, funcs["ZJ_PlayPeerSoundFile"], *params)
                print(f"  {desc}: result={result}")
                if result == 0:
                    print("  SUCCESS!")
                    break
        
        # Test ZJ_PushSoundFile
        if "ZJ_PushSoundFile" in funcs:
            print("\n--- Testing ZJ_PushSoundFile ---")
            
            tests = [
                ((dev_mem, file_mem), "deviceId, filePath"),
                ((0, dev_mem, file_mem), "0, deviceId, filePath"),
            ]
            
            for params, desc in tests:
                result = call_func(handle, funcs["ZJ_PushSoundFile"], *params)
                print(f"  {desc}: result={result}")
                if result == 0:
                    print("  SUCCESS!")
                    break
        
        # Cleanup
        VirtualFreeEx(handle, dev_mem, 0, MEM_RELEASE)
        VirtualFreeEx(handle, file_mem, 0, MEM_RELEASE)
        
    finally:
        CloseHandle(handle)
    
    print("\nDone!")


if __name__ == "__main__":
    main()
