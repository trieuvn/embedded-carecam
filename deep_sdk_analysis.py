"""
Deep SDK Analysis - Find all talkback/intercom related functions
"""
import struct

SDK_DLL = r"d:\carecam\QianXin\sdk_client.dll"


def parse_all_exports(filepath):
    """Parse all exported functions from DLL"""
    with open(filepath, 'rb') as f:
        data = f.read()
    
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
    
    exports = []
    name_table_offset = rva_to_offset(name_table_rva)
    
    for i in range(num_names):
        np_off = name_table_offset + i * 4
        name_rva = struct.unpack('<I', data[np_off:np_off+4])[0]
        name_offset = rva_to_offset(name_rva)
        end = data.find(b'\x00', name_offset)
        name = data[name_offset:end].decode('utf-8', errors='ignore')
        exports.append(name)
    
    return exports


def categorize_functions(exports):
    """Categorize functions by purpose"""
    categories = {
        'Audio/Mic/Talk': [],
        'Stream/Push': [],
        'Device Control': [],
        'Session/Init': [],
        'Callback': [],
    }
    
    for name in exports:
        lower = name.lower()
        
        if any(k in lower for k in ['audio', 'mic', 'talk', 'voice', 'speak', 'sound']):
            categories['Audio/Mic/Talk'].append(name)
        elif any(k in lower for k in ['stream', 'push', 'write', 'play']):
            categories['Stream/Push'].append(name)
        elif any(k in lower for k in ['setpeer', 'device', 'cam']):
            categories['Device Control'].append(name)
        elif any(k in lower for k in ['init', 'start', 'stop', 'login', 'session']):
            categories['Session/Init'].append(name)
        elif 'cb' in lower or 'callback' in lower or 'func' in lower:
            categories['Callback'].append(name)
    
    return categories


def main():
    print("=" * 70)
    print("SDK Deep Analysis - Finding Talkback Functions")
    print("=" * 70)
    
    exports = parse_all_exports(SDK_DLL)
    print(f"\nTotal exports: {len(exports)}")
    
    categories = categorize_functions(exports)
    
    for cat, funcs in categories.items():
        if funcs:
            print(f"\n{'=' * 50}")
            print(f"{cat} ({len(funcs)} functions):")
            print('=' * 50)
            for f in sorted(funcs):
                print(f"  - {f}")
    
    # Special focus on Push/Stream functions - these likely control talkback
    print("\n" + "=" * 70)
    print("KEY TALKBACK FUNCTIONS:")
    print("=" * 70)
    
    key_funcs = [
        'ZJ_PushAudioStream',       # Start audio stream to camera
        'ZJ_WriteAudioFrame',       # Send audio data
        'ZJ_StopPushAudioStream',   # Stop audio stream
        'ZJ_SetAudioParam',         # Set audio parameters
        'ZJ_SetAudioParameter',     # Alternative param setter
        'ZJ_SetPeerMicPhoneStatus', # Mic status (different from talkback?)
        'ZJ_PlayPeerSoundFile',     # Play sound to camera
        'ZJ_PushSoundFile',         # Push sound file
    ]
    
    print("\nFunctions to investigate:")
    for f in key_funcs:
        if f in exports:
            print(f"  [v] {f}")
        else:
            print(f"  [x] {f}")
    
    # Look for any function with "intercom" or "duplex" or "2way"
    print("\n\nSearching for intercom/duplex related...")
    for name in exports:
        lower = name.lower()
        if any(k in lower for k in ['intercom', 'duplex', '2way', 'twoway', 'bidirection']):
            print(f"  FOUND: {name}")


if __name__ == "__main__":
    main()
