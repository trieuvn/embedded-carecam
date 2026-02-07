"""
Analyze ZJ_SetPeerMicPhoneStatus function signature
by looking at how it's called in the app
"""

import struct

SDK_DLL_PATH = r"d:\carecam\QianXin\sdk_client.dll"

def analyze_function_calls():
    """Look for strings near the function to understand its usage"""
    
    with open(SDK_DLL_PATH, 'rb') as f:
        data = f.read()
    
    # Find the function name
    func_name = b"ZJ_SetPeerMicPhoneStatus"
    pos = data.find(func_name)
    
    if pos == -1:
        print("Function name not found")
        return
    
    print(f"Found function name at offset: 0x{pos:X}")
    
    # Look for related strings nearby
    print("\n🔍 Looking for related strings...")
    
    related = [
        b"SetPeerMicPhoneStatus",
        b"micphone",
        b"MicPhone",
        b"peer",
        b"Peer",
        b"deviceId",
        b"DeviceId",
        b"status",
        b"Status",
    ]
    
    for pattern in related:
        idx = 0
        while True:
            pos = data.find(pattern, idx)
            if pos == -1:
                break
            
            # Get context around the match
            start = max(0, pos - 50)
            end = min(len(data), pos + len(pattern) + 100)
            context = data[start:end]
            
            # Clean up for display
            display = b""
            for b in context:
                if 32 <= b < 127:
                    display += bytes([b])
                else:
                    display += b"."
            
            print(f"\n  0x{pos:X}: {display.decode('utf-8', errors='ignore')}")
            
            idx = pos + 1
            
            # Only show first 3 matches per pattern
            if idx - data.find(pattern, 0) > len(pattern) * 3:
                break


def look_for_function_signature():
    """Try to find function prototype in debug info or strings"""
    
    with open(SDK_DLL_PATH, 'rb') as f:
        data = f.read()
    
    # Common patterns in Chinese SDK
    patterns = [
        b"ZJ_SetPeerMicPhoneStatus",
        b"pstDeviceInfo",
        b"deviceId",
        b"szDeviceId", 
        b"nStatus",
        b"iStatus",
        b"bEnable",
        b"iMicPhone",
    ]
    
    print("\n" + "=" * 60)
    print("Looking for parameter hints...")
    print("=" * 60)
    
    for p in patterns:
        pos = data.find(p)
        if pos != -1:
            # Get null-terminated string
            end = data.find(b'\x00', pos)
            s = data[pos:end].decode('utf-8', errors='ignore')
            print(f"  Found: '{s}' at 0x{pos:X}")


def disassemble_function_start():
    """
    Look at the raw bytes near the function to understand calling convention
    """
    with open(SDK_DLL_PATH, 'rb') as f:
        data = f.read()
    
    # Find ZJ_SetPeerMicPhoneStatus in export table and get its code
    # This is a simplified version - would need full PE parsing
    
    print("\n" + "=" * 60)
    print("Function bytes analysis")
    print("=" * 60)
    
    # Look for common function prologs: push ebp; mov ebp, esp
    prolog_pattern = b"\x55\x8B\xEC"  # push ebp; mov ebp, esp
    
    # We found the function at 0x58EB1260 in process
    # The base address in process was 0x58E80000
    # So the RVA is 0x31260
    
    # Just show some common patterns used to detect number of params
    print("Based on SDK conventions, likely signatures:")
    print("  int ZJ_SetPeerMicPhoneStatus(const char* deviceId, int status)")
    print("  int ZJ_SetPeerMicPhoneStatus(void* handle, const char* deviceId, int status)")
    print("  int ZJ_SetPeerMicPhoneStatus(int sessionId, int status)")


if __name__ == "__main__":
    print("=" * 60)
    print("🔍 Analyzing ZJ_SetPeerMicPhoneStatus signature")
    print("=" * 60)
    
    analyze_function_calls()
    look_for_function_signature()
    disassemble_function_start()
