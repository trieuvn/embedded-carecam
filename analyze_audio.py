"""
Alternative approach: Hook into audio stream functions
Instead of trying to enable mic button, we can:
1. Use ZJ_PushAudioStream to send audio directly to camera
2. Or use ZJ_WriteAudioFrame to write audio frames

This script analyzes the audio-related exports
"""

import struct

SDK_DLL_PATH = r"d:\carecam\QianXin\sdk_client.dll"

def find_audio_exports():
    """Parse PE exports and analyze audio-related functions"""
    
    with open(SDK_DLL_PATH, 'rb') as f:
        data = f.read()
    
    # Find all audio-related function names
    audio_funcs = []
    
    # Simple string search for export names
    keywords = [b'Audio', b'Stream', b'Push', b'Write', b'Mic', b'Talk', b'Voice']
    
    for kw in keywords:
        idx = 0
        while True:
            pos = data.find(kw, idx)
            if pos == -1:
                break
            
            # Check if this looks like a function name (preceded by ZJ_)
            if pos >= 3 and data[pos-3:pos] == b'ZJ_':
                # Find end of name
                end = data.find(b'\x00', pos-3)
                name = data[pos-3:end].decode('utf-8', errors='ignore')
                if name not in audio_funcs:
                    audio_funcs.append(name)
            
            idx = pos + 1
    
    return audio_funcs


def analyze_pushAudioStream():
    """
    ZJ_PushAudioStream likely signature:
    int ZJ_PushAudioStream(const char* deviceId, ...)
    
    Looking at similar functions to understand parameters
    """
    print("\nAnalyzing ZJ_PushAudioStream likely parameters:")
    print("-" * 50)
    
    # Based on SDK patterns:
    print("""
    Common SDK patterns suggest:
    
    For ZJ_PushAudioStream:
        int ZJ_PushAudioStream(
            const char* szDeviceId,    // Camera device ID
            int nFormat,               // Audio format (PCM, AAC, etc.)
            int nSampleRate,           // e.g., 8000, 16000
            int nChannels,             // 1 = mono, 2 = stereo
            int nBitsPerSample         // e.g., 16
        )
    
    For ZJ_WriteAudioFrame:
        int ZJ_WriteAudioFrame(
            const char* szDeviceId,    // Camera device ID
            const void* pData,         // Audio data buffer
            int nDataLen               // Data length in bytes
        )
    
    For ZJ_StopPushAudioStream:
        int ZJ_StopPushAudioStream(
            const char* szDeviceId     // Camera device ID
        )
    """)
    
    # The key is finding the deviceId
    print("\nTo get deviceId, we need to:")
    print("1. Read it from app memory")
    print("2. Or hook a function that receives it")
    print("3. Or look in config files")


def search_for_device_id_in_files():
    """Look for device ID in QianXin config files"""
    import os
    import glob
    
    qianxin_dir = r"d:\carecam\QianXin"
    
    print("\nSearching for device ID in config files...")
    print("-" * 50)
    
    config_patterns = ["*.ini", "*.cfg", "*.conf", "*.json", "*.xml", "*.dat"]
    
    for pattern in config_patterns:
        for filepath in glob.glob(os.path.join(qianxin_dir, "**", pattern), recursive=True):
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                # Look for device ID patterns
                if 'deviceid' in content.lower() or 'device_id' in content.lower():
                    print(f"\n  Found in: {filepath}")
                    # Show relevant lines
                    for line in content.split('\n'):
                        if 'device' in line.lower():
                            print(f"    {line[:100]}")
            except:
                pass


if __name__ == "__main__":
    print("=" * 60)
    print("Audio Function Analysis")
    print("=" * 60)
    
    funcs = find_audio_exports()
    print("\nAudio-related exports found:")
    for f in sorted(funcs):
        print(f"  - {f}")
    
    analyze_pushAudioStream()
    search_for_device_id_in_files()
