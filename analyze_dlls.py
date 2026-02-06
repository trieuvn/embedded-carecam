"""Analyze QianXin DLLs for audio/mic related functions"""
import os

def find_strings_in_binary(filepath, min_len=5):
    """Extract ASCII strings from binary file"""
    with open(filepath, 'rb') as f:
        data = f.read()
    
    strings = []
    current = []
    
    for byte in data:
        if 32 <= byte < 127:
            current.append(chr(byte))
        else:
            if len(current) >= min_len:
                strings.append(''.join(current))
            current = []
    
    return strings

# Keywords related to audio/mic control
keywords = ['audio', 'mic', 'talk', 'speak', 'voice', 'start', 'stop', 
            'open', 'close', 'send', 'recv', 'stream', 'play', 'record']

dlls = [
    r'd:\carecam\QianXin\sdk_client.dll',
    r'd:\carecam\QianXin\itrd.dll',
    r'd:\carecam\QianXin\av_codec.dll',
]

for dll in dlls:
    if os.path.exists(dll):
        print(f"\n{'='*60}")
        print(f"Analyzing: {os.path.basename(dll)}")
        print('='*60)
        
        strings = find_strings_in_binary(dll, min_len=6)
        
        # Find matches
        matches = []
        for s in strings:
            lower = s.lower()
            for kw in keywords:
                if kw in lower:
                    matches.append(s)
                    break
        
        # Unique matches
        unique = list(set(matches))
        unique.sort()
        
        print(f"Found {len(unique)} matches:")
        for m in unique[:30]:
            print(f"  - {m}")
