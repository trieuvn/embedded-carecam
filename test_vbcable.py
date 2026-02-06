"""Test VB-Cable detection"""
import pyaudio

p = pyaudio.PyAudio()
print("VB-Cable Audio Devices:")
print("-" * 40)

for i in range(p.get_device_count()):
    info = p.get_device_info_by_index(i)
    name = info['name']
    if 'cable' in name.lower():
        print(f"[{i}] {name}")
        print(f"    Input channels: {info['maxInputChannels']}")
        print(f"    Output channels: {info['maxOutputChannels']}")
        print()

p.terminate()
