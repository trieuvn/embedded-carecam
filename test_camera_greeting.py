"""Test phát âm thanh qua VB-Cable đến camera"""
import asyncio
import tempfile
import os

# Find CABLE Input device index
import pyaudio
p = pyaudio.PyAudio()
cable_input_idx = None

for i in range(p.get_device_count()):
    info = p.get_device_info_by_index(i)
    if 'cable input' in info['name'].lower() and info['maxOutputChannels'] > 0:
        cable_input_idx = i
        print(f"✅ Found CABLE Input: [{i}] {info['name']}")
        break

if cable_input_idx is None:
    print("❌ CABLE Input không tìm thấy!")
    exit(1)

# Generate TTS
print("\n🔊 Generating TTS: 'Xin chào! Tớ đã kết nối với camera.'")
import edge_tts

async def generate_tts():
    communicate = edge_tts.Communicate("Xin chào! Tớ đã kết nối với camera.", "vi-VN-HoaiMyNeural")
    await communicate.save("test_greeting.mp3")

asyncio.run(generate_tts())

# Convert to WAV
from pydub import AudioSegment
audio = AudioSegment.from_mp3("test_greeting.mp3")
audio.export("test_greeting.wav", format="wav")

# Play to CABLE Input
import wave

wf = wave.open("test_greeting.wav", 'rb')
stream = p.open(
    format=p.get_format_from_width(wf.getsampwidth()),
    channels=wf.getnchannels(),
    rate=wf.getframerate(),
    output=True,
    output_device_index=cable_input_idx
)

print("📤 Đang phát qua VB-Cable → CareCam app → Camera speaker...")
print("   (Bạn cần mở app CareCam và giữ nút mic để nghe qua camera)")

data = wf.readframes(1024)
while data:
    stream.write(data)
    data = wf.readframes(1024)

stream.stop_stream()
stream.close()
wf.close()
p.terminate()

# Cleanup
os.remove("test_greeting.mp3")
os.remove("test_greeting.wav")

print("\n✅ Hoàn thành! Nếu app CareCam đang giữ nút mic, camera sẽ phát 'Xin chào!'")
