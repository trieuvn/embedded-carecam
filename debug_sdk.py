"""
Debug SDK Function - Analyze function bytecode to determine calling convention and parameters
"""

import ctypes
from ctypes import wintypes
import struct
import subprocess

# Windows API
kernel32 = ctypes.windll.kernel32
OpenProcess = kernel32.OpenProcess
CloseHandle = kernel32.CloseHandle
ReadProcessMemory = kernel32.ReadProcessMemory

PROCESS_ALL_ACCESS = 0x1F0FFF


def find_qianxin_pid():
    result = subprocess.run(
        ['powershell', '-Command', 
         "Get-Process | Where-Object { $_.ProcessName -like '*QianXin*' } | Select-Object -ExpandProperty Id"],
        capture_output=True, text=True
    )
    if result.stdout.strip():
        return int(result.stdout.strip().split('\n')[0])
    return None


def find_module_base(process_handle, module_name):
    """Find module base in process"""
    hMods = (wintypes.HMODULE * 1024)()
    cbNeeded = wintypes.DWORD()
    
    ctypes.windll.psapi.EnumProcessModulesEx(
        process_handle, 
        ctypes.byref(hMods), 
        ctypes.sizeof(hMods), 
        ctypes.byref(cbNeeded),
        0x03
    )
    
    count = cbNeeded.value // ctypes.sizeof(wintypes.HMODULE)
    for i in range(count):
        mod_name = ctypes.create_string_buffer(260)
        ctypes.windll.psapi.GetModuleBaseNameA(process_handle, hMods[i], mod_name, 260)
        if module_name.lower() in mod_name.value.decode('utf-8', errors='ignore').lower():
            return hMods[i]
    return None


def read_memory(process_handle, address, size):
    """Read memory from process"""
    buffer = ctypes.create_string_buffer(size)
    bytes_read = ctypes.c_size_t()
    ReadProcessMemory(process_handle, address, buffer, size, ctypes.byref(bytes_read))
    return buffer.raw[:bytes_read.value]


def find_function_rva(dll_path, func_name):
    """Find function RVA from DLL file"""
    with open(dll_path, 'rb') as f:
        data = f.read()
    
    # PE parsing (simplified)
    pe_offset = struct.unpack('<I', data[0x3C:0x40])[0]
    export_rva = struct.unpack('<I', data[pe_offset+120:pe_offset+124])[0]
    
    # Find section containing export
    num_sections = struct.unpack('<H', data[pe_offset+6:pe_offset+8])[0]
    opt_header_size = struct.unpack('<H', data[pe_offset+20:pe_offset+22])[0]
    sections_offset = pe_offset + 24 + opt_header_size
    
    sections = []
    for i in range(num_sections):
        sect_offset = sections_offset + i * 40
        vaddr = struct.unpack('<I', data[sect_offset+12:sect_offset+16])[0]
        vsize = struct.unpack('<I', data[sect_offset+8:sect_offset+12])[0]
        raw_addr = struct.unpack('<I', data[sect_offset+20:sect_offset+24])[0]
        sections.append((vaddr, vsize, raw_addr))
    
    def rva_to_offset(rva):
        for vaddr, vsize, raw_addr in sections:
            if vaddr <= rva < vaddr + vsize:
                return rva - vaddr + raw_addr
        return None
    
    # Parse export directory
    export_offset = rva_to_offset(export_rva)
    num_names = struct.unpack('<I', data[export_offset+24:export_offset+28])[0]
    name_table_rva = struct.unpack('<I', data[export_offset+32:export_offset+36])[0]
    ordinal_table_rva = struct.unpack('<I', data[export_offset+36:export_offset+40])[0]
    addr_table_rva = struct.unpack('<I', data[export_offset+28:export_offset+32])[0]
    
    name_table_offset = rva_to_offset(name_table_rva)
    
    for i in range(num_names):
        name_ptr_offset = name_table_offset + i * 4
        name_rva = struct.unpack('<I', data[name_ptr_offset:name_ptr_offset+4])[0]
        name_offset = rva_to_offset(name_rva)
        
        end = data.find(b'\x00', name_offset)
        name = data[name_offset:end].decode('utf-8', errors='ignore')
        
        if name == func_name:
            ordinal_offset = rva_to_offset(ordinal_table_rva) + i * 2
            ordinal = struct.unpack('<H', data[ordinal_offset:ordinal_offset+2])[0]
            
            addr_offset = rva_to_offset(addr_table_rva) + ordinal * 4
            func_rva = struct.unpack('<I', data[addr_offset:addr_offset+4])[0]
            
            return func_rva, rva_to_offset(func_rva)
    
    return None, None


def disassemble_bytes(data, start_addr):
    """Simple x86 disassembly to understand function prologue"""
    print(f"\nFunction bytes at 0x{start_addr:08X}:")
    print("-" * 60)
    
    # Common x86 patterns
    i = 0
    while i < min(64, len(data)):
        byte = data[i]
        
        # push ebp (0x55)
        if byte == 0x55:
            print(f"  {i:04X}: 55          push ebp")
            i += 1
        # mov ebp, esp (0x8B 0xEC or 0x89 0xE5)
        elif byte == 0x8B and i+1 < len(data) and data[i+1] == 0xEC:
            print(f"  {i:04X}: 8B EC       mov ebp, esp")
            i += 2
        elif byte == 0x89 and i+1 < len(data) and data[i+1] == 0xE5:
            print(f"  {i:04X}: 89 E5       mov ebp, esp")
            i += 2
        # sub esp, imm8 (0x83 0xEC)
        elif byte == 0x83 and i+1 < len(data) and data[i+1] == 0xEC:
            val = data[i+2]
            print(f"  {i:04X}: 83 EC {val:02X}    sub esp, 0x{val:02X}")
            i += 3
        # sub esp, imm32 (0x81 0xEC)
        elif byte == 0x81 and i+1 < len(data) and data[i+1] == 0xEC:
            val = struct.unpack('<I', data[i+2:i+6])[0]
            print(f"  {i:04X}: 81 EC {val:08X} sub esp, 0x{val:X}")
            i += 6
        # push imm8 (0x6A)
        elif byte == 0x6A:
            val = data[i+1]
            print(f"  {i:04X}: 6A {val:02X}       push 0x{val:02X}")
            i += 2
        # push imm32 (0x68)
        elif byte == 0x68:
            val = struct.unpack('<I', data[i+1:i+5])[0]
            print(f"  {i:04X}: 68 {val:08X} push 0x{val:08X}")
            i += 5
        # push reg (0x50-0x57)
        elif 0x50 <= byte <= 0x57:
            regs = ['eax', 'ecx', 'edx', 'ebx', 'esp', 'ebp', 'esi', 'edi']
            print(f"  {i:04X}: {byte:02X}          push {regs[byte-0x50]}")
            i += 1
        # mov reg, [ebp+X] (0x8B)
        elif byte == 0x8B:
            modrm = data[i+1] if i+1 < len(data) else 0
            print(f"  {i:04X}: 8B {modrm:02X} ...   mov (check params)")
            i += 2
        # cmp (0x83 0x7D or 0x39 etc)
        elif byte == 0x83 and i+1 < len(data) and data[i+1] == 0x7D:
            offset = data[i+2]
            val = data[i+3]
            print(f"  {i:04X}: 83 7D {offset:02X} {val:02X} cmp [ebp+0x{offset:02X}], 0x{val:02X}")
            i += 4
        # ret (0xC3)
        elif byte == 0xC3:
            print(f"  {i:04X}: C3          ret")
            i += 1
        # retn imm16 (0xC2)
        elif byte == 0xC2:
            val = struct.unpack('<H', data[i+1:i+3])[0]
            print(f"  {i:04X}: C2 {val:04X}     ret 0x{val:X}  (stdcall: {val//4} params)")
            i += 3
        else:
            print(f"  {i:04X}: {byte:02X}          ???")
            i += 1
    
    print()


def main():
    print("=" * 60)
    print("SDK Function Analysis")
    print("=" * 60)
    
    SDK_DLL = r"d:\carecam\QianXin\sdk_client.dll"
    FUNC_NAME = "ZJ_SetPeerMicPhoneStatus"
    
    # Find function in file first
    func_rva, func_offset = find_function_rva(SDK_DLL, FUNC_NAME)
    
    if func_rva:
        print(f"\n{FUNC_NAME}:")
        print(f"  RVA: 0x{func_rva:08X}")
        print(f"  File offset: 0x{func_offset:08X}")
        
        # Read function bytes from file
        with open(SDK_DLL, 'rb') as f:
            f.seek(func_offset)
            func_bytes = f.read(128)
        
        disassemble_bytes(func_bytes, func_rva)
        
        # Look for ret instruction to determine calling convention
        print("Analyzing calling convention...")
        for i in range(len(func_bytes) - 2):
            if func_bytes[i] == 0xC2:  # ret imm16
                stack_size = struct.unpack('<H', func_bytes[i+1:i+3])[0]
                param_count = stack_size // 4
                print(f"  Found stdcall return: ret {stack_size} ({param_count} parameters)")
                break
            elif func_bytes[i] == 0xC3:  # simple ret (cdecl)
                print(f"  Found cdecl return at +0x{i:X}")
                break
    else:
        print(f"Function {FUNC_NAME} not found")
    
    # Also check in running process
    print("\n" + "=" * 60)
    print("Checking running process...")
    print("=" * 60)
    
    pid = find_qianxin_pid()
    if pid:
        print(f"Found QianXin.exe (PID: {pid})")
        
        handle = OpenProcess(PROCESS_ALL_ACCESS, False, pid)
        if handle:
            sdk_base = find_module_base(handle, "sdk_client.dll")
            if sdk_base:
                func_addr = sdk_base + func_rva
                print(f"Function in memory: 0x{func_addr:08X}")
                
                # Read function from memory
                mem_bytes = read_memory(handle, func_addr, 128)
                if mem_bytes:
                    print("\nFunction bytes from memory:")
                    disassemble_bytes(mem_bytes, func_addr)
            
            CloseHandle(handle)
    else:
        print("QianXin.exe not running")


if __name__ == "__main__":
    main()
