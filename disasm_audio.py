"""
Disassemble ZJ_PushAudioStream to find correct signature
"""
import struct

SDK_DLL = r"d:\carecam\QianXin\sdk_client.dll"

def find_func_offset(data, func_name):
    """Find function RVA and file offset from PE exports"""
    pe_offset = struct.unpack('<I', data[0x3C:0x40])[0]
    export_rva = struct.unpack('<I', data[pe_offset+120:pe_offset+124])[0]
    
    num_sections = struct.unpack('<H', data[pe_offset+6:pe_offset+8])[0]
    opt_header_size = struct.unpack('<H', data[pe_offset+20:pe_offset+22])[0]
    sections_offset = pe_offset + 24 + opt_header_size
    
    sections = []
    for i in range(num_sections):
        so = sections_offset + i * 40
        vaddr = struct.unpack('<I', data[so+12:so+16])[0]
        vsize = struct.unpack('<I', data[so+8:so+12])[0]
        raw_addr = struct.unpack('<I', data[so+20:so+24])[0]
        sections.append((vaddr, vsize, raw_addr))
    
    def rva_to_offset(rva):
        for va, vs, ra in sections:
            if va <= rva < va + vs:
                return rva - va + ra
        return None
    
    export_offset = rva_to_offset(export_rva)
    num_names = struct.unpack('<I', data[export_offset+24:export_offset+28])[0]
    name_table_rva = struct.unpack('<I', data[export_offset+32:export_offset+36])[0]
    ord_table_rva = struct.unpack('<I', data[export_offset+36:export_offset+40])[0]
    addr_table_rva = struct.unpack('<I', data[export_offset+28:export_offset+32])[0]
    
    name_table_offset = rva_to_offset(name_table_rva)
    
    for i in range(num_names):
        np_off = name_table_offset + i * 4
        name_rva = struct.unpack('<I', data[np_off:np_off+4])[0]
        name_offset = rva_to_offset(name_rva)
        end = data.find(b'\x00', name_offset)
        name = data[name_offset:end].decode('utf-8', errors='ignore')
        
        if name == func_name:
            ord_off = rva_to_offset(ord_table_rva) + i * 2
            ordinal = struct.unpack('<H', data[ord_off:ord_off+2])[0]
            addr_off = rva_to_offset(addr_table_rva) + ordinal * 4
            func_rva = struct.unpack('<I', data[addr_off:addr_off+4])[0]
            return func_rva, rva_to_offset(func_rva)
    
    return None, None


def disasm_simple(data, start_addr, size=64):
    """Simple x86 disassembler showing raw bytes and basic interpretation"""
    print(f"\nBytes at 0x{start_addr:08X}:")
    
    i = 0
    while i < min(size, len(data)):
        # Show raw bytes (16 per line)
        line_bytes = data[i:min(i+16, len(data))]
        hex_str = ' '.join(f'{b:02X}' for b in line_bytes)
        
        # Try to interpret
        b = data[i]
        
        if b == 0x55:
            interp = "push ebp"
        elif b == 0x8B and i+1 < len(data):
            modrm = data[i+1]
            if modrm == 0xEC:
                interp = "mov ebp, esp"
            elif modrm >= 0x44 and modrm <= 0x4C:
                interp = f"mov reg, [esp+X]"
            else:
                interp = f"mov ..."
        elif 0x50 <= b <= 0x57:
            regs = ['eax', 'ecx', 'edx', 'ebx', 'esp', 'ebp', 'esi', 'edi']
            interp = f"push {regs[b-0x50]}"
        elif b == 0xE8:
            interp = "call rel32"
        elif b == 0xE9:
            interp = "jmp rel32"
        elif b == 0xC3:
            interp = "ret"
        elif b == 0xC2:
            if i+2 < len(data):
                imm = struct.unpack('<H', data[i+1:i+3])[0]
                interp = f"ret {imm} (stdcall, {imm//4} params)"
            else:
                interp = "ret N"
        elif b == 0x83:
            interp = "cmp/add/sub ..."
        elif b == 0x6A:
            interp = f"push imm8"
        elif b == 0x68:
            interp = "push imm32"
        else:
            interp = ""
        
        print(f"  {i:04X}: {hex_str:<48}  {interp}")
        i += 16
    
    # Look for ret instruction
    for j in range(len(data)):
        if data[j] == 0xC3:
            print(f"\n  ret (cdecl) found at offset +0x{j:X}")
            break
        elif data[j] == 0xC2 and j+2 < len(data):
            imm = struct.unpack('<H', data[j+1:j+3])[0]
            print(f"\n  ret {imm} (stdcall, {imm//4} params) found at offset +0x{j:X}")
            break


def main():
    with open(SDK_DLL, 'rb') as f:
        data = f.read()
    
    funcs = [
        "ZJ_PushAudioStream",
        "ZJ_WriteAudioFrame",
        "ZJ_StopPushAudioStream",
    ]
    
    for func_name in funcs:
        print("=" * 70)
        print(f"Analyzing: {func_name}")
        print("=" * 70)
        
        rva, offset = find_func_offset(data, func_name)
        if rva and offset:
            print(f"RVA: 0x{rva:08X}, File offset: 0x{offset:08X}")
            func_bytes = data[offset:offset+128]
            disasm_simple(func_bytes, rva, 64)
        else:
            print("NOT FOUND")
        print()


if __name__ == "__main__":
    main()
