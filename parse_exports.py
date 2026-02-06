"""Parse PE export table to find actual exported functions"""
import struct

SDK_DLL_PATH = r"d:\carecam\QianXin\sdk_client.dll"

def parse_pe_exports(filepath):
    with open(filepath, 'rb') as f:
        data = f.read()
    
    # DOS header
    if data[:2] != b'MZ':
        print("Not a valid PE file")
        return []
    
    # PE offset
    pe_offset = struct.unpack('<I', data[0x3C:0x40])[0]
    
    # PE signature
    if data[pe_offset:pe_offset+4] != b'PE\x00\x00':
        print("Invalid PE signature")
        return []
    
    # COFF header
    coff_header = pe_offset + 4
    num_sections = struct.unpack('<H', data[coff_header+2:coff_header+4])[0]
    opt_header_size = struct.unpack('<H', data[coff_header+16:coff_header+18])[0]
    
    # Optional header
    opt_header = coff_header + 20
    magic = struct.unpack('<H', data[opt_header:opt_header+2])[0]
    
    # Data directories
    if magic == 0x10b:  # PE32
        data_dir_offset = opt_header + 96
    else:  # PE32+
        data_dir_offset = opt_header + 112
    
    export_rva = struct.unpack('<I', data[data_dir_offset:data_dir_offset+4])[0]
    export_size = struct.unpack('<I', data[data_dir_offset+4:data_dir_offset+8])[0]
    
    if export_rva == 0:
        print("No export table")
        return []
    
    # Section headers
    sections_offset = opt_header + opt_header_size
    sections = []
    for i in range(num_sections):
        sect_offset = sections_offset + i * 40
        name = data[sect_offset:sect_offset+8].rstrip(b'\x00').decode('utf-8', errors='ignore')
        virtual_size = struct.unpack('<I', data[sect_offset+8:sect_offset+12])[0]
        virtual_addr = struct.unpack('<I', data[sect_offset+12:sect_offset+16])[0]
        raw_size = struct.unpack('<I', data[sect_offset+16:sect_offset+20])[0]
        raw_addr = struct.unpack('<I', data[sect_offset+20:sect_offset+24])[0]
        sections.append({
            'name': name,
            'virtual_addr': virtual_addr,
            'virtual_size': virtual_size,
            'raw_addr': raw_addr,
            'raw_size': raw_size
        })
    
    # Convert RVA to file offset
    def rva_to_offset(rva):
        for s in sections:
            if s['virtual_addr'] <= rva < s['virtual_addr'] + s['virtual_size']:
                return rva - s['virtual_addr'] + s['raw_addr']
        return None
    
    # Parse export directory
    export_offset = rva_to_offset(export_rva)
    if export_offset is None:
        print("Could not find export section")
        return []
    
    # Export directory table
    name_rva = struct.unpack('<I', data[export_offset+12:export_offset+16])[0]
    num_functions = struct.unpack('<I', data[export_offset+20:export_offset+24])[0]
    num_names = struct.unpack('<I', data[export_offset+24:export_offset+28])[0]
    addr_table_rva = struct.unpack('<I', data[export_offset+28:export_offset+32])[0]
    name_table_rva = struct.unpack('<I', data[export_offset+32:export_offset+36])[0]
    ordinal_table_rva = struct.unpack('<I', data[export_offset+36:export_offset+40])[0]
    
    print(f"DLL Name RVA: 0x{name_rva:X}")
    print(f"Number of functions: {num_functions}")
    print(f"Number of names: {num_names}")
    
    # Get function names
    exports = []
    name_table_offset = rva_to_offset(name_table_rva)
    
    for i in range(num_names):
        name_ptr_offset = name_table_offset + i * 4
        name_rva = struct.unpack('<I', data[name_ptr_offset:name_ptr_offset+4])[0]
        name_offset = rva_to_offset(name_rva)
        
        # Read null-terminated string
        end = data.find(b'\x00', name_offset)
        name = data[name_offset:end].decode('utf-8', errors='ignore')
        exports.append(name)
    
    return exports


if __name__ == "__main__":
    print("=" * 60)
    print(f"Parsing exports from: {SDK_DLL_PATH}")
    print("=" * 60)
    
    exports = parse_pe_exports(SDK_DLL_PATH)
    
    print(f"\nFound {len(exports)} exported functions:")
    print("-" * 60)
    
    for i, name in enumerate(exports):
        print(f"  [{i:3d}] {name}")
    
    # Look for mic/audio related
    print("\n" + "=" * 60)
    print("Audio/Mic related exports:")
    print("-" * 60)
    for name in exports:
        lower = name.lower()
        if any(k in lower for k in ['mic', 'audio', 'talk', 'speak', 'voice']):
            print(f"  ⭐ {name}")
