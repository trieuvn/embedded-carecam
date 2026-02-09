"""
Analyze QianXin.exe to find mutual exclusion logic between mic and speaker
"""
import struct
import os
import subprocess

QIANXIN_EXE = r"d:\carecam\QianXin\QianXin.exe"

def extract_strings(filepath, min_length=6):
    """Extract ASCII and Unicode strings from binary file"""
    with open(filepath, 'rb') as f:
        data = f.read()
    
    # Find ASCII strings
    current = []
    strings = []
    
    for byte in data:
        if 32 <= byte < 127:  # Printable ASCII
            current.append(chr(byte))
        else:
            if len(current) >= min_length:
                strings.append(''.join(current))
            current = []
    
    if len(current) >= min_length:
        strings.append(''.join(current))
    
    return strings


def find_interesting_strings(strings):
    """Find strings related to mic/speaker/audio"""
    keywords = ['mic', 'speaker', 'audio', 'sound', 'talk', 'voice', 'intercom', 
                'mute', 'unmute', 'enable', 'disable', 'status', 'switch']
    
    found = {}
    for s in strings:
        lower = s.lower()
        for kw in keywords:
            if kw in lower and len(s) < 100:
                if kw not in found:
                    found[kw] = []
                if s not in found[kw]:
                    found[kw].append(s)
    
    return found


def analyze_imports(filepath):
    """Analyze imported functions from DLLs"""
    with open(filepath, 'rb') as f:
        data = f.read()
    
    # Check PE signature
    if data[:2] != b'MZ':
        return None
    
    pe_offset = struct.unpack('<I', data[0x3C:0x40])[0]
    if data[pe_offset:pe_offset+4] != b'PE\x00\x00':
        return None
    
    # Get import directory
    opt_header = pe_offset + 24
    import_rva = struct.unpack('<I', data[opt_header + 104:opt_header + 108])[0]
    
    if import_rva == 0:
        return []
    
    # Parse sections to convert RVA to offset
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
    
    # Parse import directory
    imports = []
    import_offset = rva_to_offset(import_rva)
    if import_offset is None:
        return []
    
    i = 0
    while True:
        entry_offset = import_offset + i * 20
        if entry_offset + 20 > len(data):
            break
        
        name_rva = struct.unpack('<I', data[entry_offset + 12:entry_offset + 16])[0]
        if name_rva == 0:
            break
        
        name_offset = rva_to_offset(name_rva)
        if name_offset:
            end = data.find(b'\x00', name_offset)
            dll_name = data[name_offset:end].decode('utf-8', errors='ignore')
            imports.append(dll_name)
        
        i += 1
    
    return imports


def find_sdk_calls_in_exe():
    """Look for SDK function calls pattern in EXE"""
    with open(QIANXIN_EXE, 'rb') as f:
        data = f.read()
    
    # Look for references to function names
    sdk_funcs = [
        b'ZJ_SetPeerMicPhoneStatus',
        b'ZJ_PushAudioStream',
        b'ZJ_StopPushAudioStream',
        b'SetMicStatus',
        b'SetSpeakerStatus',
    ]
    
    found_refs = {}
    for func in sdk_funcs:
        idx = data.find(func)
        if idx != -1:
            found_refs[func.decode()] = hex(idx)
    
    return found_refs


def main():
    print("=" * 70)
    print("QianXin.exe Analysis - Finding Mic/Speaker Mutual Exclusion")
    print("=" * 70)
    
    if not os.path.exists(QIANXIN_EXE):
        print(f"File not found: {QIANXIN_EXE}")
        return
    
    file_size = os.path.getsize(QIANXIN_EXE)
    print(f"File size: {file_size:,} bytes")
    
    # Extract strings
    print("\n[1] Extracting strings...")
    all_strings = extract_strings(QIANXIN_EXE)
    print(f"    Total strings found: {len(all_strings)}")
    
    # Find interesting strings
    found = find_interesting_strings(all_strings)
    print("\n[2] Interesting strings by keyword:")
    for kw, strings in sorted(found.items()):
        print(f"\n    [{kw}]:")
        for s in strings[:10]:  # Limit to 10 per keyword
            print(f"      - {s}")
    
    # Analyze imports
    print("\n[3] Imported DLLs:")
    imports = analyze_imports(QIANXIN_EXE)
    if imports:
        for dll in imports:
            print(f"    - {dll}")
    
    # Find SDK function references
    print("\n[4] SDK function references in EXE:")
    refs = find_sdk_calls_in_exe()
    if refs:
        for func, offset in refs.items():
            print(f"    - {func} at {offset}")
    else:
        print("    No direct references found (likely dynamic loading)")
    
    print("\n" + "=" * 70)
    print("Analysis complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
