"""
DLL Injection Controller for QianXin SDK
Inject code into running QianXin.exe process to call ZJ_SetPeerMicPhoneStatus

This approach works because:
1. QianXin.exe already has sdk_client.dll loaded and initialized
2. We inject a small payload to call the exported function
3. The function call happens within the app's context with proper SDK state
"""

import ctypes
from ctypes import wintypes
import struct
import time

# Windows API constants
PROCESS_ALL_ACCESS = 0x1F0FFF
MEM_COMMIT = 0x1000
MEM_RESERVE = 0x2000
MEM_RELEASE = 0x8000
PAGE_EXECUTE_READWRITE = 0x40
INFINITE = 0xFFFFFFFF

# Windows API functions
kernel32 = ctypes.windll.kernel32
user32 = ctypes.windll.user32

OpenProcess = kernel32.OpenProcess
OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
OpenProcess.restype = wintypes.HANDLE

CloseHandle = kernel32.CloseHandle

VirtualAllocEx = kernel32.VirtualAllocEx
VirtualAllocEx.argtypes = [wintypes.HANDLE, wintypes.LPVOID, ctypes.c_size_t, wintypes.DWORD, wintypes.DWORD]
VirtualAllocEx.restype = wintypes.LPVOID

VirtualFreeEx = kernel32.VirtualFreeEx
VirtualFreeEx.argtypes = [wintypes.HANDLE, wintypes.LPVOID, ctypes.c_size_t, wintypes.DWORD]

WriteProcessMemory = kernel32.WriteProcessMemory
WriteProcessMemory.argtypes = [wintypes.HANDLE, wintypes.LPVOID, wintypes.LPCVOID, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]

ReadProcessMemory = kernel32.ReadProcessMemory
ReadProcessMemory.argtypes = [wintypes.HANDLE, wintypes.LPCVOID, wintypes.LPVOID, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]

CreateRemoteThread = kernel32.CreateRemoteThread
CreateRemoteThread.argtypes = [wintypes.HANDLE, wintypes.LPVOID, ctypes.c_size_t, wintypes.LPVOID, wintypes.LPVOID, wintypes.DWORD, wintypes.LPDWORD]
CreateRemoteThread.restype = wintypes.HANDLE

WaitForSingleObject = kernel32.WaitForSingleObject
WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]

GetExitCodeThread = kernel32.GetExitCodeThread
GetExitCodeThread.argtypes = [wintypes.HANDLE, wintypes.LPDWORD]

GetModuleHandleA = kernel32.GetModuleHandleA
GetModuleHandleA.argtypes = [wintypes.LPCSTR]
GetModuleHandleA.restype = wintypes.HMODULE

GetProcAddress = kernel32.GetProcAddress
GetProcAddress.argtypes = [wintypes.HMODULE, wintypes.LPCSTR]
GetProcAddress.restype = wintypes.LPVOID

# For enumerating modules in remote process
EnumProcessModulesEx = ctypes.windll.psapi.EnumProcessModulesEx
GetModuleBaseNameA = ctypes.windll.psapi.GetModuleBaseNameA
GetModuleFileNameExA = ctypes.windll.psapi.GetModuleFileNameExA


def find_qianxin_process():
    """Find QianXin.exe process ID"""
    import subprocess
    result = subprocess.run(
        ['powershell', '-Command', 
         "Get-Process | Where-Object { $_.ProcessName -like '*QianXin*' } | Select-Object -ExpandProperty Id"],
        capture_output=True, text=True
    )
    
    if result.stdout.strip():
        pid = int(result.stdout.strip().split('\n')[0])
        print(f"✅ Found QianXin.exe (PID: {pid})")
        return pid
    
    print("❌ QianXin.exe not found")
    return None


def find_module_in_process(process_handle, module_name):
    """Find module base address in remote process"""
    hMods = (wintypes.HMODULE * 1024)()
    cbNeeded = wintypes.DWORD()
    
    if ctypes.windll.psapi.EnumProcessModulesEx(
        process_handle, 
        ctypes.byref(hMods), 
        ctypes.sizeof(hMods), 
        ctypes.byref(cbNeeded),
        0x03  # LIST_MODULES_ALL
    ):
        count = cbNeeded.value // ctypes.sizeof(wintypes.HMODULE)
        for i in range(count):
            mod_name = ctypes.create_string_buffer(260)
            ctypes.windll.psapi.GetModuleBaseNameA(
                process_handle, 
                hMods[i], 
                mod_name, 
                260
            )
            if module_name.lower() in mod_name.value.decode('utf-8', errors='ignore').lower():
                print(f"   Found {mod_name.value.decode()}: 0x{hMods[i]:08X}")
                return hMods[i]
    
    return None


def find_function_address_in_process(process_handle, module_base, function_name):
    """
    Find function address in remote process by parsing PE export table
    """
    # Read DOS header
    dos_header = ctypes.create_string_buffer(64)
    bytes_read = ctypes.c_size_t()
    ReadProcessMemory(process_handle, module_base, dos_header, 64, ctypes.byref(bytes_read))
    
    # Check MZ signature
    if dos_header.raw[:2] != b'MZ':
        print("Invalid DOS header")
        return None
    
    # Get PE header offset
    e_lfanew = struct.unpack('<I', dos_header.raw[0x3C:0x40])[0]
    
    # Read PE header
    pe_header = ctypes.create_string_buffer(256)
    ReadProcessMemory(process_handle, module_base + e_lfanew, pe_header, 256, ctypes.byref(bytes_read))
    
    # Check PE signature
    if pe_header.raw[:4] != b'PE\x00\x00':
        print("Invalid PE header")
        return None
    
    # Get export directory RVA (offset 120 from PE header for 32-bit)
    export_rva = struct.unpack('<I', pe_header.raw[120:124])[0]
    
    if export_rva == 0:
        print("No export table")
        return None
    
    # Read export directory
    export_dir = ctypes.create_string_buffer(40)
    ReadProcessMemory(process_handle, module_base + export_rva, export_dir, 40, ctypes.byref(bytes_read))
    
    num_names = struct.unpack('<I', export_dir.raw[24:28])[0]
    addr_table_rva = struct.unpack('<I', export_dir.raw[28:32])[0]
    name_table_rva = struct.unpack('<I', export_dir.raw[32:36])[0]
    ordinal_table_rva = struct.unpack('<I', export_dir.raw[36:40])[0]
    
    # Read name pointer table
    name_ptrs = ctypes.create_string_buffer(num_names * 4)
    ReadProcessMemory(process_handle, module_base + name_table_rva, name_ptrs, num_names * 4, ctypes.byref(bytes_read))
    
    # Read ordinal table
    ordinals = ctypes.create_string_buffer(num_names * 2)
    ReadProcessMemory(process_handle, module_base + ordinal_table_rva, ordinals, num_names * 2, ctypes.byref(bytes_read))
    
    # Search for function
    for i in range(num_names):
        name_rva = struct.unpack('<I', name_ptrs.raw[i*4:(i+1)*4])[0]
        
        # Read function name
        name_buf = ctypes.create_string_buffer(128)
        ReadProcessMemory(process_handle, module_base + name_rva, name_buf, 128, ctypes.byref(bytes_read))
        
        name = name_buf.value.decode('utf-8', errors='ignore')
        
        if name == function_name:
            # Get ordinal
            ordinal = struct.unpack('<H', ordinals.raw[i*2:(i+1)*2])[0]
            
            # Read function address
            addr_offset = ordinal * 4
            addr_buf = ctypes.create_string_buffer(4)
            ReadProcessMemory(process_handle, module_base + addr_table_rva + addr_offset, addr_buf, 4, ctypes.byref(bytes_read))
            
            func_rva = struct.unpack('<I', addr_buf.raw)[0]
            func_addr = module_base + func_rva
            
            print(f"   Found {function_name}: 0x{func_addr:08X}")
            return func_addr
    
    return None


def call_remote_function(process_handle, func_addr, arg1=0, arg2=0):
    """
    Call a function in remote process using CreateRemoteThread
    This creates shellcode that calls: func_addr(arg1, arg2)
    """
    # x86 shellcode to call function with 2 int arguments
    # push arg2
    # push arg1  
    # mov eax, func_addr
    # call eax
    # ret
    
    shellcode = bytearray()
    
    # push arg2
    shellcode += b'\x68' + struct.pack('<I', arg2)
    
    # push arg1
    shellcode += b'\x68' + struct.pack('<I', arg1)
    
    # mov eax, func_addr
    shellcode += b'\xB8' + struct.pack('<I', func_addr)
    
    # call eax
    shellcode += b'\xFF\xD0'
    
    # add esp, 8 (clean up stack - cdecl convention)
    shellcode += b'\x83\xC4\x08'
    
    # ret
    shellcode += b'\xC3'
    
    # Allocate memory in remote process
    remote_mem = VirtualAllocEx(
        process_handle, 
        None, 
        len(shellcode), 
        MEM_COMMIT | MEM_RESERVE, 
        PAGE_EXECUTE_READWRITE
    )
    
    if not remote_mem:
        print("❌ Failed to allocate remote memory")
        return None
    
    print(f"   Allocated remote memory: 0x{remote_mem:08X}")
    
    # Write shellcode
    written = ctypes.c_size_t()
    WriteProcessMemory(
        process_handle, 
        remote_mem, 
        bytes(shellcode), 
        len(shellcode), 
        ctypes.byref(written)
    )
    
    print(f"   Written {written.value} bytes of shellcode")
    
    # Create remote thread
    thread_id = wintypes.DWORD()
    thread_handle = CreateRemoteThread(
        process_handle,
        None,
        0,
        remote_mem,
        None,
        0,
        ctypes.byref(thread_id)
    )
    
    if not thread_handle:
        print("❌ Failed to create remote thread")
        VirtualFreeEx(process_handle, remote_mem, 0, MEM_RELEASE)
        return None
    
    print(f"   Created remote thread (ID: {thread_id.value})")
    
    # Wait for thread to complete
    WaitForSingleObject(thread_handle, INFINITE)
    
    # Get exit code (return value)
    exit_code = wintypes.DWORD()
    GetExitCodeThread(thread_handle, ctypes.byref(exit_code))
    
    print(f"   Thread completed, return value: {exit_code.value}")
    
    # Cleanup
    CloseHandle(thread_handle)
    VirtualFreeEx(process_handle, remote_mem, 0, MEM_RELEASE)
    
    return exit_code.value


def set_mic_status(enabled=True, device_id="12000101402e36d5"):
    """
    Set mic status by injecting code into QianXin.exe
    """
    print("=" * 60)
    print("Mic Control via DLL Injection")
    print("=" * 60)
    
    # Find process
    pid = find_qianxin_process()
    if not pid:
        return False
    
    # Open process
    process_handle = OpenProcess(PROCESS_ALL_ACCESS, False, pid)
    if not process_handle:
        print(f"Failed to open process (Error: {kernel32.GetLastError()})")
        return False
    
    print(f"   Opened process handle: 0x{process_handle:X}")
    
    try:
        # Find sdk_client.dll
        print("\nFinding sdk_client.dll...")
        sdk_base = find_module_in_process(process_handle, "sdk_client.dll")
        if not sdk_base:
            print("sdk_client.dll not found in process")
            return False
        
        # Find ZJ_SetPeerMicPhoneStatus function
        print("\nFinding ZJ_SetPeerMicPhoneStatus...")
        func_addr = find_function_address_in_process(
            process_handle, 
            sdk_base, 
            "ZJ_SetPeerMicPhoneStatus"
        )
        
        if not func_addr:
            print("Function not found")
            return False
        
        # Allocate memory for device ID string
        device_id_bytes = device_id.encode('utf-8') + b'\x00'
        str_mem = VirtualAllocEx(
            process_handle,
            None,
            len(device_id_bytes),
            MEM_COMMIT | MEM_RESERVE,
            PAGE_EXECUTE_READWRITE
        )
        
        if not str_mem:
            print("Failed to allocate string memory")
            return False
        
        # Write device ID string
        written = ctypes.c_size_t()
        WriteProcessMemory(
            process_handle,
            str_mem,
            device_id_bytes,
            len(device_id_bytes),
            ctypes.byref(written)
        )
        print(f"   Device ID at: 0x{str_mem:08X}")
        
        # Call function: ZJ_SetPeerMicPhoneStatus(deviceId, status)
        status = 1 if enabled else 0
        
        print(f"\nCalling ZJ_SetPeerMicPhoneStatus(\"{device_id}\", {status})...")
        
        # Create shellcode for: func(str_mem, status)
        shellcode = bytearray()
        
        # push status
        shellcode += b'\x68' + struct.pack('<I', status)
        
        # push str_mem (device ID pointer)
        shellcode += b'\x68' + struct.pack('<I', str_mem)
        
        # mov eax, func_addr
        shellcode += b'\xB8' + struct.pack('<I', func_addr)
        
        # call eax
        shellcode += b'\xFF\xD0'
        
        # add esp, 8 (cleanup 2 params)
        shellcode += b'\x83\xC4\x08'
        
        # ret
        shellcode += b'\xC3'
        
        # Allocate and execute shellcode
        code_mem = VirtualAllocEx(
            process_handle,
            None,
            len(shellcode),
            MEM_COMMIT | MEM_RESERVE,
            PAGE_EXECUTE_READWRITE
        )
        
        WriteProcessMemory(
            process_handle,
            code_mem,
            bytes(shellcode),
            len(shellcode),
            ctypes.byref(written)
        )
        
        print(f"   Shellcode at: 0x{code_mem:08X}")
        
        # Create remote thread
        thread_id = wintypes.DWORD()
        thread_handle = CreateRemoteThread(
            process_handle,
            None,
            0,
            code_mem,
            None,
            0,
            ctypes.byref(thread_id)
        )
        
        if not thread_handle:
            print("Failed to create remote thread")
            VirtualFreeEx(process_handle, code_mem, 0, MEM_RELEASE)
            VirtualFreeEx(process_handle, str_mem, 0, MEM_RELEASE)
            return False
        
        print(f"   Remote thread created (ID: {thread_id.value})")
        
        # Wait for completion
        WaitForSingleObject(thread_handle, INFINITE)
        
        # Get result
        exit_code = wintypes.DWORD()
        GetExitCodeThread(thread_handle, ctypes.byref(exit_code))
        
        result = exit_code.value
        
        # Check for access violation (0xC0000005)
        if result == 0xC0000005:
            print(f"   Access violation - wrong parameters")
        elif result == 0:
            print(f"   Success!")
        else:
            print(f"   Result: {result}")
        
        # Cleanup
        CloseHandle(thread_handle)
        VirtualFreeEx(process_handle, code_mem, 0, MEM_RELEASE)
        VirtualFreeEx(process_handle, str_mem, 0, MEM_RELEASE)
        
        return result == 0
        
    finally:
        CloseHandle(process_handle)


if __name__ == "__main__":
    import sys
    
    # Enable debug privileges (optional, for better access)
    print("🔧 QianXin SDK Injection Controller")
    print("   This script injects code into QianXin.exe to control mic\n")
    
    enabled = True
    if len(sys.argv) > 1:
        enabled = sys.argv[1].lower() in ['1', 'true', 'on', 'enable']
    
    success = set_mic_status(enabled)
    
    if success:
        print(f"\n✅ Mic {'enabled' if enabled else 'disabled'} successfully!")
    else:
        print("\n❌ Failed to control mic")
